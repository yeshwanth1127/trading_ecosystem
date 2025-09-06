from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from app.crud.base import CRUDBase
from app.models.instrument import Instrument, InstrumentType
from app.schemas import InstrumentCreate, InstrumentUpdate
import logging

logger = logging.getLogger(__name__)

class CRUDInstrument(CRUDBase[Instrument]):
    """CRUD operations for Instrument model"""
    
    async def get_by_symbol(self, db: AsyncSession, *, symbol: str) -> Optional[Instrument]:
        """Get instrument by symbol"""
        try:
            result = await db.execute(
                select(Instrument).where(Instrument.symbol == symbol)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting instrument by symbol {symbol}: {e}")
            raise
    
    async def get_by_type(self, db: AsyncSession, *, type: InstrumentType) -> List[Instrument]:
        """Get all instruments by type"""
        try:
            result = await db.execute(
                select(Instrument)
                .where(Instrument.type == type)
                .where(Instrument.is_active == True)
                .order_by(Instrument.symbol)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting instruments by type {type}: {e}")
            raise
    
    async def get_active_instruments(self, db: AsyncSession) -> List[Instrument]:
        """Get all active instruments"""
        try:
            result = await db.execute(
                select(Instrument)
                .where(Instrument.is_active == True)
                .order_by(Instrument.type, Instrument.symbol)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting active instruments: {e}")
            raise
    
    async def update_price(self, db: AsyncSession, *, instrument_id: str, current_price: float, 
                          price_change_24h: Optional[float] = None, volume_24h: Optional[float] = None,
                          market_cap: Optional[float] = None) -> Optional[Instrument]:
        """Update instrument price and market data"""
        try:
            update_data = {
                "current_price": current_price,
                "last_updated": func.now()
            }
            
            if price_change_24h is not None:
                update_data["price_change_24h"] = price_change_24h
            if volume_24h is not None:
                update_data["volume_24h"] = volume_24h
            if market_cap is not None:
                update_data["market_cap"] = market_cap
            
            result = await db.execute(
                update(Instrument)
                .where(Instrument.instrument_id == instrument_id)
                .values(**update_data)
                .returning(Instrument)
            )
            
            await db.commit()
            return result.scalar_one_or_none()
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating instrument price for {instrument_id}: {e}")
            raise
    
    async def search_instruments(self, db: AsyncSession, *, query: str, limit: int = 20) -> List[Instrument]:
        """Search instruments by symbol or name"""
        try:
            search_term = f"%{query}%"
            result = await db.execute(
                select(Instrument)
                .where(Instrument.is_active == True)
                .where(
                    (Instrument.symbol.ilike(search_term)) |
                    (Instrument.name.ilike(search_term))
                )
                .limit(limit)
                .order_by(Instrument.symbol)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error searching instruments with query '{query}': {e}")
            raise

instrument = CRUDInstrument(Instrument)
