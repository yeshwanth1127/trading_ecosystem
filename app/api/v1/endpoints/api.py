from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.crud import (
    user, account, challenge_template, challenge_attempt, 
    trade, subscription_plan, subscription, trading_challenge, challenge_selection
)
from app.schemas import (
    # User schemas
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    # Account schemas
    AccountCreate, AccountUpdate, AccountResponse, AccountListResponse,
    # Challenge schemas
    ChallengeTemplateCreate, ChallengeTemplateUpdate, ChallengeTemplateResponse,
    ChallengeAttemptCreate, ChallengeAttemptUpdate, ChallengeAttemptResponse, ChallengeAttemptListResponse,
    # Challenge Selection schemas
    ChallengeSelectionCreate, ChallengeSelectionUpdate, ChallengeSelectionResponse, ChallengeSelectionListResponse,
    # Trading Challenge schemas
    TradingChallengeCreate, TradingChallengeUpdate, TradingChallengeResponse, TradingChallengeListResponse, TradingChallengeSummaryResponse,
    # Trade schemas
    TradeCreate, TradeUpdate, TradeResponse, TradeListResponse,
    # Subscription schemas
    SubscriptionPlanCreate, SubscriptionPlanUpdate, SubscriptionPlanResponse,
    SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse, SubscriptionListResponse,
    # Common schemas
    PaginationParams
)
from app.core.security import verify_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# ============================================================================
# USER ENDPOINTS
# ============================================================================

