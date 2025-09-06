from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum

# Enums
class InstrumentType(str, Enum):
    CRYPTO = "crypto"
    STOCK = "stock"

class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(str, Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class PositionStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"

# Instrument Schemas
class InstrumentBase(BaseModel):
    symbol: str = Field(..., description="Instrument symbol (e.g., BTC, AAPL)")
    name: str = Field(..., description="Instrument name")
    type: InstrumentType = Field(..., description="Instrument type")
    current_price: float = Field(..., description="Current market price")
    price_change_24h: Optional[float] = Field(None, description="24h price change percentage")
    volume_24h: Optional[float] = Field(None, description="24h trading volume")
    market_cap: Optional[float] = Field(None, description="Market capitalization")

class InstrumentCreate(InstrumentBase):
    pass

class InstrumentUpdate(BaseModel):
    current_price: Optional[float] = None
    price_change_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    market_cap: Optional[float] = None

class InstrumentResponse(InstrumentBase):
    instrument_id: UUID
    is_active: bool
    last_updated: datetime
    
    class Config:
        from_attributes = True

class InstrumentListResponse(BaseModel):
    instruments: List[InstrumentResponse]
    total: int

# Order Schemas
class OrderBase(BaseModel):
    instrument_id: UUID = Field(..., description="Instrument to trade")
    order_type: OrderType = Field(..., description="Type of order")
    side: OrderSide = Field(..., description="Buy or sell")
    quantity: float = Field(..., gt=0, description="Quantity to trade")
    price: Optional[float] = Field(None, gt=0, description="Limit price (required for limit orders)")
    stop_price: Optional[float] = Field(None, gt=0, description="Stop price for stop orders")
    notes: Optional[str] = Field(None, description="Order notes")

class OrderCreate(OrderBase):
    @validator('price')
    def validate_price(cls, v, values):
        if values.get('order_type') in ['limit', 'stop_limit'] and v is None:
            raise ValueError('Price is required for limit and stop-limit orders')
        return v

class OrderCreateWithSymbol(BaseModel):
    """Order creation schema that accepts instrument symbol instead of ID"""
    instrument_symbol: str = Field(..., description="Instrument symbol (e.g., BTCUSDT, RELIANCE)")
    order_type: OrderType = Field(..., description="Type of order")
    side: OrderSide = Field(..., description="Buy or sell")
    quantity: float = Field(..., gt=0, description="Quantity to trade")
    price: Optional[float] = Field(None, gt=0, description="Limit price (required for limit orders)")
    stop_price: Optional[float] = Field(None, gt=0, description="Stop price for stop orders")
    leverage: Optional[float] = Field(1.0, ge=1.0, le=100.0, description="Leverage for margin trading")
    is_margin_order: Optional[bool] = Field(False, description="Whether this is a margin order")
    notes: Optional[str] = Field(None, description="Order notes")
    
    @validator('price')
    def validate_price(cls, v, values):
        if values.get('order_type') in ['limit', 'stop_limit'] and v is None:
            raise ValueError('Price is required for limit and stop-limit orders')
        return v

class OrderUpdate(BaseModel):
    price: Optional[float] = None
    stop_price: Optional[float] = None
    notes: Optional[str] = None

class OrderResponse(OrderBase):
    order_id: UUID
    user_id: UUID
    status: OrderStatus
    filled_quantity: float
    total_amount: float
    commission: float
    created_at: datetime
    updated_at: datetime
    filled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int

# Position Schemas
class PositionBase(BaseModel):
    instrument_id: UUID = Field(..., description="Instrument")
    side: str = Field(..., description="Long or short position")
    quantity: float = Field(..., gt=0, description="Position quantity")
    average_entry_price: float = Field(..., gt=0, description="Average entry price")
    leverage: float = Field(..., gt=0, description="Leverage used")

class PositionCreate(PositionBase):
    pass

class PositionUpdate(BaseModel):
    current_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    realized_pnl: Optional[float] = None

class PositionResponse(PositionBase):
    position_id: UUID
    user_id: UUID
    status: PositionStatus
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    total_pnl: float
    margin_used: float
    opened_at: datetime
    closed_at: Optional[datetime] = None
    last_updated: datetime
    
    class Config:
        from_attributes = True

class PositionListResponse(BaseModel):
    positions: List[PositionResponse]
    total: int

# Trading Dashboard Schemas
class TradingSummary(BaseModel):
    total_balance: float
    available_balance: float
    margin_used: float
    unrealized_pnl: float
    realized_pnl: float
    total_pnl: float
    total_equity: float  # available_balance + unrealized_pnl
    open_positions_count: int
    pending_orders_count: int

class ChartDataPoint(BaseModel):
    timestamp: datetime
    price: float
    volume: float

class ChartData(BaseModel):
    instrument_id: UUID
    symbol: str
    timeframe: str
    data: List[ChartDataPoint]

# Market Data Schemas
class MarketData(BaseModel):
    instrument_id: UUID
    symbol: str
    name: str
    type: InstrumentType
    current_price: float
    price_change_24h: float
    price_change_percent_24h: float
    volume_24h: float
    market_cap: float
    high_24h: float
    low_24h: float
    last_updated: datetime

class MarketDataListResponse(BaseModel):
    instruments: List[MarketData]
    total: int
