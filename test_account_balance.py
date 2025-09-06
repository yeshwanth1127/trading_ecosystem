"""
Test Account Balance Service
============================

Test the real-time account balance and P&L management service.
"""

import asyncio
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def test_account_balance_service():
    """Test the account balance service functionality"""
    logger.info("🚀 Starting Account Balance Service Test")
    
    try:
        # Import the service
        from app.services.account_balance_service import account_balance_service
        
        # Test 1: Initialize the service
        logger.info("1. Initializing account balance service...")
        await account_balance_service.initialize()
        logger.info("✅ Account balance service initialized")
        
        # Test 2: Start the service
        logger.info("2. Starting account balance service...")
        await account_balance_service.start()
        logger.info("✅ Account balance service started")
        
        # Test 3: Wait for some balance updates
        logger.info("3. Waiting for balance updates...")
        await asyncio.sleep(5)  # Wait 5 seconds for updates
        
        # Test 4: Get account balance (if any accounts exist)
        logger.info("4. Testing balance retrieval...")
        try:
            # Try to get balance for a test user (this might not exist)
            balance_data = await account_balance_service.get_user_balance("test-user-id")
            if balance_data:
                logger.info(f"✅ Retrieved balance data: {json.dumps(balance_data, indent=2)}")
            else:
                logger.info("ℹ️ No balance data found (no accounts exist yet)")
        except Exception as e:
            logger.info(f"ℹ️ No balance data available: {e}")
        
        # Test 5: Check service status
        logger.info("5. Checking service status...")
        status = {
            "is_running": account_balance_service.is_running,
            "redis_connected": account_balance_service.redis_client is not None,
            "update_task_running": account_balance_service.update_task is not None and not account_balance_service.update_task.done()
        }
        logger.info(f"✅ Service status: {json.dumps(status, indent=2)}")
        
        # Test 6: Stop the service
        logger.info("6. Stopping account balance service...")
        await account_balance_service.stop()
        logger.info("✅ Account balance service stopped")
        
        # Test 7: Close the service
        logger.info("7. Closing account balance service...")
        await account_balance_service.close()
        logger.info("✅ Account balance service closed")
        
        logger.info("🎉 Account Balance Service test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Account Balance Service test failed: {e}")
        raise

async def test_balance_api_endpoints():
    """Test the balance API endpoints"""
    logger.info("🚀 Starting Balance API Endpoints Test")
    
    try:
        import aiohttp
        
        base_url = "http://localhost:8000/api/v1/account"
        
        async with aiohttp.ClientSession() as session:
            # Test 1: Get balance service status
            logger.info("1. Testing balance service status endpoint...")
            try:
                async with session.get(f"{base_url}/balance/status") as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Balance service status: {json.dumps(data, indent=2)}")
                    else:
                        logger.info(f"ℹ️ Balance service status endpoint returned: {response.status}")
            except Exception as e:
                logger.info(f"ℹ️ Balance service status endpoint not available: {e}")
            
            # Test 2: Get account balance (requires authentication)
            logger.info("2. Testing account balance endpoint...")
            try:
                async with session.get(f"{base_url}/balance") as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Account balance retrieved: {json.dumps(data, indent=2)}")
                    elif response.status == 401:
                        logger.info("ℹ️ Account balance endpoint requires authentication (expected)")
                    else:
                        logger.info(f"ℹ️ Account balance endpoint returned: {response.status}")
            except Exception as e:
                logger.info(f"ℹ️ Account balance endpoint not available: {e}")
            
            # Test 3: Get balance summary
            logger.info("3. Testing balance summary endpoint...")
            try:
                async with session.get(f"{base_url}/balance/summary") as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Balance summary retrieved: {json.dumps(data, indent=2)}")
                    elif response.status == 401:
                        logger.info("ℹ️ Balance summary endpoint requires authentication (expected)")
                    else:
                        logger.info(f"ℹ️ Balance summary endpoint returned: {response.status}")
            except Exception as e:
                logger.info(f"ℹ️ Balance summary endpoint not available: {e}")
        
        logger.info("🎉 Balance API Endpoints test completed!")
        
    except Exception as e:
        logger.error(f"❌ Balance API Endpoints test failed: {e}")
        raise

async def main():
    """Main test function"""
    logger.info("🚀 Starting Account Balance System Tests")
    
    try:
        # Test the service
        await test_account_balance_service()
        
        # Test the API endpoints
        await test_balance_api_endpoints()
        
        logger.info("🎉 All Account Balance tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Account Balance tests failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
