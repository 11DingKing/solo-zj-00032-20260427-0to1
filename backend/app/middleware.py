from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from .database import set_tenant_schema
from .auth import security

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        schema_name = request.state.tenant_schema if hasattr(request.state, 'tenant_schema') else None
        
        if schema_name:
            set_tenant_schema(schema_name)
        
        response = await call_next(request)
        return response
