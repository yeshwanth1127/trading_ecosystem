"""
Execution Engine API Endpoints
=============================

Provides REST API endpoints for the order matching engine.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
import logging

from app.db.database import get_async_session
from app.models.order import Order, OrderStatus
from app.models.position import Position, PositionStatus
from app.models.trade import Trade
from app.models.account_ledger import AccountLedger
from app.services.execution_engine import execution_engine, TradingEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/execution", tags=["execution-engine"])

@router.get("/status")
async def get_execution_engine_status():
    """Get the current status of the execution engine"""
    return {
        "is_running": execution_engine.is_running,
        "price_cache_size": len(execution_engine.price_cache),
        "position_cache_size": len(execution_engine.position_cache),
        "redis_connected": execution_engine.redis_client is not None
    }

@router.post("/start")
async def start_execution_engine():
    """Start the execution engine"""
    try:
        if execution_engine.is_running:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Execution engine is already running"
            )
        
        await execution_engine.start()
        return {"message": "Execution engine started successfully"}
        
    except Exception as e:
        logger.error(f"Failed to start execution engine: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start execution engine: {str(e)}"
        )

@router.post("/stop")
async def stop_execution_engine():
    """Stop the execution engine"""
    try:
        if not execution_engine.is_running:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Execution engine is not running"
            )
        
        await execution_engine.stop()
        return {"message": "Execution engine stopped successfully"}
        
    except Exception as e:
        logger.error(f"Failed to stop execution engine: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop execution engine: {str(e)}"
        )

@router.get("/orders/pending")
async def get_pending_orders(session: AsyncSession = Depends(get_async_session)):
    """Get all pending orders"""
    try:
        result = await session.execute(
            select(Order)
            .where(Order.status == OrderStatus.PENDING)
            .order_by(Order.created_at.desc())
        )
        orders = result.scalars().all()
        
        return {
            "orders": [
                {
                    "order_id": str(order.order_id),
                    "user_id": str(order.user_id),
                    "account_id": str(order.account_id),
                    "instrument_id": str(order.instrument_id),
                    "order_type": order.order_type.value,
                    "side": order.side.value,
                    "quantity": float(order.quantity),
                    "price": float(order.price) if order.price else None,
                    "stop_price": float(order.stop_price) if order.stop_price else None,
                    "leverage": float(order.leverage),
                    "is_margin_order": order.is_margin_order,
                    "created_at": order.created_at.isoformat(),
                    "notes": order.notes
                }
                for order in orders
            ],
            "count": len(orders)
        }
        
    except Exception as e:
        logger.error(f"Failed to get pending orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending orders: {str(e)}"
        )

@router.get("/positions/open")
async def get_open_positions(session: AsyncSession = Depends(get_async_session)):
    """Get all open positions"""
    try:
        result = await session.execute(
            select(Position)
            .where(Position.status == PositionStatus.OPEN)
            .order_by(Position.opened_at.desc())
        )
        positions = result.scalars().all()
        
        return {
            "positions": [
                {
                    "position_id": str(position.position_id),
                    "user_id": str(position.user_id),
                    "account_id": str(position.account_id),
                    "instrument_id": str(position.instrument_id),
                    "side": position.side.value,
                    "quantity": float(position.quantity),
                    "average_entry_price": float(position.average_entry_price),
                    "current_price": float(position.current_price),
                    "unrealized_pnl": float(position.unrealized_pnl),
                    "realized_pnl": float(position.realized_pnl),
                    "total_pnl": float(position.total_pnl),
                    "leverage": float(position.leverage),
                    "margin_used": float(position.margin_used),
                    "stop_loss": float(position.stop_loss) if position.stop_loss else None,
                    "take_profit": float(position.take_profit) if position.take_profit else None,
                    "liquidation_price": float(position.liquidation_price) if position.liquidation_price else None,
                    "opened_at": position.opened_at.isoformat(),
                    "last_updated": position.last_updated.isoformat()
                }
                for position in positions
            ],
            "count": len(positions)
        }
        
    except Exception as e:
        logger.error(f"Failed to get open positions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get open positions: {str(e)}"
        )

@router.get("/trades/recent")
async def get_recent_trades(
    limit: int = 100,
    session: AsyncSession = Depends(get_async_session)
):
    """Get recent trades"""
    try:
        result = await session.execute(
            select(Trade)
            .order_by(Trade.timestamp.desc())
            .limit(limit)
        )
        trades = result.scalars().all()
        
        return {
            "trades": [
                {
                    "trade_id": str(trade.trade_id),
                    "order_id": str(trade.order_id) if trade.order_id else None,
                    "user_id": str(trade.user_id),
                    "account_id": str(trade.account_id),
                    "instrument_id": str(trade.instrument_id),
                    "side": trade.side.value,
                    "quantity": float(trade.quantity),
                    "price": float(trade.price),
                    "amount": float(trade.amount),
                    "commission": float(trade.commission),
                    "leverage": float(trade.leverage),
                    "realized_pnl": float(trade.realized_pnl) if trade.realized_pnl else None,
                    "is_maker": trade.is_maker,
                    "timestamp": trade.timestamp.isoformat(),
                    "executed_at": trade.executed_at.isoformat() if trade.executed_at else None
                }
                for trade in trades
            ],
            "count": len(trades)
        }
        
    except Exception as e:
        logger.error(f"Failed to get recent trades: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent trades: {str(e)}"
        )

@router.get("/ledger/recent")
async def get_recent_ledger_entries(
    limit: int = 100,
    session: AsyncSession = Depends(get_async_session)
):
    """Get recent ledger entries"""
    try:
        result = await session.execute(
            select(AccountLedger)
            .order_by(AccountLedger.created_at.desc())
            .limit(limit)
        )
        entries = result.scalars().all()
        
        return {
            "entries": [
                {
                    "entry_id": str(entry.entry_id),
                    "user_id": str(entry.user_id),
                    "account_id": str(entry.account_id),
                    "order_id": str(entry.order_id) if entry.order_id else None,
                    "trade_id": str(entry.trade_id) if entry.trade_id else None,
                    "position_id": str(entry.position_id) if entry.position_id else None,
                    "entry_type": entry.entry_type.value,
                    "status": entry.status.value,
                    "amount": float(entry.amount),
                    "balance_before": float(entry.balance_before),
                    "balance_after": float(entry.balance_after),
                    "currency": entry.currency,
                    "description": entry.description,
                    "created_at": entry.created_at.isoformat(),
                    "processed_at": entry.processed_at.isoformat() if entry.processed_at else None
                }
                for entry in entries
            ],
            "count": len(entries)
        }
        
    except Exception as e:
        logger.error(f"Failed to get recent ledger entries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent ledger entries: {str(e)}"
        )

@router.get("/prices")
async def get_current_prices():
    """Get current price cache"""
    try:
        return {
            "prices": {
                symbol: {
                    "price": float(data["price"]),
                    "bid": float(data["bid"]),
                    "ask": float(data["ask"]),
                    "timestamp": data["timestamp"].isoformat()
                }
                for symbol, data in execution_engine.price_cache.items()
            },
            "count": len(execution_engine.price_cache)
        }
        
    except Exception as e:
        logger.error(f"Failed to get current prices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get current prices: {str(e)}"
        )

@router.get("/events")
async def get_trading_events():
    """Get available trading event types"""
    return {
        "events": [
            TradingEvent.ORDER_FILLED,
            TradingEvent.ORDER_PARTIALLY_FILLED,
            TradingEvent.ORDER_CANCELLED,
            TradingEvent.ORDER_REJECTED,
            TradingEvent.POSITION_OPENED,
            TradingEvent.POSITION_UPDATED,
            TradingEvent.POSITION_CLOSED,
            TradingEvent.POSITION_LIQUIDATED,
            TradingEvent.STOP_LOSS_TRIGGERED,
            TradingEvent.TAKE_PROFIT_TRIGGERED,
            TradingEvent.MARGIN_CALL,
            TradingEvent.ACCOUNT_UPDATED
        ]
    }

@router.post("/test/trigger-stop-loss")
async def test_trigger_stop_loss(
    user_id: str,
    instrument_id: str,
    stop_price: float
):
    """Test endpoint to manually trigger stop loss (for testing)"""
    try:
        from uuid import UUID
        from decimal import Decimal
        
        await execution_engine._trigger_stop_loss(
            UUID(user_id),
            UUID(instrument_id),
            Decimal(str(stop_price))
        )
        
        return {"message": "Stop loss triggered successfully"}
        
    except Exception as e:
        logger.error(f"Failed to trigger stop loss: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger stop loss: {str(e)}"
        )

@router.post("/test/trigger-take-profit")
async def test_trigger_take_profit(
    user_id: str,
    instrument_id: str,
    take_profit_price: float
):
    """Test endpoint to manually trigger take profit (for testing)"""
    try:
        from uuid import UUID
        from decimal import Decimal
        
        await execution_engine._trigger_take_profit(
            UUID(user_id),
            UUID(instrument_id),
            Decimal(str(take_profit_price))
        )
        
        return {"message": "Take profit triggered successfully"}
        
    except Exception as e:
        logger.error(f"Failed to trigger take profit: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger take profit: {str(e)}"
        )
