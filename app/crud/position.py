from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from decimal import Decimal
from app.crud.base import CRUDBase
from app.models.position import Position, PositionStatus
from app.schemas import PositionCreate, PositionUpdate
import logging

logger = logging.getLogger(__name__)

class CRUDPosition(CRUDBase[Position]):
    """CRUD operations for Position model"""
    
    def _calculate_unrealized_pnl(self, position: Position, current_price: float) -> float:
        """
        Centralized P&L calculation logic with comprehensive validation
        
        For Long Positions: Unrealized P&L = (Current Price - Entry Price) × Position Size
        For Short Positions: Unrealized P&L = (Entry Price - Current Price) × Position Size
        
        Example:
        - Long 1 BTC at $40,000, current price $42,000
        - P&L = ($42,000 - $40,000) × 1 = $2,000 profit
        """
        try:
            # Validate position object
            if not position or not hasattr(position, 'average_entry_price') or not hasattr(position, 'quantity'):
                logger.error(f"Invalid position object for P&L calculation")
                return 0.0
            
            # Convert and validate entry price
            try:
                entry_price = float(position.average_entry_price)
            except (ValueError, TypeError):
                logger.error(f"Invalid entry price for position {position.position_id}: {position.average_entry_price}")
                return 0.0
            
            # Convert and validate quantity
            try:
                quantity = float(position.quantity)
            except (ValueError, TypeError):
                logger.error(f"Invalid quantity for position {position.position_id}: {position.quantity}")
                return 0.0
            
            # Validate current price
            if not isinstance(current_price, (int, float)) or current_price <= 0:
                logger.error(f"Invalid current price for position {position.position_id}: {current_price}")
                return 0.0
            
            # Validate entry price and quantity
            if entry_price <= 0:
                logger.error(f"Invalid entry price (<=0) for position {position.position_id}: {entry_price}")
                return 0.0
            
            if quantity <= 0:
                logger.error(f"Invalid quantity (<=0) for position {position.position_id}: {quantity}")
                return 0.0
            
            # Calculate P&L based on position side
            if position.side.value == "long":
                # Long position: profit when current price > entry price
                pnl = (current_price - entry_price) * quantity
            elif position.side.value == "short":
                # Short position: profit when current price < entry price  
                pnl = (entry_price - current_price) * quantity
            else:
                logger.error(f"Invalid position side for position {position.position_id}: {position.side}")
                return 0.0
            
            # Validate calculated P&L
            if not isinstance(pnl, (int, float)) or not (pnl == pnl):  # Check for NaN
                logger.error(f"Invalid P&L calculation result for position {position.position_id}: {pnl}")
                return 0.0
            
            # Round to 2 decimal places and validate range
            rounded_pnl = round(pnl, 2)
            
            # Check for extremely large values (potential calculation errors)
            if abs(rounded_pnl) > 1000000:  # 1M limit
                logger.warning(f"Extremely large P&L value for position {position.position_id}: {rounded_pnl}")
                return 0.0
            
            return rounded_pnl
            
        except Exception as e:
            logger.error(f"Unexpected error calculating P&L for position {position.position_id}: {e}")
            return 0.0
    
    async def get_open_positions(self, db: AsyncSession, *, user_id: str) -> List[Position]:
        """Get open positions for a user"""
        try:
            from sqlalchemy.orm import selectinload
            result = await db.execute(
                select(Position)
                .where(Position.user_id == user_id)
                .where(Position.status == PositionStatus.OPEN)
                .options(selectinload(Position.instrument))
                .order_by(Position.opened_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting open positions for user {user_id}: {e}")
            raise
    
    async def get_position_by_instrument(self, db: AsyncSession, *, user_id: str, instrument_id: str) -> Optional[Position]:
        """Get position for a specific instrument and user"""
        try:
            result = await db.execute(
                select(Position)
                .where(Position.user_id == user_id)
                .where(Position.instrument_id == instrument_id)
                .where(Position.status == PositionStatus.OPEN)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting position for instrument {instrument_id} and user {user_id}: {e}")
            raise
    
    async def update_position_prices(self, db: AsyncSession, *, instrument_id: str, current_price: float) -> List[Position]:
        """Update all open positions for an instrument with new price and PnL"""
        try:
            # Get all open positions for this instrument
            result = await db.execute(
                select(Position)
                .where(Position.instrument_id == instrument_id)
                .where(Position.status == PositionStatus.OPEN)
            )
            positions = result.scalars().all()
            
            updated_positions = []
            for position in positions:
                # Use centralized P&L calculation
                unrealized_pnl = self._calculate_unrealized_pnl(position, current_price)
                
                # Update position
                position.current_price = Decimal(str(current_price))
                position.unrealized_pnl = Decimal(str(unrealized_pnl))
                position.total_pnl = position.realized_pnl + Decimal(str(unrealized_pnl))
                position.last_updated = func.now()
                
                updated_positions.append(position)
            
            await db.commit()
            return updated_positions
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating position prices for instrument {instrument_id}: {e}")
            raise
    
    async def close_position(self, db: AsyncSession, *, position_id: str, user_id: str, 
                            close_price: float, close_quantity: float) -> Optional[Position]:
        """Close a position (partial or full)"""
        try:
            from sqlalchemy.orm import selectinload
            result = await db.execute(
                select(Position)
                .where(Position.position_id == position_id)
                .where(Position.user_id == user_id)
                .options(selectinload(Position.instrument))
            )
            position = result.scalar_one_or_none()
            if not position:
                return None
            
            if close_quantity >= position.quantity:
                # Full close
                position.status = PositionStatus.CLOSED
                position.closed_at = func.now()
                position.quantity = 0
                position.unrealized_pnl = 0
            else:
                # Partial close
                position.quantity -= Decimal(str(close_quantity))
            
            # Calculate realized PnL
            if position.side.value == "long":
                realized_pnl = (Decimal(str(close_price)) - position.average_entry_price) * Decimal(str(close_quantity))
            else:  # short
                realized_pnl = (position.average_entry_price - Decimal(str(close_price))) * Decimal(str(close_quantity))
            
            position.realized_pnl = Decimal(str(position.realized_pnl)) + realized_pnl
            position.total_pnl = position.realized_pnl + position.unrealized_pnl
            position.last_updated = func.now()
            
            await db.commit()
            return position
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error closing position {position_id}: {e}")
            raise
    
    async def get_position_summary(self, db: AsyncSession, *, user_id: str) -> dict:
        """Get summary of user's positions"""
        try:
            result = await db.execute(
                select(
                    func.count(Position.position_id).label("total_positions"),
                    func.sum(Position.unrealized_pnl).label("total_unrealized_pnl"),
                    func.sum(Position.realized_pnl).label("total_realized_pnl"),
                    func.sum(Position.margin_used).label("total_margin_used")
                )
                .where(Position.user_id == user_id)
                .where(Position.status == PositionStatus.OPEN)
            )
            
            summary = result.fetchone()
            return {
                "total_positions": summary.total_positions or 0,
                "total_unrealized_pnl": float(summary.total_unrealized_pnl or 0),
                "total_realized_pnl": float(summary.total_realized_pnl or 0),
                "total_margin_used": float(summary.total_margin_used or 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting position summary for user {user_id}: {e}")
            raise

position = CRUDPosition(Position)
