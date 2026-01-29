from typing import Dict, Any, TypedDict, Annotated, Optional
import operator
import json
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
    technical_indicators: Dict[str, Any]
    market_regime: Dict[str, Any]
    macro_indicators: Dict[str, Any]
    baseline_forecasts: Dict[str, Any]
    scenarios: Dict[str, Any]
    refined_forecasts: Dict[str, Any]
    risk_metrics: Dict[str, Any]
    simulations: Dict[str, Any] # Legacy field, kept for compatibility if needed
    summary: str
    confidence_level: str
    # Plan context for running research on existing portfolios
    plan_context: Optional[Dict[str, Any]]  # Contains existing allocation, risk profile, etc.

class ResearchAgent(LangGraphAgent):
    def __init__(self, logger: LoggerService, storage: StorageService,
                 news_service: Any = None, history_service: Any = None,
                 llm_service: Any = None,
                 forecasting_engine: Any = None,
                 macro_service: Any = None,
                 risk_calculator: Any = None,
                 config_service: Any = None,
                 web_search_tool: Any = None):
        super().__init__(logger, storage)
        self.news_service = news_service
        self.history_service = history_service
        self.llm_service = llm_service
        self.forecasting_engine = forecasting_engine
        self.macro_service = macro_service
        self.risk_calculator = risk_calculator
        self.config_service = config_service or ConfigService()
        self.web_search_tool = web_search_tool  # Placeholder for future web search integration

    def search_node(self, state: AgentState) -> Dict[str, Any]:
        # In a real agent, this would call a search tool (e.g. Tavily, Google)
        query = state.get("query", "")
        return {"research_results": [f"Result for {query} 1", f"Result for {query} 2"]}

    async def fetch_market_data_node(self, state: AgentState) -> Dict[str, Any]:
        """Fetch comprehensive ETF data for analysis."""
        if self.history_service and self.config_service:
            # Get tickers from config
            tickers = self.config_service.get_all_symbols()
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
                analysis = self._analyze_etf_data(data)
                return {"market_data": data, "etf_analysis": analysis}
            except Exception as e:
                self.logger.error(f"Error fetching market data: {e}")
                return {"market_data": {}, "etf_analysis": {}}

        return {"market_data": {}, "etf_analysis": {}}

    def _analyze_etf_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
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
            
            # Dividend and Valuation logic could be added here

        if performance_by_ticker:
            sorted_by_return = sorted(performance_by_ticker.items(), key=lambda x: x[1], reverse=True)
            analysis["top_performers"] = [{"ticker": t, "return_pct": round(r, 2)} for t, r in sorted_by_return[:5]]

        return analysis

    async def analyze_scenarios_node(self, state: AgentState) -> Dict[str, Any]:
        """Generate scenarios using LLM based on market data and technicals."""
        if not self.llm_service:
            # Fallback
            return {"scenarios": {"SPY": {"base_case": {"weight": 1.0, "drift_adj": 0.0, "vol_adj": 0.0}}}}

        query = state.get("query", "")
        market_regime = state.get("market_regime", {})
        macro = state.get("macro_indicators", {})
        plan_context = state.get("plan_context", {})

        # Construct prompt for LLM
        prompt = f"""
        You are a financial analyst. Based on the following context, generate 3 specific market scenarios
        (Base Case, Bull Case, Bear Case) for the requested analysis.

        User Query: "{query}"

        Market Regime: {json.dumps(market_regime, indent=2)}
        Macro Indicators: {json.dumps(macro, indent=2)}
        """

        # Add plan context if available
        if plan_context:
            prompt += f"\nCurrent Portfolio Context: {json.dumps(plan_context, indent=2)}\n"

        prompt += """
        For each scenario, provide:
        1. A weight (probability) - must sum to 1.0
        2. 'drift_adj': A drift adjustment factor (e.g. 0.05 for +5% annual return boost, -0.05 for -5%)
        3. 'vol_adj': A volatility adjustment factor (e.g. 0.2 for +20% volatility increase)
        4. Description of the scenario logic.

        Format strictly as JSON with keys: "scenarios" -> Ticker -> Case Name.
        Use "GLOBAL" as ticker key if scenarios apply to all assets, or specific tickers like "SPY" if specific.
        """

        # Prepare tools if available
        tools = None
        if self.web_search_tool:
            # In the future, web search tool will be passed to LLM for current market context
            tools = [self.web_search_tool]
            self.logger.info("Web search tool available for scenario analysis")

        try:
            # Call LLM Service with tools
            response_json = await self.llm_service.generate_json(prompt, tools=tools)
            return {"scenarios": response_json.get("scenarios", {})}
        except Exception as e:
            self.logger.error(f"Error generating scenarios with LLM: {e}")
            return {"scenarios": {}}

    async def refined_forecast_node(self, state: AgentState) -> Dict[str, Any]:
        """Generate refined forecasts using scenario parameters from LLM."""
        if not self.forecasting_engine:
            return {"refined_forecasts": {}}

        scenarios = state.get("scenarios", {})
        # If scenarios are GLOBAL, apply to top tickers
        tickers = list(state.get("market_data", {}).keys())[:5]
        
        if not tickers:
            return {"refined_forecasts": {}}

        refined_results = {}
        
        try:
            # Iterate through cases (Base, Bull, Bear)
            # We assume the structure from LLM is Scenarios -> Ticker -> Case
            # If "GLOBAL" is in scenarios, replicate for all tickers
            
            global_scenarios = scenarios.get("GLOBAL", {})
            
            cases = ["base_case", "bull_case", "bear_case"]
            
            for case in cases:
                case_params = {}
                
                # Build params for this specific case across all tickers
                for ticker in tickers:
                    # Specific or Global?
                    ticker_scenario = scenarios.get(ticker, global_scenarios)
                    case_data = ticker_scenario.get(case)
                    
                    if case_data:
                        case_params[ticker] = {
                            "drift_adj": case_data.get("drift_adj", 0.0),
                            "vol_adj": case_data.get("vol_adj", 0.0)
                        }
                
                if case_params:
                    # Run forecast for this case
                    results = await self.forecasting_engine.run_forecast_suite(
                        tickers=list(case_params.keys()),
                        horizon="6mo",
                        models=["gbm"],
                        simulations=1000,
                        scenarios=case_params
                    )
                    refined_results[case] = results
            
            return {"refined_forecasts": refined_results}
            
        except Exception as e:
            self.logger.error(f"Error in refined forecast: {e}")
            return {"refined_forecasts": {}}

    async def simulation_node(self, state: AgentState) -> Dict[str, Any]:
        # Legacy node - using refined_forecasts instead
        # Just passing through or mapping refined base case to simulations
        refined = state.get("refined_forecasts", {})
        base_case = refined.get("base_case", {})
        if base_case:
             # Extract simple simulation format from base case ensemble
             sim_results = {}
             ensemble = base_case.get("ensemble", {})
             for ticker, data in ensemble.items():
                 # Map ensemble structure to simple structure expected by UI/Summary
                 term = data.get("terminal", {})
                 metrics = data.get("return_metrics", {})
                 sim_results[ticker] = {
                     "return_mean": metrics.get("mean_return", 0),
                     "percentile_5": term.get("p5", 0), # Engine might use different keys, need to check GBM output
                     "percentile_95": term.get("p95", 0),
                     "prob_positive_return": metrics.get("prob_positive_return", 0)
                 }
             return {"simulations": sim_results}
        return {"simulations": {}}

    def summarize_node(self, state: AgentState) -> Dict[str, Any]:
        """Generate summary using research and market data."""
        results = state.get("research_results", [])
        scenarios = state.get("scenarios", {})
        refined = state.get("refined_forecasts", {})
        
        summary = f"Summary of research based on query: {state.get('query')}\n\n"
        
        if scenarios:
             summary += "### Scenario Analysis (AI Generated)\n"
             # Simply dump the scenario descriptions
             global_sc = scenarios.get("GLOBAL", {})
             for case, data in global_sc.items():
                 summary += f"- **{case.replace('_', ' ').title()}** ({data.get('weight',0):.0%} prob): {data.get('description')}\n"

        if refined:
            summary += "\n### Forecast Results (6 Months)\n"
            base = refined.get("base_case", {}).get("ensemble", {})
            for ticker, data in base.items():
                ret = data.get("return_metrics", {}).get("mean_return", 0)
                summary += f"- **{ticker}**: Expected Return {ret:.1%}\n"

        return {"summary": summary}

    async def technical_analysis_node(self, state: AgentState) -> Dict[str, Any]:
        """Analyze technical indicators and detect market regime."""
        if not self.history_service:
            return {"technical_indicators": {}, "market_regime": {}}

        tickers = list(state.get("market_data", {}).keys())
        if not tickers:
            return {"technical_indicators": {}, "market_regime": {}}

        try:
            indicators = await self.history_service.get_technical_indicators(
                tickers=tickers[:5],
                indicators=["RSI", "MACD", "BBANDS", "SMA", "EMA", "ADX", "ATR"]
            )
            regime = await self.history_service.get_market_regime(tickers[:5])
            return {"technical_indicators": indicators, "market_regime": regime}
        except Exception as e:
            self.logger.error(f"Error in technical analysis: {e}")
            return {"technical_indicators": {}, "market_regime": {}}

    async def macro_analysis_node(self, state: AgentState) -> Dict[str, Any]:
        """Fetch and analyze macro economic indicators."""
        if not self.macro_service:
            return {"macro_indicators": {}}
        try:
            us_regime = await self.macro_service.assess_macro_regime("US")
            indicators = await self.macro_service.get_macro_indicators("US")
            return {"macro_indicators": {"regime": us_regime, "indicators": indicators}}
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
            results = await self.forecasting_engine.run_forecast_suite(
                tickers=tickers[:5],
                horizon="6mo",
                models=["gbm", "arima"],
                simulations=1000
            )
            return {"baseline_forecasts": results}
        except Exception as e:
            self.logger.error(f"Error in baseline forecast: {e}")
            return {"baseline_forecasts": {}}

    async def risk_analysis_node(self, state: AgentState) -> Dict[str, Any]:
        """Calculate risk metrics for all tickers."""
        if not self.risk_calculator or not self.history_service:
            return {"risk_metrics": {}}

        tickers = list(state.get("market_data", {}).keys())
        if not tickers:
            return {"risk_metrics": {}}

        try:
            price_history = {}
            for ticker in tickers[:5]:
                df = await self.history_service.get_history(ticker, period="2y")
                if df is not None:
                    price_history[ticker] = df

            metrics = self.risk_calculator.calculate_all_risk_metrics(
                price_history,
                confidence_levels=[0.95, 0.99]
            )
            return {"risk_metrics": metrics}
        except Exception as e:
            self.logger.error(f"Error in risk analysis: {e}")
            return {"risk_metrics": {}}

    def build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)
        
        # Add Nodes
        workflow.add_node("search", self.search_node)
        workflow.add_node("fetch_market", self.fetch_market_data_node)
        workflow.add_node("technical_analysis", self.technical_analysis_node)
        workflow.add_node("macro_analysis", self.macro_analysis_node)
        workflow.add_node("baseline_forecast", self.baseline_forecast_node)
        workflow.add_node("analyze_scenarios", self.analyze_scenarios_node) # LLM Powered
        workflow.add_node("refined_forecast", self.refined_forecast_node)
        workflow.add_node("risk_analysis", self.risk_analysis_node)
        workflow.add_node("simulation", self.simulation_node) # Adapter
        workflow.add_node("summarize", self.summarize_node)

        # Add Edges
        workflow.set_entry_point("search")
        workflow.add_edge("search", "fetch_market")
        workflow.add_edge("fetch_market", "technical_analysis")
        workflow.add_edge("technical_analysis", "macro_analysis")
        workflow.add_edge("macro_analysis", "baseline_forecast")
        workflow.add_edge("baseline_forecast", "analyze_scenarios")
        workflow.add_edge("analyze_scenarios", "refined_forecast")
        workflow.add_edge("refined_forecast", "simulation") # Chain adapter
        workflow.add_edge("simulation", "risk_analysis")
        workflow.add_edge("risk_analysis", "summarize")
        workflow.add_edge("summarize", END)

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
                "confidence_level": "medium",
                "plan_context": None
            }
        # If input_data is a dict with plan_context, ensure it's included
        elif isinstance(input_data, dict):
            if "plan_context" not in input_data:
                input_data["plan_context"] = None
        return input_data
