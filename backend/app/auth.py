from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from .config import settings
from .database import get_public_schema_session
from .models import User, Tenant
from .schemas import TokenData

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> tuple[User, Tenant]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: int = payload.get("sub")
        tenant_id: int = payload.get("tenant_id")
        schema_name: str = payload.get("schema_name")
        
        if user_id is None or tenant_id is None:
            raise credentials_exception
        
        token_data = TokenData(user_id=user_id, tenant_id=tenant_id, schema_name=schema_name)
    except JWTError:
        raise credentials_exception
    
    with get_public_schema_session() as db:
        user = db.execute(select(User).where(User.id == token_data.user_id)).scalar_one_or_none()
        tenant = db.execute(select(Tenant).where(Tenant.id == token_data.tenant_id)).scalar_one_or_none()
        
        if user is None or tenant is None:
            raise credentials_exception
        
        if user.is_active != "true":
            raise HTTPException(status_code=400, detail="Inactive user")
        
        return user, tenant

async def get_current_active_admin(current_user_data: tuple = Depends(get_current_user)) -> tuple[User, Tenant]:
    user, tenant = current_user_data
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return user, tenant
