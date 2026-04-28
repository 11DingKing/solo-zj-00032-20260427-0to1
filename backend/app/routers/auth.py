from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from typing import Optional
from datetime import timedelta
from ..config import settings
from ..database import get_public_schema_session, create_tenant_schema
from ..models import User, Tenant, UserRole
from ..schemas import (
    Token, TenantCreate, TenantResponse, UserCreate, UserResponse, UserUpdate
)
from ..auth import (
    verify_password, get_password_hash, create_access_token, 
    get_current_user, get_current_active_admin
)
import re

router = APIRouter(prefix="/api", tags=["auth"])

def generate_schema_name(company_name: str) -> str:
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '', company_name.lower().replace(' ', '_'))
    return f"tenant_{sanitized}"[:63]

@router.post("/register", response_model=TenantResponse)
async def register_tenant(tenant_data: TenantCreate):
    with get_public_schema_session() as db:
        existing_tenant = db.execute(
            select(Tenant).where(Tenant.company_name == tenant_data.company_name)
        ).scalar_one_or_none()
        
        if existing_tenant:
            raise HTTPException(
                status_code=400,
                detail="Company already registered"
            )
        
        existing_user = db.execute(
            select(User).where(User.email == tenant_data.admin_email)
        ).scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        schema_name = generate_schema_name(tenant_data.company_name)
        
        tenant = Tenant(
            company_name=tenant_data.company_name,
            schema_name=schema_name
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        
        admin_user = User(
            tenant_id=tenant.id,
            email=tenant_data.admin_email,
            password_hash=get_password_hash(tenant_data.admin_password),
            name=tenant_data.admin_name,
            role=UserRole.ADMIN.value,
            is_active="true"
        )
        db.add(admin_user)
        db.commit()
        
        await create_tenant_schema(schema_name)
        
        result = TenantResponse(
            id=tenant.id,
            company_name=tenant.company_name,
            schema_name=tenant.schema_name,
            created_at=tenant.created_at
        )
    
    return result

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with get_public_schema_session() as db:
        user = db.execute(
            select(User).where(User.email == form_data.username)
        ).scalar_one_or_none()
        
        if not user or not verify_password(form_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if user.is_active != "true":
            raise HTTPException(
                status_code=400,
                detail="Inactive user"
            )
        
        tenant = db.execute(
            select(Tenant).where(Tenant.id == user.tenant_id)
        ).scalar_one_or_none()
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "tenant_id": user.tenant_id,
                "schema_name": tenant.schema_name
            },
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            user_id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            tenant_id=tenant.id,
            schema_name=tenant.schema_name,
            company_name=tenant.company_name
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user_data: tuple = Depends(get_current_user)):
    user, tenant = user_data
    return user

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user_data: tuple = Depends(get_current_active_admin)
):
    current_user, tenant = current_user_data
    
    with get_public_schema_session() as db:
        existing_user = db.execute(
            select(User).where(User.email == user_data.email)
        ).scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        new_user = User(
            tenant_id=tenant.id,
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            name=user_data.name,
            role=user_data.role,
            is_active="true"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user

@router.get("/users", response_model=list[UserResponse])
async def list_users(current_user_data: tuple = Depends(get_current_user)):
    current_user, tenant = current_user_data
    
    with get_public_schema_session() as db:
        users = db.execute(
            select(User).where(User.tenant_id == tenant.id)
        ).scalars().all()
        
        return users

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user_data: tuple = Depends(get_current_active_admin)
):
    current_user, tenant = current_user_data
    
    with get_public_schema_session() as db:
        user = db.execute(
            select(User).where(User.id == user_id, User.tenant_id == tenant.id)
        ).scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        update_data = user_data.model_dump(exclude_unset=True)
        
        if "email" in update_data:
            existing_user = db.execute(
                select(User).where(User.email == update_data["email"], User.id != user_id)
            ).scalar_one_or_none()
            
            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail="Email already registered"
                )
        
        for key, value in update_data.items():
            setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
        
        return user
