from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.security import HTTPBearer
import json
import logging
from typing import List
from app.services.websocket_manager import websocket_manager

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)

@router.websocket("/ws/market-data")
async def websocket_market_data(websocket: WebSocket):
    """WebSocket endpoint for real-time market data"""
    client_id = "anonymous"
    
    try:
        await websocket_manager.connect(websocket, client_id)
        
        while True:
            # Wait for client messages (subscriptions, etc.)
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get('type') == 'subscribe':
                # Update client subscriptions
                subscriptions = message.get('symbols', [])
                websocket_manager.connection_metadata[websocket]['subscriptions'] = subscriptions
                
                # Send confirmation
                await websocket_manager.send_personal_message({
                    'type': 'subscription_confirmed',
                    'symbols': subscriptions,
                    'timestamp': websocket_manager.connection_metadata[websocket]['connected_at'].isoformat()
                }, websocket)
            
            elif message.get('type') == 'ping':
                # Respond to ping with pong
                await websocket_manager.send_personal_message({
                    'type': 'pong',
                    'timestamp': websocket_manager.connection_metadata[websocket]['connected_at'].isoformat()
                }, websocket)
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)

@router.websocket("/ws/market-data/{client_id}")
async def websocket_market_data_authenticated(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for authenticated real-time market data"""
    try:
        await websocket_manager.connect(websocket, client_id)
        
        while True:
            # Wait for client messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get('type') == 'subscribe':
                # Update client subscriptions
                subscriptions = message.get('symbols', [])
                websocket_manager.connection_metadata[websocket]['subscriptions'] = subscriptions
                
                # Send confirmation
                await websocket_manager.send_personal_message({
                    'type': 'subscription_confirmed',
                    'symbols': subscriptions,
                    'timestamp': websocket_manager.connection_metadata[websocket]['connected_at'].isoformat()
                }, websocket)
            
            elif message.get('type') == 'ping':
                # Respond to ping with pong
                await websocket_manager.send_personal_message({
                    'type': 'pong',
                    'timestamp': websocket_manager.connection_metadata[websocket]['connected_at'].isoformat()
                }, websocket)
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)

@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status"""
    return {
        "active_connections": websocket_manager.get_connection_count(),
        "unique_clients": websocket_manager.get_client_count(),
        "status": "active"
    }
