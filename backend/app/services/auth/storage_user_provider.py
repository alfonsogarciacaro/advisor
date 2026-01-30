from typing import Optional
from app.services.user_provider import UserProvider
from app.models.auth import User, UserInDB

class StorageUserProvider(UserProvider):
    def __init__(self, storage_service):
        self.storage = storage_service

    async def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        # TODO: Implement actual storage retrieval
        raise NotImplementedError("StorageAuth user provider not yet implemented")

    async def create_user(self, user: UserInDB) -> User:
        raise NotImplementedError("StorageAuth user provider not yet implemented")
