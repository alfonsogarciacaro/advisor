from typing import Dict, Any, TypedDict, Annotated, Optional
import operator
from langgraph.graph import StateGraph, END
from app.core.langgraph_base import LangGraphAgent
from app.services.logger_service import LoggerService
from app.services.storage_service import StorageService
from app.services.config_service import ConfigService

# Define the Agent State - Enhanced with forecasting fields
class AgentState(TypedDict):
    query: str
    research_results: list[str]
    market_data: Dict[str, Any]
    etf_analysis: Dict[str, Any]
    technical_indicators: Dict[str, Any]          # NEW
    market_regime: Dict[str, Any]                 # NEW
    macro_indicators: Dict[str, Any]              # NEW
    baseline_forecasts: Dict[str, Any]            # NEW
    scenarios: Dict[str, Any]
    refined_forecasts: Dict[str, Any]             # NEW
    risk_metrics: Dict[str, Any]                  # NEW
    simulations: Dict[str, Any]
    summary: str
    confidence_level: str                         # NEW

class ResearchAgent(LangGraphAgent):
    def __init__(self, logger: LoggerService, storage: StorageService,
                 news_service: Any = None, history_service: Any = None,
                 forecast_service: Any = None,
                 forecasting_engine: Any = None,  # NEW
                 macro_service: Any = None,       # NEW
                 risk_calculator: Any = None,     # NEW
                 config_service: Any = None):
        super().__init__(logger, storage)
        self.news_service = news_service
        self.history_service = history_service
        self.forecast_service = forecast_service
        self.forecasting_engine = forecasting_engine  # NEW
        self.macro_service = macro_service            # NEW
        self.risk_calculator = risk_calculator        # NEW
        self.config_service = config_service or ConfigService()

    def search_node(self, state: AgentState) -> Dict[str, Any]:
        # In a real agent, this would call a search tool (e.g. Tavily, Google)
        query = state.get("query", "")
        return {"research_results": [f"Result for {query} 1", f"Result for {query} 2"]}

    async def fetch_market_data_node(self, state: AgentState) -> Dict[str, Any]:
        """Fetch comprehensive ETF data for analysis."""
        if self.history_service and self.config_service:
            # Get tickers from config
            tickers = self.config_service.get_all_symbols()

            # Get settings from config
            settings = self.config_service.get_data_settings()
            period = settings.get('default_period', '5y')

            try:
                # Fetch complete data with dividends and fundamentals
                data = await self.history_service.get_complete_etf_data(
                    tickers=tickers,
                    period=period,
                    include_dividends=True,
                    include_fundamentals=True
                )

                # Analyze data
                analysis = self._analyze_etf_data(data)

                return {
                    "market_data": data,
                    "etf_analysis": analysis
                }
            except Exception as e:
                self.logger.error(f"Error fetching market data: {e}")
                return {"market_data": {}, "etf_analysis": {}}

        return {"market_data": {}, "etf_analysis": {}}

    def _analyze_etf_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform analysis on ETF data."""
        analysis = {
            "performance_summary": {},
            "dividend_analysis": {},
            "valuation_metrics": {},
            "top_performers": [],
            "top_dividend_payers": []
        }

        performance_by_ticker = {}

        for ticker, etf_data in data.items():
            if not etf_data.get("ohlcv"):
                continue

            ohlcv = etf_data["ohlcv"]
            if len(ohlcv) < 2:
                continue

            # Calculate performance metrics
            start_price = ohlcv[0]["close"]
            end_price = ohlcv[-1]["close"]
            total_return = ((end_price - start_price) / start_price) * 100

            analysis["performance_summary"][ticker] = {
                "total_return_pct": round(total_return, 2),
                "start_price": round(start_price, 2),
                "end_price": round(end_price, 2),
                "data_points": len(ohlcv)
            }
            performance_by_ticker[ticker] = total_return

            # Dividend analysis
            dividends = etf_data.get("dividends", [])
            if dividends:
                total_dividends = sum(d["amount"] for d in dividends)
                analysis["dividend_analysis"][ticker] = {
                    "total_dividends": round(total_dividends, 2),
                    "dividend_count": len(dividends),
                    "latest_dividend": dividends[-1] if dividends else None
                }

            # Valuation metrics from fundamentals
            fundamentals = etf_data.get("fundamentals", {})
            if fundamentals:
                analysis["valuation_metrics"][ticker] = {
                    "pe_ratio": fundamentals.get("trailingPE"),
                    "market_cap": fundamentals.get("marketCap"),
                    "dividend_yield": fundamentals.get("dividendYield"),
                    "beta": fundamentals.get("beta")
                }

        # Find top performers
        if performance_by_ticker:
            sorted_by_return = sorted(performance_by_ticker.items(), key=lambda x: x[1], reverse=True)
            analysis["top_performers"] = [
                {"ticker": t, "return_pct": round(r, 2)}
                for t, r in sorted_by_return[:5]
            ]

        # Find top dividend payers
        if analysis["dividend_analysis"]:
            sorted_by_dividends = sorted(
                analysis["dividend_analysis"].items(),
                key=lambda x: x[1]["total_dividends"],
                reverse=True
            )
            analysis["top_dividend_payers"] = [
                {"ticker": t, "total_dividends": d["total_dividends"]}
                for t, d in sorted_by_dividends[:5]
            ]

        return analysis

    async def analyze_scenarios_node(self, state: AgentState) -> Dict[str, Any]:
        # In a real agent, this would use an LLM to look at news and set biases
        # For now, we simulate a "Base Case" with neutral bias
        return {"scenarios": {"SPY": {"drift_adj": 0.0, "vol_adj": 0.0}}}

    async def simulation_node(self, state: AgentState) -> Dict[str, Any]:
        if not self.forecast_service:
            return {"simulations": {}}
        
        tickers = list(state.get("market_data", {}).keys())
        if not tickers:
            tickers = ["SPY"] # Fallback

        try:
            results = await self.forecast_service.run_monte_carlo(
                tickers=tickers[:5], # Limit to first 5 for performance in demo
                days=252,
                simulations=1000,
                scenarios=state.get("scenarios")
            )
            return {"simulations": results}
        except Exception as e:
            self.logger.error(f"Error running simulation: {e}")
            return {"simulations": {}}

    def summarize_node(self, state: AgentState) -> Dict[str, Any]:
        """Generate summary using research and market data."""
        results = state.get("research_results", [])
        market_data = state.get("market_data", {})
        etf_analysis = state.get("etf_analysis", {})
        sims = state.get("simulations", {})

        summary = f"Summary of {len(results)} research results."

        if market_data:
            summary += f" Analyzed {len(market_data)} ETFs with 5-year historical data."

        if etf_analysis.get("top_performers"):
            top = etf_analysis["top_performers"][0]
            summary += f" Best performer: {top['ticker']} ({top['return_pct']}%)."

        if etf_analysis.get("top_dividend_payers"):
            top_div = etf_analysis["top_dividend_payers"][0]
            summary += f" Top dividend payer: {top_div['ticker']} (${top_div['total_dividends']})."

        if sims:
            summary += "\n\nMonte Carlo Simulation Results (1-year horizon):"
            for ticker, sim in sims.items():
                summary += f"\n- {ticker}: Expected return {sim['return_mean']:.2%}, "
                summary += f"95% CI: [{sim['percentile_5']:.2f}, {sim['percentile_95']:.2f}]"
                summary += f" (Prob. of positive return: {sim['prob_positive_return']:.1%})"

        return {"summary": summary}

    async def technical_analysis_node(self, state: AgentState) -> Dict[str, Any]:
        """Analyze technical indicators and detect market regime."""
        if not self.history_service:
            return {"technical_indicators": {}, "market_regime": {}}

        tickers = list(state.get("market_data", {}).keys())
        if not tickers:
            return {"technical_indicators": {}, "market_regime": {}}

        try:
            # Get technical indicators
            indicators = await self.history_service.get_technical_indicators(
                tickers=tickers[:5],  # Limit for performance
                indicators=["RSI", "MACD", "BBANDS", "SMA", "EMA", "ADX", "ATR"]
            )

            # Get market regime
            regime = await self.history_service.get_market_regime(tickers[:5])

            return {
                "technical_indicators": indicators,
                "market_regime": regime
            }
        except Exception as e:
            self.logger.error(f"Error in technical analysis: {e}")
            return {"technical_indicators": {}, "market_regime": {}}

    async def macro_analysis_node(self, state: AgentState) -> Dict[str, Any]:
        """Fetch and analyze macro economic indicators."""
        if not self.macro_service:
            return {"macro_indicators": {}}

        try:
            # Assess US economic regime
            us_regime = await self.macro_service.assess_macro_regime("US")

            # Get key indicators
            indicators = await self.macro_service.get_macro_indicators("US")

            return {
                "macro_indicators": {
                    "regime": us_regime,
                    "indicators": indicators
                }
            }
        except Exception as e:
            self.logger.error(f"Error in macro analysis: {e}")
            return {"macro_indicators": {}}

    async def baseline_forecast_node(self, state: AgentState) -> Dict[str, Any]:
        """Run baseline forecasting models (GBM + ARIMA)."""
        if not self.forecasting_engine:
            return {"baseline_forecasts": {}}

        tickers = list(state.get("market_data", {}).keys())
        if not tickers:
            return {"baseline_forecasts": {}}

        try:
            # Run baseline forecast suite
            results = await self.forecasting_engine.run_forecast_suite(
                tickers=tickers[:5],  # Limit for performance
                horizon="6mo",
                models=["gbm", "arima"],
                simulations=1000
            )

            return {"baseline_forecasts": results}
        except Exception as e:
            self.logger.error(f"Error in baseline forecast: {e}")
            return {"baseline_forecasts": {}}

    async def scenario_generation_node(self, state: AgentState) -> Dict[str, Any]:
        """Generate scenarios based on baseline, technicals, and macro analysis."""
        baseline = state.get("baseline_forecasts", {})
        technical = state.get("technical_indicators", {})
        macro = state.get("macro_indicators", {})
        market_regime = state.get("market_regime", {})

        scenarios = {}

        # Generate scenarios for each ticker
        for ticker in baseline.get("tickers", []):
            # Get ensemble forecast from baseline
            ensemble = baseline.get("ensemble", {}).get(ticker, {})
            base_return = ensemble.get("return_metrics", {}).get("mean_return", 0)

            # Adjust scenarios based on market regime
            ticker_regime = market_regime.get(ticker, {}).get("trend", {})
            trend_direction = ticker_regime.get("direction", "sideways")

            # Base case (60% weight)
            base_drift = 0.0
            base_vol = 0.0

            # Adjust based on trend
            if trend_direction == "uptrend":
                base_drift = 0.01  # Slight positive adjustment
            elif trend_direction == "downtrend":
                base_drift = -0.01  # Slight negative adjustment

            # Bull case (20% weight)
            bull_drift = base_drift + 0.05
            bull_vol = -0.1  # Lower volatility in bull market

            # Bear case (20% weight)
            bear_drift = base_drift - 0.05
            bear_vol = 0.2  # Higher volatility in bear market

            scenarios[ticker] = {
                "base_case": {
                    "weight": 0.6,
                    "drift_adj": base_drift,
                    "vol_adj": base_vol,
                    "description": "Base case scenario with current market conditions"
                },
                "bull_case": {
                    "weight": 0.2,
                    "drift_adj": bull_drift,
                    "vol_adj": bull_vol,
                    "description": "Optimistic scenario with favorable market conditions"
                },
                "bear_case": {
                    "weight": 0.2,
                    "drift_adj": bear_drift,
                    "vol_adj": bear_vol,
                    "description": "Pessimistic scenario with adverse market conditions"
                }
            }

        return {"scenarios": scenarios}

    async def refined_forecast_node(self, state: AgentState) -> Dict[str, Any]:
        """Generate refined forecasts using scenario parameters."""
        if not self.forecasting_engine:
            return {"refined_forecasts": {}}

        scenarios = state.get("scenarios", {})
        tickers = list(scenarios.keys())
        if not tickers:
            return {"refined_forecasts": {}}

        try:
            refined = {}

            # Run forecast for each scenario
            for scenario_name in ["base_case", "bull_case", "bear_case"]:
                scenario_params = {}
                for ticker, ticker_scenarios in scenarios.items():
                    if scenario_name in ticker_scenarios:
                        scenario_params[ticker] = ticker_scenarios[scenario_name]

                if scenario_params:
                    # Run forecast with scenario parameters
                    results = await self.forecasting_engine.run_forecast_suite(
                        tickers=tickers,
                        horizon="6mo",
                        models=["gbm"],
                        simulations=1000,
                        scenarios=scenario_params
                    )

                    refined[scenario_name] = results

            return {"refined_forecasts": refined}
        except Exception as e:
            self.logger.error(f"Error in refined forecast: {e}")
            return {"refined_forecasts": {}}

    async def risk_analysis_node(self, state: AgentState) -> Dict[str, Any]:
        """Calculate risk metrics for all tickers."""
        if not self.risk_calculator or not self.history_service:
            return {"risk_metrics": {}}

        tickers = list(state.get("market_data", {}).keys())
        if not tickers:
            return {"risk_metrics": {}}

        try:
            # Fetch price history
            price_history = {}
            for ticker in tickers[:5]:
                df = await self.history_service.get_history(ticker, period="2y")
                if df is not None:
                    price_history[ticker] = df

            # Calculate risk metrics
            metrics = self.risk_calculator.calculate_all_risk_metrics(
                price_history,
                confidence_levels=[0.95, 0.99]
            )

            return {"risk_metrics": metrics}
        except Exception as e:
            self.logger.error(f"Error in risk analysis: {e}")
            return {"risk_metrics": {}}

    def build_graph(self) -> StateGraph:
        # Initialize Graph with State
        workflow = StateGraph(AgentState)

        # Add Nodes
        workflow.add_node("search", self.search_node)
        workflow.add_node("fetch_market", self.fetch_market_data_node)
        workflow.add_node("technical_analysis", self.technical_analysis_node)  # NEW
        workflow.add_node("macro_analysis", self.macro_analysis_node)  # NEW
        workflow.add_node("baseline_forecast", self.baseline_forecast_node)  # NEW
        workflow.add_node("analyze_scenarios", self.scenario_generation_node)  # Enhanced
        workflow.add_node("refined_forecast", self.refined_forecast_node)  # NEW
        workflow.add_node("risk_analysis", self.risk_analysis_node)  # NEW
        workflow.add_node("simulation", self.simulation_node)  # Legacy, kept for compatibility
        workflow.add_node("summarize", self.summarize_node)

        # Add Edges - Enhanced workflow
        workflow.set_entry_point("search")
        workflow.add_edge("search", "fetch_market")
        workflow.add_edge("fetch_market", "technical_analysis")
        workflow.add_edge("technical_analysis", "macro_analysis")
        workflow.add_edge("macro_analysis", "baseline_forecast")
        workflow.add_edge("baseline_forecast", "analyze_scenarios")
        workflow.add_edge("analyze_scenarios", "refined_forecast")
        workflow.add_edge("refined_forecast", "risk_analysis")
        workflow.add_edge("risk_analysis", "summarize")
        workflow.add_edge("summarize", END)

        # Compile
        return workflow.compile()

    def get_initial_state(self, input_data: Any) -> Dict[str, Any]:
        if isinstance(input_data, str):
            return {
                "query": input_data,
                "research_results": [],
                "market_data": {},
                "etf_analysis": {},
                "technical_indicators": {},
                "market_regime": {},
                "macro_indicators": {},
                "baseline_forecasts": {},
                "scenarios": {},
                "refined_forecasts": {},
                "risk_metrics": {},
                "simulations": {},
                "summary": "",
                "confidence_level": "medium"
            }
        return input_data
