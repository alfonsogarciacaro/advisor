from typing import Dict, Optional
from app.services.user_provider import UserProvider
from app.models.auth import User, UserInDB
from app.services.auth_service import AuthService  # Circular dependency? No, interface is separate.
# But we need to hash passwords. Ideally the provider stores them, but for mock initialization we need a hasher.
# Alternatively, we just store pre-hashed strings here or pass a hasher.
# Let's import the specific helper function from a util if possible, or just re-use the context from auth_service 
# BUT auth_service imports us (eventually). 
# Let's duplicate the hasher usage or import just the context for now to avoid circular import.
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class MockUserProvider(UserProvider):
    def __init__(self):
        self.db = {}
        # Initialize default users
        self._add_user("admin", "admin123", "admin@example.com", "System Administrator", "admin")
        self._add_user("demo", "demo123", "demo@example.com", "Demo User", "user")

    def _add_user(self, username, password, email, full_name, role):
        hashed_password = pwd_context.hash(password)
        self.db[username] = UserInDB(
            username=username,
            hashed_password=hashed_password,
            email=email,
            full_name=full_name,
            disabled=False,
            role=role
        )

    async def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        return self.db.get(username)

    async def create_user(self, user: UserInDB) -> User:
        if user.username in self.db:
            raise ValueError("User already exists")
        self.db[user.username] = user
        return user
