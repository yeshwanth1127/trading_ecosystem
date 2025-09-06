from sqlalchemy import Column, String, Enum, DateTime, Numeric, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum
import uuid

class PlanType(str, enum.Enum):
    COPY_TRADE = "copy_trade"
    ALGO = "algo"

class PlanStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    
    plan_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(Enum(PlanType), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    features = Column(JSON, nullable=True)  # e.g., access levels, signal limits
    status = Column(Enum(PlanStatus), nullable=False, default=PlanStatus.ACTIVE)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SubscriptionPlan(plan_id={self.plan_id}, name={self.name}, type={self.type}, price={self.price})>"
