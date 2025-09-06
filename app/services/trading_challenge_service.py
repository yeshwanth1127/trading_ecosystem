from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.trading_challenge import TradingChallenge, ChallengeStatus
from app.models.challenge_selection import ChallengeSelection
from app.crud import trading_challenge, challenge_selection
import logging
from decimal import Decimal
from sqlalchemy import func

logger = logging.getLogger(__name__)

class TradingChallengeService:
    """Service for managing trading challenge logic and rule enforcement"""
    
    @staticmethod
    def parse_amount(amount_str: str) -> float:
        """Parse amount string (e.g., '₹50,000') to float"""
        try:
            # Remove currency symbol and commas, then convert to float
            clean_amount = amount_str.replace('₹', '').replace(',', '')
            return float(clean_amount)
        except (ValueError, AttributeError):
            logger.error(f"Failed to parse amount: {amount_str}")
            return 0.0
    
    @staticmethod
    async def start_trading_challenge(
        db: AsyncSession, 
        selection_id: str,
        initial_balance: float = 100000.0  # Default starting balance
    ) -> Optional[TradingChallenge]:
        """Start a trading challenge from a challenge selection"""
        try:
            # Get the challenge selection
            selection = await challenge_selection.get(db, id=selection_id)
            if not selection:
                logger.error(f"Challenge selection {selection_id} not found")
                return None
            
            # Parse amounts from strings
            target_amount = TradingChallengeService.parse_amount(selection.profit_target)
            max_drawdown_amount = TradingChallengeService.parse_amount(selection.max_drawdown)
            daily_loss_limit = TradingChallengeService.parse_amount(selection.daily_limit)
            
            # Create trading challenge
            trading_challenge = TradingChallenge(
                user_id=selection.user_id,
                selection_id=selection.selection_id,
                target_amount=target_amount,
                max_drawdown_amount=max_drawdown_amount,
                daily_loss_limit=daily_loss_limit,
                current_balance=initial_balance,
                peak_balance=initial_balance,
                current_drawdown=0.0,
                daily_loss=0.0,
                status=ChallengeStatus.ACTIVE
            )
            
            # Update selection status
            selection.status = "trading"
            selection.trading_started_at = func.now()
            
            db.add(trading_challenge)
            await db.commit()
            await db.refresh(trading_challenge)
            
            logger.info(f"Trading challenge started for user {selection.user_id}")
            return trading_challenge
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error starting trading challenge: {e}")
            raise
    
    @staticmethod
    async def process_trade(
        db: AsyncSession,
        challenge_id: str,
        trade_amount: float,
        new_balance: float
    ) -> Dict[str, Any]:
        """Process a trade and check challenge conditions"""
        try:
            # Get the trading challenge
            challenge = await trading_challenge.get(db, id=challenge_id)
            if not challenge:
                return {"error": "Trading challenge not found"}
            
            # Update challenge balance and check conditions
            challenge.update_balance(new_balance, trade_amount)
            
            # Check if challenge should end
            if challenge.status in [ChallengeStatus.COMPLETED, ChallengeStatus.FAILED]:
                await db.commit()
                return {
                    "challenge_ended": True,
                    "status": challenge.status.value,
                    "reason": _get_challenge_end_reason(challenge),
                    "final_balance": float(challenge.current_balance)
                }
            
            await db.commit()
            return {
                "challenge_ended": False,
                "current_balance": float(challenge.current_balance),
                "current_drawdown": float(challenge.current_drawdown),
                "daily_loss": float(challenge.daily_loss),
                "profit_target_reached": challenge.is_profit_target_reached,
                "drawdown_breached": challenge.is_drawdown_breached,
                "daily_limit_breached": challenge.is_daily_limit_breached
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error processing trade: {e}")
            return {"error": f"Failed to process trade: {e}"}
    
    @staticmethod
    async def get_challenge_status(
        db: AsyncSession,
        challenge_id: str
    ) -> Dict[str, Any]:
        """Get current status of a trading challenge"""
        try:
            challenge = await trading_challenge.get(db, id=challenge_id)
            if not challenge:
                return {"error": "Trading challenge not found"}
            
            return {
                "status": challenge.status.value,
                "current_balance": float(challenge.current_balance),
                "peak_balance": float(challenge.peak_balance),
                "current_drawdown": float(challenge.current_drawdown),
                "daily_loss": float(challenge.daily_loss),
                "target_amount": float(challenge.target_amount),
                "max_drawdown_amount": float(challenge.max_drawdown_amount),
                "daily_loss_limit": float(challenge.daily_loss_limit),
                "profit_target_reached": challenge.is_profit_target_reached,
                "drawdown_breached": challenge.is_drawdown_breached,
                "daily_limit_breached": challenge.is_daily_limit_breached,
                "start_date": challenge.start_date.isoformat() if challenge.start_date else None,
                "end_date": challenge.end_date.isoformat() if challenge.end_date else None
            }
            
        except Exception as e:
            logger.error(f"Error getting challenge status: {e}")
            return {"error": f"Failed to get challenge status: {e}"}

def _get_challenge_end_reason(challenge: TradingChallenge) -> str:
    """Get the reason why a challenge ended"""
    if challenge.is_profit_target_reached:
        return "Profit target reached"
    elif challenge.is_drawdown_breached:
        return "Maximum drawdown exceeded"
    elif challenge.is_daily_limit_breached:
        return "Daily loss limit exceeded"
    else:
        return "Unknown reason"
