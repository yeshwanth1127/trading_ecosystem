from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.crud.base import CRUDBase
from app.models.challenge_attempt import ChallengeAttempt
from app.schemas import ChallengeAttemptCreate, ChallengeAttemptUpdate
import logging

logger = logging.getLogger(__name__)

class CRUDChallengeAttempt(CRUDBase[ChallengeAttempt]):
    """CRUD operations for ChallengeAttempt model"""
    
    async def get_by_user_id(self, db: AsyncSession, *, user_id: str, skip: int = 0, limit: int = 100) -> List[ChallengeAttempt]:
        """Get challenge attempts by user ID"""
        try:
            result = await db.execute(
                select(ChallengeAttempt)
                .where(ChallengeAttempt.user_id == user_id)
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting challenge attempts for user {user_id}: {e}")
            raise
    
    async def get_by_challenge_template_id(self, db: AsyncSession, *, challenge_template_id: str, skip: int = 0, limit: int = 100) -> List[ChallengeAttempt]:
        """Get challenge attempts by challenge template ID"""
        try:
            result = await db.execute(
                select(ChallengeAttempt)
                .where(ChallengeAttempt.challenge_template_id == challenge_template_id)
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting challenge attempts for template {challenge_template_id}: {e}")
            raise
    
    async def get_by_status(self, db: AsyncSession, *, status: str, skip: int = 0, limit: int = 100) -> List[ChallengeAttempt]:
        """Get challenge attempts by status"""
        try:
            result = await db.execute(
                select(ChallengeAttempt)
                .where(ChallengeAttempt.status == status)
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting challenge attempts by status {status}: {e}")
            raise

challenge_attempt = CRUDChallengeAttempt(ChallengeAttempt)
