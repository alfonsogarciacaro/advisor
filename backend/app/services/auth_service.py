from datetime import datetime, timedelta
from typing import Optional, Union, Any, Dict
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
import os
from abc import ABC, abstractmethod
from app.models.auth import Token, User

# Configuration
SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "your-secret-key-change-in-production-keep-safe")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 Scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

class AuthService(ABC):
    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        pass

    @abstractmethod
    def get_password_hash(self, password: str) -> str:
        pass

    @abstractmethod
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        pass
    
    @abstractmethod
    def create_refresh_token(self, data: dict) -> str:
        pass
        
    @abstractmethod
    def verify_token(self, token: str, credential_exception: Any) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        pass

class JWTAuthService(AuthService):
    def __init__(self, user_provider: Any):
        self.user_provider = user_provider

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user = await self.user_provider.get_user_by_username(username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return User(username=user.username, role=user.role, email=user.email, full_name=user.full_name)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
        
    def verify_token(self, token: str, credential_exception: Any) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            raise credential_exception
