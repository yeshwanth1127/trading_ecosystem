from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.crud.base import CRUDBase
from app.models.challenge_template import ChallengeTemplate
from app.models.challenge_attempt import ChallengeAttempt
from app.schemas import (
    ChallengeTemplateCreate, ChallengeTemplateUpdate,
    ChallengeAttemptCreate, ChallengeAttemptUpdate
)
import logging

logger = logging.getLogger(__name__)

class CRUDChallengeTemplate(CRUDBase[ChallengeTemplate]):
    """CRUD operations for ChallengeTemplate model"""
    
    async def get_active_challenges(self, db: AsyncSession, skip: int = 0, limit: int = 100, category: Optional[str] = None) -> List[ChallengeTemplate]:
        """Get active challenge templates"""
        try:
            query = select(ChallengeTemplate).where(ChallengeTemplate.status == "active")
            
            if category:
                query = query.where(ChallengeTemplate.category == category)
            
            query = query.offset(skip).limit(limit)
            
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting active challenges: {e}")
            raise
    
    async def create(self, db: AsyncSession, *, obj_in: ChallengeTemplateCreate) -> ChallengeTemplate:
        """Create a new challenge template"""
        return await super().create(db, obj_in=obj_in)
    
    async def update(self, db: AsyncSession, *, db_obj: ChallengeTemplate, obj_in: ChallengeTemplateUpdate) -> ChallengeTemplate:
        """Update a challenge template"""
        return await super().update(db, db_obj=db_obj, obj_in=obj_in)

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
            logger.error(f"Error getting challenge attempts by user_id {user_id}: {e}")
            raise
    
    async def get_by_challenge_id(self, db: AsyncSession, *, challenge_id: str, skip: int = 0, limit: int = 100) -> List[ChallengeAttempt]:
        """Get challenge attempts by challenge ID"""
        try:
            result = await db.execute(
                select(ChallengeAttempt)
                .where(ChallengeAttempt.challenge_id == challenge_id)
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting challenge attempts by challenge_id {challenge_id}: {e}")
            raise
    
    async def get_by_state(self, db: AsyncSession, *, state: str, skip: int = 0, limit: int = 100) -> List[ChallengeAttempt]:
        """Get challenge attempts by state"""
        try:
            result = await db.execute(
                select(ChallengeAttempt)
                .where(ChallengeAttempt.state == state)
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting challenge attempts by state {state}: {e}")
            raise
    
    async def get_active_attempts(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[ChallengeAttempt]:
        """Get active challenge attempts"""
        try:
            result = await db.execute(
                select(ChallengeAttempt)
                .where(ChallengeAttempt.state == "active")
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting active challenge attempts: {e}")
            raise
    
    async def create(self, db: AsyncSession, *, obj_in: ChallengeAttemptCreate) -> ChallengeAttempt:
        """Create a new challenge attempt"""
        return await super().create(db, obj_in=obj_in)
    
    async def update(self, db: AsyncSession, *, db_obj: ChallengeAttempt, obj_in: ChallengeAttemptUpdate) -> ChallengeAttempt:
        """Update a challenge attempt"""
        return await super().update(db, db_obj=db_obj, obj_in=obj_in)

challenge_template = CRUDChallengeTemplate(ChallengeTemplate)
challenge_attempt = CRUDChallengeAttempt(ChallengeAttempt)
