from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import datetime
import uuid
from app.services.logger_service import LoggerService
from app.services.storage_service import StorageService

class AgentBase(ABC):
    def __init__(self, logger: LoggerService, storage: StorageService):
        self.logger = logger
        self.storage = storage

    @abstractmethod
    async def run(self, run_id: str, input_data: Any) -> Any:
        pass

    async def log_step(self, run_id: str, step_name: str, status: str, details: Optional[Dict[str, Any]] = None):
        """
        Logs a step to the logger and saves it to Firestore for monitoring.
        """
        message = f"[{run_id}] Step: {step_name} - Status: {status}"
        if details:
            message += f" - Details: {details}"
        
        self.logger.info(message)

        # Save to storage for UI monitoring
        step_data = {
            "run_id": run_id,
            "step": step_name,
            "status": status,
            "details": details or {},
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        
        # We append to a subcollection or list for the run. 
        # For simplicity in this implementation, we'll just save unrelated log entries 
        # that can be queried by run_id, or append to a list in the run document.
        # Let's assume we save individual log entries to a 'agent_logs' collection.
        log_id = str(uuid.uuid4())
        await self.storage.save("agent_logs", log_id, step_data)
