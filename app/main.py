from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.config.settings import settings
from app.api.v1.api import api_router
from app.db.database import init_db, close_db
from app.services.redis_service import redis_service
from app.services.instrument_service import instrument_service
from app.services.real_time_market_data import real_time_market_data_service
from app.services.execution_engine import execution_engine
from app.services.account_balance_service import account_balance_service
from app.services.transaction_manager import transaction_manager
from app.api.v1.trading_events import event_manager
from app.orchestrator import orchestrator

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Set specific log levels to reduce noise
logging.getLogger('app.services.market_data_service').setLevel(logging.ERROR)
logging.getLogger('app.services.real_time_market_data').setLevel(logging.ERROR)
logging.getLogger('app.api.v1.market_data').setLevel(logging.ERROR)

# Keep only critical API endpoint logs
logging.getLogger('uvicorn.access').setLevel(logging.INFO)
logging.getLogger('app.api.v1.endpoints').setLevel(logging.INFO)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Trading Ecosystem API...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
        
        # Initialize Redis service first (required by other services)
        await redis_service.initialize()
        logger.info("Redis service initialized successfully")
        
        # Initialize transaction manager
        # Note: Transaction manager doesn't need explicit initialization
        logger.info("Transaction manager ready")
        
        # Initialize instrument service
        await instrument_service.initialize()
        logger.info("Instrument service initialized successfully")
        
        # Disable legacy internal trading subsystems when using Freqtrade orchestration
        # Start orchestrator idle monitor
        orchestrator.start_idle_monitor()
        
        # Initialize trading event manager
        await event_manager.initialize()
        logger.info("Trading event manager initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Trading Ecosystem API...")
    try:
        # Nothing to close for orchestrator beyond FastAPI shutdown
        
        # Close trading event manager
        await event_manager.stop()
        logger.info("Trading event manager closed successfully")
        
        # Close instrument service
        await instrument_service.close()
        logger.info("Instrument service closed successfully")
        
        # Close transaction manager
        await transaction_manager.close()
        logger.info("Transaction manager closed successfully")
        
        # Close Redis service
        await redis_service.close()
        logger.info("Redis service closed successfully")
        
        # Close database connections
        await close_db()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing services: {e}")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="A comprehensive trading ecosystem API supporting funded challenges, simulated trading, and subscription-based modules",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=None,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": "1.0.0",
        "environment": settings.environment
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to Trading Ecosystem API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
