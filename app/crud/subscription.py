from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.crud.base import CRUDBase
from app.models.subscription_plan import SubscriptionPlan
from app.models.subscription import Subscription
from app.schemas import (
    SubscriptionPlanCreate, SubscriptionPlanUpdate,
    SubscriptionCreate, SubscriptionUpdate
)
import logging

logger = logging.getLogger(__name__)

class CRUDSubscriptionPlan(CRUDBase[SubscriptionPlan]):
    """CRUD operations for SubscriptionPlan model"""
    
    async def get_active_plans(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[SubscriptionPlan]:
        """Get active subscription plans"""
        try:
            result = await db.execute(
                select(SubscriptionPlan)
                .where(SubscriptionPlan.status == "active")
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting active subscription plans: {e}")
            raise
    
    async def get_by_type(self, db: AsyncSession, *, plan_type: str, skip: int = 0, limit: int = 100) -> List[SubscriptionPlan]:
        """Get subscription plans by type"""
        try:
            result = await db.execute(
                select(SubscriptionPlan)
                .where(SubscriptionPlan.type == plan_type)
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting subscription plans by type {plan_type}: {e}")
            raise
    
    async def create(self, db: AsyncSession, *, obj_in: SubscriptionPlanCreate) -> SubscriptionPlan:
        """Create a new subscription plan"""
        return await super().create(db, obj_in=obj_in)
    
    async def update(self, db: AsyncSession, *, db_obj: SubscriptionPlan, obj_in: SubscriptionPlanUpdate) -> SubscriptionPlan:
        """Update a subscription plan"""
        return await super().update(db, db_obj=db_obj, obj_in=obj_in)

class CRUDSubscription(CRUDBase[Subscription]):
    """CRUD operations for Subscription model"""
    
    async def get_by_user_id(self, db: AsyncSession, *, user_id: str, skip: int = 0, limit: int = 100) -> List[Subscription]:
        """Get subscriptions by user ID"""
        try:
            result = await db.execute(
                select(Subscription)
                .where(Subscription.user_id == user_id)
                .order_by(Subscription.start_date.desc())
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting subscriptions by user_id {user_id}: {e}")
            raise
    
    async def get_active_subscriptions(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Subscription]:
        """Get active subscriptions"""
        try:
            result = await db.execute(
                select(Subscription)
                .where(Subscription.status == "active")
                .order_by(Subscription.start_date.desc())
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting active subscriptions: {e}")
            raise
    
    async def get_user_active_subscription(self, db: AsyncSession, *, user_id: str) -> Optional[Subscription]:
        """Get user's active subscription"""
        try:
            result = await db.execute(
                select(Subscription)
                .where(Subscription.user_id == user_id, Subscription.status == "active")
                .order_by(Subscription.start_date.desc())
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user active subscription: {e}")
            raise
    
    async def get_expired_subscriptions(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Subscription]:
        """Get expired subscriptions"""
        try:
            result = await db.execute(
                select(Subscription)
                .where(Subscription.status == "expired")
                .order_by(Subscription.end_date.desc())
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting expired subscriptions: {e}")
            raise
    
    async def create(self, db: AsyncSession, *, obj_in: SubscriptionCreate) -> Subscription:
        """Create a new subscription"""
        return await super().create(db, obj_in=obj_in)
    
    async def update(self, db: AsyncSession, *, db_obj: Subscription, obj_in: SubscriptionUpdate) -> Subscription:
        """Update a subscription"""
        return await super().update(db, db_obj=db_obj, obj_in=obj_in)

subscription_plan = CRUDSubscriptionPlan(SubscriptionPlan)
subscription = CRUDSubscription(Subscription)
