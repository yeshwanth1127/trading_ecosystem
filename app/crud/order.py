from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.crud.base import CRUDBase
from app.models.order import Order, OrderStatus, OrderType
from app.schemas import OrderCreate, OrderUpdate
import logging

logger = logging.getLogger(__name__)

class CRUDOrder(CRUDBase[Order]):
    """CRUD operations for Order model"""
    
    async def get_by_user_id(self, db: AsyncSession, *, user_id: str, status: Optional[OrderStatus] = None) -> List[Order]:
        """Get orders for a user, optionally filtered by status"""
        try:
            query = select(Order).where(Order.user_id == user_id)
            if status:
                query = query.where(Order.status == status)
            query = query.order_by(Order.created_at.desc())
            
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting orders for user {user_id}: {e}")
            raise
    
    async def get_pending_orders(self, db: AsyncSession, *, user_id: str) -> List[Order]:
        """Get pending orders for a user"""
        try:
            result = await db.execute(
                select(Order)
                .where(Order.user_id == user_id)
                .where(Order.status.in_([OrderStatus.PENDING, OrderStatus.PARTIAL]))
                .order_by(Order.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting pending orders for user {user_id}: {e}")
            raise
    
    async def get_by_instrument(self, db: AsyncSession, *, user_id: str, instrument_id: str) -> List[Order]:
        """Get orders for a specific instrument and user"""
        try:
            result = await db.execute(
                select(Order)
                .where(Order.user_id == user_id)
                .where(Order.instrument_id == instrument_id)
                .order_by(Order.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting orders for instrument {instrument_id} and user {user_id}: {e}")
            raise
    
    async def update_status(self, db: AsyncSession, *, order_id: str, status: OrderStatus, 
                           filled_quantity: Optional[float] = None) -> Optional[Order]:
        """Update order status and filled quantity"""
        try:
            update_data = {"status": status}
            if filled_quantity is not None:
                update_data["filled_quantity"] = filled_quantity
            
            result = await db.execute(
                update(Order)
                .where(Order.order_id == order_id)
                .values(**update_data)
                .returning(Order)
            )
            
            await db.commit()
            return result.scalar_one_or_none()
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating order status for {order_id}: {e}")
            raise
    
    async def cancel_order(self, db: AsyncSession, *, order_id: str, user_id: str) -> Optional[Order]:
        """Cancel an order (only if it belongs to the user)"""
        try:
            result = await db.execute(
                update(Order)
                .where(Order.order_id == order_id)
                .where(Order.user_id == user_id)
                .where(Order.status.in_([OrderStatus.PENDING, OrderStatus.PARTIAL]))
                .values(status=OrderStatus.CANCELLED)
                .returning(Order)
            )
            
            await db.commit()
            return result.scalar_one_or_none()
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error cancelling order {order_id}: {e}")
            raise

order = CRUDOrder(Order)
