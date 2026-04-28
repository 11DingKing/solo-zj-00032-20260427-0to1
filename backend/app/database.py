from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base
from contextvars import ContextVar
from typing import Optional
import re
from .config import settings

Base = declarative_base()

current_tenant_schema: ContextVar[Optional[str]] = ContextVar("current_tenant_schema", default=None)

def get_async_database_url() -> str:
    url = settings.DATABASE_URL
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://")
    return url

def get_sync_database_url() -> str:
    url = settings.DATABASE_URL
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://")
    return url

sync_engine = create_engine(
    get_sync_database_url(),
    echo=True
)

async_engine = create_async_engine(
    get_async_database_url(),
    echo=True
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False
)

def get_public_schema_session():
    return SyncSessionLocal()

class TenantSession:
    def __init__(self, schema_name: str):
        self.schema_name = schema_name
        self.session = None
    
    async def __aenter__(self):
        self.session = AsyncSessionLocal()
        await self.session.execute(text(f'SET search_path TO "{self.schema_name}", public'))
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        return False

def set_tenant_schema(schema_name: str):
    current_tenant_schema.set(schema_name)

def get_tenant_schema() -> Optional[str]:
    return current_tenant_schema.get()

def sanitize_schema_name(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_]', '', name)

async def create_tenant_schema(schema_name: str):
    safe_schema_name = sanitize_schema_name(schema_name)
    
    async with async_engine.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{safe_schema_name}"'))
        await conn.execute(text(f'SET search_path TO "{safe_schema_name}", public'))
        
        create_customers_sql = f'''
        CREATE TABLE IF NOT EXISTS "{safe_schema_name}".customers (
            id SERIAL PRIMARY KEY,
            company_name VARCHAR(255) NOT NULL,
            industry VARCHAR(100),
            scale VARCHAR(50),
            address VARCHAR(500),
            website VARCHAR(255),
            remark TEXT,
            status VARCHAR(50) DEFAULT 'potential',
            owner_id INTEGER,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        '''
        await conn.execute(text(create_customers_sql))
        
        create_contacts_sql = f'''
        CREATE TABLE IF NOT EXISTS "{safe_schema_name}".contacts (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            position VARCHAR(100),
            phone VARCHAR(50),
            email VARCHAR(255),
            wechat VARCHAR(100),
            is_primary VARCHAR(10) DEFAULT 'false',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        '''
        await conn.execute(text(create_contacts_sql))
        
        create_opportunities_sql = f'''
        CREATE TABLE IF NOT EXISTS "{safe_schema_name}".opportunities (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            name VARCHAR(255) NOT NULL,
            expected_amount NUMERIC(12,2),
            expected_close_date DATE,
            stage VARCHAR(50) DEFAULT 'initial_contact',
            owner_id INTEGER,
            competitor_info TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        '''
        await conn.execute(text(create_opportunities_sql))
        
        create_follow_ups_sql = f'''
        CREATE TABLE IF NOT EXISTS "{safe_schema_name}".follow_up_records (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            method VARCHAR(50) NOT NULL,
            content TEXT NOT NULL,
            next_follow_up_time TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        '''
        await conn.execute(text(create_follow_ups_sql))
        
        create_status_logs_sql = f'''
        CREATE TABLE IF NOT EXISTS "{safe_schema_name}".customer_status_logs (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            old_status VARCHAR(50) NOT NULL,
            new_status VARCHAR(50) NOT NULL,
            remark TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        '''
        await conn.execute(text(create_status_logs_sql))
        
        await conn.commit()