@router.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new user"""
    try:
        existing_user = await user.get_by_email(db, email=user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        db_user = await user.create(db, obj_in=user_in)
        return db_user
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/users/", response_model=UserListResponse)
async def get_users(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    role: Optional[str] = Query(None, description="Filter by user role"),
    status_filter: Optional[str] = Query(None, description="Filter by user status")
):
    """Get users with pagination and optional filters"""
    try:
        pagination = PaginationParams(page=page, size=size)
        
        filters = {}
        if role:
            filters["role"] = role
        if status_filter:
            filters["status"] = status_filter
        
        users = await user.get_multi(db, skip=pagination.offset, limit=pagination.size, filters=filters)
        total = await user.count(db, filters=filters)
        
        return UserListResponse(users=users, total=total)
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific user by ID"""
    try:
        db_user = await user.get(db, id=user_id)
        if not db_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return db_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_in: UserUpdate, db: AsyncSession = Depends(get_db)):
    """Update a user"""
    try:
        db_user = await user.get(db, id=user_id)
        if not db_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        if user_in.email and user_in.email != db_user.email:
            existing_user = await user.get_by_email(db, email=user_in.email)
            if existing_user:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists")
        
        updated_user = await user.update(db, db_obj=db_user, obj_in=user_in)
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a user"""
    try:
        db_user = await user.get(db, id=user_id)
        if not db_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        await user.remove(db, id=user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# ============================================================================
# ACCOUNT ENDPOINTS
# ============================================================================

@router.post("/accounts/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(account_in: AccountCreate, db: AsyncSession = Depends(get_db)):
    """Create a new account"""
    try:
        db_account = await account.create(db, obj_in=account_in)
        return db_account
    except Exception as e:
        logger.error(f"Error creating account: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/accounts/", response_model=AccountListResponse)
async def get_accounts(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    account_type: Optional[str] = Query(None, description="Filter by account type")
):
    """Get accounts with pagination and optional filters"""
    try:
        pagination = PaginationParams(page=page, size=size)
        
        filters = {}
        if user_id:
            filters["user_id"] = user_id
        if account_type:
            filters["type"] = account_type
        
        accounts = await account.get_multi(db, skip=pagination.offset, limit=pagination.size, filters=filters)
        total = await account.count(db, filters=filters)
        
        return AccountListResponse(accounts=accounts, total=total)
    except Exception as e:
        logger.error(f"Error getting accounts: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/accounts/{account_id}", response_model=AccountResponse)
async def get_account(account_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific account by ID"""
    try:
        db_account = await account.get(db, id=account_id)
        if not db_account:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        return db_account
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting account {account_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.put("/accounts/{account_id}", response_model=AccountResponse)
async def update_account(account_id: str, account_in: AccountUpdate, db: AsyncSession = Depends(get_db)):
    """Update an account"""
    try:
        db_account = await account.get(db, id=account_id)
        if not db_account:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        
        updated_account = await account.update(db, db_obj=db_account, obj_in=account_in)
        return updated_account
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating account {account_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(account_id: str, db: AsyncSession = Depends(get_db)):
    """Delete an account"""
    try:
        db_account = await account.get(db, id=account_id)
        if not db_account:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        await account.remove(db, id=account_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting account {account_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# ============================================================================
# FUNDING CHALLENGE ENDPOINTS
# ============================================================================

# Challenge Template endpoints
@router.post("/challenges/templates/", response_model=ChallengeTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_challenge_template(template_in: ChallengeTemplateCreate, db: AsyncSession = Depends(get_db)):
    """Create a new challenge template"""
    try:
        db_template = await challenge_template.create(db, obj_in=template_in)
        return db_template
    except Exception as e:
        logger.error(f"Error creating challenge template: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/challenges/templates/", response_model=List[ChallengeTemplateResponse])
async def get_challenge_templates(
    db: AsyncSession = Depends(get_db),
    active_only: bool = Query(True, description="Get only active templates"),
    category: Optional[str] = Query(None, description="Filter by category (stocks/crypto)")
):
    """Get challenge templates"""
    try:
        if active_only:
            templates = await challenge_template.get_active_challenges(db, category=category)
        else:
            filters = {}
            if category:
                filters["category"] = category
            templates = await challenge_template.get_multi(db, filters=filters)
        return templates
    except Exception as e:
        logger.error(f"Error getting challenge templates: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/challenges/templates/{template_id}", response_model=ChallengeTemplateResponse)
async def get_challenge_template(template_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific challenge template by ID"""
    try:
        db_template = await challenge_template.get(db, id=template_id)
        if not db_template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge template not found")
        return db_template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting challenge template {template_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.put("/challenges/templates/{template_id}", response_model=ChallengeTemplateResponse)
async def update_challenge_template(template_id: str, template_in: ChallengeTemplateUpdate, db: AsyncSession = Depends(get_db)):
    """Update a challenge template"""
    try:
        db_template = await challenge_template.get(db, id=template_id)
        if not db_template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge template not found")
        
        updated_template = await challenge_template.update(db, db_obj=db_template, obj_in=template_in)
        return updated_template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating challenge template {template_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.delete("/challenges/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_challenge_template(template_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a challenge template"""
    try:
        db_template = await challenge_template.get(db, id=template_id)
        if not db_template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge template not found")
        await challenge_template.remove(db, id=template_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting challenge template {template_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# Challenge Attempt endpoints
@router.post("/challenges/attempts/", response_model=ChallengeAttemptResponse, status_code=status.HTTP_201_CREATED)
async def create_challenge_attempt(attempt_in: ChallengeAttemptCreate, db: AsyncSession = Depends(get_db)):
    """Create a new challenge attempt"""
    try:
        db_attempt = await challenge_attempt.create(db, obj_in=attempt_in)
        return db_attempt
    except Exception as e:
        logger.error(f"Error creating challenge attempt: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/challenges/attempts/", response_model=ChallengeAttemptListResponse)
async def get_challenge_attempts(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    challenge_id: Optional[str] = Query(None, description="Filter by challenge ID"),
    state: Optional[str] = Query(None, description="Filter by attempt state")
):
    """Get challenge attempts with pagination and optional filters"""
    try:
        pagination = PaginationParams(page=page, size=size)
        
        filters = {}
        if user_id:
            filters["user_id"] = user_id
        if challenge_id:
            filters["challenge_id"] = challenge_id
        if state:
            filters["state"] = state
        
        attempts = await challenge_attempt.get_multi(db, skip=pagination.offset, limit=pagination.size, filters=filters)
        total = await challenge_attempt.count(db, filters=filters)
        
        return ChallengeAttemptListResponse(attempts=attempts, total=total)
    except Exception as e:
        logger.error(f"Error getting challenge attempts: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/challenges/attempts/{attempt_id}", response_model=ChallengeAttemptResponse)
async def get_challenge_attempt(attempt_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific challenge attempt by ID"""
    try:
        db_attempt = await challenge_attempt.get(db, id=attempt_id)
        if not db_attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge attempt not found")
        return db_attempt
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting challenge attempt {attempt_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.put("/challenges/attempts/{attempt_id}", response_model=ChallengeAttemptResponse)
async def update_challenge_attempt(attempt_id: str, attempt_in: ChallengeAttemptUpdate, db: AsyncSession = Depends(get_db)):
    """Update a challenge attempt"""
    try:
        db_attempt = await challenge_attempt.get(db, id=attempt_id)
        if not db_attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge attempt not found")
        
        updated_attempt = await challenge_attempt.update(db, db_obj=db_attempt, obj_in=attempt_in)
        return updated_attempt
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating challenge attempt {attempt_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.delete("/challenges/attempts/{attempt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_challenge_attempt(attempt_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a challenge attempt"""
    try:
        db_attempt = await challenge_attempt.get(db, id=attempt_id)
        if not db_attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge attempt not found")
        await challenge_attempt.remove(db, id=attempt_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting challenge attempt {attempt_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/challenges/attempts/me/active", response_model=ChallengeAttemptResponse)
async def get_current_user_active_challenge(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's active challenge attempt"""
    try:
        # Verify token and get user ID
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
        
        # Get user's active challenge attempt
        active_attempts = await challenge_attempt.get_by_user_id(db, user_id=user_id, limit=1)
        
        # Filter for active attempts
        active_attempt = None
        for attempt in active_attempts:
            if attempt.state == "active":
                active_attempt = attempt
                break
        
        if not active_attempt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active challenge found for current user"
            )
        
        return active_attempt
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user's active challenge: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# ============================================================================
# CHALLENGE SELECTION ENDPOINTS
# ============================================================================

@router.post("/challenges/selections/", response_model=ChallengeSelectionResponse, status_code=status.HTTP_201_CREATED)
async def create_challenge_selection(
    selection_in: ChallengeSelectionCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Create a new challenge selection for current user"""
    try:
        # Verify token and get user ID
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
        
        # Create challenge selection for user
        db_selection = await challenge_selection.create_for_user(db, user_id=user_id, obj_in=selection_in)
        return db_selection
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating challenge selection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/challenges/selections/me/active", response_model=ChallengeSelectionResponse)
async def get_current_user_active_selection(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's active challenge selection"""
    try:
        # Verify token and get user ID
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
                detail="No active challenge selection found for current user"
            )
        
        return active_selection
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user's active challenge selection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.put("/challenges/selections/{selection_id}/start-trading", response_model=ChallengeSelectionResponse)
async def start_trading_challenge(
    selection_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Start trading for a challenge selection"""
    try:
        # Verify token and get user ID
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
        return db_selection
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting trading for challenge selection {selection_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# ============================================================================
# TRADING CHALLENGE ENDPOINTS
# ============================================================================

@router.post("/trading-challenges/", response_model=TradingChallengeResponse, status_code=status.HTTP_201_CREATED)
async def create_trading_challenge(
    challenge_in: TradingChallengeCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Create a new trading challenge"""
    try:
        # Verify token and get user ID
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
        
        # Create trading challenge
        db_challenge = await trading_challenge.create(db, obj_in=challenge_in)
        return db_challenge
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating trading challenge: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/trading-challenges/me/active", response_model=TradingChallengeResponse)
async def get_current_user_active_trading_challenge(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's active trading challenge"""
    try:
        # Verify token and get user ID
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
        
        # Get user's active trading challenge
        active_challenge = await trading_challenge.get_active_by_user_id(db, user_id=user_id)
        
        if not active_challenge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active trading challenge found for current user"
            )
        
        return active_challenge
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user's active trading challenge: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/trading-challenges/me/balance")
async def get_current_user_challenge_balance(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's trading challenge balance and summary"""
    try:
        # Verify token and get user ID
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
        
        # Get user's active challenge selection (same as account details screen)

        active_selection = await challenge_selection.get_active_by_user_id(db, user_id=user_id)
        
        if not active_selection:

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active challenge selection found for current user"
            )
        

        
        # Extract the amount and currency from the challenge selection
        try:
            amount_value = active_selection.amount
            
            # Determine currency based on category
            if hasattr(active_selection, 'category') and active_selection.category:

                if active_selection.category == 'CRYPTO' or active_selection.category == 'crypto':
                    currency = "USD"
                else:
                    currency = "INR"
            else:

                # Fallback: determine currency based on the amount string
                if isinstance(amount_value, str) and amount_value.startswith('$'):
                    currency = "USD"
                else:
                    currency = "INR"
            
            if amount_value is None:
                logger.warning("Amount not found in challenge selection, using default")
                amount_value = 100000.0  # Default amount
            else:
                # Convert to float, handling both string and numeric values
                if isinstance(amount_value, str):
                    if currency == "USD":
                        # Remove $ symbol and commas
                        cleaned_amount = amount_value.replace('$', '').replace(',', '').replace(' ', '')
                    else:
                        # Remove ₹ symbol and commas
                        cleaned_amount = amount_value.replace('₹', '').replace(',', '').replace(' ', '')
                    
                    # Handle "Lakh" format (1.5 Lakh = 150000) for INR
                    if 'lakh' in cleaned_amount.lower():
                        # Extract the number before "lakh"
                        number_part = cleaned_amount.lower().replace('lakh', '').strip()
                        amount_value = float(number_part) * 100000
                    else:
                        amount_value = float(cleaned_amount)
                else:
                    amount_value = float(amount_value)
                    

            
        except (ValueError, AttributeError) as e:

            amount_value = 100000.0  # Default fallback amount
            currency = "INR"
            
        # Use the extracted amount as the balance
        initial_balance = amount_value
        current_balance = amount_value
        
        # Return balance data
        return {
            "challenge_id": str(active_selection.challenge_id),
            "initial_balance": initial_balance,
            "available_balance": current_balance,
            "total_equity": current_balance,
            "unrealized_pnl": current_balance - initial_balance,
            "used_margin": 0.0,  # Not implemented yet
            "currency": currency,
            "open_positions_count": 0,  # Not implemented yet
            "pending_orders_count": 0,  # Not implemented yet
            "total_trades": 0,  # Not implemented yet
            "peak_balance": current_balance,  # Not implemented yet
            "current_drawdown": 0.0,  # Not implemented yet
            "daily_loss": 0.0,  # Not implemented yet
            "target_amount": initial_balance,
            "max_drawdown_amount": 0.0,  # Not implemented yet
            "daily_loss_limit": 0.0,  # Not implemented yet
            "status": active_selection.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user's challenge balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/trading-challenges/me/summary", response_model=TradingChallengeSummaryResponse)
async def get_current_user_challenge_summary(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's trading challenge summary"""
    try:
        # Verify token and get user ID
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
        
        # Get user's challenge summary
        summary = await trading_challenge.get_challenge_summary(db, user_id=user_id)
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user's challenge summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# ============================================================================
# TRADE ENDPOINTS
# ============================================================================

@router.post("/trades/", response_model=TradeResponse, status_code=status.HTTP_201_CREATED)
async def create_trade(trade_in: TradeCreate, db: AsyncSession = Depends(get_db)):
    """Create a new trade"""
    try:
        db_trade = await trade.create(db, obj_in=trade_in)
        return db_trade
    except Exception as e:
        logger.error(f"Error creating trade: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/trades/", response_model=TradeListResponse)
async def get_trades(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    instrument: Optional[str] = Query(None, description="Filter by instrument"),
    side: Optional[str] = Query(None, description="Filter by trade side")
):
    """Get trades with pagination and optional filters"""
    try:
        pagination = PaginationParams(page=page, size=size)
        
        filters = {}
        if account_id:
            filters["account_id"] = account_id
        if user_id:
            filters["user_id"] = user_id
        if instrument:
            filters["instrument"] = instrument
        if side:
            filters["side"] = side
        
        trades = await trade.get_multi(db, skip=pagination.offset, limit=pagination.size, filters=filters)
        total = await trade.count(db, filters=filters)
        
        return TradeListResponse(trades=trades, total=total)
    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/trades/{trade_id}", response_model=TradeResponse)
async def get_trade(trade_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific trade by ID"""
    try:
        db_trade = await trade.get(db, id=trade_id)
        if not db_trade:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")
        return db_trade
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trade {trade_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.put("/trades/{trade_id}", response_model=TradeResponse)
async def update_trade(trade_id: str, trade_in: TradeUpdate, db: AsyncSession = Depends(get_db)):
    """Update a trade"""
    try:
        db_trade = await trade.get(db, id=trade_id)
        if not db_trade:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")
        
        updated_trade = await trade.update(db, db_obj=db_trade, obj_in=trade_in)
        return updated_trade
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating trade {trade_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.delete("/trades/{trade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trade(trade_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a trade"""
    try:
        db_trade = await trade.get(db, id=trade_id)
        if not db_trade:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")
        await trade.remove(db, id=trade_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting trade {trade_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# ============================================================================
# SUBSCRIPTION ENDPOINTS
# ============================================================================

# Subscription Plan endpoints
@router.post("/subscriptions/plans/", response_model=SubscriptionPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription_plan(plan_in: SubscriptionPlanCreate, db: AsyncSession = Depends(get_db)):
    """Create a new subscription plan"""
    try:
        db_plan = await subscription_plan.create(db, obj_in=plan_in)
        return db_plan
    except Exception as e:
        logger.error(f"Error creating subscription plan: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/subscriptions/plans/", response_model=List[SubscriptionPlanResponse])
async def get_subscription_plans(
    db: AsyncSession = Depends(get_db),
    active_only: bool = Query(True, description="Get only active plans")
):
    """Get subscription plans"""
    try:
        if active_only:
            plans = await subscription_plan.get_active_plans(db)
        else:
            plans = await subscription_plan.get_multi(db)
        return plans
    except Exception as e:
        logger.error(f"Error getting subscription plans: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/subscriptions/plans/{plan_id}", response_model=SubscriptionPlanResponse)
async def get_subscription_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific subscription plan by ID"""
    try:
        db_plan = await subscription_plan.get(db, id=plan_id)
        if not db_plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription plan not found")
        return db_plan
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subscription plan {plan_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.put("/subscriptions/plans/{plan_id}", response_model=SubscriptionPlanResponse)
async def update_subscription_plan(plan_id: str, plan_in: SubscriptionPlanUpdate, db: AsyncSession = Depends(get_db)):
    """Update a subscription plan"""
    try:
        db_plan = await subscription_plan.get(db, id=plan_id)
        if not db_plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription plan not found")
        
        updated_plan = await subscription_plan.update(db, db_obj=db_plan, obj_in=plan_in)
        return updated_plan
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating subscription plan {plan_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.delete("/subscriptions/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a subscription plan"""
    try:
        db_plan = await subscription_plan.get(db, id=plan_id)
        if not db_plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription plan not found")
        await subscription_plan.remove(db, id=plan_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting subscription plan {plan_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# Subscription endpoints
@router.post("/subscriptions/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(subscription_in: SubscriptionCreate, db: AsyncSession = Depends(get_db)):
    """Create a new subscription"""
    try:
        db_subscription = await subscription.create(db, obj_in=subscription_in)
        return db_subscription
    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/subscriptions/", response_model=SubscriptionListResponse)
async def get_subscriptions(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    plan_id: Optional[str] = Query(None, description="Filter by plan ID"),
    status_filter: Optional[str] = Query(None, description="Filter by subscription status")
):
    """Get subscriptions with pagination and optional filters"""
    try:
        pagination = PaginationParams(page=page, size=size)
        
        filters = {}
        if user_id:
            filters["user_id"] = user_id
        if plan_id:
            filters["plan_id"] = plan_id
        if status_filter:
            filters["status"] = status_filter
        
        subscriptions = await subscription.get_multi(db, skip=pagination.offset, limit=pagination.size, filters=filters)
        total = await subscription.count(db, filters=filters)
        
        return SubscriptionListResponse(subscriptions=subscriptions, total=total)
    except Exception as e:
        logger.error(f"Error getting subscriptions: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(subscription_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific subscription by ID"""
    try:
        db_subscription = await subscription.get(db, id=subscription_id)
        if not db_subscription:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
        return db_subscription
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subscription {subscription_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.put("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(subscription_id: str, subscription_in: SubscriptionUpdate, db: AsyncSession = Depends(get_db)):
    """Update a subscription"""
    try:
        db_subscription = await subscription.get(db, id=subscription_id)
        if not db_subscription:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
        
        updated_subscription = await subscription.update(db, db_obj=db_subscription, obj_in=subscription_in)
        return updated_subscription
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating subscription {subscription_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.delete("/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(subscription_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a subscription"""
    try:
        db_subscription = await subscription.get(db, id=subscription_id)
        if not db_subscription:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
        await subscription.remove(db, id=subscription_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting subscription {subscription_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
