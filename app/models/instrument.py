from sqlalchemy import Column, String, Enum, Boolean, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum
import uuid

class InstrumentType(str, enum.Enum):
    CRYPTO = "crypto"
    STOCK = "stock"

class Instrument(Base):
    __tablename__ = "instruments"
    
    instrument_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), nullable=False, unique=True, index=True)  # e.g., "BTC", "AAPL"
    name = Column(String(100), nullable=False)  # e.g., "Bitcoin", "Apple Inc."
    type = Column(Enum(InstrumentType), nullable=False, index=True)
    current_price = Column(Float, nullable=False, default=0.0)
    price_change_24h = Column(Float, nullable=True)  # 24h price change in percentage
    volume_24h = Column(Float, nullable=True)
    market_cap = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    orders = relationship("Order", back_populates="instrument")
    positions = relationship("Position", back_populates="instrument")
    trades = relationship("Trade", back_populates="instrument")
    
    def __repr__(self):
        return f"<Instrument(symbol={self.symbol}, name={self.name}, type={self.type})>"
