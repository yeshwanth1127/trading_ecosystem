from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.crud.base import CRUDBase
from app.models.trade import Trade
from app.schemas import TradeCreate, TradeUpdate
import logging

logger = logging.getLogger(__name__)

class CRUDTrade(CRUDBase[Trade]):
    """CRUD operations for Trade model"""
    
    async def get_by_account_id(self, db: AsyncSession, *, account_id: str, skip: int = 0, limit: int = 100) -> List[Trade]:
        """Get trades by account ID"""
        try:
            result = await db.execute(
                select(Trade)
                .where(Trade.account_id == account_id)
                .order_by(Trade.timestamp.desc())
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting trades by account_id {account_id}: {e}")
            raise
    
    async def get_by_user_id(self, db: AsyncSession, *, user_id: str, skip: int = 0, limit: int = 100) -> List[Trade]:
        """Get trades by user ID"""
        try:
            result = await db.execute(
                select(Trade)
                .where(Trade.user_id == user_id)
                .order_by(Trade.timestamp.desc())
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting trades by user_id {user_id}: {e}")
            raise
    
    async def get_by_instrument(self, db: AsyncSession, *, instrument: str, skip: int = 0, limit: int = 100) -> List[Trade]:
        """Get trades by instrument"""
        try:
            result = await db.execute(
                select(Trade)
                .where(Trade.instrument == instrument)
                .order_by(Trade.timestamp.desc())
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting trades by instrument {instrument}: {e}")
            raise
    
    async def get_open_trades(self, db: AsyncSession, *, account_id: str) -> List[Trade]:
        """Get open trades (without exit price) for an account"""
        try:
            result = await db.execute(
                select(Trade)
                .where(Trade.account_id == account_id, Trade.exit_price.is_(None))
                .order_by(Trade.timestamp.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting open trades for account {account_id}: {e}")
            raise
    
    async def get_trades_by_date_range(
        self, 
        db: AsyncSession, 
        *, 
        account_id: str, 
        start_date: str, 
        end_date: str,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Trade]:
        """Get trades within a date range for an account"""
        try:
            result = await db.execute(
                select(Trade)
                .where(
                    Trade.account_id == account_id,
                    Trade.timestamp >= start_date,
                    Trade.timestamp <= end_date
                )
                .order_by(Trade.timestamp.desc())
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting trades by date range: {e}")
            raise
    
    async def get_account_pnl(self, db: AsyncSession, *, account_id: str) -> float:
        """Get total PnL for an account"""
        try:
            result = await db.execute(
                select(func.sum(Trade.pnl))
                .where(Trade.account_id == account_id, Trade.pnl.is_not(None))
            )
            return result.scalar() or 0.0
        except Exception as e:
            logger.error(f"Error getting PnL for account {account_id}: {e}")
            raise
    
    async def create(self, db: AsyncSession, *, obj_in: TradeCreate) -> Trade:
        """Create a new trade"""
        return await super().create(db, obj_in=obj_in)
    
    async def update(self, db: AsyncSession, *, db_obj: Trade, obj_in: TradeUpdate) -> Trade:
        """Update a trade"""
        return await super().update(db, db_obj=db_obj, obj_in=obj_in)

trade = CRUDTrade(Trade)
