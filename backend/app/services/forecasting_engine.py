"""Forecasting engine with model registry and ensemble capabilities."""

import asyncio
import datetime
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor

from app.services.forecasting_models.base_model import BaseModel
from app.services.forecasting_models.gbm_model import GBMModel
from app.services.forecasting_models.arima_model import ARIMAModel
from app.services.config_service import ConfigService
from app.services.logger_service import LoggerService


class ForecastingEngine:
    """
    Main forecasting engine that manages multiple forecasting models.

    Features:
    - Plugin architecture for easy model addition
    - Parallel model execution
    - Ensemble combination of results
    - Configuration-driven behavior
    """

    def __init__(self, history_service, logger: LoggerService, config_service: Optional[ConfigService] = None, storage_service=None):
        """
        Initialize forecasting engine.

        Args:
            history_service: Service for fetching historical price data
            logger: Service for logging
            config_service: Optional configuration service
            storage_service: Optional storage service for caching forecasts
        """
        self.history_service = history_service
        self.logger = logger
        self.config_service = config_service
        self.storage_service = storage_service
        self.models: Dict[str, BaseModel] = {}
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.cache_collection = "forecast_cache"

        # Register default models
        self._register_default_models()

        # Load configuration if available
        self.config = self._load_config()

    def _register_default_models(self):
        """Register the default forecasting models."""
        self.register_model("gbm", GBMModel())
        self.register_model("arima", ARIMAModel())

    def register_model(self, name: str, model: BaseModel):
        """
        Register a forecasting model.

        Args:
            name: Model name/identifier
            model: Model instance
        """
        self.models[name] = model

    def _load_config(self) -> Dict[str, Any]:
        """
        Load forecasting configuration from config service.

        Returns:
            Configuration dict
        """
        if self.config_service is None:
            return self._get_default_config()

        try:
            config = self.config_service.get_config("forecasting")
            return config if config else self._get_default_config()
        except Exception:
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "model_defaults": {
                "equity_indices": {
                    "primary": ["gbm", "arima"],
                    "ensemble_weights": [0.7, 0.3],
                },
                "fixed_income": {
                    "primary": ["gbm", "arima"],
                    "ensemble_weights": [0.6, 0.4],
                },
                "default": {
                    "primary": ["gbm"],
                    "ensemble_weights": [1.0],
                },
            },
            "performance": {
                "default_simulations": 1000,
                "max_parallel_models": 5,
            },
        }

    def _get_forecast_cache_ttl(self) -> int:
        """Get forecast cache TTL in hours (default 24h)."""
        if self.config_service:
            try:
                settings = self.config_service.get_data_settings()
                return settings.get("forecast_cache_ttl_hours", 24)
            except Exception:
                pass
        return 24

    def _generate_cache_key(
        self,
        tickers: List[str],
        horizon: str,
        models: List[str],
        simulations: int
    ) -> str:
        """Generate cache key for forecast parameters."""
        # Sort tickers for consistent key
        sorted_tickers = sorted(tickers)
        models_str = ",".join(sorted(models)) if models else "default"
        tickers_str = ",".join(sorted_tickers)
        return f"forecast_{tickers_str}_{horizon}_{models_str}_{simulations}"

    async def _get_cached_forecast(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached forecast if available and fresh."""
        if not self.storage_service:
            return None

        try:
            cached = await self.storage_service.get(self.cache_collection, cache_key)
            if not cached:
                return None

            # Check if cache is fresh
            created_at_str = cached.get("created_at")
            if created_at_str:
                try:
                    created_at = datetime.datetime.fromisoformat(created_at_str)
                    if created_at.tzinfo is None:
                        created_at = created_at.replace(tzinfo=datetime.timezone.utc)

                    ttl_hours = self._get_forecast_cache_ttl()
                    age = datetime.datetime.now(datetime.timezone.utc) - created_at

                    if age < datetime.timedelta(hours=ttl_hours):
                        self.logger.info(f"Using cached forecast for key: {cache_key}")
                        return cached.get("data")
                except (ValueError, TypeError):
                    pass

            return None
        except Exception:
            return None

    async def _save_forecast_cache(
        self,
        cache_key: str,
        data: Dict[str, Any]
    ) -> None:
        """Save forecast results to cache."""
        if not self.storage_service:
            return

        try:
            cache_entry = {
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "data": data
            }
            await self.storage_service.save(self.cache_collection, cache_key, cache_entry)
        except Exception:
            # Fail silently - caching is optional
            pass

    async def run_forecast_suite(
        self,
        tickers: List[str],
        horizon: str = "1y",
        models: Optional[List[str]] = None,
        simulations: int = 1000,
        scenarios: Optional[Dict[str, Dict[str, float]]] = None,
        model_params: Optional[Dict[str, Dict[str, Any]]] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Run a suite of forecasting models in parallel.

        Args:
            tickers: List of ticker symbols
            horizon: Forecast horizon ("1mo", "3mo", "6mo", "1y")
            models: List of model names to run (default: from config)
            simulations: Number of simulations for Monte Carlo
            scenarios: Optional scenario adjustments
            model_params: Optional dict of {model_name: {param: value}}
            use_cache: Whether to use cached forecasts (default: True)

        Returns:
            Dict with ensemble results and individual model outputs
        """
        # Determine which models to run
        if models is None:
            models = self._get_default_models(tickers)

        # Generate cache key (needed even if not using cache, for saving later)
        cache_key = self._generate_cache_key(tickers, horizon, models, simulations)

        # Check cache first
        if use_cache:
            cached_result = await self._get_cached_forecast(cache_key)
            if cached_result:
                return cached_result

        # Convert horizon to days
        horizon_days = self._horizon_to_days(horizon)

        # Fetch price history for all tickers
        price_history = await self._fetch_price_history(tickers)

        if not price_history:
            self.logger.error(f"No price history available for tickers: {tickers}")
            return {"error": "No price history available for tickers"}

        # Run models in parallel
        model_results = await self._run_models_parallel(
            models,
            tickers,
            horizon_days,
            price_history,
            simulations,
            scenarios,
            model_params
        )

        # Create ensemble
        self.logger.info(f"Creating ensemble forecast for {len(tickers)} tickers")
        ensemble = self._create_ensemble(
            model_results,
            tickers,
            models
        )

        result = {
            "ensemble": ensemble,
            "models": model_results,
            "horizon_days": horizon_days,
            "horizon_name": horizon,
            "tickers": tickers,
        }

        # Save to cache if enabled
        if use_cache:
            await self._save_forecast_cache(cache_key, result)

        return result

    async def run_specific_model(
        self,
        model_name: str,
        tickers: List[str],
        horizon_days: int,
        simulations: int = 1000,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run a specific forecasting model.

        Args:
            model_name: Name of model to run
            tickers: List of ticker symbols
            horizon_days: Forecast horizon in days
            simulations: Number of simulations (for Monte Carlo)
            params: Optional model-specific parameters

        Returns:
            Model forecast results
        """
        if model_name not in self.models:
            return {"error": f"Model '{model_name}' not registered"}

        model = self.models[model_name]
        price_history = await self._fetch_price_history(tickers)

        if params is None:
            params = {}

        return await model.forecast(
            tickers=tickers,
            horizon_days=horizon_days,
            price_history=price_history,
            simulations=simulations,
            **params
        )

    async def _run_models_parallel(
        self,
        models: List[str],
        tickers: List[str],
        horizon_days: int,
        price_history: Dict[str, Any],
        simulations: int,
        scenarios: Optional[Dict[str, Dict[str, float]]],
        model_params: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Run multiple models in parallel.

        Args:
            models: List of model names
            tickers: List of ticker symbols
            horizon_days: Forecast horizon
            price_history: Price history data
            simulations: Number of simulations
            scenarios: Scenario adjustments
            model_params: Model-specific parameters

        Returns:
            Dict of {model_name: {ticker: results}}
        """
        results = {}
        tasks = []

        for model_name in models:
            if model_name not in self.models:
                continue

            model = self.models[model_name]

            # Create async task for each model
            self.logger.debug(f"Starting model: {model_name} for {len(tickers)} tickers")
            task = self._run_model_async(
                model,
                model_name,
                tickers,
                horizon_days,
                price_history,
                simulations,
                scenarios,
                model_params.get(model_name) if model_params else None
            )
            tasks.append(task)

        # Wait for all models to complete
        model_outputs = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, output in enumerate(model_outputs):
            model_name = models[i]
            if isinstance(output, Exception):
                results[model_name] = {"error": str(output)}
            else:
                results[model_name] = output

        return results

    async def _run_model_async(
        self,
        model: BaseModel,
        model_name: str,
        tickers: List[str],
        horizon_days: int,
        price_history: Dict[str, Any],
        simulations: int,
        scenarios: Optional[Dict[str, Dict[str, float]]],
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run a single model in an async wrapper."""
        loop = asyncio.get_event_loop()

        # Run the synchronous forecast in executor
        return await loop.run_in_executor(
            self.executor,
            lambda: asyncio.run(model.forecast(
                tickers=tickers,
                horizon_days=horizon_days,
                price_history=price_history,
                simulations=simulations,
                scenarios=scenarios,
                **(params or {})
            ))
        )

    def _create_ensemble(
        self,
        model_results: Dict[str, Dict[str, Any]],
        tickers: List[str],
        models: List[str],
    ) -> Dict[str, Any]:
        """
        Create ensemble forecast from multiple models.

        Args:
            model_results: Results from each model
            tickers: List of ticker symbols
            models: List of model names

        Returns:
            Ensemble forecast results
        """
        ensemble = {}

        # Get weights from config
        weights = self._get_ensemble_weights(tickers, models)

        for ticker in tickers:
            ticker_ensemble = {
                "model": "ensemble",
                "constituent_models": [],
                "terminal": {},
                "return_metrics": {},
            }

            weighted_returns = []
            weighted_prices = []
            total_weight = 0.0

            for i, model_name in enumerate(models):
                if model_name not in model_results:
                    continue

                if ticker not in model_results[model_name]:
                    continue

                model_result = model_results[model_name][ticker]

                # Skip if model had an error
                if "error" in model_result:
                    continue

                weight = weights.get(model_name, 1.0 / len(models))

                # Get metrics
                if "return_metrics" in model_result:
                    ret = model_result["return_metrics"].get("mean_return", 0)
                    weighted_returns.append(ret * weight)

                if "terminal" in model_result:
                    price = model_result["terminal"].get("mean", 0)
                    weighted_prices.append(price * weight)

                ticker_ensemble["constituent_models"].append({
                    "name": model_name,
                    "weight": weight,
                    "return": model_result.get("return_metrics", {}).get("mean_return"),
                })

                total_weight += weight

            # Calculate ensemble metrics
            if weighted_returns:
                ensemble_return = sum(weighted_returns) / total_weight if total_weight > 0 else 0
                ticker_ensemble["return_metrics"]["mean_return"] = ensemble_return

            if weighted_prices:
                ensemble_price = sum(weighted_prices) / total_weight if total_weight > 0 else 0
                ticker_ensemble["terminal"]["mean"] = ensemble_price

            ensemble[ticker] = ticker_ensemble

        return ensemble

    def _get_ensemble_weights(
        self,
        tickers: List[str],
        models: List[str]
    ) -> Dict[str, float]:
        """Get ensemble weights from configuration."""
        # Simple equal weighting for now
        # Can be enhanced to use config-based weights
        return {model: 1.0 / len(models) for model in models}

    def _get_default_models(self, tickers: List[str]) -> List[str]:
        """Get default models based on ticker types."""
        # For now, return all available models
        # Can be enhanced to determine asset class
        return [name for name in self.models.keys()]

    def _horizon_to_days(self, horizon: str) -> int:
        """Convert horizon string to days."""
        mapping = {
            "1mo": 21,
            "3mo": 63,
            "6mo": 126,
            "1y": 252,
            "2y": 504,
        }

        horizon_lower = horizon.lower().replace(" ", "")
        return mapping.get(horizon_lower, 252)  # Default to 1 year

    async def _fetch_price_history(
        self,
        tickers: List[str],
        period: str = "2y"
    ) -> Dict[str, Any]:
        """
        Fetch price history for all tickers.

        Args:
            tickers: List of ticker symbols
            period: Historical period to fetch

        Returns:
            Dict of {ticker: DataFrame with OHLCV data}
        """
        history = {}

        for ticker in tickers:
            try:
                # Use history service to fetch data
                data = await self.history_service.get_history(ticker, period=period)
                if data is not None and not data.empty:
                    history[ticker] = data
            except Exception as e:
                self.logger.error(f"Failed to fetch history for {ticker}: {e}")
                pass

        return history

    def get_registered_models(self) -> List[str]:
        """Get list of registered model names."""
        return list(self.models.keys())

    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model."""
        if model_name not in self.models:
            return None
        return self.models[model_name].get_model_info()

    def extract_expected_returns(self, forecast_result: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract expected returns from forecast results for portfolio optimization.

        Args:
            forecast_result: Result from run_forecast_suite

        Returns:
            Dict of {ticker: expected_annual_return}
        """
        ensemble = forecast_result.get("ensemble", {})
        expected_returns = {}

        for ticker, ticker_forecast in ensemble.items():
            # Get return metrics from ensemble forecast
            return_metrics = ticker_forecast.get("return_metrics", {})
            expected_return = return_metrics.get("mean_return", 0.0)

            # If it's a short-term forecast (e.g., 3 months), annualize it
            horizon_days = forecast_result.get("horizon_days", 252)
            if horizon_days < 252:
                # Annualize the return: (1 + r)^(365/days) - 1
                expected_return = (1 + expected_return) ** (365 / horizon_days) - 1

            expected_returns[ticker] = expected_return

        return expected_returns
