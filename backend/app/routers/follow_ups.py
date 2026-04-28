from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime, timedelta
from ..database import TenantSession
from ..models import FollowUpRecord, Customer, FollowUpMethod, User
from ..schemas import (
    FollowUpRecordCreate, FollowUpRecordResponse, FollowUpRecordListResponse,
    PendingFollowUp
)
from ..auth import get_current_user
from ..database import get_public_schema_session

router = APIRouter(prefix="/api", tags=["follow_ups"])

def get_user_map(tenant_id: int) -> dict:
    with get_public_schema_session() as db:
        users = db.execute(select(User).where(User.tenant_id == tenant_id)).scalars().all()
        return {u.id: u.name for u in users}

@router.post("/follow-ups", response_model=FollowUpRecordResponse)
async def create_follow_up(
    follow_up_data: FollowUpRecordCreate,
    user_data: tuple = Depends(get_current_user)
):
    user, tenant = user_data
    user_map = get_user_map(tenant.id)
    
    async with TenantSession(tenant.schema_name) as session:
        customer_result = await session.execute(
            select(Customer).where(Customer.id == follow_up_data.customer_id)
        )
        customer = customer_result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        follow_up = FollowUpRecord(
            customer_id=follow_up_data.customer_id,
            user_id=user.id,
            method=follow_up_data.method,
            content=follow_up_data.content,
            next_follow_up_time=follow_up_data.next_follow_up_time
        )
        
        session.add(follow_up)
        await session.commit()
        await session.refresh(follow_up)
        
        response = FollowUpRecordResponse.model_validate(follow_up)
        response.user_name = user_map.get(follow_up.user_id)
        
        return response

@router.get("/follow-ups", response_model=FollowUpRecordListResponse)
async def list_follow_ups(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    sort_by: Optional[str] = Query("created_at"),
    sort_order: Optional[str] = Query("desc"),
    user_data: tuple = Depends(get_current_user)
):
    user, tenant = user_data
    user_map = get_user_map(tenant.id)
    
    async with TenantSession(tenant.schema_name) as session:
        query = select(FollowUpRecord)
        
        if customer_id:
            query = query.where(FollowUpRecord.customer_id == customer_id)
        if user_id:
            query = query.where(FollowUpRecord.user_id == user_id)
        
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar_one()
        
        sort_column = getattr(FollowUpRecord, sort_by, FollowUpRecord.created_at)
        if sort_order == "desc":
            sort_column = sort_column.desc()
        else:
            sort_column = sort_column.asc()
        
        query = query.order_by(sort_column)
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await session.execute(query)
        follow_ups = result.scalars().all()
        
        follow_up_responses = []
        for fu in follow_ups:
            resp = FollowUpRecordResponse.model_validate(fu)
            resp.user_name = user_map.get(fu.user_id)
            follow_up_responses.append(resp)
        
        return FollowUpRecordListResponse(total=total, items=follow_up_responses)

@router.get("/follow-ups/pending", response_model=List[PendingFollowUp])
async def get_pending_follow_ups(
    user_data: tuple = Depends(get_current_user)
):
    user, tenant = user_data
    
    async with TenantSession(tenant.schema_name) as session:
        now = datetime.utcnow()
        
        query = select(
            FollowUpRecord.id,
            FollowUpRecord.customer_id,
            FollowUpRecord.next_follow_up_time,
            FollowUpRecord.content,
            Customer.company_name
        ).join(
            Customer, FollowUpRecord.customer_id == Customer.id
        ).where(
            and_(
                FollowUpRecord.next_follow_up_time.isnot(None),
                FollowUpRecord.next_follow_up_time <= now,
                FollowUpRecord.user_id == user.id
            )
        ).order_by(FollowUpRecord.next_follow_up_time.asc())
        
        result = await session.execute(query)
        rows = result.all()
        
        pending_list = []
        for row in rows:
            pending_list.append(PendingFollowUp(
                id=row.id,
                customer_id=row.customer_id,
                customer_name=row.company_name,
                next_follow_up_time=row.next_follow_up_time,
                content=row.content
            ))
        
        return pending_list

@router.get("/follow-ups/{follow_up_id}", response_model=FollowUpRecordResponse)
async def get_follow_up(
    follow_up_id: int,
    user_data: tuple = Depends(get_current_user)
):
    user, tenant = user_data
    user_map = get_user_map(tenant.id)
    
    async with TenantSession(tenant.schema_name) as session:
        result = await session.execute(
            select(FollowUpRecord).where(FollowUpRecord.id == follow_up_id)
        )
        follow_up = result.scalar_one_or_none()
        
        if not follow_up:
            raise HTTPException(status_code=404, detail="Follow-up record not found")
        
        response = FollowUpRecordResponse.model_validate(follow_up)
        response.user_name = user_map.get(follow_up.user_id)
        
        return response

@router.delete("/follow-ups/{follow_up_id}")
async def delete_follow_up(
    follow_up_id: int,
    user_data: tuple = Depends(get_current_user)
):
    user, tenant = user_data
    
    async with TenantSession(tenant.schema_name) as session:
        result = await session.execute(
            select(FollowUpRecord).where(
                FollowUpRecord.id == follow_up_id,
                FollowUpRecord.user_id == user.id
            )
        )
        follow_up = result.scalar_one_or_none()
        
        if not follow_up:
            raise HTTPException(status_code=404, detail="Follow-up record not found")
        
        await session.delete(follow_up)
        await session.commit()
        
        return {"message": "Follow-up record deleted successfully"}

@router.get("/customers/{customer_id}/follow-ups", response_model=List[FollowUpRecordResponse])
async def get_customer_follow_ups(
    customer_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user_data: tuple = Depends(get_current_user)
):
    user, tenant = user_data
    user_map = get_user_map(tenant.id)
    
    async with TenantSession(tenant.schema_name) as session:
        customer_result = await session.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = customer_result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        query = select(FollowUpRecord).where(
            FollowUpRecord.customer_id == customer_id
        ).order_by(FollowUpRecord.created_at.desc())
        
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await session.execute(query)
        follow_ups = result.scalars().all()
        
        follow_up_responses = []
        for fu in follow_ups:
            resp = FollowUpRecordResponse.model_validate(fu)
            resp.user_name = user_map.get(fu.user_id)
            follow_up_responses.append(resp)
        
        return follow_up_responses
