from typing import Dict, Any, TypedDict, Annotated, Optional
import operator
from langgraph.graph import StateGraph, END
from app.core.langgraph_base import LangGraphAgent
from app.services.logger_service import LoggerService
from app.services.storage_service import StorageService
from app.services.config_service import ConfigService

# Define the Agent State
class AgentState(TypedDict):
    query: str
    research_results: list[str]
    market_data: Dict[str, Any]
    etf_analysis: Dict[str, Any]
    scenarios: Dict[str, Any]
    simulations: Dict[str, Any]
    summary: str

class ResearchAgent(LangGraphAgent):
    def __init__(self, logger: LoggerService, storage: StorageService,
                 news_service: Any = None, history_service: Any = None,
                 forecast_service: Any = None, config_service: Any = None):
        super().__init__(logger, storage)
        self.news_service = news_service
        self.history_service = history_service
        self.forecast_service = forecast_service
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

    def build_graph(self) -> StateGraph:
        # Initialize Graph with State
        workflow = StateGraph(AgentState)

        # Add Nodes
        workflow.add_node("search", self.search_node)
        workflow.add_node("fetch_market", self.fetch_market_data_node)
        workflow.add_node("analyze_scenarios", self.analyze_scenarios_node)
        workflow.add_node("simulation", self.simulation_node)
        workflow.add_node("summarize", self.summarize_node)

        # Add Edges
        workflow.set_entry_point("search")
        workflow.add_edge("search", "fetch_market")
        workflow.add_edge("fetch_market", "analyze_scenarios")
        workflow.add_edge("analyze_scenarios", "simulation")
        workflow.add_edge("simulation", "summarize")
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
                "scenarios": {},
                "simulations": {},
                "summary": ""
            }
        return input_data
