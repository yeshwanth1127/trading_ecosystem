"""
Trading Events WebSocket API
============================

Provides real-time WebSocket connection for trading events.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any, Optional
import json
import logging
import asyncio
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.database import AsyncSessionLocal
from app.services.redis_service import redis_service
from app.models.order import Order, OrderStatus
from app.models.position import Position, PositionStatus
from app.models.account import Account

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trading-events", tags=["trading-events"])

class TradingEventManager:
    """Manages WebSocket connections for trading events"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.redis_client: redis.Redis = None
        self.subscriber_task: asyncio.Task = None
        self.is_running = False
    
    async def initialize(self):
        """Initialize the event manager"""
        try:
            self.redis_client = redis_service.get_client()
            await self.redis_client.ping()
            logger.info("✅ Trading Event Manager: Redis connection established")
            
        except Exception as e:
            logger.error(f"❌ Trading Event Manager initialization failed: {e}")
            raise
    
    async def start(self):
        """Start the Redis subscriber"""
        if self.is_running:
            return
        
        self.is_running = True
        self.subscriber_task = asyncio.create_task(self._redis_subscriber())
        logger.info("🎯 Trading Event Manager started")
    
    async def stop(self):
        """Stop the Redis subscriber"""
        self.is_running = False
        if self.subscriber_task:
            self.subscriber_task.cancel()
            try:
                await self.subscriber_task
            except asyncio.CancelledError:
                pass
        
        # Close all WebSocket connections
        for connection in self.active_connections:
            try:
                await connection.close()
            except:
                pass
        self.active_connections.clear()
        
        logger.info("⏹️ Trading Event Manager stopped")
    
    async def _redis_subscriber(self):
        """Subscribe to Redis trading events"""
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe('trading_events')
            
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        # Handle different event types
                        if message['data'].startswith('balance_update:'):
                            # Balance update event
                            parts = message['data'].split(':')
                            if len(parts) >= 3:
                                user_id = parts[1]
                                account_id = parts[2]
                                
                                # Get balance data from Redis
                                balance_data = await self.redis_client.hgetall(f"user_balance:{user_id}")
                                if balance_data:
                                    event_data = {
                                        'event_type': 'balance_update',
                                        'user_id': user_id,
                                        'account_id': account_id,
                                        'balance_data': balance_data,
                                        'timestamp': balance_data.get('last_updated')
                                    }
                                    await self._broadcast_event(event_data)
                        else:
                            # Regular trading event
                            event_data = json.loads(message['data'])
                            await self._broadcast_event(event_data)
                            
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in trading event: {message['data']}")
                    except Exception as e:
                        logger.error(f"❌ Error processing trading event: {e}")
                        
        except Exception as e:
            logger.error(f"❌ Redis subscriber error: {e}")
    
    async def _broadcast_event(self, event_data: Dict[str, Any]):
        """Broadcast event to all connected WebSocket clients"""
        if not self.active_connections:
            return
        
        message = json.dumps(event_data)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.active_connections.remove(connection)
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"📡 New WebSocket connection established. Total connections: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection with proper cleanup"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            try:
                # Close the WebSocket connection properly
                if websocket.client_state.name == "CONNECTED":
                    await websocket.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket: {e}")
        logger.info(f"📡 WebSocket connection closed. Total connections: {len(self.active_connections)}")

# Global event manager instance
event_manager = TradingEventManager()

