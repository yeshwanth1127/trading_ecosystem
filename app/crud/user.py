from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
import logging

logger = logging.getLogger(__name__)

class CRUDUser(CRUDBase[User]):
    """CRUD operations for User model"""
    
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            result = await db.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            raise
    
    async def authenticate(self, db: AsyncSession, *, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        try:
            user = await self.get_by_email(db, email=email)
            if not user:
                return None
            if not verify_password(password, user.hashed_password):
                return None
            return user
        except Exception as e:
            logger.error(f"Error authenticating user {email}: {e}")
            raise
    
    async def get_by_role(self, db: AsyncSession, *, role: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users by role"""
        try:
            result = await db.execute(
                select(User)
                .where(User.role == role)
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting users by role {role}: {e}")
            raise
    
    async def get_active_users(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        """Get active users"""
        try:
            result = await db.execute(
                select(User)
                .where(User.status == "active")
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            raise
    
    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """Create a new user with hashed password"""
        try:
            # Create user data dict
            user_data = obj_in.dict()
            # Hash the password
            hashed_password = get_password_hash(user_data.pop("password"))
            # Create user object with hashed password
            db_obj = User(
                name=user_data["name"],
                email=user_data["email"],
                hashed_password=hashed_password,
                role=user_data["role"],
                status=user_data["status"]
            )
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating user: {e}")
            raise
    
    async def update(self, db: AsyncSession, *, db_obj: User, obj_in: UserUpdate) -> User:
        """Update a user"""
        return await super().update(db, db_obj=db_obj, obj_in=obj_in)

user = CRUDUser(User)
