from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.crud.base import CRUDBase
from app.models.challenge_template import ChallengeTemplate
from app.schemas import ChallengeTemplateCreate, ChallengeTemplateUpdate
import logging

logger = logging.getLogger(__name__)

class CRUDChallengeTemplate(CRUDBase[ChallengeTemplate]):
    """CRUD operations for ChallengeTemplate model"""
    
    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[ChallengeTemplate]:
        """Get challenge template by name"""
        try:
            result = await db.execute(select(ChallengeTemplate).where(ChallengeTemplate.name == name))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting challenge template by name {name}: {e}")
            raise
    
    async def get_by_difficulty(self, db: AsyncSession, *, difficulty: str, skip: int = 0, limit: int = 100) -> List[ChallengeTemplate]:
        """Get challenge templates by difficulty level"""
        try:
            result = await db.execute(
                select(ChallengeTemplate)
                .where(ChallengeTemplate.difficulty == difficulty)
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting challenge templates by difficulty {difficulty}: {e}")
            raise
    
    async def get_active_templates(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[ChallengeTemplate]:
        """Get active challenge templates"""
        try:
            result = await db.execute(
                select(ChallengeTemplate)
                .where(ChallengeTemplate.is_active == True)
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting active challenge templates: {e}")
            raise

challenge_template = CRUDChallengeTemplate(ChallengeTemplate)
