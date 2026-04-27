from fastapi import APIRouter, Depends, UploadFile, File, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from typing import Optional, List, Dict, Any
import io
import csv
from ..database import TenantSession
from ..models import Customer, Contact, Opportunity, User, CustomerStatus, OpportunityStage
from ..schemas import ImportResult
from ..auth import get_current_user
from ..database import get_public_schema_session

router = APIRouter(prefix="/api", tags=["import_export"])

FIELD_MAPPINGS = {
    'company_name': ['公司名称', 'company_name', 'company'],
    'industry': ['行业', 'industry'],
    'scale': ['规模', 'scale', '企业规模'],
    'address': ['地址', 'address'],
    'website': ['官网', 'website', '网址'],
    'remark': ['备注', 'remark'],
    'contact_name': ['联系人姓名', '联系人', 'contact_name', 'contact'],
    'contact_position': ['职位', 'contact_position', 'position'],
    'contact_phone': ['电话', '手机', 'contact_phone', 'phone'],
    'contact_email': ['邮箱', 'contact_email', 'email'],
    'contact_wechat': ['微信', 'contact_wechat', 'wechat']
}

def normalize_field_name(header: str) -> Optional[str]:
    header_lower = header.strip().lower()
    for field_name, aliases in FIELD_MAPPINGS.items():
        if header_lower in [a.lower() for a in aliases]:
            return field_name
    return None

def validate_row(row: Dict[str, Any], row_num: int) -> tuple[bool, List[str]]:
    errors = []
    valid = True
    
    if not row.get('company_name'):
        errors.append(f"第 {row_num} 行：公司名称不能为空")
        valid = False
    
    if row.get('contact_email') and '@' not in row['contact_email']:
        errors.append(f"第 {row_num} 行：邮箱格式不正确")
        valid = False
    
    return valid, errors

@router.post("/import/customers", response_model=ImportResult)
async def import_customers(
    file: UploadFile = File(...),
    user_data: tuple = Depends(get_current_user)
):
    user, tenant = user_data
    
    if not file.filename.endswith('.csv'):
        return ImportResult(
            total=0,
            success=0,
            failed=0,
            errors=[{"message": "仅支持 CSV 格式文件"}]
        )
    
    contents = await file.read()
    csv_file = io.StringIO(contents.decode('utf-8-sig'))
    
    reader = csv.DictReader(csv_file)
    
    field_mapping = {}
    for header in reader.fieldnames:
        normalized = normalize_field_name(header)
        if normalized:
            field_mapping[header] = normalized
    
    success_count = 0
    failed_count = 0
    all_errors = []
    row_num = 1
    
    async with TenantSession(tenant.schema_name) as session:
        for row in reader:
            row_num += 1
            
            normalized_row = {}
            for original_header, value in row.items():
                if original_header in field_mapping:
                    normalized_row[field_mapping[original_header]] = value.strip() if value else None
            
            valid, errors = validate_row(normalized_row, row_num)
            if not valid:
                failed_count += 1
                all_errors.extend(errors)
                continue
            
            try:
                customer = Customer(
                    company_name=normalized_row.get('company_name'),
                    industry=normalized_row.get('industry'),
                    scale=normalized_row.get('scale'),
                    address=normalized_row.get('address'),
                    website=normalized_row.get('website'),
                    remark=normalized_row.get('remark'),
                    status=CustomerStatus.POTENTIAL,
                    owner_id=user.id
                )
                
                if normalized_row.get('contact_name'):
                    contact = Contact(
                        name=normalized_row.get('contact_name'),
                        position=normalized_row.get('contact_position'),
                        phone=normalized_row.get('contact_phone'),
                        email=normalized_row.get('contact_email'),
                        wechat=normalized_row.get('contact_wechat'),
                        is_primary="true"
                    )
                    customer.contacts.append(contact)
                
                session.add(customer)
                success_count += 1
                
            except Exception as e:
                failed_count += 1
                all_errors.append(f"第 {row_num} 行：{str(e)}")
        
        await session.commit()
    
    return ImportResult(
        total=success_count + failed_count,
        success=success_count,
        failed=failed_count,
        errors=[{"message": e} for e in all_errors[:100]]
    )

