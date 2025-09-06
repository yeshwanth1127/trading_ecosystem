"""
Instrument Mapping Service
=========================

Provides mapping between instrument symbols and IDs for frontend-backend compatibility.
Handles instrument validation and caching for optimal performance.
"""

import asyncio
import logging
from typing import Dict, Optional, List
from uuid import UUID
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.database import AsyncSessionLocal
from app.services.redis_service import redis_service
from app.models.instrument import Instrument, InstrumentType

logger = logging.getLogger(__name__)

class InstrumentService:
    """Service for instrument symbol to ID mapping and validation"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.symbol_to_id_cache: Dict[str, UUID] = {}
        self.id_to_symbol_cache: Dict[UUID, str] = {}
        self.cache_loaded = False
        
    async def initialize(self):
        """Initialize the instrument service with Redis connection"""
        try:
            # Use centralized Redis service
            self.redis_client = redis_service.get_client()
            await self.redis_client.ping()
            logger.info("✅ Instrument Service: Redis connection established")
            
            # Load instrument cache
            await self._load_instrument_cache()
            
            logger.info("🚀 Instrument Service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Instrument Service: {e}")
            raise
    
    async def close(self):
        """Close the instrument service"""
        # Redis connection is managed by redis_service, no need to close here
        logger.info("🔒 Instrument Service closed")
    
    async def _load_instrument_cache(self):
        """Load all instruments into cache"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(Instrument)
                    .where(Instrument.is_active == True)
                )
                instruments = result.scalars().all()
                
                # Clear existing cache
                self.symbol_to_id_cache.clear()
                self.id_to_symbol_cache.clear()
                
                # Populate cache
                for instrument in instruments:
                    self.symbol_to_id_cache[instrument.symbol] = instrument.instrument_id
                    self.id_to_symbol_cache[instrument.instrument_id] = instrument.symbol
                    
                    # Also cache in Redis for persistence
                    await self.redis_client.hset(
                        "instrument_mapping",
                        instrument.symbol,
                        str(instrument.instrument_id)
                    )
                    await self.redis_client.hset(
                        "instrument_mapping_reverse",
                        str(instrument.instrument_id),
                        instrument.symbol
                    )
                
                self.cache_loaded = True
                logger.info(f"📊 Loaded {len(instruments)} instruments into cache")
                
            except Exception as e:
                logger.error(f"❌ Failed to load instrument cache: {e}")
                raise
    
    async def get_instrument_id_by_symbol(self, symbol: str) -> Optional[UUID]:
        """Get instrument ID by symbol"""
        try:
            # Check memory cache first
            if symbol in self.symbol_to_id_cache:
                return self.symbol_to_id_cache[symbol]
            
            # Check Redis cache
            if self.redis_client:
                instrument_id_str = await self.redis_client.hget("instrument_mapping", symbol)
                if instrument_id_str:
                    instrument_id = UUID(instrument_id_str)
                    # Update memory cache
                    self.symbol_to_id_cache[symbol] = instrument_id
                    return instrument_id
            
            # Fallback to database
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Instrument)
                    .where(
                        Instrument.symbol == symbol,
                        Instrument.is_active == True
                    )
                )
                instrument = result.scalar_one_or_none()
                
                if instrument:
                    # Update caches
                    self.symbol_to_id_cache[symbol] = instrument.instrument_id
                    self.id_to_symbol_cache[instrument.instrument_id] = symbol
                    
                    if self.redis_client:
                        await self.redis_client.hset(
                            "instrument_mapping",
                            symbol,
                            str(instrument.instrument_id)
                        )
                        await self.redis_client.hset(
                            "instrument_mapping_reverse",
                            str(instrument.instrument_id),
                            symbol
                        )
                    
                    return instrument.instrument_id
            
            # If not found in database, try to create from market data
            logger.info(f"🔍 Instrument {symbol} not found in database, attempting to create from market data...")
            instrument_id = await self._create_instrument_from_market_data(symbol)
            if instrument_id:
                return instrument_id
            
            logger.warning(f"⚠️ Could not create instrument for symbol: {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get instrument ID for symbol {symbol}: {e}")
            return None
    
    async def get_symbol_by_instrument_id(self, instrument_id: UUID) -> Optional[str]:
        """Get instrument symbol by ID"""
        try:
            # Check memory cache first
            if instrument_id in self.id_to_symbol_cache:
                return self.id_to_symbol_cache[instrument_id]
            
            # Check Redis cache
            if self.redis_client:
                symbol = await self.redis_client.hget("instrument_mapping_reverse", str(instrument_id))
                if symbol:
                    # Update memory cache
                    self.id_to_symbol_cache[instrument_id] = symbol
                    return symbol
            
            # Fallback to database
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Instrument)
                    .where(
                        Instrument.instrument_id == instrument_id,
                        Instrument.is_active == True
                    )
                )
                instrument = result.scalar_one_or_none()
                
                if instrument:
                    # Update caches
                    self.symbol_to_id_cache[instrument.symbol] = instrument.instrument_id
                    self.id_to_symbol_cache[instrument.instrument_id] = instrument.symbol
                    
                    if self.redis_client:
                        await self.redis_client.hset(
                            "instrument_mapping",
                            instrument.symbol,
                            str(instrument.instrument_id)
                        )
                        await self.redis_client.hset(
                            "instrument_mapping_reverse",
                            str(instrument.instrument_id),
                            instrument.symbol
                        )
                    
                    return instrument.symbol
            
            logger.warning(f"⚠️ Instrument not found for ID: {instrument_id}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get symbol for instrument ID {instrument_id}: {e}")
            return None
    
    async def validate_instrument_symbol(self, symbol: str) -> bool:
        """Validate if instrument symbol exists and is active"""
        instrument_id = await self.get_instrument_id_by_symbol(symbol)
        return instrument_id is not None
    
    async def get_all_active_instruments(self) -> List[Dict[str, str]]:
        """Get all active instruments as list of {symbol, instrument_id}"""
        try:
            if not self.cache_loaded:
                await self._load_instrument_cache()
            
            instruments = []
            for symbol, instrument_id in self.symbol_to_id_cache.items():
                instruments.append({
                    "symbol": symbol,
                    "instrument_id": str(instrument_id)
                })
            
            return instruments
            
        except Exception as e:
            logger.error(f"❌ Failed to get all active instruments: {e}")
            return []
    
    async def refresh_cache(self):
        """Refresh the instrument cache from database"""
        await self._load_instrument_cache()
        logger.info("🔄 Instrument cache refreshed")
    
    async def _create_instrument_from_market_data(self, symbol: str) -> Optional[UUID]:
        """Create instrument from market data if it exists"""
        try:
            # Import here to avoid circular imports
            from app.services.real_time_market_data import real_time_market_data_service
            
            # Get current price from market data service
            price_data = await real_time_market_data_service.get_latest_price(symbol)
            if not price_data:
                logger.warning(f"⚠️ No market data available for symbol: {symbol}")
                return None
            
            # Determine instrument type based on symbol
            instrument_type = InstrumentType.CRYPTO if symbol.endswith('USDT') else InstrumentType.STOCK
            
            # Create instrument name
            if instrument_type == InstrumentType.CRYPTO:
                base_currency = symbol.replace('USDT', '')
                name = f"{base_currency}/USDT"
            else:
                name = symbol  # For stocks, use symbol as name
            
            # Create instrument data
            instrument_data = {
                "symbol": symbol,
                "name": name,
                "type": instrument_type,
                "current_price": float(price_data.get('price', 0.0)),
                "price_change_24h": float(price_data.get('price_change_24h', 0.0)),
                "volume_24h": float(price_data.get('volume_24h', 0.0)),
                "market_cap": float(price_data.get('market_cap', 0.0)),
                "is_active": True
            }
            
            # Create instrument in database
            async with AsyncSessionLocal() as session:
                try:
                    instrument = Instrument(**instrument_data)
                    session.add(instrument)
                    await session.commit()
                    await session.refresh(instrument)
                    
                    # Update caches
                    self.symbol_to_id_cache[symbol] = instrument.instrument_id
                    self.id_to_symbol_cache[instrument.instrument_id] = symbol
                    
                    if self.redis_client:
                        await self.redis_client.hset(
                            "instrument_mapping",
                            symbol,
                            str(instrument.instrument_id)
                        )
                        await self.redis_client.hset(
                            "instrument_mapping_reverse",
                            str(instrument.instrument_id),
                            symbol
                        )
                    
                    logger.info(f"✅ Created instrument from market data: {symbol} - {name}")
                    return instrument.instrument_id
                    
                except Exception as e:
                    await session.rollback()
                    logger.error(f"❌ Failed to create instrument {symbol}: {e}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error creating instrument from market data for {symbol}: {e}")
            return None

# Global instance
instrument_service = InstrumentService()
