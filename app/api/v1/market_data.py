from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.services.market_data_service import market_data_service
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market-data", tags=["market-data"])

@router.get("/instruments")
async def get_instruments(
    market_type: str = "all"
):
    """
    Get live market data for instruments
    
    Args:
        market_type: Type of market data to fetch ('crypto', 'stock', or 'all')
        current_user: Current authenticated user (optional for public data)
    
    Returns:
        Dictionary containing crypto and/or stock market data
    """
    try:
        data = await market_data_service.get_market_data(market_type)
        return {
            "success": True,
            "data": data,
            "timestamp": market_data_service.cache_expiry.get(f"market_data_{market_type}", None)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch market data: {str(e)}")

@router.get("/instruments/{symbol}")
async def get_instrument(
    symbol: str,
    market_type: str = "all"
):
    """
    Get specific instrument data
    
    Args:
        symbol: Instrument symbol (e.g., 'BTC', 'AAPL')
        market_type: Type of market ('crypto' or 'stock')
        current_user: Current authenticated user (optional for public data)
    
    Returns:
        Instrument data
    """
    try:
        data = await market_data_service.get_instrument_data(symbol, market_type)
        if not data:
            raise HTTPException(status_code=404, detail=f"Instrument {symbol} not found")
        
        return {
            "success": True,
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch instrument data: {str(e)}")

@router.get("/price/{symbol}")
async def get_instrument_price(
    symbol: str,
    market_type: str = "crypto"
):
    """
    Get current price for a specific instrument (lightweight endpoint)
    
    Args:
        symbol: Instrument symbol (e.g., 'BTC', 'ETH', 'XRP', 'RELIANCE.NS')
        market_type: Type of market ('crypto' or 'stock')
    
    Returns:
        Current price data
    """
    try:
        # Get just the price data
        data = await market_data_service.get_instrument_data(symbol, market_type)
        if not data:
            # Try to refresh cache and search again
            await market_data_service.refresh_cache()
            data = await market_data_service.get_instrument_data(symbol, market_type)
            
            if not data:
                # If still not found, return a fallback response for known symbols
                # Try alternative data sources for real-time fallback
                if market_type == "crypto":
                    # Try CoinMarketCap as fallback for crypto
                    try:
                        fallback_data = await market_data_service._fetch_coingecko_fallback(symbol)
                        if fallback_data:
                            return {
                                "success": True,
                                "data": fallback_data
                            }
                    except:
                        pass
                elif market_type == "stock":
                    # Try Alpha Vantage as fallback for stocks
                    try:
                        fallback_data = await market_data_service._fetch_alpha_vantage_fallback(symbol)
                        if fallback_data:
                            return {
                                "success": True,
                                "data": fallback_data
                            }
                    except:
                        pass
                
                raise HTTPException(status_code=404, detail=f"Instrument {symbol} not found")
        
        return {
            "success": True,
            "data": {
                "symbol": data.get("symbol"),
                "current_price": data.get("current_price"),
                "price_change_24h": data.get("price_change_24h"),
                "last_updated": data.get("last_updated")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch price for {symbol}: {str(e)}")

@router.post("/refresh")
async def refresh_market_data():
    """
    Force refresh of market data cache
    
    Args:
        current_user: Current authenticated user (required)
    
    Returns:
        Success status
    """
    try:
        await market_data_service.refresh_cache()
        return {
            "success": True,
            "message": "Market data cache refreshed successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh market data: {str(e)}")

@router.get("/crypto")
async def get_crypto_data():
    """
    Get crypto market data only
    
    Args:
        current_user: Current authenticated user (optional for public data)
    
    Returns:
        Crypto market data
    """
    try:
        data = await market_data_service.get_market_data("crypto")
        return {
            "success": True,
            "data": data.get("crypto", []),
            "timestamp": market_data_service.cache_expiry.get("market_data_crypto", None)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch crypto data: {str(e)}")

@router.get("/stocks")
async def get_stock_data():
    """
    Get stock market data only
    
    Args:
        current_user: Current authenticated user (optional for public data)
    
    Returns:
        Stock market data
    """
    try:
        data = await market_data_service.get_market_data("stock")
        return {
            "success": True,
            "data": data.get("stock", []),
            "timestamp": market_data_service.cache_expiry.get("market_data_stock", None)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stock data: {str(e)}")

@router.get("/status")
async def get_market_data_status():
    """
    Get market data service status and cache info
    
    Args:
        current_user: Current authenticated user (optional for public data)
    
    Returns:
        Service status information
    """
    try:
        cache_keys = list(market_data_service.cache.keys())
        cache_status = {}
        
        for key in cache_keys:
            cache_status[key] = {
                "valid": market_data_service._is_cache_valid(key),
                "expires": market_data_service.cache_expiry.get(key, None)
            }
        
        return {
            "success": True,
            "status": "running",
            "cache_status": cache_status,
            "session_active": market_data_service.session is not None and not market_data_service.session.closed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get service status: {str(e)}")
