from typing import Dict, Any, TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END
from app.core.langgraph_base import LangGraphAgent

# Define the Agent State
class AgentState(TypedDict):
    query: str
    research_results: list[str]
    summary: str

# Define Nodes
def search_node(state: AgentState) -> Dict[str, Any]:
    # In a real agent, this would call a search tool (e.g. Tavily, Google)
    query = state.get("query", "")
    return {"research_results": [f"Result for {query} 1", f"Result for {query} 2"]}

def summarize_node(state: AgentState) -> Dict[str, Any]:
    # In a real agent, this would call an LLM to summarize
    results = state.get("research_results", [])
    return {"summary": f"Summary of {len(results)} results: " + ", ".join(results)}

class ResearchAgent(LangGraphAgent):
    def build_graph(self) -> StateGraph:
        # Initialize Graph with State
        workflow = StateGraph(AgentState)

        # Add Nodes
        workflow.add_node("search", search_node)
        workflow.add_node("summarize", summarize_node)

        # Add Edges
        workflow.set_entry_point("search")
        workflow.add_edge("search", "summarize")
        workflow.add_edge("summarize", END)

        # Compile
        return workflow.compile()

    def get_initial_state(self, input_data: Any) -> Dict[str, Any]:
        # Transform simple input string to State dict if needed
        if isinstance(input_data, str):
            return {"query": input_data, "research_results": [], "summary": ""}
        return input_data
