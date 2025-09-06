from sqlalchemy import Column, String, Enum, DateTime, Numeric, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum
import uuid

class ChallengeStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"

class ChallengeType(str, enum.Enum):
    FUNDED = "funded"
    DEMO = "demo"
    EVALUATION = "evaluation"

class ChallengeCategory(str, enum.Enum):
    STOCKS = "stocks"
    CRYPTO = "crypto"

class ChallengeTemplate(Base):
    __tablename__ = "challenge_templates"
    
    challenge_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    challenge_type = Column(Enum(ChallengeType), nullable=False, default=ChallengeType.FUNDED)
    category = Column(Enum(ChallengeCategory), nullable=False, default=ChallengeCategory.STOCKS)
    
    # Financial details
    account_size = Column(Numeric(15, 2), nullable=False)  # e.g., 50000.00 for ₹50,000
    fee_amount = Column(Numeric(10, 2), nullable=False)    # e.g., 2499.00 for ₹2,499
    currency = Column(String(3), nullable=False, default='INR')
    
    # Challenge rules
    profit_target_pct = Column(Numeric(5, 2), nullable=False, default=10.00)   # 10% profit target
    max_drawdown_pct = Column(Numeric(5, 2), nullable=False, default=10.00)    # 10% trailing drawdown
    daily_loss_pct = Column(Numeric(5, 2), nullable=False, default=5.00)       # 5% daily loss limit
    
    # Additional rules
    min_trading_days = Column(Numeric(3, 0), nullable=True, default=5)         # Minimum trading days
    max_challenge_days = Column(Numeric(4, 0), nullable=True, default=30)      # Maximum challenge duration
    weekend_holding = Column(Boolean, nullable=False, default=True)            # Allow weekend holding
    news_trading = Column(Boolean, nullable=False, default=True)               # Allow news trading
    
    # Status and metadata
    status = Column(Enum(ChallengeStatus), nullable=False, default=ChallengeStatus.ACTIVE)
    is_featured = Column(Boolean, nullable=False, default=False)               # Featured challenge
    sort_order = Column(Numeric(3, 0), nullable=True, default=0)               # Display order
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    challenge_attempts = relationship("ChallengeAttempt", back_populates="challenge_template", cascade="all, delete-orphan")
    
    @property
    def profit_target_amount(self):
        """Calculate profit target amount in currency"""
        return self.account_size * (self.profit_target_pct / 100)
    
    @property
    def max_drawdown_amount(self):
        """Calculate maximum drawdown amount in currency"""
        return self.account_size * (self.max_drawdown_pct / 100)
    
    @property
    def daily_loss_amount(self):
        """Calculate daily loss limit amount in currency"""
        return self.account_size * (self.daily_loss_pct / 100)
    
    @property
    def formatted_account_size(self):
        """Format account size for display"""
        if self.currency == 'INR':
            if self.account_size >= 100000:
                return f"₹{self.account_size / 100000:.1f} Lakh"
            else:
                return f"₹{self.account_size:,.0f}"
        return f"{self.currency} {self.account_size:,.2f}"
    
    @property
    def formatted_fee_amount(self):
        """Format fee amount for display"""
        if self.currency == 'INR':
            return f"₹{self.fee_amount:,.0f}"
        return f"{self.currency} {self.fee_amount:,.2f}"
    
    def __repr__(self):
        return f"<ChallengeTemplate(challenge_id={self.challenge_id}, name={self.name}, account_size={self.account_size})>"
