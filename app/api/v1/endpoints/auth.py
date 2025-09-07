from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.crud import user
from app.schemas import UserCreate, UserResponse, UserLogin, Token
from app.core.security import create_access_token, verify_token
import logging
from app.orchestrator import orchestrator
from app.crud import challenge_selection as challenge_selection_crud
from app.services.trading_challenge_service import TradingChallengeService

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = await user.get_by_email(db, email=user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create new user
        db_user = await user.create(db, obj_in=user_in)
        logger.info(f"User registered successfully: {db_user.email}")

        # Create per-user user_data directory from template
        orchestrator.ensure_user_userdir(str(db_user.user_id))

        # Initialize whitelist with Binance USDT futures pairs on first account creation
        try:
            from app.api.v1.endpoints.freqtrade_proxy import sync_whitelist  # type: ignore
            # Simulate a call by directly invoking whitelist builder logic
            import importlib
            ccxt = importlib.import_module("ccxt")
            ex = ccxt.binance({"options": {"defaultType": "future"}})
            markets = ex.load_markets()
            usdt_pairs = []
            for symbol, m in markets.items():
                try:
                    # Futures: contract markets, USDT margined, active
                    if (
                        isinstance(symbol, str)
                        and symbol.endswith("/USDT")
                        and m.get("contract") is True
                        and (m.get("linear") is True or m.get("settle") == "USDT")
                        and m.get("type") in ("future", "swap")
                        and m.get("active", True)
                    ):
                        usdt_pairs.append(symbol)
                except Exception:
                    continue
            if usdt_pairs:
                orchestrator.update_user_pair_whitelist(str(db_user.user_id), sorted(list(set(usdt_pairs))))
        except Exception as e:
            logger.warning(f"Whitelist prefill failed: {e}")

        # Immediately start a Freqtrade instance for this user (will be re-provisioned by challenge later)
        try:
            initial_wallet = orchestrator._read_user_dry_run_wallet(str(db_user.user_id))
            orchestrator.start_instance(str(db_user.user_id), dry_run_wallet=initial_wallet)
            logger.info(f"Started Freqtrade instance for user {db_user.user_id}")
        except Exception as e:
            logger.warning(f"Failed to start Freqtrade for new user {db_user.user_id}: {e}")

        return db_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during user registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during registration"
        )

@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return access token"""
    try:
        # Authenticate user
        db_user = await user.authenticate(
            db, 
            email=user_credentials.email, 
            password=user_credentials.password
        )
        
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        if db_user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is not active"
            )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": str(db_user.user_id), "email": db_user.email}
        )

        # On login, start user's Freqtrade instance using active challenge amount
        active = await challenge_selection_crud.get_active_by_user_id(db, user_id=str(db_user.user_id))
        if active:
            initial_balance = TradingChallengeService.parse_amount(active.amount)
            if initial_balance <= 0:
                initial_balance = 1000.0
            orchestrator.start_instance(str(db_user.user_id), dry_run_wallet=initial_balance)
        
        logger.info(f"User logged in successfully: {db_user.email}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "user_id": str(db_user.user_id),
                "email": db_user.email,
                "name": db_user.name
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during user login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        payload = verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        orchestrator.stop_instance(str(user_id))
        return {"detail": "Logged out"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get current authenticated user"""
    try:
        # Verify token
        payload = verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        # Get user from database
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        db_user = await user.get(db, id=user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return db_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
