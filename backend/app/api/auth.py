from fastapi import APIRouter, Depends, HTTPException, status, Body, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Tuple
import re

from app.services.auth_service import AuthService
from app.core.dependencies import get_auth_service, get_current_user
from app.models.auth import Token, User, UserInDB

router = APIRouter()

# Password strength requirements
MIN_PASSWORD_LENGTH = 8
# Requires at least one letter and one digit (minimum)


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """Validate password strength. Returns (is_valid, error_message)."""
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain at least one letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    return True, ""

@router.post("/token", response_model=Token)
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    refresh_token = auth_service.create_refresh_token(
        data={"sub": user.username}
    )
    
    # Set HttpOnly, Secure cookie for refresh token
    # Note: secure=False for dev/http, True for prod/https
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False, # Set to True in production
        samesite="lax",
        max_age=7 * 24 * 60 * 60 # 7 days
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token)
async def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    auth_service: AuthService = Depends(get_auth_service)
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = auth_service.verify_token(refresh_token, credentials_exception)
        if payload.get("type") != "refresh":
            raise credentials_exception
            
        # Check if refresh token is revoked
        if await auth_service.is_token_revoked(refresh_token):
            raise credentials_exception
            
        username = payload.get("sub")
        # Validate user still exists - optional but recommended
        # user = await auth_service.user_provider.get_user_by_username(username)
        # if not user: raise credentials_exception
        
        # Here we might want to preserve the role if we don't fetch the user, 
        # but access token needs a role. 
        # Ideally we fetch the user to get the role.
        # Since we have access to user_provider via auth_service, let's do it if possible.
        # But for now, let's look up the user again.
        
        user = await auth_service.user_provider.get_user_by_username(username)
        if not user:
            raise credentials_exception
            
        new_access_token = auth_service.create_access_token(
            data={"sub": username, "role": user.role}
        )
        new_refresh_token = auth_service.create_refresh_token(
            data={"sub": username}
        )
        
        # Rotate refresh token
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=7 * 24 * 60 * 60
        )
        
        return {"access_token": new_access_token, "token_type": "bearer"}
    except Exception:
        raise credentials_exception

@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_user)
):
    """
    Logout user by revoking the refresh token.
    Requires authentication (access token) and the refresh token to revoke.
    """
    if refresh_token:
        await auth_service.revoke_token(refresh_token)
    
    response.delete_cookie("refresh_token")
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


class RegisterRequest(BaseModel):
    username: str
    password: str


@router.post("/register", response_model=User)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user."""
    # Validate username
    if not request.username or len(request.username.strip()) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 3 characters long"
        )

    # Validate password strength
    is_valid, error_msg = validate_password_strength(request.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Check if user already exists
    existing_user = await auth_service.user_provider.get_user_by_username(request.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )

    # Hash password and create user
    hashed_password = auth_service.get_password_hash(request.password)
    user_in_db = UserInDB(
        username=request.username,
        hashed_password=hashed_password,
        role="user",
        disabled=False
    )

    created_user = await auth_service.user_provider.create_user(user_in_db)

    return created_user
