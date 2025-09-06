from sqlalchemy import Column, String, Enum, DateTime, ForeignKey, Numeric, Boolean, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum
import uuid

class TradeSide(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"

class TradeType(str, enum.Enum):
    """Type of trade execution"""
    FILL = "fill"           # Order fill/execution
    LIQUIDATION = "liquidation"  # Forced liquidation
    FUNDING = "funding"     # Funding fee payment
    ADJUSTMENT = "adjustment"  # Manual adjustment

class Trade(Base):
    """
    Represents individual trade executions (fills).
    Every fill event = new row in this table.
    """
    __tablename__ = "trades"
    
    # Primary key
    trade_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.account_id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.order_id"), nullable=True, index=True)  # Parent order
    instrument_id = Column(UUID(as_uuid=True), ForeignKey("instruments.instrument_id"), nullable=False, index=True)
    trading_challenge_id = Column(UUID(as_uuid=True), ForeignKey("trading_challenges.challenge_id"), nullable=True, index=True)
    
    # Trade details
    trade_type = Column(Enum(TradeType), nullable=False, default=TradeType.FILL, index=True)
    side = Column(Enum(TradeSide), nullable=False, index=True)
    
    # Quantities and prices (using Numeric for precision)
    quantity = Column(Numeric(20, 8), nullable=False)
    entry_price = Column(Numeric(20, 8), nullable=False)
    amount = Column(Numeric(20, 8), nullable=False)  # quantity * entry_price
    
    # Fees and costs
    commission = Column(Numeric(20, 8), nullable=False, default=0.0)
    commission_rate = Column(Numeric(8, 6), nullable=False, default=0.001)
    funding_fee = Column(Numeric(20, 8), nullable=False, default=0.0)
    
    # Margin and leverage
    leverage = Column(Numeric(8, 2), nullable=False, default=1.0)
    margin_used = Column(Numeric(20, 8), nullable=False, default=0.0)
    
    # PnL tracking (for position-closing trades)
    realized_pnl = Column(Numeric(20, 8), nullable=True)  # PnL realized from this trade
    unrealized_pnl = Column(Numeric(20, 8), nullable=True)  # PnL before this trade
    
    # Trade execution details
    is_maker = Column(Boolean, nullable=False, default=False)  # True if this was a maker trade
    execution_id = Column(String(100), nullable=True, index=True)  # Exchange execution ID
    liquidity = Column(String(20), nullable=True)  # "maker" or "taker"
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)  # Actual execution time
    
    # Additional fields
    notes = Column(Text, nullable=True)
    extra_data = Column(Text, nullable=True)  # JSON metadata for additional context
    
    # Relationships
    account = relationship("Account", back_populates="trades")
    user = relationship("User", back_populates="trades")
    order = relationship("Order", back_populates="trades")
    instrument = relationship("Instrument", back_populates="trades")
    trading_challenge = relationship("TradingChallenge", back_populates="trades")
    ledger_entries = relationship("AccountLedger", back_populates="trade")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_trades_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_trades_account_timestamp', 'account_id', 'timestamp'),
        Index('idx_trades_instrument_timestamp', 'instrument_id', 'timestamp'),
        Index('idx_trades_order_id', 'order_id'),
        Index('idx_trades_execution_id', 'execution_id'),
    )
    
    def __repr__(self):
        return f"<Trade(trade_id={self.trade_id}, instrument_id={self.instrument_id}, side={self.side}, quantity={self.quantity})>"
