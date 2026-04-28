from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, case
from sqlalchemy.orm import selectinload
from typing import Optional, List
from decimal import Decimal
from ..database import TenantSession
from ..models import Opportunity, Customer, OpportunityStage, User
from ..schemas import (
    OpportunityCreate, OpportunityUpdate, OpportunityResponse, OpportunityListResponse
)
from ..auth import get_current_user, get_current_active_admin
from ..database import get_public_schema_session

router = APIRouter(prefix="/api", tags=["opportunities"])

async def get_user_map(tenant_id: int) -> dict:
    with get_public_schema_session() as db:
        users = db.execute(select(User).where(User.tenant_id == tenant_id)).scalars().all()
        return {u.id: u.name for u in users}

@router.post("/opportunities", response_model=OpportunityResponse)
async def create_opportunity(
    opportunity_data: OpportunityCreate,
    user_data: tuple = Depends(get_current_user)
):
    user, tenant = user_data
    user_map = await get_user_map(tenant.id)
    
    async with TenantSession(tenant.schema_name) as session:
        customer_result = await session.execute(
            select(Customer).where(Customer.id == opportunity_data.customer_id)
        )
        customer = customer_result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        opportunity = Opportunity(
            name=opportunity_data.name,
            customer_id=opportunity_data.customer_id,
            expected_amount=opportunity_data.expected_amount,
            expected_close_date=opportunity_data.expected_close_date,
            stage=OpportunityStage.INITIAL_CONTACT.value,
            owner_id=user.id,
            competitor_info=opportunity_data.competitor_info
        )
        
        session.add(opportunity)
        await session.commit()
        await session.refresh(opportunity)
        
        response = OpportunityResponse.model_validate(opportunity)
        response.owner_name = user_map.get(opportunity.owner_id)
        response.customer_name = customer.company_name
        
        return response

@router.get("/opportunities", response_model=OpportunityListResponse)
async def list_opportunities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query("created_at"),
    sort_order: Optional[str] = Query("desc"),
    stage: Optional[List[OpportunityStage]] = Query(None),
    owner_id: Optional[List[int]] = Query(None),
    user_data: tuple = Depends(get_current_user)
):
    user, tenant = user_data
    user_map = await get_user_map(tenant.id)
    
    async with TenantSession(tenant.schema_name) as session:
        query = select(Opportunity)
        
        if stage:
            query = query.where(Opportunity.stage.in_(stage))
        if owner_id:
            query = query.where(Opportunity.owner_id.in_(owner_id))
        
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar_one()
        
        sort_column = getattr(Opportunity, sort_by, Opportunity.created_at)
        if sort_order == "desc":
            sort_column = sort_column.desc()
        else:
            sort_column = sort_column.asc()
        
        query = query.order_by(sort_column)
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await session.execute(query)
        opportunities = result.scalars().all()
        
        customer_ids = [o.customer_id for o in opportunities]
        if customer_ids:
            customers_result = await session.execute(
                select(Customer.id, Customer.company_name)
                .where(Customer.id.in_(customer_ids))
            )
            customer_map = {r[0]: r[1] for r in customers_result.all()}
        else:
            customer_map = {}
        
        opportunity_responses = []
        for opp in opportunities:
            resp = OpportunityResponse.model_validate(opp)
            resp.owner_name = user_map.get(opp.owner_id)
            resp.customer_name = customer_map.get(opp.customer_id)
            opportunity_responses.append(resp)
        
        return OpportunityListResponse(total=total, items=opportunity_responses)

@router.get("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opportunity_id: int,
    user_data: tuple = Depends(get_current_user)
):
    user, tenant = user_data
    user_map = await get_user_map(tenant.id)
    
    async with TenantSession(tenant.schema_name) as session:
        result = await session.execute(
            select(Opportunity).where(Opportunity.id == opportunity_id)
        )
        opportunity = result.scalar_one_or_none()
        
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        customer_result = await session.execute(
            select(Customer.company_name).where(Customer.id == opportunity.customer_id)
        )
        customer_name = customer_result.scalar_one_or_none()
        
        response = OpportunityResponse.model_validate(opportunity)
        response.owner_name = user_map.get(opportunity.owner_id)
        response.customer_name = customer_name
        
        return response

@router.put("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def update_opportunity(
    opportunity_id: int,
    opportunity_data: OpportunityUpdate,
    user_data: tuple = Depends(get_current_user)
):
    user, tenant = user_data
    user_map = await get_user_map(tenant.id)
    
    async with TenantSession(tenant.schema_name) as session:
        result = await session.execute(
            select(Opportunity).where(Opportunity.id == opportunity_id)
        )
        opportunity = result.scalar_one_or_none()
        
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        update_data = opportunity_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(opportunity, key, value)
        
        await session.commit()
        await session.refresh(opportunity)
        
        customer_result = await session.execute(
            select(Customer.company_name).where(Customer.id == opportunity.customer_id)
        )
        customer_name = customer_result.scalar_one_or_none()
        
        response = OpportunityResponse.model_validate(opportunity)
        response.owner_name = user_map.get(opportunity.owner_id)
        response.customer_name = customer_name
        
        return response

@router.delete("/opportunities/{opportunity_id}")
async def delete_opportunity(
    opportunity_id: int,
    user_data: tuple = Depends(get_current_active_admin)
):
    user, tenant = user_data
    
    async with TenantSession(tenant.schema_name) as session:
        result = await session.execute(
            select(Opportunity).where(Opportunity.id == opportunity_id)
        )
        opportunity = result.scalar_one_or_none()
        
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        await session.delete(opportunity)
        await session.commit()
        
        return {"message": "Opportunity deleted successfully"}

@router.get("/opportunity-funnel")
async def get_opportunity_funnel(
    user_data: tuple = Depends(get_current_user)
):
    user, tenant = user_data
    
    async with TenantSession(tenant.schema_name) as session:
        stage_order = {
            'initial_contact': 1,
            'requirement_confirmation': 2,
            'proposal_quote': 3,
            'negotiation': 4,
            'won': 5,
            'lost': 6
        }
        
        query = select(
            Opportunity.stage,
            func.count(Opportunity.id).label('count'),
            func.coalesce(func.sum(Opportunity.expected_amount), 0).label('amount')
        ).group_by(Opportunity.stage)
        
        result = await session.execute(query)
        rows = result.all()
        
        funnel_data = []
        for row in rows:
            funnel_data.append({
                'stage': row.stage,
                'count': row.count,
                'amount': float(row.amount) if row.amount else 0
            })
        
        funnel_data.sort(key=lambda x: stage_order.get(x['stage'], 99))
        
        return funnel_data
