from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class StorageService(ABC):
    @abstractmethod
    async def save(self, collection: str, id: str, data: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    async def get(self, collection: str, id: str) -> Optional[Dict[str, Any]]:
        pass
        
    @abstractmethod
    async def update(self, collection: str, id: str, data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def delete(self, collection: str, id: str) -> None:
        pass
