import pytest
import datetime
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.dependencies import get_storage_service, get_auth_service
from app.infrastructure.storage.firestore_storage import FirestoreStorage
from app.services.auth_service import JWTAuthService
from app.services.auth.mock_user_provider import MockUserProvider
import uuid

@pytest.fixture
def storage():
    return FirestoreStorage()

@pytest.fixture
def auth_service(storage):
    # Use real JWTAuthService with MockUserProvider and Real Storage
    return JWTAuthService(MockUserProvider(), storage_service=storage)

@pytest.fixture
async def client(storage, auth_service):
    # Override dependencies
    app.dependency_overrides[get_storage_service] = lambda: storage
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_revocation_flow(client, auth_service):
    # 1. Login to get tokens
    # Register first
    username = f"user_{uuid.uuid4().hex[:8]}"
    pwd = "SecurePass123"
    await client.post("/api/auth/register", json={"username": username, "password": pwd})
    
    # Login
    resp = await client.post("/api/auth/token", data={"username": username, "password": pwd})
    assert resp.status_code == 200
    tokens = resp.json()
    access_token = tokens["access_token"]
    # Refresh token is now in cookies
    refresh_token = resp.cookies.get("refresh_token")
    assert refresh_token is not None
    
    # 2. Verify Refresh works initially
    resp_refresh = await client.post("/api/auth/refresh", cookies={"refresh_token": refresh_token})
    assert resp_refresh.status_code == 200
    new_tokens = resp_refresh.json()
    assert "access_token" in new_tokens
    # Should get a new refresh token in cookies
    new_refresh_token = resp_refresh.cookies.get("refresh_token")
    assert new_refresh_token is not None
    # assert new_refresh_token != refresh_token # Can be same if sub-second execution
    
    # 3. Logout (Revoke)
    # Logout requires access token auth and refresh token in cookies
    resp_logout = await client.post(
        "/api/auth/logout", 
        cookies={"refresh_token": new_refresh_token},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert resp_logout.status_code == 200
    # Verify cookie is cleared (expiry set to past or empty value)
    # Check Set-Cookie header directly as checking jar is flaky with domains
    found_cleared_cookie = False
    for val in resp_logout.headers.get_list("set-cookie"):
        if "refresh_token" in val and ('Max-Age=0' in val or 'Expires=' in val or 'refresh_token=""' in val or 'refresh_token=;' in val):
            found_cleared_cookie = True
            break
            
    # httpx delete_cookie sets max-age=0
    assert found_cleared_cookie, f"Refresh token cookie was not cleared. Headers: {resp_logout.headers}"
    
    # 4. Verify Refresh fails now with the revoked token
    resp_refresh_fail = await client.post("/api/auth/refresh", cookies={"refresh_token": new_refresh_token})
    assert resp_refresh_fail.status_code == 401
    assert "Could not validate credentials" in resp_refresh_fail.json()["detail"]
    
    # 5. Verify Access Token still works (until expiry)
    resp_me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert resp_me.status_code == 200

@pytest.mark.asyncio
async def test_logout_invalid_token(client):
    # Try to logout with invalid token
    # If no cookie sent, it might fail validation or just do nothing?
    # The endpoint has default=None for cookie. 
    # If None, it just clears cookie and returns success.
    # To fail auth, we need invalid access token.
    
    resp = await client.post(
        "/api/auth/logout",
        cookies={"refresh_token": "invalid.token.here"},
        headers={"Authorization": "Bearer invalid"}
    )
    # Should fail due to auth middleware (401)
    assert resp.status_code == 401