@router.get("/export/customers")
async def export_customers(
    user_data: tuple = Depends(get_current_user)
):
    user, tenant = user_data
    user_map = {}
    with get_public_schema_session() as db:
        users = db.execute(select(User).where(User.tenant_id == tenant.id)).scalars().all()
        user_map = {u.id: u.name for u in users}
    
    async with TenantSession(tenant.schema_name) as session:
        query = select(Customer).order_by(Customer.created_at.desc())
        result = await session.execute(query)
        customers = result.scalars().all()
        
        contact_query = select(Contact).where(
            Contact.customer_id.in_([c.id for c in customers])
        )
        contact_result = await session.execute(contact_query)
        contacts = contact_result.scalars().all()
        
        contacts_by_customer = {}
        for contact in contacts:
            if contact.customer_id not in contacts_by_customer:
                contacts_by_customer[contact.customer_id] = []
            contacts_by_customer[contact.customer_id].append(contact)
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            '公司名称', '行业', '规模', '地址', '官网', '备注', '状态', '负责人',
            '联系人姓名', '职位', '电话', '邮箱', '微信', '创建时间'
        ])
        
        status_display = {
            CustomerStatus.POTENTIAL: '潜在客户',
            CustomerStatus.INTERESTED: '意向客户',
            CustomerStatus.OPPORTUNITY: '商机客户',
            CustomerStatus.CLOSED: '成交客户',
            CustomerStatus.LOST: '流失客户'
        }
        
        for customer in customers:
            primary_contact = None
            if customer.id in contacts_by_customer:
                customer_contacts = contacts_by_customer[customer.id]
                primary_contact = next((c for c in customer_contacts if c.is_primary == "true"), None)
                if not primary_contact and customer_contacts:
                    primary_contact = customer_contacts[0]
            
            writer.writerow([
                customer.company_name or '',
                customer.industry or '',
                customer.scale or '',
                customer.address or '',
                customer.website or '',
                customer.remark or '',
                status_display.get(customer.status, customer.status.value) if customer.status else '',
                user_map.get(customer.owner_id, '') or '',
                primary_contact.name if primary_contact else '',
                primary_contact.position if primary_contact else '',
                primary_contact.phone if primary_contact else '',
                primary_contact.email if primary_contact else '',
                primary_contact.wechat if primary_contact else '',
                customer.created_at.strftime('%Y-%m-%d %H:%M:%S') if customer.created_at else ''
            ])
        
        output.seek(0)
        content = output.getvalue().encode('utf-8-sig')
        
        return Response(
            content=content,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": "attachment; filename=customers.csv"
            }
        )

@router.get("/export/opportunities")
async def export_opportunities(
    user_data: tuple = Depends(get_current_user)
):
    user, tenant = user_data
    user_map = {}
    with get_public_schema_session() as db:
        users = db.execute(select(User).where(User.tenant_id == tenant.id)).scalars().all()
        user_map = {u.id: u.name for u in users}
    
    async with TenantSession(tenant.schema_name) as session:
        query = select(Opportunity).order_by(Opportunity.created_at.desc())
        result = await session.execute(query)
        opportunities = result.scalars().all()
        
        customer_ids = [o.customer_id for o in opportunities]
        customer_map = {}
        if customer_ids:
            customer_query = select(Customer.id, Customer.company_name).where(
                Customer.id.in_(customer_ids)
            )
            customer_result = await session.execute(customer_query)
            customer_map = {r[0]: r[1] for r in customer_result.all()}
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            '商机名称', '客户名称', '预计金额', '预计成交日期', '阶段', '负责人',
            '竞争对手信息', '创建时间'
        ])
        
        stage_display = {
            OpportunityStage.INITIAL_CONTACT: '初步接触',
            OpportunityStage.REQUIREMENT_CONFIRMATION: '需求确认',
            OpportunityStage.PROPOSAL_QUOTE: '方案报价',
            OpportunityStage.NEGOTIATION: '商务谈判',
            OpportunityStage.WON: '赢单',
            OpportunityStage.LOST: '输单'
        }
        
        for opp in opportunities:
            writer.writerow([
                opp.name or '',
                customer_map.get(opp.customer_id, '') or '',
                float(opp.expected_amount) if opp.expected_amount else '',
                opp.expected_close_date.strftime('%Y-%m-%d') if opp.expected_close_date else '',
                stage_display.get(opp.stage, opp.stage.value) if opp.stage else '',
                user_map.get(opp.owner_id, '') or '',
                opp.competitor_info or '',
                opp.created_at.strftime('%Y-%m-%d %H:%M:%S') if opp.created_at else ''
            ])
        
        output.seek(0)
        content = output.getvalue().encode('utf-8-sig')
        
        return Response(
            content=content,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": "attachment; filename=opportunities.csv"
            }
        )

@router.get("/import/template")
async def get_import_template():
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        '公司名称', '行业', '规模', '地址', '官网', '备注',
        '联系人姓名', '职位', '电话', '邮箱', '微信'
    ])
    
    writer.writerow([
        '示例科技有限公司', '互联网', '50-100人', '北京市朝阳区xxx路xxx号',
        'https://example.com', '这是备注信息',
        '张三', '销售总监', '13800138000', 'zhangsan@example.com', 'zhangsan_wx'
    ])
    
    output.seek(0)
    content = output.getvalue().encode('utf-8-sig')
    
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=customer_import_template.csv"
        }
    )
