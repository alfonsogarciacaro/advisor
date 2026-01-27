from abc import ABC, abstractmethod
from typing import Dict, Any

class PubSubService(ABC):
    @abstractmethod
    async def publish(self, topic: str, data: Dict[str, Any]) -> str:
        pass
