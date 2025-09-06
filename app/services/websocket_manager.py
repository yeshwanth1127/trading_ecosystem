import asyncio
import json
import logging
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections for real-time market data"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_metadata: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str, subscriptions: List[str] = None):
        """Accept a WebSocket connection and add to active connections"""
        await websocket.accept()
        
        if client_id not in self.active_connections:
            self.active_connections[client_id] = set()
        
        self.active_connections[client_id].add(websocket)
        self.connection_metadata[websocket] = {
            'client_id': client_id,
            'subscriptions': subscriptions or [],
            'connected_at': datetime.now()
        }
        
        # Send initial connection confirmation
        await self.send_personal_message({
            'type': 'connection_established',
            'client_id': client_id,
            'timestamp': datetime.now().isoformat()
        }, websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection from active connections"""
        if websocket in self.connection_metadata:
            client_id = self.connection_metadata[websocket]['client_id']
            
            if client_id in self.active_connections:
                self.active_connections[client_id].discard(websocket)
                
                # Remove client if no more connections
                if not self.active_connections[client_id]:
                    del self.active_connections[client_id]
            
            del self.connection_metadata[websocket]
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to a specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            # Connection might be closed, remove it
            self.disconnect(websocket)
    
    async def broadcast_to_client(self, message: dict, client_id: str):
        """Broadcast message to all connections of a specific client"""
        if client_id in self.active_connections:
            disconnected = set()
            for websocket in self.active_connections[client_id]:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception:
                    disconnected.add(websocket)
            
            # Clean up disconnected connections
            for websocket in disconnected:
                self.disconnect(websocket)
    
    async def broadcast_market_data(self, symbol: str, data: dict):
        """Broadcast market data to all interested clients"""
        message = {
            'type': 'market_data_update',
            'symbol': symbol,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        # Broadcast to all active connections
        disconnected = set()
        for client_id, connections in self.active_connections.items():
            for websocket in connections:
                try:
                    # Check if client is subscribed to this symbol
                    metadata = self.connection_metadata.get(websocket, {})
                    subscriptions = metadata.get('subscriptions', [])
                    
                    if not subscriptions or symbol in subscriptions or 'all' in subscriptions:
                        await websocket.send_text(json.dumps(message))
                except Exception:
                    disconnected.add(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def broadcast_price_update(self, symbol: str, price: float, change_24h: float = None):
        """Broadcast price update to all interested clients"""
        message = {
            'type': 'price_update',
            'symbol': symbol,
            'price': price,
            'change_24h': change_24h,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.broadcast_market_data(symbol, message)
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(connections) for connections in self.active_connections.values())
    
    def get_client_count(self) -> int:
        """Get number of unique clients connected"""
        return len(self.active_connections)

# Global WebSocket manager instance
websocket_manager = WebSocketManager()
