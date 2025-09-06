"""
Redis Connection Pool Service
============================

Centralized Redis connection management with connection pooling for optimal performance.
All services should use this singleton instance to avoid connection exhaustion.
"""

import asyncio
import logging
from typing import Optional
import redis.asyncio as redis
from redis.asyncio import ConnectionPool

logger = logging.getLogger(__name__)

class RedisService:
    """Centralized Redis connection service with connection pooling"""
    
    _instance: Optional['RedisService'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.redis_client: Optional[redis.Redis] = None
            self.connection_pool: Optional[ConnectionPool] = None
            self.is_initialized = False
            self.initialized = True
    
    async def initialize(self, 
                        host: str = 'localhost', 
                        port: int = 6379, 
                        db: int = 0,
                        max_connections: int = 20,
                        decode_responses: bool = True):
        """Initialize Redis connection pool"""
        async with self._lock:
            if self.is_initialized:
                logger.warning("⚠️ Redis Service already initialized")
                return
            
            try:
                # Create connection pool
                self.connection_pool = ConnectionPool(
                    host=host,
                    port=port,
                    db=db,
                    max_connections=max_connections,
                    decode_responses=decode_responses,
                    retry_on_timeout=True,
                    socket_keepalive=True,
                    socket_keepalive_options={},
                    health_check_interval=30
                )
                
                # Create Redis client with connection pool
                self.redis_client = redis.Redis(connection_pool=self.connection_pool)
                
                # Test connection
                await self.redis_client.ping()
                
                self.is_initialized = True
                logger.info(f"✅ Redis Service initialized with connection pool (max_connections={max_connections})")
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize Redis Service: {e}")
                raise
    
    async def close(self):
        """Close Redis connections"""
        async with self._lock:
            if not self.is_initialized:
                return
            
            try:
                if self.redis_client:
                    await self.redis_client.close()
                
                if self.connection_pool:
                    await self.connection_pool.disconnect()
                
                self.is_initialized = False
                logger.info("🔒 Redis Service closed")
                
            except Exception as e:
                logger.error(f"❌ Error closing Redis Service: {e}")
    
    def get_client(self) -> redis.Redis:
        """Get Redis client instance"""
        if not self.is_initialized:
            raise RuntimeError("Redis Service not initialized. Call initialize() first.")
        return self.redis_client
    
    async def health_check(self) -> bool:
        """Check Redis connection health"""
        try:
            if not self.is_initialized or not self.redis_client:
                return False
            
            await self.redis_client.ping()
            return True
            
        except Exception as e:
            logger.error(f"❌ Redis health check failed: {e}")
            return False
    
    async def get_connection_info(self) -> dict:
        """Get Redis connection pool information"""
        try:
            if not self.is_initialized or not self.connection_pool:
                return {"status": "not_initialized"}
            
            return {
                "status": "connected",
                "max_connections": self.connection_pool.max_connections,
                "created_connections": len(self.connection_pool._created_connections),
                "available_connections": len(self.connection_pool._available_connections),
                "in_use_connections": len(self.connection_pool._in_use_connections)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get connection info: {e}")
            return {"status": "error", "error": str(e)}

# Global singleton instance
redis_service = RedisService()
