from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.config.settings import settings
import logging
import asyncio

# Import all models to ensure they are registered withis the why
# 
#  SQLAlchemy metadata
# This will be done in init_db function to avoid circular imports

logger = logging.getLogger(__name__)

# Create async engine with proper pool configuration
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=settings.db_pool_recycle,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_reset_on_return='commit',
)

# Create sync engine for migrations with proper pool configuration
sync_engine = create_engine(
    settings.database_url_sync,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=settings.db_pool_recycle,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_reset_on_return='commit',
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create sync session factory for migrations
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()

async def get_async_session() -> AsyncSession:
    """Dependency to get async database session with proper error handling"""
    session = None
    try:
        session = AsyncSessionLocal()
        yield session
    except Exception as e:
        if session:
            await session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        if session:
            try:
                await session.close()
            except Exception as e:
                logger.error(f"Error closing database session: {e}")

async def get_async_session_with_retry(max_retries: int = 3) -> AsyncSession:
    """Get async database session with retry logic for connection issues"""
    for attempt in range(max_retries):
        try:
            session = AsyncSessionLocal()
            # Test the connection
            await session.execute("SELECT 1")
            return session
        except Exception as e:
            if session:
                await session.close()
            logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff

def get_sync_session():
    """Get sync database session for migrations"""
    return SyncSessionLocal()

async def init_db():
    """Initialize database tables"""
    # Import all models here to avoid circular imports
    from app.models.user import User
    from app.models.account import Account
    from app.models.challenge_template import ChallengeTemplate
    from app.models.challenge_attempt import ChallengeAttempt
    from app.models.trade import Trade
    from app.models.subscription_plan import SubscriptionPlan
    from app.models.subscription import Subscription
    from app.models.challenge_selection import ChallengeSelection
    from app.models.trading_challenge import TradingChallenge
    from app.models.instrument import Instrument
    from app.models.order import Order
    from app.models.position import Position
    from app.models.account_ledger import AccountLedger
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")

async def close_db():
    """Close database connections"""
    await async_engine.dispose()
    logger.info("Database connections closed")
