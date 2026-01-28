from typing import Dict, Any, TypedDict, Annotated, Optional
import operator
from langgraph.graph import StateGraph, END
from app.core.langgraph_base import LangGraphAgent
from app.services.logger_service import LoggerService
from app.services.storage_service import StorageService

# Define the Agent State
class AgentState(TypedDict):
    query: str
    research_results: list[str]
    market_data: Dict[str, Any]
    summary: str

class ResearchAgent(LangGraphAgent):
    def __init__(self, logger: LoggerService, storage: StorageService, 
                 news_service: Any = None, history_service: Any = None):
        super().__init__(logger, storage)
        self.news_service = news_service
        self.history_service = history_service

    def search_node(self, state: AgentState) -> Dict[str, Any]:
        # In a real agent, this would call a search tool (e.g. Tavily, Google)
        query = state.get("query", "")
        return {"research_results": [f"Result for {query} 1", f"Result for {query} 2"]}

    async def fetch_market_data_node(self, state: AgentState) -> Dict[str, Any]:
        # Fetch default ETFs
        if self.history_service:
            # Default tickers as per plan
            # US: SPY, QQQ, IWM, AGG, VNQ, GLD, USO
            # Japan: 1306.T, 1321.T, 1343.T, 2561.T
            tickers = ['SPY', 'QQQ', 'IWM', 'AGG', 'VNQ', 'GLD', 'USO', '1306.T', '1321.T', '1343.T', '2561.T']
            try:
                data = await self.history_service.get_historical_data(tickers, period="1y")
                return {"market_data": data}
            except Exception as e:
                self.logger.error(f"Error fetching market data: {e}")
                return {"market_data": {}}
        return {"market_data": {}}

    def summarize_node(self, state: AgentState) -> Dict[str, Any]:
        # In a real agent, this would call an LLM to summarize
        results = state.get("research_results", [])
        market_data = state.get("market_data", {})
        summary = f"Summary of {len(results)} research results."
        if market_data:
            summary += f" Also fetched market data for {len(market_data)} tickers."
            # Simple summarization for now
            top_tickers = list(market_data.keys())[:3]
            summary += f" (e.g. {', '.join(top_tickers)})"
        return {"summary": summary}

    def build_graph(self) -> StateGraph:
        # Initialize Graph with State
        workflow = StateGraph(AgentState)

        # Add Nodes
        workflow.add_node("search", self.search_node)
        workflow.add_node("fetch_market", self.fetch_market_data_node)
        workflow.add_node("summarize", self.summarize_node)

        # Add Edges
        workflow.set_entry_point("search")
        workflow.add_edge("search", "fetch_market")
        workflow.add_edge("fetch_market", "summarize")
        workflow.add_edge("summarize", END)

        # Compile
        return workflow.compile()

    def get_initial_state(self, input_data: Any) -> Dict[str, Any]:
        # Transform simple input string to State dict if needed
        if isinstance(input_data, str):
            return {"query": input_data, "research_results": [], "market_data": {}, "summary": ""}
        return input_data
