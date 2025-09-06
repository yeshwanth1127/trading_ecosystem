from sqlalchemy import Column, String, Enum, DateTime, ForeignKey, Numeric, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum
import uuid

class LedgerEntryType(str, enum.Enum):
    """Types of ledger entries for immutable financial journal"""
    DEPOSIT = "deposit"           # Initial deposit or funding
    WITHDRAWAL = "withdrawal"     # Withdrawal of funds
    PNL = "pnl"                  # Profit/Loss from trading
    FEE = "fee"                  # Trading fees, commissions
    MARGIN_CALL = "margin_call"   # Margin call requirement
    INTEREST = "interest"         # Interest earned/paid
    DIVIDEND = "dividend"         # Dividend payments
    REFUND = "refund"            # Refunds or corrections
    BONUS = "bonus"              # Bonus credits
    PENALTY = "penalty"          # Penalties or fines
    POSITION_CLOSE = "position_close"  # Position close P&L

class LedgerEntryStatus(str, enum.Enum):
    """Status of ledger entries"""
    PENDING = "pending"          # Entry is pending processing
    COMPLETED = "completed"      # Entry has been processed
    FAILED = "failed"           # Entry failed to process
    CANCELLED = "cancelled"     # Entry was cancelled

class AccountLedger(Base):
    """
    Immutable journal of all financial transactions for audit trail.
    This table should NEVER be updated - only new entries added.
    """
    __tablename__ = "account_ledger"
    
    # Primary key
    ledger_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.account_id"), nullable=False, index=True)
    
    # Optional references to related entities
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.order_id"), nullable=True, index=True)
    trade_id = Column(UUID(as_uuid=True), ForeignKey("trades.trade_id"), nullable=True, index=True)
    position_id = Column(UUID(as_uuid=True), ForeignKey("positions.position_id"), nullable=True, index=True)
    
    # Entry details
    entry_type = Column(Enum(LedgerEntryType), nullable=False, index=True)
    status = Column(Enum(LedgerEntryStatus), nullable=False, default=LedgerEntryStatus.COMPLETED, index=True)
    
    # Financial amounts (using Numeric for precision)
    amount = Column(Numeric(20, 8), nullable=False)  # Can be positive or negative
    balance_before = Column(Numeric(20, 8), nullable=False)  # Balance before this transaction
    balance_after = Column(Numeric(20, 8), nullable=False)   # Balance after this transaction
    
    # Additional financial tracking
    currency = Column(String(10), nullable=False, default="USD")  # Currency of the transaction
    exchange_rate = Column(Numeric(15, 8), nullable=True)  # Exchange rate if currency conversion
    
    # Metadata
    description = Column(Text, nullable=True)  # Human-readable description
    reference_id = Column(String(100), nullable=True, index=True)  # External reference (payment ID, etc.)
    extra_data = Column(Text, nullable=True)  # JSON metadata for additional context
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)  # When the entry was processed
    
    # Relationships
    user = relationship("User", back_populates="ledger_entries")
    account = relationship("Account", back_populates="ledger_entries")
    order = relationship("Order", back_populates="ledger_entries")
    trade = relationship("Trade", back_populates="ledger_entries")
    position = relationship("Position", back_populates="ledger_entries")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_ledger_user_account_type', 'user_id', 'account_id', 'entry_type'),
        Index('idx_ledger_user_timestamp', 'user_id', 'created_at'),
        Index('idx_ledger_account_timestamp', 'account_id', 'created_at'),
        Index('idx_ledger_type_timestamp', 'entry_type', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AccountLedger(ledger_id={self.ledger_id}, type={self.entry_type}, amount={self.amount}, balance_after={self.balance_after})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "entry_id": str(self.ledger_id),
            "user_id": str(self.user_id),
            "account_id": str(self.account_id),
            "entry_type": self.entry_type.value,
            "status": self.status.value,
            "amount": float(self.amount),
            "balance_before": float(self.balance_before),
            "balance_after": float(self.balance_after),
            "currency": self.currency,
            "description": self.description,
            "reference_id": self.reference_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }
