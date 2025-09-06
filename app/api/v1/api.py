from fastapi import APIRouter
from app.api.v1.endpoints import api, auth, challenge_selection, trading
from app.api.v1 import market_data, error_monitoring
from app.api.v1.endpoints import freqtrade_proxy

api_router = APIRouter()

# Include all endpoints from the consolidated api.py file
api_router.include_router(api.router, tags=["trading-ecosystem"])

# Include authentication endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Include challenge selection endpoints
api_router.include_router(challenge_selection.router, prefix="/challenge-selections", tags=["challenge-selections"])

# Include trading platform endpoints
api_router.include_router(trading.router, prefix="/trading", tags=["trading"])

# New Freqtrade proxy endpoints
api_router.include_router(freqtrade_proxy.router, prefix="/ft", tags=["freqtrade"])

# Include market data endpoints
api_router.include_router(market_data.router, tags=["market-data"])

# Include error monitoring endpoints
api_router.include_router(error_monitoring.router, tags=["error-monitoring"])
