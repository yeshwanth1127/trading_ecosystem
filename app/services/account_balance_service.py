"""
Real-time Account Balance & P&L Management Service
=================================================

This service manages real-time account balances, equity, and P&L calculations.
It updates Redis with current account states and provides real-time balance tracking.
"""

import asyncio
import redis.asyncio as redis
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.db.database import AsyncSessionLocal
from app.services.redis_service import redis_service
from app.models.account import Account
from app.models.position import Position, PositionStatus, PositionSide
from app.models.trade import Trade
from app.models.account_ledger import AccountLedger, LedgerEntryType, LedgerEntryStatus


logger = logging.getLogger(__name__)

class AccountBalanceService:
    """Real-time account balance and P&L management service"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.is_running = False
        self.update_task: Optional[asyncio.Task] = None
        
    async def initialize(self):
        """Initialize the account balance service"""
        try:
            # Use centralized Redis service
            self.redis_client = redis_service.get_client()
            
            # Test Redis connection
            await self.redis_client.ping()
            logger.info("✅ Account Balance Service: Redis connection established")
            
            # Load initial account data
            await self._load_account_balances()
            
            logger.info("🚀 Account Balance Service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Account Balance Service: {e}")
            raise
    
    async def close(self):
        """Close the account balance service"""
        self.is_running = False
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
        
        # Redis connection is managed by redis_service, no need to close here
        
        logger.info("🔒 Account Balance Service closed")
    
    async def start(self):
        """Start the real-time balance update service"""
        if self.is_running:
            logger.warning("⚠️ Account Balance Service is already running")
            return
        
        self.is_running = True
        self.update_task = asyncio.create_task(self._balance_update_loop())
        logger.info("🎯 Account Balance Service started")
    
    async def stop(self):
        """Stop the balance update service"""
        self.is_running = False
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
        logger.info("⏹️ Account Balance Service stopped")
    
    async def _balance_update_loop(self):
        """Main balance update loop - updates every second"""
        logger.info("🔄 Starting balance update loop")
        
        while self.is_running:
            try:
                # Update all account balances and P&L
                await self._update_all_account_balances()
                
                # Wait 1 second before next update
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"❌ Balance update loop error: {e}")
                await asyncio.sleep(5)  # Wait longer on error
    
    async def _load_account_balances(self):
        """Load initial account balances into Redis"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(Account)
                    .options(selectinload(Account.user))
                )
                accounts = result.scalars().all()
                
                for account in accounts:
                    await self._calculate_and_store_account_balance(session, account)
                
                logger.info(f"📊 Loaded {len(accounts)} account balances into Redis")
                
            except Exception as e:
                logger.error(f"❌ Failed to load account balances: {e}")
    
    async def _update_all_account_balances(self):
        """Update balances for all accounts"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(Account)
                    .options(selectinload(Account.user))
                )
                accounts = result.scalars().all()
                
                for account in accounts:
                    await self._calculate_and_store_account_balance(session, account)
                
            except Exception as e:
                logger.error(f"❌ Failed to update account balances: {e}")
    
    async def _calculate_and_store_account_balance(self, session: AsyncSession, account: Account):
        """Calculate and store account balance in Redis"""
        try:
            # Get all open positions for this account
            positions_result = await session.execute(
                select(Position)
                .where(
                    Position.account_id == account.account_id,
                    Position.status == PositionStatus.OPEN
                )
                .options(selectinload(Position.instrument))
            )
            positions = positions_result.scalars().all()
            
            # Calculate unrealized P&L
            total_unrealized_pnl = Decimal('0')
            total_margin_used = Decimal('0')
            
            for position in positions:
                # Get current price from Redis
                symbol = position.instrument.symbol
                current_price_data = await self._get_current_price(symbol)
                
                if current_price_data:
                    current_price = Decimal(str(current_price_data['price']))
                    
                    # Calculate unrealized P&L with proper validation
                    try:
                        entry_price = float(position.average_entry_price)
                        quantity = float(position.quantity)
                        current_price_float = float(current_price)
                        
                        # Validate inputs
                        if entry_price <= 0 or quantity <= 0 or current_price_float <= 0:
                            unrealized_pnl = Decimal('0')
                        else:
                            if position.side == PositionSide.LONG:
                                unrealized_pnl = Decimal(str(round((current_price_float - entry_price) * quantity, 2)))
                            else:  # SHORT
                                unrealized_pnl = Decimal(str(round((entry_price - current_price_float) * quantity, 2)))
                    except (ValueError, TypeError, AttributeError) as e:
                        logger.error(f"Error calculating P&L for position {position.position_id}: {e}")
                        unrealized_pnl = Decimal('0')
                    
                    total_unrealized_pnl += unrealized_pnl
                    total_margin_used += position.margin_used or Decimal('0')
                    
                    # Update position with current price and unrealized P&L
                    await session.execute(
                        update(Position)
                        .where(Position.position_id == position.position_id)
                        .values(
                            current_price=current_price,
                            unrealized_pnl=unrealized_pnl,
                            last_updated=datetime.utcnow()
                        )
                    )
            
            # Calculate account metrics
            balance = account.balance or Decimal('0')
            realized_pnl = account.realized_pnl or Decimal('0')
            equity = balance + realized_pnl + total_unrealized_pnl
            free_margin = balance - total_margin_used
            
            # Update account in database
            await session.execute(
                update(Account)
                .where(Account.account_id == account.account_id)
                .values(
                    equity=equity,
                    unrealized_pnl=total_unrealized_pnl,
                    margin_used=total_margin_used,
                    margin_available=free_margin,
                    last_updated=datetime.utcnow()
                )
            )
            
            # Store in Redis for real-time access
            account_data = {
                'account_id': str(account.account_id),
                'user_id': str(account.user_id),
                'balance': str(balance),
                'equity': str(equity),
                'realized_pnl': str(realized_pnl),
                'unrealized_pnl': str(total_unrealized_pnl),
                'margin_used': str(total_margin_used),
                'free_margin': str(free_margin),
                'margin_ratio': str(total_margin_used / equity if equity > 0 else 0),
                'last_updated': datetime.utcnow().isoformat()
            }
            
            await self.redis_client.hset(
                f"account_balance:{account.account_id}",
                mapping=account_data
            )
            
            # Also store by user_id for easy access
            await self.redis_client.hset(
                f"user_balance:{account.user_id}",
                mapping=account_data
            )
            
            # Publish balance update event
            await self._publish_balance_update(account.user_id, account_data)
            
            await session.commit()
            
        except Exception as e:
            logger.error(f"❌ Failed to calculate balance for account {account.account_id}: {e}")
            await session.rollback()
    
    async def _get_current_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current price from Redis"""
        try:
            if not self.redis_client:
                return None
            
            price_data = await self.redis_client.hgetall(f"latest_price:{symbol}")
            if not price_data:
                return None
            
            return {
                'price': float(price_data.get('price', 0)),
                'bid': float(price_data.get('bid', 0)),
                'ask': float(price_data.get('ask', 0)),
                'timestamp': price_data.get('timestamp')
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get current price for {symbol}: {e}")
            return None
    
    async def _publish_balance_update(self, user_id: str, account_data: Dict[str, Any]):
        """Publish balance update event to Redis"""
        try:
            if not self.redis_client:
                return
            
            event_data = {
                'event_type': 'balance_update',
                'user_id': user_id,
                'account_data': account_data,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            await self.redis_client.publish(
                'trading_events',
                f"balance_update:{user_id}:{account_data['account_id']}"
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to publish balance update: {e}")
    
    async def get_account_balance(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get current account balance from Redis"""
        try:
            if not self.redis_client:
                return None
            
            balance_data = await self.redis_client.hgetall(f"account_balance:{account_id}")
            if not balance_data:
                return None
            
            return {
                'account_id': balance_data.get('account_id'),
                'user_id': balance_data.get('user_id'),
                'balance': float(balance_data.get('balance', 0)),
                'equity': float(balance_data.get('equity', 0)),
                'realized_pnl': float(balance_data.get('realized_pnl', 0)),
                'unrealized_pnl': float(balance_data.get('unrealized_pnl', 0)),
                'margin_used': float(balance_data.get('margin_used', 0)),
                'free_margin': float(balance_data.get('free_margin', 0)),
                'margin_ratio': float(balance_data.get('margin_ratio', 0)),
                'last_updated': balance_data.get('last_updated')
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get account balance: {e}")
            return None
    
    async def get_user_balance(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get current user balance from Redis"""
        try:
            if not self.redis_client:
                return None
            
            balance_data = await self.redis_client.hgetall(f"user_balance:{user_id}")
            if not balance_data:
                return None
            
            return {
                'account_id': balance_data.get('account_id'),
                'user_id': balance_data.get('user_id'),
                'balance': float(balance_data.get('balance', 0)),
                'equity': float(balance_data.get('equity', 0)),
                'realized_pnl': float(balance_data.get('realized_pnl', 0)),
                'unrealized_pnl': float(balance_data.get('unrealized_pnl', 0)),
                'margin_used': float(balance_data.get('margin_used', 0)),
                'free_margin': float(balance_data.get('free_margin', 0)),
                'margin_ratio': float(balance_data.get('margin_ratio', 0)),
                'last_updated': balance_data.get('last_updated')
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get user balance: {e}")
            return None
    
    async def update_account_balance_on_trade(self, account_id: str, trade: Trade):
        """Update account balance when a trade is executed"""
        try:
            # This will be called by the execution engine when trades are executed
            # The balance will be recalculated in the next update cycle
            logger.info(f"📊 Trade executed for account {account_id}, balance will be updated")
            
        except Exception as e:
            logger.error(f"❌ Failed to update balance on trade: {e}")

# Global instance
account_balance_service = AccountBalanceService()
