from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from app.api.deps import get_db, get_current_user
from app.crud import instrument, order, position, user, account
from app.schemas import (
    InstrumentListResponse, InstrumentResponse, MarketDataListResponse,
    OrderCreate, OrderResponse, OrderListResponse,
    PositionResponse, PositionListResponse,
    TradingSummary, ChartData
)
from app.schemas.trading import OrderCreateWithSymbol
from app.services.instrument_service import instrument_service
from app.core.security import verify_token
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.trading_challenge import TradingChallenge
from app.models.position import Position
from app.models.order import Order, OrderType as ModelOrderType, OrderSide as ModelOrderSide, OrderTimeInForce as ModelOrderTimeInForce
from app.schemas.trading import PositionCreate, PositionUpdate, OrderCreate, OrderUpdate
from app.services.trading_challenge_service import TradingChallengeService
from app.services.market_data_service import market_data_service

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# Helper function to get current user
async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Get current user ID from JWT token"""
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    return user_id

@router.get("/balance")
async def get_user_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get user balance for their active challenge"""
    try:
        # Get user's active challenge selection
        from app.crud import challenge_selection
        active_selection = await challenge_selection.get_active_by_user_id(db, user_id=str(current_user.id))
        
        if not active_selection:
            raise HTTPException(status_code=404, detail="No active challenge found")
        
        # Determine currency based on challenge category
        currency = "USD" if active_selection.category.value == "crypto" else "INR"
        
        # Get user's account
        from app.crud import account
        user_accounts = await account.get_by_user_id(db, user_id=str(current_user.id))
        if not user_accounts:
            raise HTTPException(status_code=404, detail="No account found")
        
        user_account = user_accounts[0]
        
        # Get all open positions for this user
        open_positions = await position.get_open_positions(db, user_id=str(current_user.id))
        
        # Get all pending orders for this user
        from app.crud import order
        pending_orders = await order.get_pending_orders(db, user_id=str(current_user.id))
        
        # Calculate total unrealized P&L from open positions
        total_unrealized_pnl = sum(float(pos.unrealized_pnl) for pos in open_positions)
        
        # Calculate total margin used
        total_margin_used = sum(float(pos.margin_used) for pos in open_positions)
        
        # Calculate available balance
        available_balance = float(user_account.balance) - total_margin_used
        
        # Calculate total equity
        total_equity = available_balance + total_unrealized_pnl
        
        return {
            "success": True,
            "data": {
                "challenge_id": active_selection.challenge_id,
                "initial_balance": float(user_account.balance),
                "available_balance": available_balance,
                "total_equity": total_equity,
                "unrealized_pnl": total_unrealized_pnl,
                "realized_pnl": float(user_account.realized_pnl),
                "used_margin": total_margin_used,
                "currency": currency,
                "open_positions_count": len(open_positions),
                "pending_orders_count": len(pending_orders),
                "total_trades": len(await order.get_by_user_id(db, user_id=str(current_user.id))),
                "peak_balance": float(user_account.balance),  # Could be tracked separately
                "current_drawdown": 0.0,  # Could be calculated
                "daily_loss": 0.0,  # Could be calculated
                "target_amount": float(active_selection.amount.replace("$" if currency == "USD" else "₹", "").replace(",", "")),
                "max_drawdown_amount": float(active_selection.max_drawdown.replace("$" if currency == "USD" else "₹", "").replace(",", "")),
                "daily_loss_limit": float(active_selection.daily_limit.replace("$" if currency == "USD" else "₹", "").replace(",", "")),
                "status": active_selection.status.value
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid request data: {str(e)}")
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    except Exception as e:
        logger.error(f"Unexpected error fetching balance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/dashboard-summary")
async def get_dashboard_summary(
    challenge_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get comprehensive dashboard summary for a challenge"""
    try:
        # Get balance data
        balance_data = await get_user_balance(challenge_id, current_user, db)
        
        # Get recent positions
        recent_positions = db.query(Position).filter(
            Position.challenge_id == challenge_id
        ).order_by(Position.created_at.desc()).limit(5).all()
        
        # Get recent orders
        recent_orders = db.query(Order).filter(
            Order.challenge_id == challenge_id
        ).order_by(Order.created_at.desc()).limit(5).all()
        
        return {
            "success": True,
            "data": {
                **balance_data["data"],
                "recent_positions": [
                    {
                        "id": pos.id,
                        "symbol": pos.symbol,
                        "side": pos.side,
                        "quantity": pos.quantity,
                        "entry_price": pos.entry_price,
                        "status": pos.status,
                        "created_at": pos.created_at.isoformat()
                    } for pos in recent_positions
                ],
                "recent_orders": [
                    {
                        "id": order.id,
                        "symbol": order.symbol,
                        "side": order.side,
                        "quantity": order.quantity,
                        "price": order.price,
                        "status": order.status,
                        "created_at": order.created_at.isoformat()
                    } for order in recent_orders
                ]
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid request data: {str(e)}")
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    except Exception as e:
        logger.error(f"Unexpected error fetching dashboard summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Instrument Endpoints
@router.get("/instruments", response_model=InstrumentListResponse)
async def get_instruments(
    type: Optional[str] = Query(None, description="Filter by instrument type (crypto/stock)"),
    search: Optional[str] = Query(None, description="Search by symbol or name"),
    db: AsyncSession = Depends(get_db)
):
    """Get all available trading instruments"""
    try:
        if search:
            instruments = await instrument.search_instruments(db, query=search)
        elif type:
            if type.lower() == "crypto":
                instruments = await instrument.get_by_type(db, type="crypto")
            elif type.lower() == "stock":
                instruments = await instrument.get_by_type(db, type="stock")
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid instrument type. Use 'crypto' or 'stock'"
                )
        else:
            instruments = await instrument.get_active_instruments(db)
        
        return InstrumentListResponse(
            instruments=instruments,
            total=len(instruments)
        )
        
    except ValueError as e:
        logger.error(f"Invalid request parameters: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request parameters"
        )
    except ConnectionError as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error getting instruments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/instruments/{instrument_id}", response_model=InstrumentResponse)
async def get_instrument(
    instrument_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get specific instrument details"""
    try:
        instrument_obj = await instrument.get(db, id=instrument_id)
        if not instrument_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instrument not found"
            )
        
        return instrument_obj
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting instrument {instrument_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Market Data Endpoints
@router.get("/market-data", response_model=MarketDataListResponse)
async def get_market_data(
    type: Optional[str] = Query(None, description="Filter by instrument type"),
    db: AsyncSession = Depends(get_db)
):
    """Get current market data for all instruments"""
    try:
        if type:
            if type.lower() == "crypto":
                instruments = await instrument.get_by_type(db, type="crypto")
            elif type.lower() == "stock":
                instruments = await instrument.get_by_type(db, type="stock")
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid instrument type"
                )
        else:
            instruments = await instrument.get_active_instruments(db)
        
        # Convert to market data format
        market_data = []
        for inst in instruments:
            market_data.append({
                "instrument_id": inst.instrument_id,
                "symbol": inst.symbol,
                "name": inst.name,
                "type": inst.type,
                "current_price": inst.current_price,
                "price_change_24h": inst.price_change_24h or 0.0,
                "price_change_percent_24h": inst.price_change_24h or 0.0,
                "volume_24h": inst.volume_24h or 0.0,
                "market_cap": inst.market_cap or 0.0,
                "high_24h": inst.current_price,  # Placeholder - would come from real market data
                "low_24h": inst.current_price,   # Placeholder - would come from real market data
                "last_updated": inst.last_updated
            })
        
        return MarketDataListResponse(
            instruments=market_data,
            total=len(market_data)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Order Endpoints
@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_in: OrderCreateWithSymbol,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new trading order with symbol-based instrument identification"""
    try:
        # Convert instrument symbol to ID using instrument service
        instrument_id = await instrument_service.get_instrument_id_by_symbol(order_in.instrument_symbol)
        if not instrument_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Instrument not found for symbol: {order_in.instrument_symbol}"
            )
        
        # Validate instrument exists in database
        instrument_obj = await instrument.get(db, id=instrument_id)
        if not instrument_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instrument not found in database"
            )
        
        # Get user's account or create one if none exists
        user_accounts = await account.get_by_user_id(db, user_id=user_id)
        if not user_accounts:
            # Create a default trading account for the user
            from app.models.account import AccountType, AccountStatus
            account_data = {
                "user_id": user_id,
                "type": AccountType.SIMULATED,
                "status": AccountStatus.ACTIVE,
                "balance": 10000.0,  # Default demo balance
                "equity": 10000.0,
                "margin_used": 0.0,
                "margin_available": 10000.0,
                "unrealized_pnl": 0.0,
                "realized_pnl": 0.0,
                "max_leverage": 100.0,
                "is_margin_enabled": True,
                "auto_liquidation": True
            }
            user_account = await account.create(db, obj_in=account_data)
            logger.info(f"✅ Created default account for user {user_id}")
        else:
            user_account = user_accounts[0]  # Use first account
        
        # Get current market price for calculations
        current_price = instrument_obj.current_price or 0.0
        
        # Calculate total amount
        if order_in.price:
            total_amount = order_in.quantity * order_in.price
        else:
            # For market orders, use current price
            total_amount = order_in.quantity * current_price
        
        # Calculate margin requirements for margin orders
        margin_used = 0.0
        if order_in.is_margin_order and order_in.leverage > 1:
            margin_used = total_amount / order_in.leverage
        
        # Create order data
        order_data = {
            "user_id": user_id,
            "account_id": user_account.account_id,
            "instrument_id": instrument_id,
            "order_type": ModelOrderType(order_in.order_type.value),
            "side": ModelOrderSide(order_in.side.value),
            "quantity": order_in.quantity,
            "price": order_in.price,
            "stop_price": order_in.stop_price,
            "time_in_force": ModelOrderTimeInForce.GTC,
            "leverage": order_in.leverage,
            "is_margin_order": order_in.is_margin_order,
            "margin_used": margin_used,
            "total_amount": total_amount,
            "remaining_quantity": order_in.quantity,
            "remaining_amount": total_amount,
            "commission": 0.0,  # Will be calculated by execution engine
            "commission_rate": 0.001,  # 0.1% default commission rate
            "notes": order_in.notes
        }
        
        # Create order in database
        db_order = await order.create(db, obj_in=order_data)
        
        logger.info(f"✅ Order created: {db_order.order_id} for user {user_id} - {order_in.side.value} {order_in.quantity} {order_in.instrument_symbol}")
        
        # Start execution engine if not already running
        from app.services.execution_engine import execution_engine
        if not execution_engine.is_running:
            import asyncio
            asyncio.create_task(execution_engine.start())
            logger.info("🚀 Execution engine started due to new order")
        
        # Return order response with instrument symbol for frontend compatibility
        response_data = db_order.to_dict() if hasattr(db_order, 'to_dict') else db_order
        response_data['instrument_symbol'] = order_in.instrument_symbol
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/orders", response_model=OrderListResponse)
async def get_user_orders(
    status: Optional[str] = Query(None, description="Filter by order status"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get user's trading orders"""
    try:
        if status:
            orders = await order.get_by_user_id(db, user_id=user_id, status=status)
        else:
            orders = await order.get_by_user_id(db, user_id=user_id)
        
        return OrderListResponse(
            orders=orders,
            total=len(orders)
        )
        
    except Exception as e:
        logger.error(f"Error getting orders for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/orders/pending", response_model=OrderListResponse)
async def get_pending_orders(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get user's pending orders"""
    try:
        orders = await order.get_pending_orders(db, user_id=user_id)
        
        return OrderListResponse(
            orders=orders,
            total=len(orders)
        )
        
    except Exception as e:
        logger.error(f"Error getting pending orders for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.delete("/orders/{order_id}")
async def cancel_order(
    order_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Cancel a pending order"""
    try:
        cancelled_order = await order.cancel_order(db, order_id=order_id, user_id=user_id)
        if not cancelled_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found or cannot be cancelled"
            )
        
        logger.info(f"Order {order_id} cancelled by user {user_id}")
        return {"message": "Order cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling order {order_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Position Endpoints
@router.get("/positions", response_model=PositionListResponse)
async def get_user_positions(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get user's open positions"""
    try:
        positions = await position.get_open_positions(db, user_id=user_id)
        
        return PositionListResponse(
            positions=positions,
            total=len(positions)
        )
        
    except Exception as e:
        logger.error(f"Error getting positions for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/positions/update-prices")
async def update_position_prices(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Manually update position prices with latest market data"""
    try:
        from app.services.execution_engine import execution_engine
        from app.crud.position import position
        
        # Trigger price cache update
        await execution_engine._update_price_cache()
        
        # Get all open positions for the user
        open_positions = await position.get_open_positions(db, user_id=user_id)
        
        # Update each position with current market prices
        updated_count = 0
        for pos in open_positions:
            if pos.instrument and pos.instrument.symbol:
                # Get current price from execution engine cache
                current_price = execution_engine.price_cache.get(pos.instrument.symbol, {}).get('price')
                if current_price:
                    # Update position prices
                    await position.update_position_prices(
                        db, 
                        instrument_id=str(pos.instrument_id),
                        current_price=float(current_price)
                    )
                    updated_count += 1
        
        return {
            "message": "Position prices updated successfully",
            "updated_positions": updated_count
        }
        
    except Exception as e:
        logger.error(f"Error updating position prices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/positions/{position_id}/close")
async def close_position(
    position_id: str,
    close_quantity: Optional[float] = None,  # If None, close entire position
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Close a position (partial or full)"""
    try:
        # Get the position
        position_obj = await position.get_by_id(db, position_id=position_id, user_id=user_id)
        if not position_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Position not found"
            )
        
        if position_obj.status.value != "open":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Position is not open"
            )
        
        # Determine close quantity
        if close_quantity is None:
            close_quantity = float(position_obj.quantity)
        else:
            close_quantity = min(close_quantity, float(position_obj.quantity))
        
        if close_quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid close quantity"
            )
        
        # Get current market price for closing
        current_price = float(position_obj.current_price)
        
        # Close the position
        closed_position = await position.close_position(
            db, 
            position_id=position_id, 
            user_id=user_id,
            close_price=current_price,
            close_quantity=close_quantity
        )
        
        if not closed_position:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to close position"
            )
        
        # Update account balance with realized PnL
        from app.crud import account
        user_accounts = await account.get_by_user_id(db, user_id=user_id)
        if user_accounts:
            user_account = user_accounts[0]
            
            # Add realized PnL to balance
            realized_pnl = float(closed_position.realized_pnl) - float(position_obj.realized_pnl)
            user_account.balance += realized_pnl
            user_account.realized_pnl += realized_pnl
            user_account.equity = user_account.balance + user_account.unrealized_pnl
            
            # Update margin used
            if close_quantity >= float(position_obj.quantity):
                # Full close - release all margin
                user_account.margin_used -= float(position_obj.margin_used)
            else:
                # Partial close - release proportional margin
                margin_released = float(position_obj.margin_used) * (close_quantity / float(position_obj.quantity))
                user_account.margin_used -= margin_released
            
            user_account.margin_available = user_account.balance - user_account.margin_used
            
            await db.commit()
            
            # Create ledger entry for the position close
            from app.models.account_ledger import AccountLedger, LedgerEntryType, LedgerStatus
            ledger_entry = AccountLedger(
                user_id=user_id,
                account_id=user_account.account_id,
                position_id=position_id,
                entry_type=LedgerEntryType.POSITION_CLOSE,
                status=LedgerStatus.COMPLETED,
                amount=realized_pnl,
                balance_before=user_account.balance - realized_pnl,
                balance_after=user_account.balance,
                currency="USD" if position_obj.instrument.type == "crypto" else "INR",
                description=f"Position closed: {position_obj.instrument.symbol} {close_quantity} @ {current_price}"
            )
            db.add(ledger_entry)
            await db.commit()
        
        logger.info(f"Position {position_id} closed by user {user_id} - Quantity: {close_quantity}, PnL: {realized_pnl}")
        
        return {
            "message": "Position closed successfully",
            "position": closed_position.to_dict(),
            "realized_pnl": realized_pnl,
            "close_quantity": close_quantity
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error closing position {position_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Dashboard Endpoints
@router.get("/dashboard/summary", response_model=TradingSummary)
async def get_trading_summary(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get trading dashboard summary"""
    try:
        # Get account balance
        user_accounts = await account.get_by_user_id(db, user_id=user_id)
        total_balance = sum(acc.balance for acc in user_accounts)
        
        # Get position summary
        position_summary = await position.get_position_summary(db, user_id=user_id)
        
        # Get pending orders count
        pending_orders = await order.get_pending_orders(db, user_id=user_id)
        
        available_balance = float(total_balance - position_summary["total_margin_used"])
        total_equity = available_balance + position_summary["total_unrealized_pnl"]
        
        return TradingSummary(
            total_balance=float(total_balance),
            available_balance=available_balance,
            margin_used=position_summary["total_margin_used"],
            unrealized_pnl=position_summary["total_unrealized_pnl"],
            realized_pnl=position_summary["total_realized_pnl"],
            total_pnl=position_summary["total_unrealized_pnl"] + position_summary["total_realized_pnl"],
            total_equity=total_equity,
            open_positions_count=position_summary["total_positions"],
            pending_orders_count=len(pending_orders)
        )
        
    except Exception as e:
        logger.error(f"Error getting trading summary for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Chart Data Endpoint (placeholder for real chart data)
@router.get("/chart/{instrument_id}")
async def get_chart_data(
    instrument_id: str,
    timeframe: str = Query("1d", description="Chart timeframe"),
    db: AsyncSession = Depends(get_db)
):
    """Get chart data for an instrument (placeholder implementation)"""
    try:
        # Get instrument details
        instrument_obj = await instrument.get(db, id=instrument_id)
        if not instrument_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instrument not found"
            )
        
        # This is a placeholder - in a real implementation, you would:
        # 1. Connect to a market data provider (e.g., Alpha Vantage, Yahoo Finance)
        # 2. Fetch historical price data
        # 3. Return formatted chart data
        
        # For now, return mock data
        from datetime import datetime, timedelta
        import random
        
        data_points = []
        base_price = instrument_obj.current_price
        current_time = datetime.now()
        
        for i in range(100):
            timestamp = current_time - timedelta(hours=i)
            # Generate some realistic price movement
            price_change = random.uniform(-0.02, 0.02) * base_price
            price = base_price + price_change
            volume = random.uniform(1000, 10000)
            
            data_points.append({
                "timestamp": timestamp,
                "price": round(price, 2),
                "volume": round(volume, 2)
            })
        
        data_points.reverse()  # Oldest first
        
        return ChartData(
            instrument_id=instrument_id,
            symbol=instrument_obj.symbol,
            timeframe=timeframe,
            data=data_points
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chart data for instrument {instrument_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
