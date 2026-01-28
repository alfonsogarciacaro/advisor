import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional

class ForecastService:
    def __init__(self, history_service: Any):
        self.history_service = history_service

    async def run_monte_carlo(
        self, 
        tickers: List[str], 
        days: int = 252, 
        simulations: int = 1000,
        scenarios: Optional[Dict[str, Dict[str, float]]] = None
    ) -> Dict[str, Any]:
        """
        Runs Monte Carlo simulations for given tickers.
        scenarios: optional dict of {ticker: {drift_adj: float, vol_adj: float}}
        """
        metrics = await self.history_service.get_return_metrics(tickers)
        results = {}

        for ticker in tickers:
            if ticker not in metrics or metrics[ticker]["last_price"] == 0:
                continue

            m = metrics[ticker]
            last_price = m["last_price"]
            
            # Annualized expected return (drift) and volatility
            mu = m["annual_return"]
            sigma = m["annual_volatility"]

            # Apply scenario adjustments if provided
            if scenarios and ticker in scenarios:
                adj = scenarios[ticker]
                mu += adj.get("drift_adj", 0.0)
                sigma *= (1.0 + adj.get("vol_adj", 0.0))

            # Convert to daily (GBM parameters)
            dt = 1 / 252
            daily_mu = mu * dt
            daily_sigma = sigma * np.sqrt(dt)

            # Simulation using Geometric Brownian Motion
            # S_t = S_{t-1} * exp((mu - 0.5 * sigma^2) * dt + sigma * sqrt(dt) * Z)
            
            # Generate all random shocks at once
            Z = np.random.standard_normal((simulations, days))
            
            # Daily returns: exp((mu - 0.5 * sigma^2) * dt + sigma * sqrt(dt) * Z)
            daily_returns = np.exp((daily_mu - 0.5 * daily_sigma**2) + daily_sigma * Z)
            
            # Price paths
            price_paths = np.zeros((simulations, days + 1))
            price_paths[:, 0] = last_price
            
            for t in range(1, days + 1):
                price_paths[:, t] = price_paths[:, t-1] * daily_returns[:, t-1]

            # Calculate stats on terminal prices
            terminal_prices = price_paths[:, -1]
            
            results[ticker] = {
                "current_price": last_price,
                "mean_terminal_price": float(np.mean(terminal_prices)),
                "median_terminal_price": float(np.median(terminal_prices)),
                "min_terminal_price": float(np.min(terminal_prices)),
                "max_terminal_price": float(np.max(terminal_prices)),
                "std_terminal_price": float(np.std(terminal_prices)),
                "percentile_5": float(np.percentile(terminal_prices, 5)),
                "percentile_25": float(np.percentile(terminal_prices, 25)),
                "percentile_75": float(np.percentile(terminal_prices, 75)),
                "percentile_95": float(np.percentile(terminal_prices, 95)),
                "return_mean": float((np.mean(terminal_prices) / last_price) - 1),
                "prob_positive_return": float(np.mean(terminal_prices > last_price))
            }

        return results
