"""LangChain-compatible forecasting tools for the agent."""

from typing import Optional, Dict, Any
from langchain.tools import BaseTool


class MonteCarloTool(BaseTool):
    """
    Run Monte Carlo simulation with custom parameters.

    Use for scenario-specific forecasts with adjusted drift/volatility.
    """

    name = "monte_carlo_simulation"
    description = """
    Run Monte Carlo simulation using Geometric Brownian Motion (GBM) model.

    Use this tool to generate forecasts with custom parameters.
    Supports scenario analysis by adjusting drift and volatility.

    Args:
        tickers: List of ticker symbols (e.g., ["SPY", "QQQ"])
        horizon: Forecast horizon (e.g., "1mo", "3mo", "6mo", "1y")
        simulations: Number of simulation paths (default: 1000)
        drift_adj: Drift adjustment for scenarios (e.g., 0.05 for +5%)
        vol_adj: Volatility adjustment multiplier (e.g., 0.2 for +20% vol)

    Returns:
        Forecast results with confidence intervals and return metrics
    """

    def __init__(self, forecasting_engine):
        super().__init__()
        self.forecasting_engine = forecasting_engine

    async def _arun(
        self,
        tickers: str,
        horizon: str = "1y",
        simulations: int = 1000,
        drift_adj: float = 0.0,
        vol_adj: float = 0.0,
    ) -> Dict[str, Any]:
        """Async run method."""
        # Parse tickers from comma-separated string
        ticker_list = [t.strip().upper() for t in tickers.split(",")]

        # Create scenarios dict
        scenarios = {}
        if drift_adj != 0.0 or vol_adj != 0.0:
            for ticker in ticker_list:
                scenarios[ticker] = {
                    "drift_adj": drift_adj,
                    "vol_adj": vol_adj
                }

        # Run forecast
        result = await self.forecasting_engine.run_forecast_suite(
            tickers=ticker_list,
            horizon=horizon,
            models=["gbm"],
            simulations=simulations,
            scenarios=scenarios if scenarios else None
        )

        return result

    def _run(
        self,
        tickers: str,
        horizon: str = "1y",
        simulations: int = 1000,
        drift_adj: float = 0.0,
        vol_adj: float = 0.0,
    ) -> Dict[str, Any]:
        """Synchronous run method (wraps async)."""
        import asyncio
        return asyncio.run(self._arun(tickers, horizon, simulations, drift_adj, vol_adj))


class ARIMATool(BaseTool):
    """
    Run ARIMA forecast for short-term trend analysis.

    Best for:
    - Short-term forecasts (1-2 months)
    - Trend detection
    - Mean-reverting assets
    """

    name = "arima_forecast"
    description = """
    Run ARIMA (AutoRegressive Integrated Moving Average) forecast.

    Best for short-term forecasts and trend analysis.
    Auto-tunes parameters for optimal fit.

    Args:
        tickers: List of ticker symbols (e.g., ["SPY", "QQQ"])
        horizon_days: Forecast horizon in days (max 60 for ARIMA)

    Returns:
        ARIMA forecast with confidence intervals and model diagnostics
    """

    def __init__(self, forecasting_engine):
        super().__init__()
        self.forecasting_engine = forecasting_engine

    async def _arun(
        self,
        tickers: str,
        horizon_days: int = 30,
    ) -> Dict[str, Any]:
        """Async run method."""
        # Parse tickers
        ticker_list = [t.strip().upper() for t in tickers.split(",")]

        # Run ARIMA forecast
        result = await self.forecasting_engine.run_specific_model(
            model_name="arima",
            tickers=ticker_list,
            horizon_days=horizon_days,
        )

        return result

    def _run(
        self,
        tickers: str,
        horizon_days: int = 30,
    ) -> Dict[str, Any]:
        """Synchronous run method (wraps async)."""
        import asyncio
        return asyncio.run(self._arun(tickers, horizon_days))


