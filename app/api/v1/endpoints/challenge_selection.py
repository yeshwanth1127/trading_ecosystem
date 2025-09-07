from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.crud import challenge_selection, user
from app.schemas import ChallengeSelectionCreate, ChallengeSelectionResponse, ChallengeSelectionListResponse
from app.core.security import verify_token
import logging
from app.orchestrator import orchestrator
from app.services.trading_challenge_service import TradingChallengeService

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

@router.post("/", response_model=ChallengeSelectionResponse, status_code=status.HTTP_201_CREATED)
async def create_challenge_selection(
    selection_in: ChallengeSelectionCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Create a new challenge selection for the authenticated user"""
    try:
        # Verify token and get user
        payload = verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Check if user already has a selection for the same challenge
        existing_selections = await challenge_selection.get_by_user_id(db, user_id=user_id)
        for selection in existing_selections:
            if selection.challenge_id == selection_in.challenge_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You already have a selection for this challenge"
                )
        
        # Create challenge selection
        db_selection = await challenge_selection.create_for_user(
            db, user_id=user_id, obj_in=selection_in
        )
        
        logger.info(f"Challenge selection created for user {user_id}: {db_selection.selection_id}")

        # Prepare per-user user_data and provision config with starting balance
        orchestrator.ensure_user_userdir(user_id)
        initial_balance = TradingChallengeService.parse_amount(db_selection.amount)
        if initial_balance <= 0:
            initial_balance = 1000.0
        orchestrator.provision_user_config(user_id, dry_run_wallet=initial_balance)

        # Start the user's Freqtrade instance immediately using this challenge amount
        try:
            orchestrator.start_instance(user_id, dry_run_wallet=initial_balance)
            logger.info(f"Started Freqtrade for user {user_id} with wallet {initial_balance}")
        except Exception as e:
            logger.error(f"Failed to start Freqtrade for user {user_id}: {e}")

        return db_selection
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating challenge selection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/my-selections", response_model=ChallengeSelectionListResponse)
async def get_user_challenge_selections(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get all challenge selections for the authenticated user"""
    try:
        # Verify token and get user
        payload = verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Get user's challenge selections
        selections = await challenge_selection.get_by_user_id(db, user_id=user_id)
        
        return ChallengeSelectionListResponse(
            selections=selections,
            total=len(selections)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user challenge selections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/active", response_model=ChallengeSelectionResponse)
async def get_active_challenge_selection(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get the active challenge selection for the authenticated user"""
    try:
        # Verify token and get user
        payload = verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Get user's active challenge selection
        active_selection = await challenge_selection.get_active_by_user_id(db, user_id=user_id)
        
        if not active_selection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active challenge selection found"
            )
        
        return active_selection
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting active challenge selection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Note: The activate endpoint is no longer needed since challenges are automatically active
# when created. Use start-trading endpoint when user begins placing trades.

@router.post("/{selection_id}/start-trading", response_model=ChallengeSelectionResponse)
async def start_trading_challenge(
    selection_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Start trading for a challenge selection"""
    try:
        # Verify token and get user
        payload = verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Start trading for the challenge selection
        db_selection = await challenge_selection.start_trading(db, selection_id=selection_id)
        
        logger.info(f"Challenge selection {selection_id} started trading for user {user_id}")
        return db_selection
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting trading for challenge selection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
