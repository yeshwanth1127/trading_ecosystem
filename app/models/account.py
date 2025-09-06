from sqlalchemy import Column, String, Enum, DateTime, Numeric, ForeignKey, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum
import uuid

class AccountType(str, enum.Enum):
    SIMULATED = "simulated"
    COPY = "copy"
    ALGO = "algo"
    LIVE = "live"  # Real money trading

class AccountStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"

class Account(Base):
    __tablename__ = "accounts"
    
    # Primary key
    account_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    
    # Account details
    type = Column(Enum(AccountType), nullable=False, index=True)
    status = Column(Enum(AccountStatus), nullable=False, default=AccountStatus.ACTIVE, index=True)
    
    # Financial balances (using Numeric for precision)
    balance = Column(Numeric(20, 8), nullable=False, default=0.00)  # Available balance
    equity = Column(Numeric(20, 8), nullable=False, default=0.00)  # Total equity (balance + unrealized PnL)
    margin_used = Column(Numeric(20, 8), nullable=False, default=0.00)  # Total margin used
    margin_available = Column(Numeric(20, 8), nullable=False, default=0.00)  # Available margin
    unrealized_pnl = Column(Numeric(20, 8), nullable=False, default=0.00)  # Total unrealized PnL
    realized_pnl = Column(Numeric(20, 8), nullable=False, default=0.00)  # Total realized PnL
    
    # Risk management
    max_leverage = Column(Numeric(8, 2), nullable=False, default=1.0)  # Maximum allowed leverage
    margin_call_threshold = Column(Numeric(8, 4), nullable=False, default=0.8)  # 80% margin call
    liquidation_threshold = Column(Numeric(8, 4), nullable=False, default=0.5)  # 50% liquidation
    
    # Account settings
    is_margin_enabled = Column(Boolean, nullable=False, default=False)
    auto_liquidation = Column(Boolean, nullable=False, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    challenge_attempts = relationship("ChallengeAttempt", back_populates="account", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="account", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="account", cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="account", cascade="all, delete-orphan")
    ledger_entries = relationship("AccountLedger", back_populates="account", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_accounts_user_type', 'user_id', 'type'),
        Index('idx_accounts_user_status', 'user_id', 'status'),
        Index('idx_accounts_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Account(account_id={self.account_id}, user_id={self.user_id}, type={self.type}, balance={self.balance})>"
