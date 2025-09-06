from sqlalchemy import Column, String, Enum, Float, DateTime, ForeignKey, Text, Numeric, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum
import uuid

class OrderType(str, enum.Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderSide(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"

class OrderTimeInForce(str, enum.Enum):
    GTC = "gtc"  # Good Till Cancelled
    IOC = "ioc"  # Immediate or Cancel
    FOK = "fok"  # Fill or Kill
    DAY = "day"  # Day order

class Order(Base):
    __tablename__ = "orders"
    
    # Primary key
    order_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.account_id"), nullable=False, index=True)
    instrument_id = Column(UUID(as_uuid=True), ForeignKey("instruments.instrument_id"), nullable=False, index=True)
    
    # Order details
    order_type = Column(Enum(OrderType), nullable=False, index=True)
    side = Column(Enum(OrderSide), nullable=False, index=True)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING, index=True)
    time_in_force = Column(Enum(OrderTimeInForce), nullable=False, default=OrderTimeInForce.GTC)
    
    # Quantities and prices (using Numeric for precision)
    quantity = Column(Numeric(20, 8), nullable=False)
    filled_quantity = Column(Numeric(20, 8), nullable=False, default=0.0)
    remaining_quantity = Column(Numeric(20, 8), nullable=False)  # quantity - filled_quantity
    
    # Price fields
    price = Column(Numeric(20, 8), nullable=True)  # NULL for market orders
    stop_price = Column(Numeric(20, 8), nullable=True)  # For stop orders
    average_fill_price = Column(Numeric(20, 8), nullable=True)  # Average price of fills
    
    # Financial calculations
    total_amount = Column(Numeric(20, 8), nullable=False)  # quantity * price
    filled_amount = Column(Numeric(20, 8), nullable=False, default=0.0)  # filled_quantity * average_fill_price
    remaining_amount = Column(Numeric(20, 8), nullable=False)  # total_amount - filled_amount
    
    # Fees and costs
    commission = Column(Numeric(20, 8), nullable=False, default=0.0)
    commission_rate = Column(Numeric(8, 6), nullable=False, default=0.001)  # 0.1% default
    
    # Margin and leverage
    leverage = Column(Numeric(8, 2), nullable=False, default=1.0)  # 1x to 100x
    margin_required = Column(Numeric(20, 8), nullable=False, default=0.0)
    margin_used = Column(Numeric(20, 8), nullable=False, default=0.0)
    
    # Order management
    is_margin_order = Column(Boolean, nullable=False, default=False)
    reduce_only = Column(Boolean, nullable=False, default=False)  # Only reduce position size
    post_only = Column(Boolean, nullable=False, default=False)  # Maker only order
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    filled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    expired_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional fields
    client_order_id = Column(String(100), nullable=True, index=True)  # Client-provided order ID
    notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)  # Reason for rejection
    
    # Relationships
    user = relationship("User", back_populates="orders")
    account = relationship("Account", back_populates="orders")
    instrument = relationship("Instrument", back_populates="orders")
    trades = relationship("Trade", back_populates="order")
    ledger_entries = relationship("AccountLedger", back_populates="order")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_orders_user_status', 'user_id', 'status'),
        Index('idx_orders_account_status', 'account_id', 'status'),
        Index('idx_orders_instrument_status', 'instrument_id', 'status'),
        Index('idx_orders_created_at', 'created_at'),
        Index('idx_orders_client_order_id', 'client_order_id'),
    )

    
    def __repr__(self):
        return f"<Order(order_id={self.order_id}, {self.side} {self.quantity} {self.instrument.symbol if self.instrument else 'N/A'})>"
    
    def to_dict(self):
        """Convert order to dictionary for API responses"""
        return {
            "order_id": str(self.order_id),
            "user_id": str(self.user_id),
            "account_id": str(self.account_id) if self.account_id else None,
            "instrument_id": str(self.instrument_id),
            "instrument_symbol": self.instrument.symbol if self.instrument else None,
            "side": self.side.value if self.side else None,
            "order_type": self.order_type.value if self.order_type else None,
            "quantity": float(self.quantity) if self.quantity else 0,
            "price": float(self.price) if self.price else None,
            "stop_price": float(self.stop_price) if self.stop_price else None,
            "total_amount": float(self.total_amount) if self.total_amount else 0,
            "filled_amount": float(self.filled_amount) if self.filled_amount else 0,
            "remaining_amount": float(self.remaining_amount) if self.remaining_amount else 0,
            "status": self.status.value if self.status else None,
            "time_in_force": self.time_in_force.value if self.time_in_force else None,
            "filled_quantity": float(self.filled_quantity) if self.filled_quantity else 0,
            "remaining_quantity": float(self.remaining_quantity) if self.remaining_quantity else 0,
            "average_fill_price": float(self.average_fill_price) if self.average_fill_price else None,
            "commission": float(self.commission) if self.commission else 0,
            "leverage": float(self.leverage) if self.leverage else 1,
            "margin_used": float(self.margin_used) if self.margin_used else 0,
            "is_margin_order": self.is_margin_order,
            "client_order_id": self.client_order_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
