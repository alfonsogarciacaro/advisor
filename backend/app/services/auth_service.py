from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel

class User(BaseModel):
    id: str
    email: str
    name: Optional[str] = None

class AuthService(ABC):
    @abstractmethod
    async def get_current_user(self, token: Optional[str] = None) -> User:
        pass
