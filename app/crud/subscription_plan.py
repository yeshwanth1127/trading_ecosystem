from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.crud.base import CRUDBase
from app.models.subscription_plan import SubscriptionPlan
from app.schemas import SubscriptionPlanCreate, SubscriptionPlanUpdate
import logging

logger = logging.getLogger(__name__)

class CRUDSubscriptionPlan(CRUDBase[SubscriptionPlan]):
    """CRUD operations for SubscriptionPlan model"""
    
    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[SubscriptionPlan]:
        """Get subscription plan by name"""
        try:
            result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.name == name))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting subscription plan by name {name}: {e}")
            raise
    
    async def get_by_price_range(self, db: AsyncSession, *, min_price: float, max_price: float, skip: int = 0, limit: int = 100) -> List[SubscriptionPlan]:
        """Get subscription plans within a price range"""
        try:
            result = await db.execute(
                select(SubscriptionPlan)
                .where(SubscriptionPlan.price >= min_price)
                .where(SubscriptionPlan.price <= max_price)
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting subscription plans in price range {min_price}-{max_price}: {e}")
            raise
    
    async def get_active_plans(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[SubscriptionPlan]:
        """Get active subscription plans"""
        try:
            result = await db.execute(
                select(SubscriptionPlan)
                .where(SubscriptionPlan.is_active == True)
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting active subscription plans: {e}")
            raise

subscription_plan = CRUDSubscriptionPlan(SubscriptionPlan)