class RiskAnalysisTool(BaseTool):
    """
    Calculate comprehensive risk metrics.

    Metrics include:
    - VaR (Value at Risk)
    - CVaR (Conditional VaR)
    - Maximum Drawdown
    - Sharpe Ratio
    - Sortino Ratio
    """

    name = "risk_analysis"
    description = """
    Calculate comprehensive risk metrics for financial assets.

    Metrics:
    - VaR: Maximum expected loss at given confidence level
    - CVaR: Expected loss beyond VaR threshold
    - Maximum Drawdown: Worst-case peak-to-trough decline
    - Sharpe Ratio: Risk-adjusted return metric
    - Sortino Ratio: Downside risk-adjusted return

    Args:
        tickers: List of ticker symbols (e.g., ["SPY", "QQQ"])
        confidence_levels: List of confidence levels (default: [0.95, 0.99])

    Returns:
        Comprehensive risk metrics for each ticker
    """

    def __init__(self, risk_calculator, history_service):
        super().__init__()
        self.risk_calculator = risk_calculator
        self.history_service = history_service

    async def _arun(
        self,
        tickers: str,
        confidence_levels: str = "0.95,0.99",
    ) -> Dict[str, Any]:
        """Async run method."""
        # Parse inputs
        ticker_list = [t.strip().upper() for t in tickers.split(",")]
        conf_levels = [float(c.strip()) for c in confidence_levels.split(",")]

        # Fetch price history for all tickers
        price_history = {}
        for ticker in ticker_list:
            df = await self.history_service.get_history(ticker, period="2y")
            if df is not None:
                price_history[ticker] = df

        # Calculate risk metrics
        results = self.risk_calculator.calculate_all_risk_metrics(
            price_history,
            confidence_levels=conf_levels
        )

        return results

    def _run(
        self,
        tickers: str,
        confidence_levels: str = "0.95,0.99",
    ) -> Dict[str, Any]:
        """Synchronous run method (wraps async)."""
        import asyncio
        return asyncio.run(self._arun(tickers, confidence_levels))


class TechnicalAnalysisTool(BaseTool):
    """
    Calculate technical indicators and detect market regime.

    Indicators:
    - RSI (Relative Strength Index)
    - MACD (Moving Average Convergence Divergence)
    - Bollinger Bands
    - SMA/EMA (Simple/Exponential Moving Averages)
    - ADX (Average Directional Index)
    - ATR (Average True Range)
    """

    name = "technical_analysis"
    description = """
    Calculate technical indicators and detect market regime.

    Provides:
    - Trend indicators (SMA, EMA, ADX)
    - Momentum indicators (RSI, MACD)
    - Volatility indicators (Bollinger Bands, ATR)
    - Market regime classification (trend, volatility, sentiment)

    Args:
        tickers: List of ticker symbols (e.g., ["SPY", "QQQ"])

    Returns:
        Technical indicators and regime analysis for each ticker
    """

    def __init__(self, history_service):
        super().__init__()
        self.history_service = history_service

    async def _arun(
        self,
        tickers: str,
    ) -> Dict[str, Any]:
        """Async run method."""
        # Parse tickers
        ticker_list = [t.strip().upper() for t in tickers.split(",")]

        # Get technical indicators
        indicators = await self.history_service.get_technical_indicators(
            ticker_list,
            indicators=["RSI", "MACD", "BBANDS", "SMA", "EMA", "ADX", "ATR"]
        )

        # Get market regime
        regime = await self.history_service.get_market_regime(ticker_list)

        return {
            "indicators": indicators,
            "regime": regime
        }

    def _run(
        self,
        tickers: str,
    ) -> Dict[str, Any]:
        """Synchronous run method (wraps async)."""
        import asyncio
        return asyncio.run(self._arun(tickers))


class MacroAnalysisTool(BaseTool):
    """
    Fetch and analyze macro economic indicators.

    Supports:
    - US economic indicators (GDP, unemployment, inflation, Fed funds rate)
    - Japan indicators (limited data available)
    - Market regime assessment
    """

    name = "macro_analysis"
    description = """
    Fetch macro economic indicators and assess economic regime.

    US Indicators:
    - GDP growth rate
    - Unemployment rate
    - CPI inflation
    - Fed funds rate
    - Treasury yields (2y, 10y, 30y)

    Japan Indicators (limited):
    - USD/JPY exchange rate
    - 10-year JGB yield (approximated)

    Args:
        market: Market code ("US" or "JP")

    Returns:
        Macro indicators and economic regime assessment
    """

    def __init__(self, macro_service):
        super().__init__()
        self.macro_service = macro_service

    async def _arun(
        self,
        market: str = "US",
    ) -> Dict[str, Any]:
        """Async run method."""
        # Get macro indicators
        indicators = await self.macro_service.get_macro_indicators(market)

        # Assess macro regime
        regime = await self.macro_service.assess_macro_regime(market)

        return {
            "indicators": indicators,
            "regime": regime,
            "market": market
        }

    def _run(
        self,
        market: str = "US",
    ) -> Dict[str, Any]:
        """Synchronous run method (wraps async)."""
        import asyncio
        return asyncio.run(self._arun(market))


def create_forecasting_tools(
    forecasting_engine,
    risk_calculator,
    history_service,
    macro_service
) -> list[BaseTool]:
    """
    Create all forecasting tools for the agent.

    Args:
        forecasting_engine: ForecastingEngine instance
        risk_calculator: RiskCalculator instance
        history_service: HistoryService instance
        macro_service: MacroService instance

    Returns:
        List of LangChain tools
    """
    return [
        MonteCarloTool(forecasting_engine),
        ARIMATool(forecasting_engine),
        RiskAnalysisTool(risk_calculator, history_service),
        TechnicalAnalysisTool(history_service),
        MacroAnalysisTool(macro_service),
    ]
