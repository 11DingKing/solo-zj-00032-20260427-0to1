from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric, Enum, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    SALES = "sales"
    READ_ONLY = "read_only"

class CustomerStatus(str, enum.Enum):
    POTENTIAL = "potential"
    INTERESTED = "interested"
    OPPORTUNITY = "opportunity"
    CLOSED = "closed"
    LOST = "lost"

class OpportunityStage(str, enum.Enum):
    INITIAL_CONTACT = "initial_contact"
    REQUIREMENT_CONFIRMATION = "requirement_confirmation"
    PROPOSAL_QUOTE = "proposal_quote"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"

class FollowUpMethod(str, enum.Enum):
    PHONE = "phone"
    VISIT = "visit"
    WECHAT = "wechat"
    EMAIL = "email"

class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), unique=True, nullable=False)
    schema_name = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.SALES, nullable=False)
    is_active = Column(String(10), default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False)
    industry = Column(String(100))
    scale = Column(String(50))
    address = Column(String(500))
    website = Column(String(255))
    remark = Column(Text)
    status = Column(Enum(CustomerStatus), default=CustomerStatus.POTENTIAL)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    contacts = relationship("Contact", back_populates="customer", cascade="all, delete-orphan")
    opportunities = relationship("Opportunity", back_populates="customer", cascade="all, delete-orphan")
    follow_ups = relationship("FollowUpRecord", back_populates="customer", cascade="all, delete-orphan")
    status_logs = relationship("CustomerStatusLog", back_populates="customer", cascade="all, delete-orphan")

class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    name = Column(String(100), nullable=False)
    position = Column(String(100))
    phone = Column(String(50))
    email = Column(String(255))
    wechat = Column(String(100))
    is_primary = Column(String(10), default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    customer = relationship("Customer", back_populates="contacts")

class Opportunity(Base):
    __tablename__ = "opportunities"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    name = Column(String(255), nullable=False)
    expected_amount = Column(Numeric(12, 2))
    expected_close_date = Column(Date)
    stage = Column(Enum(OpportunityStage), default=OpportunityStage.INITIAL_CONTACT)
    owner_id = Column(Integer, ForeignKey("users.id"))
    competitor_info = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    customer = relationship("Customer", back_populates="opportunities")

class FollowUpRecord(Base):
    __tablename__ = "follow_up_records"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    method = Column(Enum(FollowUpMethod), nullable=False)
    content = Column(Text, nullable=False)
    next_follow_up_time = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    customer = relationship("Customer", back_populates="follow_ups")

class CustomerStatusLog(Base):
    __tablename__ = "customer_status_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    old_status = Column(Enum(CustomerStatus), nullable=False)
    new_status = Column(Enum(CustomerStatus), nullable=False)
    remark = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    customer = relationship("Customer", back_populates="status_logs")
