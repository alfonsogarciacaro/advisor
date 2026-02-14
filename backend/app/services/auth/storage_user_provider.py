from typing import Optional
from datetime import datetime
from app.services.user_provider import UserProvider
from app.models.auth import User, UserInDB


class StorageUserProvider(UserProvider):
    def __init__(self, storage_service):
        self.storage = storage_service

    async def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        """Retrieve a user by username from Firestore."""
        user_data = await self.storage.get("users", username)
        if not user_data:
            return None

        return UserInDB(
            username=user_data["username"],
            hashed_password=user_data["hashed_password"],
            role=user_data.get("role", "user"),
            disabled=user_data.get("disabled", False)
        )

    async def create_user(self, user: UserInDB) -> User:
        """Create a new user in Firestore."""
        user_data = {
            "username": user.username,
            "hashed_password": user.hashed_password,
            "role": user.role or "user",
            "disabled": user.disabled if user.disabled is not None else False,
            "created_at": datetime.utcnow().isoformat()
        }

        await self.storage.save("users", user.username, user_data)

        return User(
            username=user.username,
            role=user_data["role"],
            disabled=user_data["disabled"]
        )
