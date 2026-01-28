from typing import Dict, Any, Type, Optional, List
import uuid
import datetime
from app.services.logger_service import LoggerService
from app.services.storage_service import StorageService
from app.core.agent_base import AgentBase

class AgentService:
    def __init__(self, logger: LoggerService, storage: StorageService):
        self.logger = logger
        self.storage = storage
        self._agents: Dict[str, Type[AgentBase]] = {}

    def register_agent(self, name: str, agent_cls: Type[AgentBase]):
        self._agents[name] = agent_cls

    async def create_run(self, agent_name: str, input_data: Any) -> str:
        """
        Creates a run record and returns the run_id.
        """
        if agent_name not in self._agents:
            raise ValueError(f"Agent '{agent_name}' not found")

        run_id = str(uuid.uuid4())
        self.logger.info(f"Creating agent run: {agent_name} [{run_id}]")

        # Record run start
        await self.storage.save("agent_runs", run_id, {
            "agent": agent_name,
            "status": "queued",
            "input": input_data,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })
        return run_id

    async def execute_run(self, run_id: str, agent_name: str, input_data: Any):
        """
        Executes the agent run. to be called in the background.
        """
        self.logger.info(f"Executing agent run: {agent_name} [{run_id}]")
        
        try:
            # Update status to running
            await self.storage.update("agent_runs", run_id, {
                "status": "running",
                "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            })

            # Instantiate agent for this run
            agent_cls = self._agents[agent_name]
            agent = agent_cls(self.logger, self.storage)

            result = await agent.run(run_id, input_data)
            
            await self.storage.update("agent_runs", run_id, {
                "status": "completed",
                "result": result,
                "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            })
        except Exception as e:
            self.logger.error(f"Agent run failed: {run_id} - {e}")
            await self.storage.update("agent_runs", run_id, {
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            })

    async def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        return await self.storage.get("agent_runs", run_id)

    async def get_run_logs(self, run_id: str) -> Any:
        logs = await self.storage.list("agent_logs", filters={"run_id": run_id})
        logs.sort(key=lambda x: x.get("timestamp", ""))
        return logs
