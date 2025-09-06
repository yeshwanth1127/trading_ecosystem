"""
Professional Order Matching Engine
=================================

This is the core trading engine that processes orders in real-time.
Handles all order types: Market, Limit, Stop, Stop-Limit, Stop Loss, Take Profit.

Key Features:
- Real-time order matching and execution
- Position management with stop loss/take profit
- Complete audit trail via account ledger
- Redis Pub/Sub event system
- Comprehensive error handling and logging
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID

import redis.asyncio as redis
from sqlalchemy import select, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import AsyncSessionLocal
from app.services.redis_service import redis_service
from app.services.transaction_manager import transaction_manager, retry_on_deadlock
from app.services.error_handler import error_handler, ErrorContext, ErrorCategory, ErrorSeverity, DatabaseError, RedisError, BusinessLogicError
from app.models.account import Account
from app.models.account_ledger import AccountLedger, LedgerEntryType, LedgerEntryStatus
from app.models.instrument import Instrument
from app.models.order import Order, OrderType, OrderSide, OrderStatus, OrderTimeInForce
from app.models.position import Position, PositionStatus, PositionSide
from app.models.trade import Trade, TradeSide, TradeType
from app.models.user import User
from app.services.account_balance_service import account_balance_service

logger = logging.getLogger(__name__)

class TradingEvent:
    """Trading events for Redis Pub/Sub"""
    ORDER_FILLED = "order_filled"
    ORDER_PARTIALLY_FILLED = "order_partially_filled"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_REJECTED = "order_rejected"
    POSITION_OPENED = "position_opened"
    POSITION_UPDATED = "position_updated"
    POSITION_CLOSED = "position_closed"
    POSITION_LIQUIDATED = "position_liquidated"
    STOP_LOSS_TRIGGERED = "stop_loss_triggered"
    TAKE_PROFIT_TRIGGERED = "take_profit_triggered"
    MARGIN_CALL = "margin_call"
    ACCOUNT_UPDATED = "account_updated"

class ExecutionEngine:
    """
    Professional Order Matching Engine
    
    Processes orders in real-time with the following capabilities:
    - Market orders: Immediate execution at current market price
    - Limit orders: Execution when price conditions are met
    - Stop orders: Convert to market orders when stop price is hit
    - Stop-Limit orders: Convert to limit orders when stop price is hit
    - Stop Loss orders: Triggered by position price movements
    - Take Profit orders: Triggered by position price movements
    """
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.is_running = False
        self.execution_task: Optional[asyncio.Task] = None
        self.price_cache: Dict[str, Dict] = {}  # symbol -> {price, bid, ask, timestamp}
        self.position_cache: Dict[Tuple[UUID, UUID], Position] = {}  # (user_id, instrument_id) -> position
        
    async def initialize(self):
        """Initialize the execution engine"""
        try:
            # Use centralized Redis service
            self.redis_client = redis_service.get_client()
            await self.redis_client.ping()
            logger.info("✅ Execution Engine: Redis connection established")
            
            # Load existing positions into cache
            await self._load_positions_cache()
            logger.info("✅ Execution Engine: Position cache loaded")
            
            logger.info("🚀 Execution Engine initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Execution Engine initialization failed: {e}")
            raise
    
    async def close(self):
        """Close the execution engine"""
        self.is_running = False
        if self.execution_task:
            self.execution_task.cancel()
            try:
                await self.execution_task
            except asyncio.CancelledError:
                pass
        
        # Redis connection is managed by redis_service, no need to close here
        
        logger.info("🔒 Execution Engine closed")
    
    async def start(self):
        """Start the execution engine background task"""
        if self.is_running:
            logger.warning("⚠️ Execution Engine is already running")
            return
        
        self.is_running = True
        self.execution_task = asyncio.create_task(self._execution_loop())
        logger.info("🎯 Execution Engine started")
    
    async def stop(self):
        """Stop the execution engine"""
        self.is_running = False
        if self.execution_task:
            self.execution_task.cancel()
            try:
                await self.execution_task
            except asyncio.CancelledError:
                pass
        logger.info("⏹️ Execution Engine stopped")
    
    async def _execution_loop(self):
        """Main execution loop - processes orders every 100ms"""
        logger.info("🔄 Starting execution loop")
        
        while self.is_running:
            try:
                # Update price cache from Redis
                await self._update_price_cache()
                
                # Process pending orders
                await self._process_pending_orders()
                
                # Process stop loss and take profit orders
                await self._process_stop_orders()
                
                # Update positions with current prices
                await self._update_positions()
                
                # Check for margin calls and liquidations
                await self._check_risk_management()
                
                # Small delay to prevent excessive CPU usage
                await asyncio.sleep(0.1)  # 100ms
                
            except Exception as e:
                logger.error(f"❌ Execution loop error: {e}")
                await asyncio.sleep(1)  # Wait longer on error
    
    async def _update_price_cache(self):
        """Update price cache from Redis using SCAN instead of KEYS"""
        try:
            # Use SCAN instead of KEYS to avoid blocking Redis
            cursor = 0
            price_keys = []
            
            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor=cursor, 
                    match="latest_price:*", 
                    count=100
                )
                price_keys.extend(keys)
                if cursor == 0:
                    break
            
            # Process keys in batches to avoid memory issues
            batch_size = 50
            for i in range(0, len(price_keys), batch_size):
                batch = price_keys[i:i + batch_size]
                
                # Use pipeline for better performance
                pipe = self.redis_client.pipeline()
                for key in batch:
                    pipe.hgetall(key)
                
                results = await pipe.execute()
                
                for key, price_data in zip(batch, results):
                    if price_data:
                        symbol = key.replace("latest_price:", "")
                        self.price_cache[symbol] = {
                            'price': Decimal(price_data.get('price', '0')),
                            'bid': Decimal(price_data.get('bid', '0')),
                            'ask': Decimal(price_data.get('ask', '0')),
                            'timestamp': datetime.fromisoformat(price_data.get('timestamp', datetime.now().isoformat()))
                        }
            
            # Update positions with new prices
            await self._update_positions_with_latest_prices()
                    
        except Exception as e:
            logger.error(f"❌ Failed to update price cache: {e}")
    
    async def _update_positions_with_latest_prices(self):
        """Update all open positions with latest market prices"""
        try:
            from app.crud.position import position
            from app.crud.instrument import instrument
            
            async with AsyncSessionLocal() as session:
                # Get all instruments that have price data
                for symbol, price_data in self.price_cache.items():
                    # Get instrument by symbol
                    instrument_obj = await instrument.get_by_symbol(session, symbol=symbol)
                    if instrument_obj:
                        # Update positions for this instrument in database
                        updated_positions = await position.update_position_prices(
                            session, 
                            instrument_id=str(instrument_obj.instrument_id),
                            current_price=float(price_data['price'])
                        )
                        
                        # Update cache with fresh data from database to ensure consistency
                        for position_obj in updated_positions:
                            cache_key = (str(position_obj.user_id), str(position_obj.instrument_id))
                            if cache_key in self.position_cache:
                                # Update cache with database values to ensure consistency
                                self.position_cache[cache_key] = position_obj
                                
                await session.commit()
                        
        except Exception as e:
            logger.error(f"❌ Failed to update positions with latest prices: {e}")
    
    async def _clear_missing_price_log(self):
        """Clear the missing price log after 5 minutes to allow retry logging"""
        await asyncio.sleep(300)  # 5 minutes
        if hasattr(self, '_missing_price_logged'):
            self._missing_price_logged.clear()
            logger.info("🧹 Cleared missing price log cache")
    
    async def _acquire_order_lock(self, lock_key: str, timeout: int = 30) -> bool:
        """Acquire a distributed lock for order processing"""
        try:
            # Use Redis SET with NX and EX for atomic lock acquisition
            result = await self.redis_client.set(
                lock_key, 
                "locked", 
                nx=True,  # Only set if key doesn't exist
                ex=timeout  # Expire after timeout seconds
            )
            return result is not None
        except Exception as e:
            logger.error(f"Error acquiring order lock {lock_key}: {e}")
            return False
    
    async def _release_order_lock(self, lock_key: str):
        """Release a distributed lock for order processing"""
        try:
            await self.redis_client.delete(lock_key)
        except Exception as e:
            logger.error(f"Error releasing order lock {lock_key}: {e}")
    
    async def _get_fresh_order(self, order_id: str, session: AsyncSession) -> Optional[Order]:
        """Get fresh order data from database to avoid stale state"""
        try:
            from sqlalchemy.orm import selectinload
            result = await session.execute(
                select(Order)
                .where(Order.order_id == order_id)
                .options(selectinload(Order.instrument))
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching fresh order {order_id}: {e}")
            return None
    
    async def _load_positions_cache(self):
        """Load existing positions into cache"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(Position)
                    .where(Position.status == PositionStatus.OPEN)
                    .options(selectinload(Position.instrument))
                )
                positions = result.scalars().all()
                
                for position in positions:
                    key = (position.user_id, position.instrument_id)
                    self.position_cache[key] = position
                    
                logger.info(f"📊 Loaded {len(positions)} open positions into cache")
                
            except Exception as e:
                logger.error(f"❌ Failed to load positions cache: {e}")
    
    async def _process_pending_orders(self):
        """Process all pending orders with proper transaction management"""
        try:
            await transaction_manager.execute_with_retry(
                self._process_pending_orders_operation,
                read_only=False,
                max_retries=2
            )
        except Exception as e:
            error_context = ErrorContext(
                operation="process_pending_orders",
                additional_data={"retry_count": 2}
            )
            error_handler.handle_error(
                error=e,
                context=error_context,
                user_message="Failed to process pending orders. System will retry automatically.",
                severity=ErrorSeverity.HIGH
            )
    
    async def _process_pending_orders_operation(self, session: AsyncSession):
        """Internal operation to process pending orders"""
        # Get all pending orders
        result = await session.execute(
            select(Order)
            .where(Order.status == OrderStatus.PENDING)
            .options(
                selectinload(Order.instrument),
                selectinload(Order.account),
                selectinload(Order.user)
            )
        )
        orders = result.scalars().all()
        
        for order in orders:
            await self._process_order(session, order)
    
    async def _process_order(self, session: AsyncSession, order: Order):
        """Process a single order based on its type with proper locking"""
        # Use order ID as lock key to prevent concurrent processing
        lock_key = f"order_lock:{order.order_id}"
        
        try:
            # Acquire distributed lock to prevent race conditions
            lock_acquired = await self._acquire_order_lock(lock_key, timeout=30)
            if not lock_acquired:
                logger.warning(f"Could not acquire lock for order {order.order_id}")
                return
            
            try:
                # Re-fetch order from database to ensure we have latest state
                fresh_order = await self._get_fresh_order(order.order_id, session)
                if not fresh_order:
                    logger.error(f"Order {order.order_id} not found or already processed")
                    return
                
                # Check if order is still in pending state
                if fresh_order.status != OrderStatus.PENDING:
                    logger.info(f"Order {order.order_id} already processed (status: {fresh_order.status})")
                    return
                
                symbol = fresh_order.instrument.symbol
                current_price_data = self.price_cache.get(symbol)
            
                if not current_price_data:
                    # Check if this is a test symbol
                    if symbol.startswith('TEST'):
                        # Reject test orders
                        await self._reject_order(session, fresh_order, f"Symbol {symbol} is a test symbol and not supported")
                        logger.warning(f"🚫 Rejected order for test symbol: {symbol}")
                        return
                
                # For valid symbols, only log error occasionally to prevent spam
                if not hasattr(self, '_missing_price_logged'):
                    self._missing_price_logged = set()
                
                if symbol not in self._missing_price_logged:
                    error_context = ErrorContext(
                        user_id=str(fresh_order.user_id),
                        account_id=str(fresh_order.account_id),
                        order_id=str(fresh_order.order_id),
                        instrument_symbol=symbol,
                        operation="process_order"
                    )
                    error_handler.handle_error(
                        error=BusinessLogicError(f"No price data available for {symbol}"),
                        context=error_context,
                        user_message=f"Market data unavailable for {symbol}. Order will be retried.",
                        severity=ErrorSeverity.MEDIUM
                    )
                    self._missing_price_logged.add(symbol)
                    # Clear the logged set every 5 minutes to allow retry logging
                    asyncio.create_task(self._clear_missing_price_log())
                
                    return
                
                current_price = current_price_data['price']
                current_bid = current_price_data['bid']
                current_ask = current_price_data['ask']
                
                # Process based on order type
                if fresh_order.order_type == OrderType.MARKET:
                    await self._execute_market_order(session, fresh_order, current_price)
                    
                elif fresh_order.order_type == OrderType.LIMIT:
                    await self._check_limit_order(session, fresh_order, current_price, current_bid, current_ask)
                    
                elif fresh_order.order_type == OrderType.STOP:
                    await self._check_stop_order(session, fresh_order, current_price)
                    
                elif fresh_order.order_type == OrderType.STOP_LIMIT:
                    await self._check_stop_limit_order(session, fresh_order, current_price)
                
            finally:
                # Always release the lock
                await self._release_order_lock(lock_key)
                
        except Exception as e:
            error_context = ErrorContext(
                user_id=str(order.user_id),
                account_id=str(order.account_id),
                order_id=str(order.order_id),
                instrument_symbol=order.instrument.symbol,
                operation="process_order"
            )
            error_handler.handle_error(
                error=e,
                context=error_context,
                user_message="Order processing failed. Order will be rejected.",
                severity=ErrorSeverity.HIGH
            )
            await self._reject_order(session, order, f"Processing error: {str(e)}")
            # Ensure lock is released even on error
            try:
                await self._release_order_lock(lock_key)
            except:
                pass
    
    async def _execute_market_order(self, session: AsyncSession, order: Order, current_price: Decimal):
        """Execute a market order immediately"""
        try:
            # Calculate execution price (use bid for sell, ask for buy)
            if order.side == OrderSide.BUY:
                execution_price = current_price  # Use current market price
            else:
                execution_price = current_price  # Use current market price
            
            # Execute the full order
            await self._fill_order(session, order, order.quantity, execution_price)
            
        except Exception as e:
            logger.error(f"❌ Failed to execute market order {order.order_id}: {e}")
            await self._reject_order(session, order, f"Market execution error: {str(e)}")
    
    async def _check_limit_order(self, session: AsyncSession, order: Order, current_price: Decimal, 
                                current_bid: Decimal, current_ask: Decimal):
        """Check if limit order should be executed"""
        try:
            should_execute = False
            execution_price = current_price
            
            if order.side == OrderSide.BUY:
                # Buy limit: execute if current price <= limit price
                if current_price <= order.price:
                    should_execute = True
                    execution_price = min(current_price, order.price)
            else:
                # Sell limit: execute if current price >= limit price
                if current_price >= order.price:
                    should_execute = True
                    execution_price = max(current_price, order.price)
            
            if should_execute:
                await self._fill_order(session, order, order.remaining_quantity, execution_price)
                
        except Exception as e:
            logger.error(f"❌ Failed to check limit order {order.order_id}: {e}")
    
    async def _check_stop_order(self, session: AsyncSession, order: Order, current_price: Decimal):
        """Check if stop order should be triggered"""
        try:
            should_trigger = False
            
            if order.side == OrderSide.BUY:
                # Buy stop: trigger if current price >= stop price
                if current_price >= order.stop_price:
                    should_trigger = True
            else:
                # Sell stop: trigger if current price <= stop price
                if current_price <= order.stop_price:
                    should_trigger = True
            
            if should_trigger:
                # Convert to market order
                order.order_type = OrderType.MARKET
                order.price = None  # Market orders don't have limit price
                await session.commit()
                
                # Execute as market order
                await self._execute_market_order(session, order, current_price)
                
                # Emit event
                await self._emit_event(TradingEvent.ORDER_FILLED, {
                    'order_id': str(order.order_id),
                    'order_type': 'stop_to_market',
                    'trigger_price': float(current_price),
                    'stop_price': float(order.stop_price)
                })
                
        except Exception as e:
            logger.error(f"❌ Failed to check stop order {order.order_id}: {e}")
    
    async def _check_stop_limit_order(self, session: AsyncSession, order: Order, current_price: Decimal):
        """Check if stop-limit order should be triggered"""
        try:
            should_trigger = False
            
            if order.side == OrderSide.BUY:
                # Buy stop-limit: trigger if current price >= stop price
                if current_price >= order.stop_price:
                    should_trigger = True
            else:
                # Sell stop-limit: trigger if current price <= stop price
                if current_price <= order.stop_price:
                    should_trigger = True
            
            if should_trigger:
                # Convert to limit order
                order.order_type = OrderType.LIMIT
                # Keep the limit price, remove stop price
                order.stop_price = None
                await session.commit()
                
                # Emit event
                await self._emit_event(TradingEvent.ORDER_FILLED, {
                    'order_id': str(order.order_id),
                    'order_type': 'stop_limit_to_limit',
                    'trigger_price': float(current_price),
                    'limit_price': float(order.price)
                })
                
        except Exception as e:
            logger.error(f"❌ Failed to check stop-limit order {order.order_id}: {e}")
    
    async def _process_stop_orders(self):
        """Process stop loss and take profit orders based on position prices"""
        try:
            for (user_id, instrument_id), position in self.position_cache.items():
                if position.status != PositionStatus.OPEN:
                    continue
                
                symbol = position.instrument.symbol
                current_price_data = self.price_cache.get(symbol)
                
                if not current_price_data:
                    continue
                
                current_price = current_price_data['price']
                
                # Check stop loss
                if position.stop_loss and self._should_trigger_stop_loss(position, current_price):
                    await self._trigger_stop_loss(user_id, instrument_id, position.stop_loss)
                
                # Check take profit
                if position.take_profit and self._should_trigger_take_profit(position, current_price):
                    await self._trigger_take_profit(user_id, instrument_id, position.take_profit)
                    
        except Exception as e:
            logger.error(f"❌ Failed to process stop orders: {e}")
    
    def _should_trigger_stop_loss(self, position: Position, current_price: Decimal) -> bool:
        """Check if stop loss should be triggered"""
        if position.side == PositionSide.LONG:
            # Long position: trigger if price falls below stop loss
            return current_price <= position.stop_loss
        else:
            # Short position: trigger if price rises above stop loss
            return current_price >= position.stop_loss
    
    def _should_trigger_take_profit(self, position: Position, current_price: Decimal) -> bool:
        """Check if take profit should be triggered"""
        if position.side == PositionSide.LONG:
            # Long position: trigger if price rises above take profit
            return current_price >= position.take_profit
        else:
            # Short position: trigger if price falls below take profit
            return current_price <= position.take_profit
    
    async def _trigger_stop_loss(self, user_id: UUID, instrument_id: UUID, stop_price: Decimal):
        """Create and execute stop loss order"""
        try:
            async with AsyncSessionLocal() as session:
                # Get the position
                position = self.position_cache.get((user_id, instrument_id))
                if not position:
                    return
                
                # Create stop loss order (opposite side of position)
                stop_side = OrderSide.SELL if position.side == PositionSide.LONG else OrderSide.BUY
                
                stop_order = Order(
                    user_id=user_id,
                    account_id=position.account_id,
                    instrument_id=instrument_id,
                    order_type=OrderType.MARKET,  # Stop loss executes as market order
                    side=stop_side,
                    quantity=position.quantity,
                    status=OrderStatus.PENDING,
                    is_margin_order=position.leverage > 1,
                    leverage=position.leverage,
                    notes=f"Stop loss triggered for position {position.position_id}"
                )
                
                session.add(stop_order)
                await session.commit()
                
                # Execute immediately as market order
                symbol = position.instrument.symbol
                current_price_data = self.price_cache.get(symbol)
                if current_price_data:
                    await self._execute_market_order(session, stop_order, current_price_data['price'])
                
                # Emit event
                await self._emit_event(TradingEvent.STOP_LOSS_TRIGGERED, {
                    'position_id': str(position.position_id),
                    'user_id': str(user_id),
                    'instrument_id': str(instrument_id),
                    'stop_price': float(stop_price),
                    'current_price': float(current_price_data['price']) if current_price_data else None
                })
                
        except Exception as e:
            logger.error(f"❌ Failed to trigger stop loss: {e}")
    
    async def _trigger_take_profit(self, user_id: UUID, instrument_id: UUID, take_profit_price: Decimal):
        """Create and execute take profit order"""
        try:
            async with AsyncSessionLocal() as session:
                # Get the position
                position = self.position_cache.get((user_id, instrument_id))
                if not position:
                    return
                
                # Create take profit order (opposite side of position)
                profit_side = OrderSide.SELL if position.side == PositionSide.LONG else OrderSide.BUY
                
                profit_order = Order(
                    user_id=user_id,
                    account_id=position.account_id,
                    instrument_id=instrument_id,
                    order_type=OrderType.MARKET,  # Take profit executes as market order
                    side=profit_side,
                    quantity=position.quantity,
                    status=OrderStatus.PENDING,
                    is_margin_order=position.leverage > 1,
                    leverage=position.leverage,
                    notes=f"Take profit triggered for position {position.position_id}"
                )
                
                session.add(profit_order)
                await session.commit()
                
                # Execute immediately as market order
                symbol = position.instrument.symbol
                current_price_data = self.price_cache.get(symbol)
                if current_price_data:
                    await self._execute_market_order(session, profit_order, current_price_data['price'])
                
                # Emit event
                await self._emit_event(TradingEvent.TAKE_PROFIT_TRIGGERED, {
                    'position_id': str(position.position_id),
                    'user_id': str(user_id),
                    'instrument_id': str(instrument_id),
                    'take_profit_price': float(take_profit_price),
                    'current_price': float(current_price_data['price']) if current_price_data else None
                })
                
        except Exception as e:
            logger.error(f"❌ Failed to trigger take profit: {e}")
    
    @retry_on_deadlock(max_retries=3)
    async def _fill_order(self, session: AsyncSession, order: Order, fill_quantity: Decimal, fill_price: Decimal):
        """Fill an order and create trade record with proper locking to prevent race conditions"""
        try:
            # Use row-level locking to prevent race conditions
            locked_order = await session.get(
                Order, 
                order.order_id, 
                with_for_update=True
            )
            
            if not locked_order:
                raise ValueError(f"Order {order.order_id} not found or already processed")
            
            # Check if order is still pending (prevent double execution)
            if locked_order.status != OrderStatus.PENDING:
                logger.warning(f"⚠️ Order {order.order_id} is no longer pending (status: {locked_order.status})")
                return None
            
            # Calculate fill amount and commission
            fill_amount = fill_quantity * fill_price
            commission = fill_amount * locked_order.commission_rate
            
            # Create trade record
            trade = Trade(
                order_id=locked_order.order_id,
                user_id=locked_order.user_id,
                account_id=locked_order.account_id,
                instrument_id=locked_order.instrument_id,
                side=TradeSide.BUY if locked_order.side == OrderSide.BUY else TradeSide.SELL,
                quantity=fill_quantity,
                entry_price=fill_price,
                amount=fill_amount,
                commission=commission,
                commission_rate=locked_order.commission_rate,
                leverage=locked_order.leverage,
                margin_used=fill_amount / locked_order.leverage if locked_order.leverage > 1 else fill_amount,
                executed_at=datetime.now(timezone.utc)
            )
            
            session.add(trade)
            
            # Update order with proper locking
            locked_order.filled_quantity += fill_quantity
            locked_order.filled_amount += fill_amount
            locked_order.remaining_quantity = locked_order.quantity - locked_order.filled_quantity
            locked_order.remaining_amount = locked_order.total_amount - locked_order.filled_amount
            
            # Calculate average fill price
            if locked_order.filled_quantity > 0:
                locked_order.average_fill_price = locked_order.filled_amount / locked_order.filled_quantity
            
            # Update order status
            if locked_order.remaining_quantity <= 0:
                locked_order.status = OrderStatus.FILLED
                locked_order.filled_at = datetime.now(timezone.utc)
            else:
                locked_order.status = OrderStatus.PARTIAL
            
            # Update position
            await self._update_position(session, locked_order, trade)
            
            # Update account ledger
            await self._update_account_ledger(session, locked_order, trade)
            
            # Note: No explicit commit here - transaction manager handles it
            
            # Update position cache (outside transaction)
            await self._update_position_cache(locked_order.user_id, locked_order.instrument_id)
            
            # Trigger balance update for the account (outside transaction)
            await account_balance_service.update_account_balance_on_trade(str(locked_order.account_id), trade)
            
            # Emit events (outside transaction)
            event_type = TradingEvent.ORDER_FILLED if locked_order.status == OrderStatus.FILLED else TradingEvent.ORDER_PARTIALLY_FILLED
            await self._emit_event(event_type, {
                'order_id': str(locked_order.order_id),
                'trade_id': str(trade.trade_id),
                'user_id': str(locked_order.user_id),
                'account_id': str(locked_order.account_id),
                'instrument_id': str(locked_order.instrument_id),
                'side': locked_order.side.value,
                'quantity': float(fill_quantity),
                'price': float(fill_price),
                'amount': float(fill_amount),
                'commission': float(commission),
                'leverage': float(locked_order.leverage),
                'order_status': locked_order.status.value
            })
            
            logger.info(f"✅ Order {locked_order.order_id} filled: {fill_quantity} @ {fill_price}")
            return trade
            
        except Exception as e:
            logger.error(f"❌ Failed to fill order {order.order_id}: {e}")
            raise
    
    async def _update_position(self, session: AsyncSession, order: Order, trade: Trade):
        """Update or create position based on trade"""
        try:
            # Check if position exists
            position_key = (order.user_id, order.instrument_id)
            existing_position = self.position_cache.get(position_key)
            
            if existing_position and existing_position.status == PositionStatus.OPEN:
                # Update existing position
                await self._update_existing_position(session, existing_position, order, trade)
            else:
                # Create new position
                await self._create_new_position(session, order, trade)
                
        except Exception as e:
            logger.error(f"❌ Failed to update position: {e}")
            raise
    
    @retry_on_deadlock(max_retries=3)
    async def _update_existing_position(self, session: AsyncSession, position: Position, order: Order, trade: Trade):
        """Update existing position with proper locking"""
        try:
            # Use row-level locking to prevent race conditions
            locked_position = await session.get(
                Position, 
                position.position_id, 
                with_for_update=True
            )
            
            if not locked_position:
                raise ValueError(f"Position {position.position_id} not found or already processed")
            
            # Check if position is still open
            if locked_position.status != PositionStatus.OPEN:
                logger.warning(f"⚠️ Position {position.position_id} is no longer open (status: {locked_position.status})")
                return
            
            # Determine if this trade increases or decreases the position
            is_increasing = (
                (locked_position.side == PositionSide.LONG and order.side == OrderSide.BUY) or
                (locked_position.side == PositionSide.SHORT and order.side == OrderSide.SELL)
            )
            
            if is_increasing:
                # Increase position size
                new_quantity = locked_position.quantity + trade.quantity
                new_total_cost = (locked_position.quantity * locked_position.average_entry_price) + trade.amount
                locked_position.average_entry_price = new_total_cost / new_quantity
                locked_position.quantity = new_quantity
                locked_position.margin_used += trade.margin_used
            else:
                # Decrease position size
                if trade.quantity >= locked_position.quantity:
                    # Close position completely
                    realized_pnl = self._calculate_realized_pnl(locked_position, trade)
                    locked_position.realized_pnl = Decimal(str(locked_position.realized_pnl)) + realized_pnl
                    locked_position.status = PositionStatus.CLOSED
                    locked_position.closed_at = datetime.now(timezone.utc)
                    locked_position.quantity = Decimal('0')
                    
                    # Emit position closed event (outside transaction)
                    await self._emit_event(TradingEvent.POSITION_CLOSED, {
                        'position_id': str(locked_position.position_id),
                        'user_id': str(locked_position.user_id),
                        'instrument_id': str(locked_position.instrument_id),
                        'realized_pnl': float(realized_pnl),
                        'total_pnl': float(locked_position.realized_pnl)
                    })
                else:
                    # Partial close
                    realized_pnl = self._calculate_realized_pnl(locked_position, trade)
                    locked_position.realized_pnl = Decimal(str(locked_position.realized_pnl)) + realized_pnl
                    locked_position.quantity -= trade.quantity
                    locked_position.margin_used -= trade.margin_used
                    
                    # Emit position updated event (outside transaction)
                    await self._emit_event(TradingEvent.POSITION_UPDATED, {
                        'position_id': str(locked_position.position_id),
                        'user_id': str(locked_position.user_id),
                        'instrument_id': str(locked_position.instrument_id),
                        'quantity': float(locked_position.quantity),
                        'realized_pnl': float(realized_pnl)
                    })
            
            # Update trade with realized PnL
            if not is_increasing:
                trade.realized_pnl = self._calculate_realized_pnl(locked_position, trade)
            
            locked_position.total_trades += 1
            locked_position.total_volume += trade.amount
            locked_position.total_fees += trade.commission
            locked_position.last_updated = datetime.now(timezone.utc)
            
        except Exception as e:
            logger.error(f"❌ Failed to update existing position: {e}")
            raise
    
    async def _create_new_position(self, session: AsyncSession, order: Order, trade: Trade):
        """Create new position"""
        try:
            position_side = PositionSide.LONG if order.side == OrderSide.BUY else PositionSide.SHORT
            
            position = Position(
                user_id=order.user_id,
                account_id=order.account_id,
                instrument_id=order.instrument_id,
                side=position_side,
                quantity=trade.quantity,
                average_entry_price=trade.entry_price,
                current_price=trade.entry_price,
                leverage=order.leverage,
                margin_used=trade.margin_used,
                status=PositionStatus.OPEN,
                opened_at=datetime.now(timezone.utc)
            )
            
            session.add(position)
            await session.flush()  # Get the position_id
            
            # Add to cache
            position_key = (order.user_id, order.instrument_id)
            self.position_cache[position_key] = position
            
            # Emit position opened event
            await self._emit_event(TradingEvent.POSITION_OPENED, {
                'position_id': str(position.position_id),
                'user_id': str(order.user_id),
                'account_id': str(order.account_id),
                'instrument_id': str(order.instrument_id),
                'side': position_side.value,
                'quantity': float(trade.quantity),
                'entry_price': float(trade.entry_price),
                'leverage': float(order.leverage)
            })
            
        except Exception as e:
            logger.error(f"❌ Failed to create new position: {e}")
            raise
    
    def _calculate_realized_pnl(self, position: Position, trade: Trade) -> Decimal:
        """Calculate realized PnL for a trade"""
        if position.side == PositionSide.LONG:
            # Long position: profit when selling above entry price
            return (trade.entry_price - position.average_entry_price) * trade.quantity
        else:
            # Short position: profit when buying below entry price
            return (position.average_entry_price - trade.entry_price) * trade.quantity
    
    async def _update_account_ledger(self, session: AsyncSession, order: Order, trade: Trade):
        """Update account ledger with trade information"""
        try:
            # Get current account balance
            account_result = await session.execute(
                select(Account).where(Account.account_id == order.account_id)
            )
            account = account_result.scalar_one()
            
            balance_before = account.balance
            
            # Calculate net amount (positive for buy, negative for sell)
            net_amount = trade.amount if order.side == OrderSide.BUY else -trade.amount
            net_amount -= trade.commission  # Always subtract commission
            
            # Update account balance
            account.balance += net_amount
            balance_after = account.balance
            
            # Create ledger entry for the trade
            ledger_entry = AccountLedger(
                user_id=order.user_id,
                account_id=order.account_id,
                order_id=order.order_id,
                trade_id=trade.trade_id,
                entry_type=LedgerEntryType.PNL,
                amount=net_amount,
                balance_before=balance_before,
                balance_after=balance_after,
                description=f"Trade execution: {order.side.value} {trade.quantity} @ {trade.entry_price}"
            )
            
            session.add(ledger_entry)
            
            # Create separate ledger entry for commission
            if trade.commission > 0:
                commission_entry = AccountLedger(
                    user_id=order.user_id,
                    account_id=order.account_id,
                    order_id=order.order_id,
                    trade_id=trade.trade_id,
                    entry_type=LedgerEntryType.FEE,
                    amount=-trade.commission,
                    balance_before=balance_after,
                    balance_after=balance_after - trade.commission,
                    description=f"Trading commission: {trade.commission_rate * 100:.3f}%"
                )
                
                session.add(commission_entry)
                account.balance -= trade.commission
            
        except Exception as e:
            logger.error(f"❌ Failed to update account ledger: {e}")
            raise
    
    async def _update_positions(self):
        """Update all positions with current market prices"""
        try:
            from app.crud.position import position as position_crud
            
            async with AsyncSessionLocal() as session:
                for (user_id, instrument_id), position in self.position_cache.items():
                    if position.status != PositionStatus.OPEN:
                        continue
                    
                    symbol = position.instrument.symbol
                    current_price_data = self.price_cache.get(symbol)
                    
                    if current_price_data:
                        current_price = current_price_data['price']
                        
                        # Update cache (P&L will be calculated by the CRUD layer)
                        position.current_price = current_price
                        position.last_updated = datetime.now(timezone.utc)
                        
                        # Update database
                        updated_positions = await position_crud.update_position_prices(
                            session, 
                            instrument_id=str(instrument_id), 
                            current_price=float(current_price)
                        )
                        if updated_positions:
                            logger.info(f"📊 Updated {len(updated_positions)} positions for {symbol} at price {current_price}")
                            for pos in updated_positions:
                                logger.info(f"   Position {pos.position_id}: P&L = {pos.unrealized_pnl}")
                        
                await session.commit()
                    
        except Exception as e:
            logger.error(f"❌ Failed to update positions: {e}")
    
    async def _update_position_cache(self, user_id: UUID, instrument_id: UUID):
        """Update position in cache"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Position)
                    .where(
                        and_(
                            Position.user_id == user_id,
                            Position.instrument_id == instrument_id,
                            Position.status == PositionStatus.OPEN
                        )
                    )
                    .options(selectinload(Position.instrument))
                )
                position = result.scalar_one_or_none()
                
                position_key = (user_id, instrument_id)
                if position:
                    self.position_cache[position_key] = position
                else:
                    # Position was closed, remove from cache
                    self.position_cache.pop(position_key, None)
                    
        except Exception as e:
            logger.error(f"❌ Failed to update position cache: {e}")
    
    async def _check_risk_management(self):
        """Check for margin calls and liquidations"""
        try:
            for (user_id, instrument_id), position in self.position_cache.items():
                if position.status != PositionStatus.OPEN:
                    continue
                
                # Calculate margin ratio
                if position.margin_used > 0:
                    margin_ratio = position.unrealized_pnl / position.margin_used
                    
                    # Check for liquidation (negative equity)
                    if position.total_pnl <= -position.margin_used:
                        await self._liquidate_position(user_id, instrument_id, "Insufficient margin")
                    
                    # Check for margin call (80% of margin used)
                    elif margin_ratio <= -0.8:
                        await self._emit_event(TradingEvent.MARGIN_CALL, {
                            'position_id': str(position.position_id),
                            'user_id': str(user_id),
                            'instrument_id': str(instrument_id),
                            'margin_ratio': float(margin_ratio),
                            'unrealized_pnl': float(position.unrealized_pnl)
                        })
                        
        except Exception as e:
            logger.error(f"❌ Failed to check risk management: {e}")
    
    async def _liquidate_position(self, user_id: UUID, instrument_id: UUID, reason: str):
        """Liquidate a position due to insufficient margin"""
        try:
            async with AsyncSessionLocal() as session:
                position = self.position_cache.get((user_id, instrument_id))
                if not position:
                    return
                
                # Create liquidation order
                liquidation_side = OrderSide.SELL if position.side == PositionSide.LONG else OrderSide.BUY
                
                liquidation_order = Order(
                    user_id=user_id,
                    account_id=position.account_id,
                    instrument_id=instrument_id,
                    order_type=OrderType.MARKET,
                    side=liquidation_side,
                    quantity=position.quantity,
                    status=OrderStatus.PENDING,
                    is_margin_order=True,
                    leverage=position.leverage,
                    notes=f"Liquidation: {reason}"
                )
                
                session.add(liquidation_order)
                await session.commit()
                
                # Execute immediately
                symbol = position.instrument.symbol
                current_price_data = self.price_cache.get(symbol)
                if current_price_data:
                    await self._execute_market_order(session, liquidation_order, current_price_data['price'])
                
                # Mark position as liquidated
                position.status = PositionStatus.LIQUIDATED
                position.closed_at = datetime.now(timezone.utc)
                
                # Emit liquidation event
                await self._emit_event(TradingEvent.POSITION_LIQUIDATED, {
                    'position_id': str(position.position_id),
                    'user_id': str(user_id),
                    'instrument_id': str(instrument_id),
                    'reason': reason,
                    'final_pnl': float(position.total_pnl)
                })
                
        except Exception as e:
            logger.error(f"❌ Failed to liquidate position: {e}")
    
    async def _reject_order(self, session: AsyncSession, order: Order, reason: str):
        """Reject an order"""
        try:
            order.status = OrderStatus.REJECTED
            order.rejection_reason = reason
            order.cancelled_at = datetime.now(timezone.utc)
            
            await session.commit()
            
            # Emit rejection event
            await self._emit_event(TradingEvent.ORDER_REJECTED, {
                'order_id': str(order.order_id),
                'user_id': str(order.user_id),
                'reason': reason
            })
            
            logger.warning(f"❌ Order {order.order_id} rejected: {reason}")
            
        except Exception as e:
            logger.error(f"❌ Failed to reject order {order.order_id}: {e}")
    
    async def _emit_event(self, event_type: str, data: dict):
        """Emit trading event to Redis Pub/Sub"""
        try:
            if not self.redis_client:
                return
            
            event_data = {
                'event_type': event_type,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'data': data
            }
            
            await self.redis_client.publish('trading_events', json.dumps(event_data))
            
        except Exception as e:
            logger.error(f"❌ Failed to emit event {event_type}: {e}")

# Global execution engine instance
execution_engine = ExecutionEngine()
