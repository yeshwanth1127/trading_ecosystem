from sqlalchemy import Column, String, Enum, Float, DateTime, ForeignKey, Boolean, Numeric, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum
import uuid

class PositionStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    LIQUIDATED = "liquidated"  # Forced liquidation

class PositionSide(str, enum.Enum):
    LONG = "long"
    SHORT = "short"

class Position(Base):
    """
    Represents user positions. Don't delete - mark closed positions as status=CLOSED.
    """
    __tablename__ = "positions"
    
    # Primary key
    position_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.account_id"), nullable=False, index=True)
    instrument_id = Column(UUID(as_uuid=True), ForeignKey("instruments.instrument_id"), nullable=False, index=True)
    
    # Position details
    status = Column(Enum(PositionStatus), nullable=False, default=PositionStatus.OPEN, index=True)
    side = Column(Enum(PositionSide), nullable=False, index=True)
    
    # Quantities and prices (using Numeric for precision)
    quantity = Column(Numeric(20, 8), nullable=False)  # Current position size
    average_entry_price = Column(Numeric(20, 8), nullable=False)  # Average entry price
    current_price = Column(Numeric(20, 8), nullable=False)  # Current market price
    mark_price = Column(Numeric(20, 8), nullable=True)  # Mark price for margin calculations
    
    # PnL calculations
    unrealized_pnl = Column(Numeric(20, 8), nullable=False, default=0.0)
    realized_pnl = Column(Numeric(20, 8), nullable=False, default=0.0)
    total_pnl = Column(Numeric(20, 8), nullable=False, default=0.0)
    
    # Margin and leverage
    leverage = Column(Numeric(8, 2), nullable=False, default=1.0)
    margin_used = Column(Numeric(20, 8), nullable=False, default=0.0)
    margin_required = Column(Numeric(20, 8), nullable=False, default=0.0)
    margin_ratio = Column(Numeric(8, 4), nullable=False, default=0.0)  # margin_used / margin_required
    
    # Risk management
    liquidation_price = Column(Numeric(20, 8), nullable=True)  # Price at which position gets liquidated
    stop_loss = Column(Numeric(20, 8), nullable=True)  # Stop loss price
    take_profit = Column(Numeric(20, 8), nullable=True)  # Take profit price
    
    # Position statistics
    total_trades = Column(Numeric(10, 0), nullable=False, default=0)  # Number of trades in this position
    total_volume = Column(Numeric(20, 8), nullable=False, default=0.0)  # Total volume traded
    total_fees = Column(Numeric(20, 8), nullable=False, default=0.0)  # Total fees paid
    
    # Timestamps
    opened_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Additional fields
    notes = Column(Text, nullable=True)
    extra_data = Column(Text, nullable=True)  # JSON metadata for additional context
    
    # Relationships
    user = relationship("User", back_populates="positions")
    account = relationship("Account", back_populates="positions")
    instrument = relationship("Instrument", back_populates="positions")
    ledger_entries = relationship("AccountLedger", back_populates="position")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_positions_user_status', 'user_id', 'status'),
        Index('idx_positions_account_status', 'account_id', 'status'),
        Index('idx_positions_instrument_status', 'instrument_id', 'status'),
        Index('idx_positions_opened_at', 'opened_at'),
        Index('idx_positions_liquidation_price', 'liquidation_price'),
    )
    
    def __repr__(self):
        return f"<Position(position_id={self.position_id}, {self.side} {self.quantity} {self.instrument.symbol if self.instrument else 'N/A'})>"
    
    def to_dict(self):
        """Convert position to dictionary for API responses"""
        return {
            "position_id": str(self.position_id),
            "user_id": str(self.user_id),
            "account_id": str(self.account_id) if self.account_id else None,
            "instrument_id": str(self.instrument_id),
            "instrument_symbol": self.instrument.symbol if self.instrument else None,
            "side": self.side.value if self.side else None,
            "quantity": float(self.quantity) if self.quantity else 0,
            "average_entry_price": float(self.average_entry_price) if self.average_entry_price else 0,
            "current_price": float(self.current_price) if self.current_price else 0,
            "mark_price": float(self.mark_price) if self.mark_price else 0,
            "unrealized_pnl": float(self.unrealized_pnl) if self.unrealized_pnl else 0,
            "realized_pnl": float(self.realized_pnl) if self.realized_pnl else 0,
            "total_pnl": float(self.total_pnl) if self.total_pnl else 0,
            "margin_used": float(self.margin_used) if self.margin_used else 0,
            "margin_required": float(self.margin_required) if self.margin_required else 0,
            "margin_ratio": float(self.margin_ratio) if self.margin_ratio else 0,
            "leverage": float(self.leverage) if self.leverage else 1,
            "liquidation_price": float(self.liquidation_price) if self.liquidation_price else None,
            "stop_loss": float(self.stop_loss) if self.stop_loss else None,
            "take_profit": float(self.take_profit) if self.take_profit else None,
            "status": self.status.value if self.status else None,
            "total_trades": self.total_trades,
            "total_volume": float(self.total_volume) if self.total_volume else 0,
            "total_fees": float(self.total_fees) if self.total_fees else 0,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }
