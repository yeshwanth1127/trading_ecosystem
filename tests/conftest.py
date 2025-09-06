import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from app.config.settings import settings
import logging

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_password@localhost:5432/test_trading_ecosystem"
TEST_DATABASE_URL_SYNC = "postgresql://test_user:test_password@localhost:5432/test_trading_ecosystem"

# Create test engines
test_async_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
)

test_sync_engine = create_engine(
    TEST_DATABASE_URL_SYNC,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create test session factories
TestingAsyncSessionLocal = async_sessionmaker(
    test_async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

TestingSyncSessionLocal = sessionmaker(
    bind=test_sync_engine,
    expire_on_commit=False,
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db_setup():
    """Set up test database tables."""
    async with test_async_engine.begin() as conn:
        # Import all models to ensure they are registered
        from app.models import user, account, challenge_template, challenge_attempt, trade, subscription_plan, subscription
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Test database tables created successfully")
    
    yield
    
    # Cleanup
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        logger.info("Test database tables dropped successfully")

@pytest.fixture
async def db_session(test_db_setup) -> AsyncGenerator[AsyncSession, None]:
    """Get test database session."""
    async with TestingAsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Test database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

@pytest.fixture
def sync_db_session(test_db_setup):
    """Get test sync database session for migrations."""
    return TestingSyncSessionLocal()

@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "name": "Test User",
        "email": "test@example.com",
        "role": "trader",
        "status": "active"
    }

@pytest.fixture
def test_account_data():
    """Sample account data for testing."""
    return {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",  # UUID placeholder
        "type": "simulated",
        "balance": "10000.00"
    }

@pytest.fixture
def test_challenge_template_data():
    """Sample challenge template data for testing."""
    return {
        "name": "Test Challenge",
        "account_size": "50000.00",
        "fee_amount": "99.99",
        "profit_target_pct": "8.00",
        "max_drawdown_pct": "5.00",
        "daily_loss_pct": "3.00",
        "status": "active"
    }

@pytest.fixture
def test_trade_data():
    """Sample trade data for testing."""
    return {
        "account_id": "550e8400-e29b-41d4-a716-446655440001",  # UUID placeholder
        "user_id": "550e8400-e29b-41d4-a716-446655440000",  # UUID placeholder
        "instrument": "EURUSD",
        "side": "buy",
        "qty": "1.0",
        "entry_price": "1.0850"
    }

@pytest.fixture
def test_subscription_plan_data():
    """Sample subscription plan data for testing."""
    return {
        "name": "Basic Copy Trading",
        "type": "copy_trade",
        "price": "29.99",
        "features": {"max_copiers": 10, "real_time_signals": True},
        "status": "active"
    }
