"""Geometric Brownian Motion (GBM) forecasting model."""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from .base_model import BaseModel


class GBMModel(BaseModel):
    """
    Geometric Brownian Motion model for Monte Carlo simulation.

    Enhanced version with:
    - Multiple time horizon support
    - Confidence intervals
    - Scenario parameter handling
    - Parallel execution support
    """

    def __init__(self):
        super().__init__("GBM")
        self.metadata.update({
            "description": "Geometric Brownian Motion Monte Carlo simulation",
            "best_for": ["equity_indices", "etfs", "stocks"],
            "supports_scenarios": True,
            "default_simulations": 1000,
        })

    async def forecast(
        self,
        tickers: List[str],
        horizon_days: int,
        price_history: Dict[str, pd.DataFrame],
        simulations: int = 1000,
        scenarios: Optional[Dict[str, Dict[str, float]]] = None,
        confidence_levels: Optional[List[float]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run GBM Monte Carlo simulation.

        Args:
            tickers: List of ticker symbols
            horizon_days: Forecast horizon in days
            price_history: Dict of {ticker: DataFrame with OHLCV data}
            simulations: Number of Monte Carlo paths
            scenarios: Optional dict of {ticker: {drift_adj, vol_adj}}
            confidence_levels: List of confidence levels (e.g., [0.95, 0.99])
            **kwargs: Additional parameters

        Returns:
            Dict of {ticker: forecast_results}
        """
        if confidence_levels is None:
            confidence_levels = [0.90, 0.95, 0.99]

        results = {}

        for ticker in tickers:
            if ticker not in price_history:
                continue

            hist = price_history[ticker]
            if not self.validate_history(hist):
                results[ticker] = {"error": "Insufficient historical data"}
                continue

            # Use 'Close' price for calculations
            prices = hist["Close"]
            last_price = float(prices.iloc[-1])

            # Calculate daily returns
            returns = self.calculate_returns(prices)

            # Annualized drift and volatility
            daily_mu = float(returns.mean())
            daily_sigma = float(returns.std())
            mu, sigma = self.annualize_metrics(daily_mu, daily_sigma)

            # Apply scenario adjustments if provided
            drift_adj = 0.0
            vol_adj = 0.0

            if scenarios and ticker in scenarios:
                adj = scenarios[ticker]
                drift_adj = adj.get("drift_adj", 0.0)
                vol_adj = adj.get("vol_adj", 0.0)

            # Apply adjustments
            mu += drift_adj
            sigma *= (1.0 + vol_adj)

            # Convert to daily GBM parameters
            dt = 1 / 252
            daily_mu_gbm = mu * dt
            daily_sigma_gbm = sigma * np.sqrt(dt)

            # Generate all random shocks at once for efficiency
            Z = np.random.standard_normal((simulations, horizon_days))

            # Daily returns: exp((mu - 0.5 * sigma^2) * dt + sigma * sqrt(dt) * Z)
            daily_returns = np.exp(
                (daily_mu_gbm - 0.5 * daily_sigma_gbm**2) + daily_sigma_gbm * Z
            )

            # Price paths
            price_paths = np.zeros((simulations, horizon_days + 1))
            price_paths[:, 0] = last_price

            for t in range(1, horizon_days + 1):
                price_paths[:, t] = price_paths[:, t - 1] * daily_returns[:, t - 1]

            # Calculate statistics
            terminal_prices = price_paths[:, -1]

            # Confidence intervals
            ci_percentiles = [int((1 - cl) * 100) for cl in confidence_levels]
            ci_percentiles.extend([100 - p for p in ci_percentiles])  # Both sides
            ci_percentiles = sorted(set(ci_percentiles))

            confidence_intervals = self.calculate_confidence_intervals(
                terminal_prices,
                percentiles=ci_percentiles
            )

            # Path statistics at different horizons
            horizon_stats = self._calculate_horizon_stats(
                price_paths,
                [21, 63, 126, horizon_days],  # 1mo, 3mo, 6mo, final
                last_price
            )

            results[ticker] = {
                "model": "GBM",
                "current_price": last_price,
                "horizon_days": horizon_days,
                "simulations": simulations,
                "parameters": {
                    "annual_drift": mu,
                    "annual_volatility": sigma,
                    "drift_adjustment": drift_adj,
                    "volatility_adjustment": vol_adj,
                },
                "terminal": {
                    "mean": float(np.mean(terminal_prices)),
                    "median": float(np.median(terminal_prices)),
                    "std": float(np.std(terminal_prices)),
                    "min": float(np.min(terminal_prices)),
                    "max": float(np.max(terminal_prices)),
                    **confidence_intervals,
                },
                "return_metrics": {
                    "mean_return": float((np.mean(terminal_prices) / last_price) - 1),
                    "median_return": float((np.median(terminal_prices) / last_price) - 1),
                    "prob_positive_return": float(np.mean(terminal_prices > last_price)),
                },
                "horizon_stats": horizon_stats,
                "metadata": self.get_model_info(),
            }

        return results

    def _calculate_horizon_stats(
        self,
        price_paths: np.ndarray,
        horizons: List[int],
        current_price: float
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate statistics at different time horizons.

        Args:
            price_paths: Array of price paths (simulations x days)
            horizons: List of day indices to analyze
            current_price: Current price

        Returns:
            Dict of horizon names and their stats
        """
        stats = {}

        for horizon in horizons:
            if horizon >= price_paths.shape[1]:
                continue

            prices = price_paths[:, horizon]
            horizon_name = self._horizon_to_name(horizon)

            stats[horizon_name] = {
                "days": horizon,
                "mean_price": float(np.mean(prices)),
                "median_price": float(np.median(prices)),
                "mean_return": float((np.mean(prices) / current_price) - 1),
                "prob_profit": float(np.mean(prices > current_price)),
            }

        return stats

    def _horizon_to_name(self, days: int) -> str:
        """Convert days to readable horizon name."""
        if days <= 21:
            return "1_month"
        elif days <= 63:
            return "3_months"
        elif days <= 126:
            return "6_months"
        elif days <= 252:
            return "1_year"
        else:
            return f"{days}_days"
