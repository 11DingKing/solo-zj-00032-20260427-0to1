from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime
import logging
from ..database import TenantSession
from ..models import (
    Customer, Contact, CustomerStatusLog, CustomerStatus, User, OpportunityStage
)
from ..schemas import (
    CustomerCreate, CustomerUpdate, CustomerResponse, CustomerListResponse,
    ContactCreate, ContactUpdate, ContactResponse, CustomerStatusLogResponse,
    AdvancedFilter
)
from ..auth import get_current_user, get_current_active_admin
from ..database import get_public_schema_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["customers"])

def get_user_map(tenant_id: int) -> dict:
    with get_public_schema_session() as db:
        users = db.execute(select(User).where(User.tenant_id == tenant_id)).scalars().all()
        return {u.id: u.name for u in users}

@router.post("/customers", response_model=CustomerResponse)
async def create_customer(
    customer_data: CustomerCreate,
    user_data: tuple = Depends(get_current_user)
):
    user, tenant = user_data
    user_map = get_user_map(tenant.id)
    
    async with TenantSession(tenant.schema_name) as session:
        customer = Customer(
            company_name=customer_data.company_name,
            industry=customer_data.industry,
            scale=customer_data.scale,
            address=customer_data.address,
            website=customer_data.website,
            remark=customer_data.remark,
            status=CustomerStatus.POTENTIAL.value,
            owner_id=user.id
        )
        
        if customer_data.contacts:
            for contact_data in customer_data.contacts:
                contact = Contact(
                    name=contact_data.name,
                    position=contact_data.position,
                    phone=contact_data.phone,
                    email=contact_data.email,
                    wechat=contact_data.wechat,
                    is_primary=contact_data.is_primary
                )
                customer.contacts.append(contact)
        
        session.add(customer)
        await session.commit()
        await session.refresh(customer)
        
        # Eager load contacts
        result = await session.execute(
            select(Customer).options(selectinload(Customer.contacts)).where(Customer.id == customer.id)
        )
        customer = result.scalar_one()
        
        response = CustomerResponse.model_validate(customer)
        response.owner_name = user_map.get(customer.owner_id)
        
        return response

@router.get("/customers", response_model=CustomerListResponse)
async def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query("created_at"),
    sort_order: Optional[str] = Query("desc"),
    industry: Optional[str] = Query(None),
    scale: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    owner_id: Optional[int] = Query(None),
    created_at_start: Optional[datetime] = Query(None),
    created_at_end: Optional[datetime] = Query(None),
    user_data: tuple = Depends(get_current_user)
):
    user, tenant = user_data
    user_map = get_user_map(tenant.id)
    
    async with TenantSession(tenant.schema_name) as session:
        query = select(Customer).options(selectinload(Customer.contacts))
        
        if industry:
            query = query.where(Customer.industry == industry)
        if scale:
            query = query.where(Customer.scale == scale)
        if status:
            query = query.where(Customer.status == status)
        if owner_id:
            query = query.where(Customer.owner_id == owner_id)
        if created_at_start:
            query = query.where(Customer.created_at >= created_at_start)
        if created_at_end:
            query = query.where(Customer.created_at <= created_at_end)
        
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar_one()
        
        sort_column = getattr(Customer, sort_by, Customer.created_at)
        if sort_order == "desc":
            sort_column = sort_column.desc()
        else:
            sort_column = sort_column.asc()
        
        query = query.order_by(sort_column)
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await session.execute(query)
        customers = result.scalars().unique().all()
        
        customer_responses = []
        for customer in customers:
            resp = CustomerResponse.model_validate(customer)
            resp.owner_name = user_map.get(customer.owner_id)
            customer_responses.append(resp)
        
        return CustomerListResponse(total=total, items=customer_responses)

