from typing import Any, Dict, Optional, AsyncGenerator
from langgraph.graph import StateGraph
from app.core.agent_base import AgentBase
from app.services.logger_service import LoggerService
from app.services.storage_service import StorageService

class LangGraphAgent(AgentBase):
    def __init__(self, logger: LoggerService, storage: StorageService):
        super().__init__(logger, storage)

    async def run(self, run_id: str, input_data: Any) -> Any:
        # Build the graph
        graph = self.build_graph()
        
        # Initial state setup
        state = self.get_initial_state(input_data)
        
        self.logger.info(f"Starting LangGraph run: {run_id}")
        await self.log_step(run_id, "Workflow Start", "running", {"input": input_data})

        last_state = state
        try:
            # We use astream to capture node transitions
            # Note: This is a simplified version. LangGraph v0.2+ has 
            # astream_events which is even more powerful.
            async for output in graph.astream(state):
                # LangGraph output is a dict where keys are node names
                for node_name, node_output in output.items():
                    await self.log_step(
                        run_id, 
                        f"Node: {node_name}", 
                        "completed", 
                        {"output": str(node_output)[:500]} # Truncate for UI safety
                    )
                    last_state = node_output

            await self.log_step(run_id, "Workflow End", "completed", {"result": str(last_state)[:500]})
            return last_state
        except Exception as e:
            await self.log_step(run_id, "Workflow Error", "failed", {"error": str(e)})
            raise e

    def build_graph(self) -> StateGraph:
        """
        Subclasses must implement this to return a compiled LangGraph.
        """
        raise NotImplementedError()

    def get_initial_state(self, input_data: Any) -> Dict[str, Any]:
        """
        Subclasses can override this to transform input_data into the Graph State.
        """
        return input_data if isinstance(input_data, dict) else {"input": input_data}
