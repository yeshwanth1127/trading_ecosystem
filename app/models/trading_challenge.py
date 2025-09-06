from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum
import uuid

class ChallengeStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class TradingChallenge(Base):
    __tablename__ = "trading_challenges"
    
    challenge_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    selection_id = Column(UUID(as_uuid=True), ForeignKey("challenge_selections.selection_id"), nullable=False)
    
    # Challenge Parameters
    target_amount = Column(Numeric(15, 2), nullable=False)  # Target profit amount
    max_drawdown_amount = Column(Numeric(15, 2), nullable=False)  # Maximum allowed drawdown
    daily_loss_limit = Column(Numeric(15, 2), nullable=False)  # Daily loss limit
    
    # Current State
    current_balance = Column(Numeric(15, 2), nullable=False)  # Current account balance
    peak_balance = Column(Numeric(15, 2), nullable=False)  # Highest balance reached
    current_drawdown = Column(Numeric(15, 2), nullable=False, default=0)  # Current drawdown from peak
    daily_loss = Column(Numeric(15, 2), nullable=False, default=0)  # Today's loss
    
    # Challenge Status
    status = Column(Enum(ChallengeStatus), nullable=False, default=ChallengeStatus.ACTIVE)
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Win/Loss Conditions
    is_profit_target_reached = Column(Boolean, default=False)
    is_drawdown_breached = Column(Boolean, default=False)
    is_daily_limit_breached = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="trading_challenges")
    selection = relationship("ChallengeSelection", back_populates="trading_challenge")
    trades = relationship("Trade", back_populates="trading_challenge")
    
    def __repr__(self):
        return f"<TradingChallenge(challenge_id={self.challenge_id}, user_id={self.user_id}, status={self.status})>"
    
    @property
    def profit_target_reached(self) -> bool:
        """Check if profit target has been reached"""
        return self.current_balance >= self.target_amount
    
    @property
    def drawdown_breached(self) -> bool:
        """Check if max drawdown has been breached"""
        return self.current_drawdown > self.max_drawdown_amount
    
    @property
    def daily_limit_breached(self) -> bool:
        """Check if daily loss limit has been breached"""
        return self.daily_loss > self.daily_loss_limit
    
    def calculate_drawdown(self) -> float:
        """Calculate current drawdown from peak balance"""
        if self.peak_balance > 0:
            return float(self.peak_balance - self.current_balance)
        return 0.0
    
    def update_balance(self, new_balance: float, trade_amount: float = 0):
        """Update challenge balance and check conditions"""
        old_balance = float(self.current_balance)
        self.current_balance = new_balance
        
        # Update peak balance if new balance is higher
        if new_balance > float(self.peak_balance):
            self.peak_balance = new_balance
        
        # Calculate drawdown
        self.current_drawdown = self.calculate_drawdown()
        
        # Update daily loss if trade resulted in a loss
        if trade_amount < 0:
            self.daily_loss += abs(trade_amount)
        
        # Check win/loss conditions
        self.check_challenge_conditions()
    
    def check_challenge_conditions(self):
        """Check if any win/loss conditions have been met"""
        # Check profit target
        if self.profit_target_reached and not self.is_profit_target_reached:
            self.is_profit_target_reached = True
            self.status = ChallengeStatus.COMPLETED
            self.end_date = func.now()
        
        # Check drawdown breach
        if self.drawdown_breached and not self.is_drawdown_breached:
            self.is_drawdown_breached = True
            self.status = ChallengeStatus.FAILED
            self.end_date = func.now()
        
        # Check daily loss limit
        if self.daily_limit_breached and not self.is_daily_limit_breached:
            self.is_daily_limit_breached = True
            self.status = ChallengeStatus.FAILED
            self.end_date = func.now()
