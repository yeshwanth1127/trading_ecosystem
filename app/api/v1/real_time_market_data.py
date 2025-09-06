from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, List, Optional
import json
import logging
from datetime import datetime
from app.services.real_time_market_data import real_time_market_data_service, MarketTick

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/real-time-market-data", tags=["real-time-market-data"])

@router.get("/latest-prices")
async def get_latest_prices():
    """Get all latest market prices"""
    try:
        prices = await real_time_market_data_service.get_all_latest_prices()
        return {
            "success": True,
            "data": prices,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting latest prices: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch latest prices")

@router.get("/latest-price/{symbol}")
async def get_latest_price(symbol: str):
    """Get latest price for a specific symbol"""
    try:
        price_data = await real_time_market_data_service.get_latest_price(symbol)
        if not price_data:
            raise HTTPException(status_code=404, detail=f"Price data not found for symbol: {symbol}")
        
        return {
            "success": True,
            "data": price_data,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest price for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch latest price")

@router.get("/crypto-prices")
async def get_crypto_prices():
    """Get all crypto prices"""
    try:
        all_prices = await real_time_market_data_service.get_all_latest_prices()
        crypto_prices = {
            symbol: data for symbol, data in all_prices.items() 
            if not symbol.endswith('.NSE')
        }
        
        return {
            "success": True,
            "data": crypto_prices,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting crypto prices: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch crypto prices")

@router.get("/stock-prices")
async def get_stock_prices():
    """Get all stock prices"""
    try:
        all_prices = await real_time_market_data_service.get_all_latest_prices()
        stock_prices = {
            symbol: data for symbol, data in all_prices.items() 
            if symbol.endswith('.NSE')
        }
        
        return {
            "success": True,
            "data": stock_prices,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting stock prices: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stock prices")

@router.post("/start-feed")
async def start_market_data_feed(interval_seconds: int = 5):
    """Start the real-time market data feed"""
    try:
        if real_time_market_data_service.is_running:
            return {
                "success": True,
                "message": "Market data feed is already running",
                "status": "running"
            }
        
        # Start the feed in the background
        import asyncio
        asyncio.create_task(real_time_market_data_service.start_market_data_feed(interval_seconds))
        
        return {
            "success": True,
            "message": f"Market data feed started with {interval_seconds}s interval",
            "status": "started"
        }
    except Exception as e:
        logger.error(f"Error starting market data feed: {e}")
        raise HTTPException(status_code=500, detail="Failed to start market data feed")

@router.post("/stop-feed")
async def stop_market_data_feed():
    """Stop the real-time market data feed"""
    try:
        await real_time_market_data_service.stop_market_data_feed()
        return {
            "success": True,
            "message": "Market data feed stopped",
            "status": "stopped"
        }
    except Exception as e:
        logger.error(f"Error stopping market data feed: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop market data feed")

@router.get("/feed-status")
async def get_feed_status():
    """Get the current status of the market data feed"""
    try:
        return {
            "success": True,
            "data": {
                "is_running": real_time_market_data_service.is_running,
                "websocket_connections": len(real_time_market_data_service.websocket_connections),
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error getting feed status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get feed status")

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time market data updates"""
    await websocket.accept()
    
    try:
        # Add connection to the service
        await real_time_market_data_service.add_websocket_connection(websocket)
        
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "message": "Connected to real-time market data feed",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for client messages (ping/pong for keepalive)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in WebSocket connection: {e}")
                break
                
    except Exception as e:
        logger.error(f"Error establishing WebSocket connection: {e}")
    finally:
        # Remove connection from the service
        await real_time_market_data_service.remove_websocket_connection(websocket)
        logger.info("WebSocket connection closed")

@router.get("/symbols")
async def get_available_symbols():
    """Get list of available trading symbols"""
    try:
        return {
            "success": True,
            "data": {
                "crypto_symbols": real_time_market_data_service.crypto_symbols,
                "stock_symbols": real_time_market_data_service.stock_symbols,
                "total_crypto": len(real_time_market_data_service.crypto_symbols),
                "total_stocks": len(real_time_market_data_service.stock_symbols)
            }
        }
    except Exception as e:
        logger.error(f"Error getting available symbols: {e}")
        raise HTTPException(status_code=500, detail="Failed to get available symbols")
