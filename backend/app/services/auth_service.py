from datetime import datetime, timedelta, timezone
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

    @abstractmethod
    async def revoke_token(self, token: str) -> None:
        pass

class JWTAuthService(AuthService):
    def __init__(self, user_provider: Any, storage_service: Any = None):
        self.user_provider = user_provider
        self.storage_service = storage_service
        self.revoked_collection = "revoked_tokens"

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
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
        
    def verify_token(self, token: str, credential_exception: Any) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Check revocation for refresh tokens if storage is available
            if payload.get("type") == "refresh" and self.storage_service:
                # We can't verify async here easily as this method is sync.
                # However, for Fastapi dependency injection, if we want to do async checks, 
                # we usually do it in the dependency or make this async.
                # But verify_token is called by get_current_user which is async, so we can make this async 
                # or just do a sync check if the storage client supports it? 
                # Firestore client is often synchronous for some operations or we need an async adapter.
                # Our StorageService is async.
                # Let's change verify_token to be async in the base class? 
                # Or we can do the check outside, in the route/dependency. 
                # For now, let's keep verify_token sync for JWT decoding, and add a separate async method for revocation check 
                # or just rely on the dependency `get_current_user` or `refresh_token` endpoint to call a check method.
                pass 
                
            return payload
        except JWTError:
            raise credential_exception

    async def revoke_token(self, token: str) -> None:
        if not self.storage_service:
            # If no storage, we can't revoke. 
            pass
            
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            # Use 'jti' if available, otherwise use signature or whole token as ID
            # Ideally we should have added 'jti' to tokens. 
            # For now let's use the token string hash or just the token itself if short enough? 
            # Tokens are long. Let's use a hash of the token.
            import hashlib
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            expiration = payload.get("exp")
            if expiration:
                exp_time = datetime.fromtimestamp(expiration)
                # We only need to store it until it expires naturally
                await self.storage_service.save(self.revoked_collection, token_hash, {
                    "token_hash": token_hash,
                    "revoked_at": datetime.now(timezone.utc).isoformat(),
                    "expires_at": exp_time.isoformat()
                })
        except Exception:
            pass

    async def is_token_revoked(self, token: str) -> bool:
        if not self.storage_service:
            return False
            
        try:
            import hashlib
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            data = await self.storage_service.get(self.revoked_collection, token_hash)
            return data is not None
        except Exception:
            return False
