"""Forecasting engine with model registry and ensemble capabilities."""

import asyncio
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor

from app.services.forecasting_models.base_model import BaseModel
from app.services.forecasting_models.gbm_model import GBMModel
from app.services.forecasting_models.arima_model import ARIMAModel
from app.services.config_service import ConfigService


class ForecastingEngine:
    """
    Main forecasting engine that manages multiple forecasting models.

    Features:
    - Plugin architecture for easy model addition
    - Parallel model execution
    - Ensemble combination of results
    - Configuration-driven behavior
    """

    def __init__(self, history_service, config_service: Optional[ConfigService] = None):
        """
        Initialize forecasting engine.

        Args:
            history_service: Service for fetching historical price data
            config_service: Optional configuration service
        """
        self.history_service = history_service
        self.config_service = config_service
        self.models: Dict[str, BaseModel] = {}
        self.executor = ThreadPoolExecutor(max_workers=5)

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

    async def run_forecast_suite(
        self,
        tickers: List[str],
        horizon: str = "1y",
        models: Optional[List[str]] = None,
        simulations: int = 1000,
        scenarios: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> Dict[str, Any]:
        """
        Run a suite of forecasting models in parallel.

        Args:
            tickers: List of ticker symbols
            horizon: Forecast horizon ("1mo", "3mo", "6mo", "1y")
            models: List of model names to run (default: from config)
            simulations: Number of simulations for Monte Carlo
            scenarios: Optional scenario adjustments

        Returns:
            Dict with ensemble results and individual model outputs
        """
        # Convert horizon to days
        horizon_days = self._horizon_to_days(horizon)

        # Determine which models to run
        if models is None:
            models = self._get_default_models(tickers)

        # Fetch price history for all tickers
        price_history = await self._fetch_price_history(tickers)

        if not price_history:
            return {"error": "No price history available for tickers"}

        # Run models in parallel
        model_results = await self._run_models_parallel(
            models,
            tickers,
            horizon_days,
            price_history,
            simulations,
            scenarios
        )

        # Create ensemble
        ensemble = self._create_ensemble(
            model_results,
            tickers,
            models
        )

        return {
            "ensemble": ensemble,
            "models": model_results,
            "horizon_days": horizon_days,
            "horizon_name": horizon,
            "tickers": tickers,
        }

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
            task = self._run_model_async(
                model,
                model_name,
                tickers,
                horizon_days,
                price_history,
                simulations,
                scenarios
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
                scenarios=scenarios
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
                if data and not data.empty:
                    history[ticker] = data
            except Exception as e:
                # Log error but continue with other tickers
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
