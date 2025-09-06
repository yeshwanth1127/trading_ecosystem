from typing import Generic, TypeVar, Type, Optional, List, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from app.db.database import Base
from app.schemas import PaginationParams
import logging

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)

class CRUDBase(Generic[ModelType]):
    """
    Base CRUD class with common database operations
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        
        Args:
            model: A SQLAlchemy model class
        """
        self.model = model
    
    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """Get a single record by ID"""
        try:
            result = await db.execute(select(self.model).where(self.model.__table__.columns[0] == id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} with id {id}: {e}")
            raise
    
    async def get_multi(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[dict] = None
    ) -> List[ModelType]:
        """Get multiple records with pagination and optional filters"""
        try:
            query = select(self.model)
            
            # Apply filters if provided
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model, field) and value is not None:
                        if isinstance(value, (list, tuple)):
                            query = query.where(getattr(self.model, field).in_(value))
                        else:
                            query = query.where(getattr(self.model, field) == value)
            
            query = query.offset(skip).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting multiple {self.model.__name__}: {e}")
            raise
    
    async def create(self, db: AsyncSession, *, obj_in: Any) -> ModelType:
        """Create a new record"""
        try:
            if isinstance(obj_in, dict):
                db_obj = self.model(**obj_in)
            else:
                db_obj = self.model(**obj_in.model_dump())
            
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise
    
    async def update(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: ModelType, 
        obj_in: Union[dict, Any]
    ) -> ModelType:
        """Update an existing record"""
        try:
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)
            
            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating {self.model.__name__}: {e}")
            raise
    
    async def remove(self, db: AsyncSession, *, id: Any) -> Optional[ModelType]:
        """Delete a record by ID"""
        try:
            obj = await self.get(db, id)
            if obj:
                await db.delete(obj)
                await db.commit()
            return obj
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting {self.model.__name__} with id {id}: {e}")
            raise
    
    async def count(self, db: AsyncSession, filters: Optional[dict] = None) -> int:
        """Count total records with optional filters"""
        try:
            query = select(func.count(self.model.__table__.columns[0]))
            
            # Apply filters if provided
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model, field) and value is not None:
                        if isinstance(value, (list, tuple)):
                            query = query.where(getattr(self.model, field).in_(value))
                        else:
                            query = query.where(getattr(self.model, field) == value)
            
            result = await db.execute(query)
            return result.scalar()
        except Exception as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            raise
    
    async def exists(self, db: AsyncSession, id: Any) -> bool:
        """Check if a record exists by ID"""
        try:
            result = await db.execute(
                select(func.count(self.model.__table__.columns[0])).where(
                    self.model.__table__.columns[0] == id
                )
            )
            return result.scalar() > 0
        except Exception as e:
            logger.error(f"Error checking existence of {self.model.__name__} with id {id}: {e}")
            raise
