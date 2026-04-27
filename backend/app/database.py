from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base
from contextvars import ContextVar
from typing import Optional
from .config import settings

Base = declarative_base()

current_tenant_schema: ContextVar[Optional[str]] = ContextVar("current_tenant_schema", default=None)

sync_engine = create_engine(
    settings.DATABASE_URL,
    echo=True
)

AsyncSessionLocal = None
async_engine = None

def get_async_engine():
    global async_engine, AsyncSessionLocal
    if async_engine is None:
        async_engine = create_async_engine(
            settings.DATABASE_URL,
            echo=True
        )
        AsyncSessionLocal = async_sessionmaker(
            async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    return async_engine

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
        engine = get_async_engine()
        self.session = AsyncSessionLocal()
        
        await self.session.execute(text(f'SET search_path TO {self.schema_name}, public'))
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        return False

def set_tenant_schema(schema_name: str):
    current_tenant_schema.set(schema_name)

def get_tenant_schema() -> Optional[str]:
    return current_tenant_schema.get()

async def create_tenant_schema(schema_name: str):
    engine = get_async_engine()
    
    async with engine.connect() as conn:
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS {schema_name}'))
        await conn.execute(text(f'SET search_path TO {schema_name}, public'))
        
        from .models import Base
        async with conn.begin():
            for table in Base.metadata.tables.values():
                if table.schema is None or table.schema == schema_name:
                    create_stmt = text(str(table.compile(
                        dialect=engine.dialect,
                        compile_kwargs={"literal_binds": True}
                    )))
                    await conn.execute(create_stmt)
        
        await conn.commit()
