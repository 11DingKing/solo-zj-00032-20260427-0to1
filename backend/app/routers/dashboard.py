from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_, extract, case
from typing import List, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
import json
import redis.asyncio as redis
from ..database import TenantSession
from ..models import Customer, Opportunity, CustomerStatus, OpportunityStage, User
from ..schemas import DashboardStats
from ..auth import get_current_user
from ..config import settings
from ..database import get_public_schema_session

router = APIRouter(prefix="/api", tags=["dashboard"])

CACHE_TTL = 600

async def get_redis_client():
    return redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)

async def get_cached_stats(tenant_id: int) -> Dict[str, Any]:
    redis_client = await get_redis_client()
    cache_key = f"dashboard:stats:{tenant_id}"
    
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    return None

async def set_cached_stats(tenant_id: int, stats: Dict[str, Any]):
    redis_client = await get_redis_client()
    cache_key = f"dashboard:stats:{tenant_id}"
    
    await redis_client.setex(cache_key, CACHE_TTL, json.dumps(stats, default=str))

async def get_user_map(tenant_id: int) -> dict:
    with get_public_schema_session() as db:
        users = db.execute(select(User).where(User.tenant_id == tenant_id)).scalars().all()
        return {u.id: u.name for u in users}

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    refresh: bool = False,
    user_data: tuple = Depends(get_current_user)
):
    user, tenant = user_data
    user_map = await get_user_map(tenant.id)
    
    if not refresh:
        cached = await get_cached_stats(tenant.id)
        if cached:
            return DashboardStats(**cached)
    
    async with TenantSession(tenant.schema_name) as session:
        now = datetime.utcnow()
        start_of_month = datetime(now.year, now.month, 1)
        
        monthly_customers_query = select(func.count(Customer.id)).where(
            Customer.created_at >= start_of_month
        )
        monthly_customers_result = await session.execute(monthly_customers_query)
        monthly_new_customers = monthly_customers_result.scalar_one()
        
        monthly_opportunities_query = select(
            func.coalesce(func.sum(Opportunity.expected_amount), 0)
        ).where(
            and_(
                Opportunity.created_at >= start_of_month,
                Opportunity.stage == OpportunityStage.WON.value
            )
        )
        monthly_opps_result = await session.execute(monthly_opportunities_query)
        monthly_new_opportunity_amount = monthly_opps_result.scalar_one()
        
        sales_rank_query = select(
            Opportunity.owner_id,
            func.count(Opportunity.id).label('won_count'),
            func.coalesce(func.sum(Opportunity.expected_amount), 0).label('won_amount')
        ).where(
            Opportunity.stage == OpportunityStage.WON.value
        ).group_by(
            Opportunity.owner_id
        ).order_by(
            func.sum(Opportunity.expected_amount).desc()
        ).limit(10)
        
        sales_rank_result = await session.execute(sales_rank_query)
        sales_rank_rows = sales_rank_result.all()
        
        sales_rank = []
        for row in sales_rank_rows:
            sales_rank.append({
                'user_id': row.owner_id,
                'user_name': user_map.get(row.owner_id, 'Unknown'),
                'won_count': row.won_count,
                'won_amount': float(row.won_amount) if row.won_amount else 0
            })
        
        industry_query = select(
            Customer.industry,
            func.count(Customer.id).label('count')
        ).where(
            Customer.industry.isnot(None)
        ).group_by(
            Customer.industry
        ).order_by(
            func.count(Customer.id).desc()
        )
        
        industry_result = await session.execute(industry_query)
        industry_rows = industry_result.all()
        
        industry_distribution = []
        for row in industry_rows:
            industry_distribution.append({
                'industry': row.industry,
                'count': row.count
            })
        
        funnel_query = select(
            Opportunity.stage,
            func.count(Opportunity.id).label('count'),
            func.coalesce(func.sum(Opportunity.expected_amount), 0).label('amount')
        ).group_by(
            Opportunity.stage
        )
        
        funnel_result = await session.execute(funnel_query)
        funnel_rows = funnel_result.all()
        
        stage_order = {
            'initial_contact': 1,
            'requirement_confirmation': 2,
            'proposal_quote': 3,
            'negotiation': 4,
            'won': 5,
            'lost': 6
        }
        
        opportunity_funnel = []
        for row in funnel_rows:
            opportunity_funnel.append({
                'stage': row.stage,
                'count': row.count,
                'amount': float(row.amount) if row.amount else 0
            })
        
        opportunity_funnel.sort(key=lambda x: stage_order.get(x['stage'], 99))
        
        monthly_trend = []
        for i in range(11, -1, -1):
            month_date = now - timedelta(days=i*30)
            year = month_date.year
            month = month_date.month
            
            trend_query = select(
                func.coalesce(func.sum(Opportunity.expected_amount), 0)
            ).where(
                and_(
                    Opportunity.stage == OpportunityStage.WON.value,
                    extract('year', Opportunity.created_at) == year,
                    extract('month', Opportunity.created_at) == month
                )
            )
            
            trend_result = await session.execute(trend_query)
            amount = trend_result.scalar_one()
            
            monthly_trend.append({
                'month': f"{year}-{month:02d}",
                'amount': float(amount) if amount else 0
            })
        
        stats = {
            'monthly_new_customers': monthly_new_customers,
            'monthly_new_opportunity_amount': float(monthly_new_opportunity_amount) if monthly_new_opportunity_amount else 0,
            'sales_rank': sales_rank,
            'industry_distribution': industry_distribution,
            'opportunity_funnel': opportunity_funnel,
            'monthly_trend': monthly_trend
        }
        
        await set_cached_stats(tenant.id, stats)
        
        return DashboardStats(**stats)

@router.post("/dashboard/refresh")
async def refresh_dashboard(
    user_data: tuple = Depends(get_current_user)
):
    result = await get_dashboard_stats(refresh=True, user_data=user_data)
    return {"message": "Dashboard refreshed successfully", "stats": result}
