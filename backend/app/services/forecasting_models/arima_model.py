"""ARIMA forecasting model."""

import os
import numpy as np
import pandas as pd
import warnings

import json
import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

from scipy import stats
from .base_model import BaseModel

# Import statsmodels conditionally - will fail gracefully if not installed
try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.stattools import adfuller
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False


class ARIMAModel(BaseModel):
    """
    ARIMA (AutoRegressive Integrated Moving Average) forecasting model.

    Features:
    - Automatic parameter tuning using AIC
    - Stationarity testing
    - Forecast with confidence intervals
    - Handles different market regimes
    """

    def __init__(self):
        super().__init__("ARIMA")
        self.metadata.update({
            "description": "ARIMA time series forecasting",
            "best_for": ["short_term", "trend_detection", "mean_reverting"],
            "supports_scenarios": False,
            "max_horizon_days": 60,  # Best for short-term
            "requires_statsmodels": STATSMODELS_AVAILABLE,
        })

    async def forecast(
        self,
        tickers: List[str],
        horizon_days: int,
        price_history: Dict[str, pd.DataFrame],
        auto_tune: bool = True,
        p_range: Tuple[int, int] = (0, 5),
        d_range: Tuple[int, int] = (0, 2),
        q_range: Tuple[int, int] = (0, 5),
        confidence_level: float = 0.95,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run ARIMA forecast.

        Args:
            tickers: List of ticker symbols
            horizon_days: Forecast horizon in days
            price_history: Dict of {ticker: DataFrame with OHLCV data}
            auto_tune: Whether to auto-tune (p,d,q) parameters
            p_range: Range for AR parameter to search
            d_range: Range for differencing parameter to search
            q_range: Range for MA parameter to search
            confidence_level: Confidence level for intervals
            **kwargs: Additional parameters

        Returns:
            Dict of {ticker: forecast_results}
        """
        if not STATSMODELS_AVAILABLE:
            return {
                ticker: {
                    "error": "statsmodels not available. Install with: pip install statsmodels"
                }
                for ticker in tickers
            }

        results = {}

        for ticker in tickers:
            if ticker not in price_history:
                continue

            hist = price_history[ticker]
            if not self.validate_history(hist, min_days=60):
                results[ticker] = {"error": "Insufficient historical data for ARIMA"}
                continue

            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    forecast_result = await self._forecast_single(
                        ticker,
                        hist,
                        horizon_days,
                        auto_tune,
                        p_range,
                        d_range,
                        q_range,
                        confidence_level
                    )
                    results[ticker] = forecast_result

            except Exception as e:
                results[ticker] = {
                    "error": f"ARIMA forecast failed: {str(e)}",
                    "model": "ARIMA"
                }

        return results

    async def _forecast_single(
        self,
        ticker: str,
        hist: pd.DataFrame,
        horizon_days: int,
        auto_tune: bool,
        p_range: Tuple[int, int],
        d_range: Tuple[int, int],
        q_range: Tuple[int, int],
        confidence_level: float
    ) -> Dict[str, Any]:
        """Run ARIMA forecast for a single ticker."""
        # Use log prices for better numerical stability
        prices = hist["Close"]
        log_prices = np.log(prices)
        last_price = float(prices.iloc[-1])
        last_log_price = float(log_prices.iloc[-1])

        # Limit horizon for ARIMA (best for short-term)
        forecast_horizon = min(horizon_days, self.metadata["max_horizon_days"])

        # Enforce business day frequency for statsmodels
        # This fixes ValueWarning: A date index has been provided, but it has no associated frequency information
        if log_prices.index.freq is None:
            log_prices = log_prices.asfreq('B')
            # Fill any missing values created by asfreq (e.g. holidays)
            log_prices = log_prices.ffill()

        # Determine if we need differencing (stationarity test)
        is_stationary, d = self._check_stationarity(log_prices)

        # Check for FAST_OPTIMIZE (skip expensive auto-tuning in test mode)
        fast_mode = os.environ.get("FAST_OPTIMIZE", "false").lower() == "true"

        # Try to get cached parameters
        cached_params = None
        if auto_tune and not fast_mode:
            cached_params = await self._get_cached_params(ticker)
            
        if fast_mode:
            # Fast mode: skip auto-tuning entirely, use default params
            p, d, q = 1, 1, 1
        elif cached_params:
            p, d, q = cached_params
        elif auto_tune:
            best_order = self._auto_tune_arima(
                log_prices,
                p_range=p_range,
                d_range=(d, d + 1) if is_stationary else d_range,
                q_range=q_range
            )
            p, d, q = best_order
            
            # Save to cache
            await self._save_params_cache(ticker, (p, d, q))
        else:
            # Use default (1,1,1) which often works well
            p, d, q = 1, 1, 1

        # Fit ARIMA model
        model = ARIMA(log_prices, order=(p, d, q))
        model_fit = model.fit(method_kwargs={"warn_convergence": False})

        # Make forecast
        forecast_result = model_fit.get_forecast(steps=forecast_horizon)
        forecast_log_mean = forecast_result.predicted_mean
        forecast_log_ci = forecast_result.conf_int(alpha=1 - confidence_level)

        # Convert back from log scale
        forecast_mean = np.exp(forecast_log_mean)
        forecast_lower = np.exp(forecast_log_ci.iloc[:, 0])
        forecast_upper = np.exp(forecast_log_ci.iloc[:, 1])

        # Calculate metrics
        terminal_mean = float(forecast_mean.iloc[-1])
        terminal_lower = float(forecast_lower.iloc[-1])
        terminal_upper = float(forecast_upper.iloc[-1])

        # Detect regime
        regime = self._detect_regime(prices, p, d)

        return {
            "model": "ARIMA",
            "current_price": last_price,
            "horizon_days": forecast_horizon,
            "parameters": {
                "order": (p, d, q),
                "aic": float(model_fit.aic),
                "bic": float(model_fit.bic),
            },
            "terminal": {
                "mean": terminal_mean,
                "lower": terminal_lower,
                "upper": terminal_upper,
                "median": terminal_mean,  # Approximate
            },
            "return_metrics": {
                "mean_return": (terminal_mean / last_price) - 1,
                "lower_return": (terminal_lower / last_price) - 1,
                "upper_return": (terminal_upper / last_price) - 1,
            },
            "regime": regime,
            "forecast_path": {
                "mean": forecast_mean.tolist(),
                "lower": forecast_lower.tolist(),
                "upper": forecast_upper.tolist(),
            },
            "metadata": self.get_model_info(),
        }

    def _check_stationarity(self, series: pd.Series, significance: float = 0.05) -> Tuple[bool, int]:
        """
        Check if series is stationary using Augmented Dickey-Fuller test.

        Args:
            series: Time series to test
            significance: Significance level

        Returns:
            Tuple of (is_stationary, suggested_differencing)
        """
        try:
            result = adfuller(series.dropna(), regression='ct')
            p_value = result[1]

            # If p-value < significance, series is stationary
            if p_value < significance:
                return True, 0
            else:
                # Try first differencing
                diff_series = series.diff().dropna()
                result_diff = adfuller(diff_series, regression='c')
                p_value_diff = result_diff[1]

                if p_value_diff < significance:
                    return True, 1
                else:
                    return False, 1  # Default to d=1

        except Exception:
            # Fallback to d=1 if test fails
            return False, 1

    def _auto_tune_arima(
        self,
        series: pd.Series,
        p_range: Tuple[int, int] = (0, 5),
        d_range: Tuple[int, int] = (0, 2),
        q_range: Tuple[int, int] = (0, 5),
        max_iter: int = 50
    ) -> Tuple[int, int, int]:
        """
        Find optimal ARIMA parameters using AIC.

        Args:
            series: Time series
            p_range: Range of AR values to try
            d_range: Range of differencing values to try
            q_range: Range of MA values to try
            max_iter: Maximum iterations to prevent excessive computation

        Returns:
            Tuple of (p, d, q) with lowest AIC
        """
        best_aic = np.inf
        best_order = (1, 1, 1)  # Default fallback
        iterations = 0

        for d in range(d_range[0], d_range[1] + 1):
            for p in range(p_range[0], p_range[1] + 1):
                for q in range(q_range[0], q_range[1] + 1):
                    iterations += 1
                    if iterations > max_iter:
                        return best_order

                    try:
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
                            model = ARIMA(series, order=(p, d, q))
                            model_fit = model.fit(
                                method_kwargs={"warn_convergence": False}
                            )

                            if model_fit.aic < best_aic:
                                best_aic = model_fit.aic
                                best_order = (p, d, q)

                    except Exception:
                        continue

        return best_order

    def _detect_regime(self, prices: pd.Series, p: int, d: int) -> Dict[str, str]:
        """
        Detect market regime based on ARIMA parameters and price behavior.

        Args:
            prices: Price series
            p: AR order
            d: Differencing order

        Returns:
            Dict with regime classification
        """
        returns = prices.pct_change().dropna()

        # Trend detection
        recent_returns = returns.tail(20)
        avg_return = recent_returns.mean()

        if avg_return > 0.001:
            trend = "uptrend"
        elif avg_return < -0.001:
            trend = "downtrend"
        else:
            trend = "sideways"

        # Volatility regime
        volatility = returns.std()
        if volatility > 0.02:
            vol_regime = "high"
        elif volatility > 0.01:
            vol_regime = "normal"
        else:
            vol_regime = "low"

        # Mean reversion tendency
        mean_reverting = d > 0 or p > 1

        return {
            "trend": trend,
            "volatility_regime": vol_regime,
            "mean_reverting": mean_reverting,
        }

    async def _get_cached_params(self, ticker: str) -> Optional[Tuple[int, int, int]]:
        """
        Get cached ARIMA parameters for a ticker.
        
        Args:
            ticker: Ticker symbol
            
        Returns:
            Tuple of (p, d, q) or None if not found/expired
        """
        if not self._storage_service:
            return None
            
        try:
            cache_key = f"arima_params_{ticker}"
            cached = await self._storage_service.get("model_params_cache", cache_key)
            
            if not cached:
                return None
                
            # Check expiration (24h)
            created_at_str = cached.get("created_at")
            if created_at_str:
                created_at = datetime.datetime.fromisoformat(created_at_str)
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=datetime.timezone.utc)
                    
                age = datetime.datetime.now(datetime.timezone.utc) - created_at
                if age > datetime.timedelta(hours=24):
                    return None
                    
            params = cached.get("params")
            if params and len(params) == 3:
                return tuple(params)
                
            return None
        except Exception:
            return None

    async def _save_params_cache(self, ticker: str, params: Tuple[int, int, int]) -> None:
        """
        Save ARIMA parameters to cache.
        
        Args:
            ticker: Ticker symbol
            params: Tuple of (p, d, q)
        """
        if not self._storage_service:
            return
            
        try:
            cache_key = f"arima_params_{ticker}"
            data = {
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "params": list(params),
                "ticker": ticker,
                "model": "ARIMA"
            }
            await self._storage_service.save("model_params_cache", cache_key, data)
        except Exception:
            pass

