from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.crud.base import CRUDBase
from app.models.trading_challenge import TradingChallenge, ChallengeStatus
from app.schemas import TradingChallengeCreate, TradingChallengeUpdate
import logging

logger = logging.getLogger(__name__)

class CRUDTradingChallenge(CRUDBase[TradingChallenge]):
    """CRUD operations for TradingChallenge model"""
    
    async def get_by_user_id(self, db: AsyncSession, *, user_id: str) -> List[TradingChallenge]:
        """Get all trading challenges for a user"""
        try:
            result = await db.execute(
                select(TradingChallenge).where(TradingChallenge.user_id == user_id)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting trading challenges for user {user_id}: {e}")
            raise
    
    async def get_active_by_user_id(self, db: AsyncSession, *, user_id: str) -> Optional[TradingChallenge]:
        """Get active trading challenge for a user"""
        try:
            result = await db.execute(
                select(TradingChallenge)
                .where(TradingChallenge.user_id == user_id)
                .where(TradingChallenge.status == ChallengeStatus.ACTIVE)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting active trading challenge for user {user_id}: {e}")
            raise
    
    async def get_by_selection_id(self, db: AsyncSession, *, selection_id: str) -> Optional[TradingChallenge]:
        """Get trading challenge by selection ID"""
        try:
            result = await db.execute(
                select(TradingChallenge).where(TradingChallenge.selection_id == selection_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting trading challenge by selection {selection_id}: {e}")
            raise
    
    async def update_balance(self, db: AsyncSession, *, challenge_id: str, new_balance: float, trade_amount: float = 0) -> Optional[TradingChallenge]:
        """Update challenge balance and check conditions"""
        try:
            challenge = await self.get(db, id=challenge_id)
            if not challenge:
                return None
            
            # Update balance and check conditions
            challenge.update_balance(new_balance, trade_amount)
            
            await db.commit()
            await db.refresh(challenge)
            return challenge
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating challenge balance: {e}")
            raise
    
    async def get_challenge_summary(self, db: AsyncSession, *, user_id: str) -> dict:
        """Get summary of user's trading challenges"""
        try:
            challenges = await self.get_by_user_id(db, user_id=user_id)
            
            total_challenges = len(challenges)
            active_challenges = len([c for c in challenges if c.status == ChallengeStatus.ACTIVE])
            completed_challenges = len([c for c in challenges if c.status == ChallengeStatus.COMPLETED])
            failed_challenges = len([c for c in challenges if c.status == ChallengeStatus.FAILED])
            
            return {
                "total": total_challenges,
                "active": active_challenges,
                "completed": completed_challenges,
                "failed": failed_challenges
            }
            
        except Exception as e:
            logger.error(f"Error getting challenge summary for user {user_id}: {e}")
            raise

trading_challenge = CRUDTradingChallenge(TradingChallenge)
