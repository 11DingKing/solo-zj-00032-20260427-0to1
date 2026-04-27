from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
from sqlalchemy import text
import logging

from .config import settings
from .database import sync_engine, Base, get_public_schema_session
from .models import Tenant, User
from .routers import auth, customers, opportunities, follow_ups, dashboard, import_export

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

def init_public_schema():
    from .models import Tenant, User
    Base.metadata.create_all(bind=sync_engine)
    logger.info("Public schema tables initialized")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting CRM system...")
    init_public_schema()
    logger.info("CRM system started successfully")
    yield
    logger.info("Shutting down CRM system...")

app = FastAPI(
    title="多租户 CRM 系统",
    description="基于 FastAPI 的多租户客户关系管理系统",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def tenant_middleware(request: Request, call_next):
    path = request.url.path
    
    if path.startswith("/api/register") or path.startswith("/api/login") or path.startswith("/docs") or path.startswith("/openapi.json") or path.startswith("/redoc"):
        response = await call_next(request)
        return response
    
    from jose import JWTError, jwt
    auth_header = request.headers.get("Authorization")
    
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            schema_name = payload.get("schema_name")
            if schema_name:
                request.state.tenant_schema = schema_name
        except JWTError:
            pass
    
    response = await call_next(request)
    return response

app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(opportunities.router)
app.include_router(follow_ups.router)
app.include_router(dashboard.router)
app.include_router(import_export.router)

@app.get("/")
async def root():
    return {"message": "多租户 CRM 系统 API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    try:
        with get_public_schema_session() as db:
            db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}
