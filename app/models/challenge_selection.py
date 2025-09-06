from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum
import uuid

class ChallengeSelectionStatus(str, enum.Enum):
    ACTIVE = "active"      # Default status when challenge is selected
    TRADING = "trading"    # Status when user starts placing trades
    COMPLETED = "completed" # Status when challenge is completed
    CANCELLED = "cancelled" # Status when challenge is cancelled

class ChallengeCategory(str, enum.Enum):
    STOCKS = "stocks"
    CRYPTO = "crypto"

class ChallengeSelection(Base):
    __tablename__ = "challenge_selections"
    
    selection_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    challenge_id = Column(String(255), nullable=False)  # Frontend challenge identifier
    amount = Column(String(255), nullable=False)  # Challenge amount (e.g., "₹50,000" or "$5,000")
    price = Column(String(255), nullable=False)  # Challenge price (e.g., "₹999" or "$39")
    profit_target = Column(String(255), nullable=False)  # Profit target (e.g., "₹5,000" or "$500")
    max_drawdown = Column(String(255), nullable=False)  # Max drawdown (e.g., "₹5,000" or "$4,500")
    daily_limit = Column(String(255), nullable=False)  # Daily limit (e.g., "₹2,500" or "$250")
    category = Column(Enum(ChallengeCategory), nullable=False, default=ChallengeCategory.STOCKS)  # Challenge category
    status = Column(Enum(ChallengeSelectionStatus), nullable=False, default=ChallengeSelectionStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    activated_at = Column(DateTime(timezone=True), nullable=True)
    trading_started_at = Column(DateTime(timezone=True), nullable=True)  # When trading begins
    
    # Relationships
    user = relationship("User", back_populates="challenge_selections")
    trading_challenge = relationship("TradingChallenge", back_populates="selection", uselist=False)
    
    def __repr__(self):
        return f"<ChallengeSelection(selection_id={self.selection_id}, user_id={self.user_id}, challenge_id={self.challenge_id})>"