@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    user_data: tuple = Depends(get_current_user)
):
    user, tenant = user_data
    user_map = get_user_map(tenant.id)
    
    async with TenantSession(tenant.schema_name) as session:
        result = await session.execute(
            select(Customer)
            .options(selectinload(Customer.contacts))
            .where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        response = CustomerResponse.model_validate(customer)
        response.owner_name = user_map.get(customer.owner_id)
        
        return response

@router.put("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    user_data: tuple = Depends(get_current_user)
):
    user, tenant = user_data
    user_map = get_user_map(tenant.id)
    
    async with TenantSession(tenant.schema_name) as session:
        result = await session.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        update_data = customer_data.model_dump(exclude_unset=True)
        
        if "status" in update_data and update_data["status"] is not None and update_data["status"] != customer.status:
            status_log = CustomerStatusLog(
                customer_id=customer_id,
                user_id=user.id,
                old_status=customer.status,
                new_status=update_data["status"],
                remark=f"Status changed from {customer.status} to {update_data['status']}"
            )
            session.add(status_log)
        
        for key, value in update_data.items():
            setattr(customer, key, value)
        
        await session.commit()
        await session.refresh(customer)
        
        # Eager load contacts
        result = await session.execute(
            select(Customer).options(selectinload(Customer.contacts)).where(Customer.id == customer_id)
        )
        customer = result.scalar_one()
        
        response = CustomerResponse.model_validate(customer)
        response.owner_name = user_map.get(customer.owner_id)
        
        return response

@router.delete("/customers/{customer_id}")
async def delete_customer(
    customer_id: int,
    user_data: tuple = Depends(get_current_active_admin)
):
    user, tenant = user_data
    
    async with TenantSession(tenant.schema_name) as session:
        result = await session.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        await session.delete(customer)
        await session.commit()
        
        return {"message": "Customer deleted successfully"}

@router.get("/customers/{customer_id}/contacts", response_model=List[ContactResponse])
async def get_customer_contacts(
    customer_id: int,
    user_data: tuple = Depends(get_current_user)
):
    user, tenant = user_data
    
    async with TenantSession(tenant.schema_name) as session:
        result = await session.execute(
            select(Contact).where(Contact.customer_id == customer_id)
        )
        contacts = result.scalars().all()
        
        return contacts

@router.post("/customers/{customer_id}/contacts", response_model=ContactResponse)
async def add_contact(
    customer_id: int,
    contact_data: ContactCreate,
    user_data: tuple = Depends(get_current_user)
):
    user, tenant = user_data
    
    async with TenantSession(tenant.schema_name) as session:
        result = await session.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        contact = Contact(
            customer_id=customer_id,
            name=contact_data.name,
            position=contact_data.position,
            phone=contact_data.phone,
            email=contact_data.email,
            wechat=contact_data.wechat,
            is_primary=contact_data.is_primary
        )
        
        session.add(contact)
        await session.commit()
        await session.refresh(contact)
        
        return contact

@router.put("/customers/{customer_id}/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(
    customer_id: int,
    contact_id: int,
    contact_data: ContactUpdate,
    user_data: tuple = Depends(get_current_user)
):
    user, tenant = user_data
    
    async with TenantSession(tenant.schema_name) as session:
        result = await session.execute(
            select(Contact).where(
                Contact.id == contact_id,
                Contact.customer_id == customer_id
            )
        )
        contact = result.scalar_one_or_none()
        
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        update_data = contact_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(contact, key, value)
        
        await session.commit()
        await session.refresh(contact)
        
        return contact

@router.delete("/customers/{customer_id}/contacts/{contact_id}")
async def delete_contact(
    customer_id: int,
    contact_id: int,
    user_data: tuple = Depends(get_current_user)
):
    user, tenant = user_data
    
    async with TenantSession(tenant.schema_name) as session:
        result = await session.execute(
            select(Contact).where(
                Contact.id == contact_id,
                Contact.customer_id == customer_id
            )
        )
        contact = result.scalar_one_or_none()
        
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        await session.delete(contact)
        await session.commit()
        
        return {"message": "Contact deleted successfully"}

@router.get("/customers/{customer_id}/status-logs", response_model=List[CustomerStatusLogResponse])
async def get_customer_status_logs(
    customer_id: int,
    user_data: tuple = Depends(get_current_user)
):
    user, tenant = user_data
    user_map = get_user_map(tenant.id)
    
    async with TenantSession(tenant.schema_name) as session:
        result = await session.execute(
            select(CustomerStatusLog)
            .where(CustomerStatusLog.customer_id == customer_id)
            .order_by(CustomerStatusLog.created_at.desc())
        )
        logs = result.scalars().all()
        
        log_responses = []
        for log in logs:
            resp = CustomerStatusLogResponse.model_validate(log)
            resp.user_name = user_map.get(log.user_id)
            log_responses.append(resp)
        
        return log_responses
