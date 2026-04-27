from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from .models import UserRole, CustomerStatus, OpportunityStage, FollowUpMethod

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    name: str
    role: UserRole
    tenant_id: int
    schema_name: str
    company_name: str

class TokenData(BaseModel):
    user_id: Optional[int] = None
    tenant_id: Optional[int] = None
    schema_name: Optional[str] = None

class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: UserRole = UserRole.SALES

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[str] = None

class UserResponse(UserBase):
    id: int
    tenant_id: int
    is_active: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TenantBase(BaseModel):
    company_name: str

class TenantCreate(TenantBase):
    admin_email: EmailStr
    admin_name: str
    admin_password: str

class TenantResponse(TenantBase):
    id: int
    schema_name: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ContactBase(BaseModel):
    name: str
    position: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    wechat: Optional[str] = None
    is_primary: str = "false"

class ContactCreate(ContactBase):
    pass

class ContactUpdate(BaseModel):
    name: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    wechat: Optional[str] = None
    is_primary: Optional[str] = None

class ContactResponse(ContactBase):
    id: int
    customer_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CustomerBase(BaseModel):
    company_name: str
    industry: Optional[str] = None
    scale: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    remark: Optional[str] = None

class CustomerCreate(CustomerBase):
    contacts: Optional[List[ContactCreate]] = None

class CustomerUpdate(BaseModel):
    company_name: Optional[str] = None
    industry: Optional[str] = None
    scale: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    remark: Optional[str] = None
    status: Optional[CustomerStatus] = None
    owner_id: Optional[int] = None

class CustomerResponse(CustomerBase):
    id: int
    status: CustomerStatus
    owner_id: Optional[int] = None
    owner_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    contacts: List[ContactResponse] = []

    class Config:
        from_attributes = True

class CustomerListResponse(BaseModel):
    total: int
    items: List[CustomerResponse]

class CustomerStatusLogBase(BaseModel):
    old_status: CustomerStatus
    new_status: CustomerStatus
    remark: Optional[str] = None

class CustomerStatusLogResponse(CustomerStatusLogBase):
    id: int
    customer_id: int
    user_id: int
    user_name: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class OpportunityBase(BaseModel):
    name: str
    customer_id: int
    expected_amount: Optional[Decimal] = None
    expected_close_date: Optional[date] = None
    competitor_info: Optional[str] = None

class OpportunityCreate(OpportunityBase):
    pass

class OpportunityUpdate(BaseModel):
    name: Optional[str] = None
    expected_amount: Optional[Decimal] = None
    expected_close_date: Optional[date] = None
    stage: Optional[OpportunityStage] = None
    owner_id: Optional[int] = None
    competitor_info: Optional[str] = None

class OpportunityResponse(OpportunityBase):
    id: int
    stage: OpportunityStage
    owner_id: Optional[int] = None
    owner_name: Optional[str] = None
    customer_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class OpportunityListResponse(BaseModel):
    total: int
    items: List[OpportunityResponse]

class FollowUpRecordBase(BaseModel):
    method: FollowUpMethod
    content: str
    next_follow_up_time: Optional[datetime] = None

class FollowUpRecordCreate(FollowUpRecordBase):
    customer_id: int

class FollowUpRecordResponse(FollowUpRecordBase):
    id: int
    customer_id: int
    user_id: int
    user_name: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class FollowUpRecordListResponse(BaseModel):
    total: int
    items: List[FollowUpRecordResponse]

class DashboardStats(BaseModel):
    monthly_new_customers: int
    monthly_new_opportunity_amount: Decimal
    sales_rank: List[Dict[str, Any]]
    industry_distribution: List[Dict[str, Any]]
    opportunity_funnel: List[Dict[str, Any]]
    monthly_trend: List[Dict[str, Any]]

class ImportResult(BaseModel):
    total: int
    success: int
    failed: int
    errors: List[Dict[str, Any]]

class AdvancedFilter(BaseModel):
    industry: Optional[List[str]] = None
    scale: Optional[List[str]] = None
    status: Optional[List[CustomerStatus]] = None
    owner_id: Optional[List[int]] = None
    created_at_start: Optional[datetime] = None
    created_at_end: Optional[datetime] = None
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[str] = "desc"
    page: int = 1
    page_size: int = 20

class PendingFollowUp(BaseModel):
    id: int
    customer_id: int
    customer_name: str
    next_follow_up_time: datetime
    content: str
