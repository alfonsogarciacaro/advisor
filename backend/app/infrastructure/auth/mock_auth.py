from typing import Optional
from app.services.auth_service import AuthService, User

class MockAuthService(AuthService):
    async def get_current_user(self, token: Optional[str] = None) -> User:
        return User(id="mock-user-123", email="mock@example.com", name="Mock User")
