from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from app.models.auth import User, UserInDB

class UserProvider(ABC):
    @abstractmethod
    async def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        """Retrieve a user by username."""
        pass

    @abstractmethod
    async def create_user(self, user: UserInDB) -> User:
        """Create a new user."""
        pass
