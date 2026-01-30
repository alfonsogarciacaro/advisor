from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from app.services.auth_service import AuthService
from app.core.dependencies import get_auth_service, get_current_user
from app.models.auth import Token, User

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(
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
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str = Body(..., embed=True),
    auth_service: AuthService = Depends(get_auth_service)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = auth_service.verify_token(refresh_token, credentials_exception)
        if payload.get("type") != "refresh":
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
        
        return {"access_token": new_access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}
    except Exception:
        raise credentials_exception

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
