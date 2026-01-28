"""Risk metrics calculators for financial analysis."""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from scipy import stats


class RiskCalculator:
    """
    Calculate financial risk metrics.

    Metrics include:
    - VaR (Value at Risk)
    - CVaR (Conditional Value at Risk / Expected Shortfall)
    - Maximum Drawdown
    - Sharpe Ratio
    - Sortino Ratio
    """

    def __init__(self, risk_free_rate: float = 0.04):
        """
        Initialize risk calculator.

        Args:
            risk_free_rate: Annual risk-free rate (default 4%)
        """
        self.risk_free_rate = risk_free_rate

    def calculate_var(
        self,
        returns: pd.Series,
        confidence: float = 0.95,
        method: str = "historical"
    ) -> Dict[str, float]:
        """
        Calculate Value at Risk (VaR).

        VaR is the maximum expected loss at a given confidence level.

        Args:
            returns: Return series
            confidence: Confidence level (e.g., 0.95 for 95%)
            method: "historical", "parametric", or "both"

        Returns:
            Dict with VaR values
        """
        if len(returns) == 0:
            return {"error": "Empty returns series"}

        result = {}

        if method in ["historical", "both"]:
            # Historical VaR (empirical quantile)
            var_hist = float(np.percentile(returns, (1 - confidence) * 100))
            result["var_historical"] = var_hist
            result["var_historical_pct"] = var_hist * 100

        if method in ["parametric", "both"]:
            # Parametric VaR (assuming normal distribution)
            mu = float(returns.mean())
            sigma = float(returns.std())

            # VaR = mu - sigma * z_score
            z_score = stats.norm.ppf(1 - confidence)
            var_param = mu - sigma * z_score

            result["var_parametric"] = var_param
            result["var_parametric_pct"] = var_param * 100
            result["mean_return"] = mu
            result["volatility"] = sigma

        return result

    def calculate_cvar(
        self,
        returns: pd.Series,
        confidence: float = 0.95
    ) -> Dict[str, float]:
        """
        Calculate Conditional VaR (CVaR), also known as Expected Shortfall.

        CVaR is the average loss beyond the VaR threshold.

        Args:
            returns: Return series
            confidence: Confidence level

        Returns:
            Dict with CVaR values
        """
        if len(returns) == 0:
            return {"error": "Empty returns series"}

        # Calculate VaR threshold
        var_threshold = np.percentile(returns, (1 - confidence) * 100)

        # CVaR is the mean of returns below VaR
        tail_losses = returns[returns <= var_threshold]
        cvar = float(tail_losses.mean()) if len(tail_losses) > 0 else var_threshold

        return {
            "cvar": cvar,
            "cvar_pct": cvar * 100,
            "var_threshold": var_threshold,
            "confidence": confidence,
            "tail_observations": len(tail_losses),
        }

    def calculate_drawdown(
        self,
        prices: pd.Series,
        periods: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Calculate drawdown metrics.

        Args:
            prices: Price series
            periods: List of periods to analyze (in days)

        Returns:
            Dict with drawdown metrics
        """
        if len(prices) == 0:
            return {"error": "Empty price series"}

        # Calculate cumulative returns
        cumulative = (1 + prices.pct_change()).cumprod()

        # Calculate running maximum
        running_max = cumulative.expanding().max()

        # Calculate drawdown
        drawdown = (cumulative - running_max) / running_max

        # Maximum drawdown
        max_dd = float(drawdown.min())

        # Find maximum drawdown period
        max_dd_idx = drawdown.idxmin()
        max_dd_date = max_dd_idx if hasattr(max_dd_idx, "strftime") else None

        result = {
            "max_drawdown": max_dd,
            "max_drawdown_pct": max_dd * 100,
            "max_drawdown_date": str(max_dd_date) if max_dd_date else None,
            "avg_drawdown": float(drawdown.mean()),
            "current_drawdown": float(drawdown.iloc[-1]),
        }

        # Calculate drawdowns for specific periods if requested
        if periods:
            period_drawdowns = {}
            for period in periods:
                if len(drawdown) >= period:
                    period_dd = drawdown.tail(period)
                    period_drawdowns[f"{period}_day"] = {
                        "max": float(period_dd.min()),
                        "avg": float(period_dd.mean()),
                    }
            result["period_drawdowns"] = period_drawdowns

        return result

    def calculate_sharpe_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: Optional[float] = None,
        periods_per_year: int = 252
    ) -> Dict[str, float]:
        """
        Calculate Sharpe Ratio (risk-adjusted return).

        Args:
            returns: Return series (daily returns)
            risk_free_rate: Annual risk-free rate (uses instance default if None)
            periods_per_year: Number of periods per year (252 for daily)

        Returns:
            Dict with Sharpe ratio and related metrics
        """
        if len(returns) == 0:
            return {"error": "Empty returns series"}

        rf = risk_free_rate if risk_free_rate is not None else self.risk_free_rate

        # Convert annual risk-free rate to daily
        daily_rf = rf / periods_per_year

        # Calculate excess returns
        excess_returns = returns - daily_rf

        # Calculate Sharpe ratio
        mean_excess = float(excess_returns.mean())
        std_excess = float(excess_returns.std())

        # Annualize
        annual_mean = mean_excess * periods_per_year
        annual_std = std_excess * np.sqrt(periods_per_year)

        sharpe = annual_mean / annual_std if annual_std > 0 else 0.0

        return {
            "sharpe_ratio": sharpe,
            "annual_return": annual_mean,
            "annual_volatility": annual_std,
            "risk_free_rate": rf,
        }

    def calculate_sortino_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: Optional[float] = None,
        periods_per_year: int = 252,
        target_return: float = 0.0
    ) -> Dict[str, float]:
        """
        Calculate Sortino Ratio (downside risk-adjusted return).

        Args:
            returns: Return series
            risk_free_rate: Annual risk-free rate
            periods_per_year: Number of periods per year
            target_return: Minimum acceptable return (default 0)

        Returns:
            Dict with Sortino ratio
        """
        if len(returns) == 0:
            return {"error": "Empty returns series"}

        rf = risk_free_rate if risk_free_rate is not None else self.risk_free_rate
        daily_rf = rf / periods_per_year

        # Calculate excess returns
        excess_returns = returns - daily_rf

        # Calculate downside deviation (only negative returns)
        downside_returns = excess_returns[excess_returns < target_return]
        downside_std = float(downside_returns.std()) if len(downside_returns) > 0 else 0.0

        # Annualize
        annual_mean = float(excess_returns.mean()) * periods_per_year
        annual_downside_std = downside_std * np.sqrt(periods_per_year)

        sortino = annual_mean / annual_downside_std if annual_downside_std > 0 else 0.0

        return {
            "sortino_ratio": sortino,
            "annual_return": annual_mean,
            "annual_downside_deviation": annual_downside_std,
        }

    def calculate_all_risk_metrics(
        self,
        tickers: Dict[str, pd.DataFrame],
        confidence_levels: Optional[List[float]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate comprehensive risk metrics for multiple tickers.

        Args:
            tickers: Dict of {ticker: DataFrame with OHLCV data}
            confidence_levels: List of confidence levels for VaR/CVaR

        Returns:
            Dict of {ticker: {metric: value}}
        """
        if confidence_levels is None:
            confidence_levels = [0.95, 0.99]

        results = {}

        for ticker, df in tickers.items():
            if "Close" not in df.columns:
                continue

            prices = df["Close"]
            returns = prices.pct_change().dropna()

            # Calculate all metrics
            metrics = {}

            # VaR at multiple confidence levels
            var_metrics = {}
            for conf in confidence_levels:
                var_result = self.calculate_var(returns, confidence=conf, method="both")
                var_metrics[f"var_{int(conf*100)}"] = var_result
            metrics["var"] = var_metrics

            # CVaR at multiple confidence levels
            cvar_metrics = {}
            for conf in confidence_levels:
                cvar_result = self.calculate_cvar(returns, confidence=conf)
                cvar_metrics[f"cvar_{int(conf*100)}"] = cvar_result
            metrics["cvar"] = cvar_metrics

            # Drawdown analysis
            drawdown_result = self.calculate_drawdown(
                prices,
                periods=[1, 5, 20, 60]
            )
            metrics["drawdown"] = drawdown_result

            # Sharpe and Sortino ratios
            sharpe_result = self.calculate_sharpe_ratio(returns)
            metrics["sharpe"] = sharpe_result

            sortino_result = self.calculate_sortino_ratio(returns)
            metrics["sortino"] = sortino_result

            # Additional summary metrics
            metrics["summary"] = {
                "total_return": float((prices.iloc[-1] / prices.iloc[0]) - 1),
                "annual_volatility": float(returns.std() * np.sqrt(252)),
                "avg_daily_return": float(returns.mean()),
                "worst_day_return": float(returns.min()),
                "best_day_return": float(returns.max()),
            }

            results[ticker] = metrics

        return results

    def stress_test_scenarios(
        self,
        current_prices: Dict[str, float],
        forecast_results: Dict[str, Dict[str, Any]],
        scenarios: List[Dict[str, float]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Stress test portfolios under different scenarios.

        Args:
            current_prices: Dict of {ticker: current_price}
            forecast_results: Forecast results for each ticker
            scenarios: List of scenario dicts with adjustments

        Returns:
            Stress test results
        """
        results = {}

        for scenario in scenarios:
            scenario_name = scenario.get("name", "unnamed")
            scenario_results = {}

            for ticker, current_price in current_prices.items():
                if ticker not in forecast_results:
                    continue

                forecast = forecast_results[ticker]

                # Get base forecast return
                base_return = forecast.get("return_metrics", {}).get("mean_return", 0)

                # Apply scenario adjustments
                shock = scenario.get("shock", 0)
                stressed_return = base_return + shock

                stressed_price = current_price * (1 + stressed_return)

                scenario_results[ticker] = {
                    "current_price": current_price,
                    "base_return": base_return,
                    "shock": shock,
                    "stressed_return": stressed_return,
                    "stressed_price": stressed_price,
                    "pct_change": (stressed_price / current_price) - 1,
                }

            results[scenario_name] = scenario_results

        return results
