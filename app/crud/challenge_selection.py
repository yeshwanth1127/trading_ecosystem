from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.crud.base import CRUDBase
from app.models.challenge_selection import ChallengeSelection
from app.schemas import ChallengeSelectionCreate, ChallengeSelectionUpdate
import logging
from sqlalchemy import func

logger = logging.getLogger(__name__)

class CRUDChallengeSelection(CRUDBase[ChallengeSelection]):
    """CRUD operations for ChallengeSelection model"""
    
    async def get_by_user_id(self, db: AsyncSession, *, user_id: str) -> List[ChallengeSelection]:
        """Get all challenge selections for a user"""
        try:
            result = await db.execute(
                select(ChallengeSelection).where(ChallengeSelection.user_id == user_id)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting challenge selections for user {user_id}: {e}")
            raise
    
    async def get_active_by_user_id(self, db: AsyncSession, *, user_id: str) -> Optional[ChallengeSelection]:
        """Get active challenge selection for a user"""
        try:
            result = await db.execute(
                select(ChallengeSelection)
                .where(ChallengeSelection.user_id == user_id)
                .where(ChallengeSelection.status == "active")
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting active challenge selection for user {user_id}: {e}")
            raise
    
    async def create_for_user(self, db: AsyncSession, *, user_id: str, obj_in: ChallengeSelectionCreate) -> ChallengeSelection:
        """Create a new challenge selection for a user with active status"""
        try:
            db_obj = ChallengeSelection(
                user_id=user_id,
                challenge_id=obj_in.challenge_id,
                amount=obj_in.amount,
                price=obj_in.price,
                profit_target=obj_in.profit_target,
                max_drawdown=obj_in.max_drawdown,
                daily_limit=obj_in.daily_limit,
                category=obj_in.category,  # Set the category field
                status="active",  # Automatically set to active
                activated_at=func.now(),  # Set activation timestamp
            )
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating challenge selection for user {user_id}: {e}")
            raise
    
    # Note: activate_selection method removed - challenges are automatically active when created
    
    async def start_trading(self, db: AsyncSession, *, selection_id: str) -> ChallengeSelection:
        """Mark challenge selection as trading when user starts placing trades"""
        try:
            db_obj = await self.get(db, id=selection_id)
            if not db_obj:
                raise ValueError(f"Challenge selection {selection_id} not found")
            
            if db_obj.status != "active":
                raise ValueError(f"Challenge selection must be active to start trading. Current status: {db_obj.status}")
            
            db_obj.status = "trading"
            db_obj.trading_started_at = func.now()
            
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except Exception as e:
            await db.rollback()
            logger.error(f"Error starting trading for challenge selection {selection_id}: {e}")
            raise

challenge_selection = CRUDChallengeSelection(ChallengeSelection)
