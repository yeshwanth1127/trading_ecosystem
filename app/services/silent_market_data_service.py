import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from app.services.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

class SilentMarketDataService:
    """Silent market data service that only logs significant changes"""
    
    def __init__(self):
        self.price_cache: Dict[str, Dict[str, Any]] = {}
        self.last_logged: Dict[str, datetime] = {}
        self.significant_change_threshold = 0.01  # 1% change threshold
        self.log_interval = timedelta(minutes=5)  # Minimum time between logs for same symbol
        
    async def update_price_silently(self, symbol: str, price: float, change_24h: float = None, 
                                  market_type: str = "crypto") -> bool:
        """
        Update price silently, only log if significant change or time threshold
        Returns True if price was updated, False if no significant change
        """
        try:
            current_time = datetime.now()
            previous_data = self.price_cache.get(symbol, {})
            previous_price = previous_data.get('price', 0)
            
            # Calculate price change percentage
            if previous_price > 0:
                price_change_percent = abs(price - previous_price) / previous_price
            else:
                price_change_percent = 1.0  # First time seeing this symbol
            
            # Check if this is a significant change
            is_significant_change = price_change_percent >= self.significant_change_threshold
            
            # Check if enough time has passed since last log
            last_logged_time = self.last_logged.get(symbol, datetime.min)
            time_since_last_log = current_time - last_logged_time
            should_log_time = time_since_last_log >= self.log_interval
            
            # Update cache
            self.price_cache[symbol] = {
                'price': price,
                'change_24h': change_24h,
                'market_type': market_type,
                'last_updated': current_time,
                'price_change_percent': price_change_percent
            }
            
            # Log only if significant change or time threshold
            if is_significant_change or should_log_time:
                logger.info(f"Significant price change: {symbol} - {previous_price:.4f} → {price:.4f} "
                          f"({price_change_percent:.2%}) - {market_type}")
                self.last_logged[symbol] = current_time
                
                # Broadcast via WebSocket
                await websocket_manager.broadcast_price_update(symbol, price, change_24h)
                return True
            
            # Silent update - no logging, but still broadcast via WebSocket
            await websocket_manager.broadcast_price_update(symbol, price, change_24h)
            return True
            
        except Exception as e:
            # Only log errors, not regular operations
            logger.error(f"Error updating price for {symbol}: {e}")
            return False
    
    async def batch_update_prices(self, price_updates: List[Dict[str, Any]]) -> Dict[str, bool]:
        """
        Batch update multiple prices silently
        Returns dict of symbol -> success status
        """
        results = {}
        
        for update in price_updates:
            symbol = update.get('symbol')
            price = update.get('price')
            change_24h = update.get('change_24h')
            market_type = update.get('market_type', 'crypto')
            
            if symbol and price:
                results[symbol] = await self.update_price_silently(symbol, price, change_24h, market_type)
        
        return results
    
    def get_cached_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached price data for a symbol"""
        return self.price_cache.get(symbol)
    
    def get_all_cached_prices(self) -> Dict[str, Dict[str, Any]]:
        """Get all cached price data"""
        return self.price_cache.copy()
    
    def clear_cache(self):
        """Clear all cached data"""
        self.price_cache.clear()
        self.last_logged.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'total_symbols': len(self.price_cache),
            'cache_size_mb': sum(len(str(data)) for data in self.price_cache.values()) / 1024 / 1024,
            'oldest_entry': min((data['last_updated'] for data in self.price_cache.values()), default=None),
            'newest_entry': max((data['last_updated'] for data in self.price_cache.values()), default=None)
        }

# Global silent market data service instance
silent_market_data_service = SilentMarketDataService()