@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time trading events with comprehensive data"""
    await event_manager.connect(websocket)
    
    try:
        # Send initial data snapshot
        await _send_initial_data(websocket)
        
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            
            # Handle client messages (e.g., subscription requests)
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "subscribe":
                    # Could implement event filtering here
                    await websocket.send_text(json.dumps({
                        "type": "subscribed",
                        "events": message.get("events", "all")
                    }))
                elif message.get("type") == "request_data":
                    # Send current data snapshot
                    await _send_data_snapshot(websocket, message.get("user_id"))
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
                
    except WebSocketDisconnect:
        await event_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        await event_manager.disconnect(websocket)

@router.get("/status")
async def get_event_manager_status():
    """Get the status of the trading event manager"""
    return {
        "is_running": event_manager.is_running,
        "active_connections": len(event_manager.active_connections),
        "redis_connected": event_manager.redis_client is not None
    }

@router.post("/start")
async def start_event_manager():
    """Start the trading event manager"""
    try:
        if event_manager.is_running:
            return {"message": "Event manager is already running"}
        
        await event_manager.start()
        return {"message": "Event manager started successfully"}
        
    except Exception as e:
        logger.error(f"Failed to start event manager: {e}")
        return {"error": f"Failed to start event manager: {str(e)}"}

@router.post("/stop")
async def stop_event_manager():
    """Stop the trading event manager"""
    try:
        if not event_manager.is_running:
            return {"message": "Event manager is not running"}
        
        await event_manager.stop()
        return {"message": "Event manager stopped successfully"}
        
    except Exception as e:
        logger.error(f"Failed to stop event manager: {e}")
        return {"error": f"Failed to stop event manager: {str(e)}"}

@router.get("/events/types")
async def get_event_types():
    """Get available trading event types"""
    return {
        "event_types": [
            "order_filled",
            "order_partially_filled", 
            "order_cancelled",
            "order_rejected",
            "position_opened",
            "position_updated",
            "position_closed",
            "position_liquidated",
            "stop_loss_triggered",
            "take_profit_triggered",
            "margin_call",
            "account_updated",
            "balance_update",
            "price_update"
        ]
    }

async def _send_initial_data(websocket: WebSocket):
    """Send initial data snapshot to new WebSocket connection"""
    try:
        # Get market prices from Redis
        market_data = await _get_market_prices()
        
        # Send initial market data
        initial_message = {
            "type": "initial_data",
            "timestamp": asyncio.get_event_loop().time(),
            "market_prices": market_data
        }
        
        await websocket.send_text(json.dumps(initial_message))
        logger.info("📡 Sent initial data to WebSocket client")
        
    except Exception as e:
        logger.error(f"❌ Failed to send initial data: {e}")

async def _send_data_snapshot(websocket: WebSocket, user_id: Optional[str] = None):
    """Send comprehensive data snapshot including orders, positions, and account data"""
    try:
        async with AsyncSessionLocal() as session:
            # Get market prices
            market_prices = await _get_market_prices()
            
            # Get user-specific data if user_id provided
            orders = []
            positions = []
            account_data = {}
            
            if user_id:
                # Get user's orders
                orders_result = await session.execute(
                    select(Order)
                    .where(Order.user_id == user_id)
                    .where(Order.status.in_([OrderStatus.PENDING, OrderStatus.PARTIAL, OrderStatus.FILLED]))
                    .options(selectinload(Order.instrument))
                )
                orders = [order.to_dict() for order in orders_result.scalars().all()]
                
                # Get user's positions
                positions_result = await session.execute(
                    select(Position)
                    .where(Position.user_id == user_id)
                    .where(Position.status == PositionStatus.OPEN)
                    .options(selectinload(Position.instrument))
                )
                positions = [position.to_dict() for position in positions_result.scalars().all()]
                
                # Get user's account data from Redis
                if event_manager.redis_client:
                    account_data = await event_manager.redis_client.hgetall(f"user_balance:{user_id}")
            
            # Send comprehensive data snapshot
            snapshot_message = {
                "type": "data_snapshot",
                "timestamp": asyncio.get_event_loop().time(),
                "market_prices": market_prices,
                "orders": orders,
                "positions": positions,
                "account": account_data
            }
            
            await websocket.send_text(json.dumps(snapshot_message))
            logger.info(f"📡 Sent data snapshot to WebSocket client (user: {user_id})")
            
    except Exception as e:
        logger.error(f"❌ Failed to send data snapshot: {e}")

async def _get_market_prices() -> Dict[str, Dict[str, Any]]:
    """Get current market prices from Redis"""
    try:
        if not event_manager.redis_client:
            return {}
        
        price_keys = await event_manager.redis_client.keys("latest_price:*")
        market_prices = {}
        
        for key in price_keys:
            symbol = key.replace("latest_price:", "")
            price_data = await event_manager.redis_client.hgetall(key)
            if price_data:
                market_prices[symbol] = {
                    "price": float(price_data.get("price", 0)),
                    "bid": float(price_data.get("bid", 0)),
                    "ask": float(price_data.get("ask", 0)),
                    "volume": float(price_data.get("volume", 0)),
                    "timestamp": price_data.get("timestamp")
                }
        
        return market_prices
        
    except Exception as e:
        logger.error(f"❌ Failed to get market prices: {e}")
        return {}
