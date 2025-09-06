"""
Simple Execution Engine Test
============================

Quick test to validate basic execution engine functionality.
"""

import asyncio
import logging
import sys
import os
from decimal import Decimal
from datetime import datetime, timezone

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.execution_engine import execution_engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_basic_functionality():
    """Test basic execution engine functionality"""
    logger.info("🚀 Starting Simple Execution Engine Test")
    
    try:
        # Initialize execution engine
        logger.info("1. Initializing execution engine...")
        await execution_engine.initialize()
        logger.info("✅ Execution engine initialized")
        
        # Check status
        logger.info("2. Checking execution engine status...")
        logger.info(f"   - Is running: {execution_engine.is_running}")
        logger.info(f"   - Price cache size: {len(execution_engine.price_cache)}")
        logger.info(f"   - Position cache size: {len(execution_engine.position_cache)}")
        logger.info(f"   - Redis connected: {execution_engine.redis_client is not None}")
        
        # Start execution engine
        logger.info("3. Starting execution engine...")
        await execution_engine.start()
        logger.info("✅ Execution engine started")
        
        # Let it run for a few seconds
        logger.info("4. Running execution engine for 5 seconds...")
        await asyncio.sleep(5)
        
        # Check status again
        logger.info("5. Checking status after running...")
        logger.info(f"   - Is running: {execution_engine.is_running}")
        logger.info(f"   - Price cache size: {len(execution_engine.price_cache)}")
        logger.info(f"   - Position cache size: {len(execution_engine.position_cache)}")
        
        # Stop execution engine
        logger.info("6. Stopping execution engine...")
        await execution_engine.stop()
        logger.info("✅ Execution engine stopped")
        
        # Close execution engine
        logger.info("7. Closing execution engine...")
        await execution_engine.close()
        logger.info("✅ Execution engine closed")
        
        logger.info("🎉 Simple test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise

async def main():
    """Main test function"""
    await test_basic_functionality()

if __name__ == "__main__":
    asyncio.run(main())
