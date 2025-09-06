from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.crud.base import CRUDBase
from app.models.account import Account
from app.schemas import AccountCreate, AccountUpdate
import logging

logger = logging.getLogger(__name__)

class CRUDAccount(CRUDBase[Account]):
    """CRUD operations for Account model"""
    
    async def get_by_user_id(self, db: AsyncSession, *, user_id: str) -> List[Account]:
        """Get accounts by user ID"""
        try:
            result = await db.execute(select(Account).where(Account.user_id == user_id))
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting accounts by user_id {user_id}: {e}")
            raise
    
    async def get_by_type(self, db: AsyncSession, *, account_type: str, skip: int = 0, limit: int = 100) -> List[Account]:
        """Get accounts by type"""
        try:
            result = await db.execute(
                select(Account)
                .where(Account.type == account_type)
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting accounts by type {account_type}: {e}")
            raise
    
    async def get_user_accounts_by_type(self, db: AsyncSession, *, user_id: str, account_type: str) -> List[Account]:
        """Get user accounts by type"""
        try:
            result = await db.execute(
                select(Account)
                .where(Account.user_id == user_id, Account.type == account_type)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting user accounts by type: {e}")
            raise
    
    async def create(self, db: AsyncSession, *, obj_in: AccountCreate) -> Account:
        """Create a new account"""
        return await super().create(db, obj_in=obj_in)
    
    async def update(self, db: AsyncSession, *, db_obj: Account, obj_in: AccountUpdate) -> Account:
        """Update an account"""
        return await super().update(db, db_obj=db_obj, obj_in=obj_in)

account = CRUDAccount(Account)
