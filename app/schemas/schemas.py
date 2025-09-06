from pydantic import BaseModel, ConfigDict, validator
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from decimal import Decimal

# Import enums from models
from app.models.user import UserRole, UserStatus
from app.models.account import AccountType
from app.models.challenge_template import ChallengeStatus, ChallengeCategory
from app.models.challenge_selection import ChallengeSelectionStatus, ChallengeCategory as SelectionChallengeCategory
from app.models.challenge_attempt import ChallengeState
from app.models.trade import TradeSide
from app.models.subscription_plan import PlanType, PlanStatus
from app.models.subscription import SubscriptionStatus

# Import trading schemas
from .trading import *

# Base Schema Classes
class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: str
        }
    )

class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints"""
    page: int = 1
    size: int = 20
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper"""
    items: list
    total: int
    page: int
    size: int
    pages: int
    
    @property
    def has_next(self) -> bool:
        return self.page < self.pages
    
    @property
    def has_prev(self) -> bool:
        return self.page > 1

# User Schemas
class UserBase(BaseSchema):
    name: str
    email: str
    role: UserRole = UserRole.TRADER
    status: UserStatus = UserStatus.ACTIVE

class UserCreate(UserBase):
    password: str  # Plain text password for registration

class UserUpdate(BaseSchema):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None

class UserResponse(UserBase):
    user_id: UUID
    created_at: datetime

class UserListResponse(BaseSchema):
    users: List[UserResponse]
    total: int

# Authentication Schemas
class UserLogin(BaseSchema):
    email: str
    password: str

class Token(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 30  # minutes

class TokenData(BaseSchema):
    email: Optional[str] = None

# Account Schemas
class AccountBase(BaseSchema):
    user_id: UUID
    type: AccountType
    balance: Decimal

class AccountCreate(BaseSchema):
    user_id: UUID
    type: AccountType
    balance: Decimal = Decimal('0.00')

class AccountUpdate(BaseSchema):
    balance: Optional[Decimal] = None

class AccountResponse(AccountBase):
    account_id: UUID
    created_at: datetime

class AccountListResponse(BaseSchema):
    accounts: List[AccountResponse]
    total: int

# Challenge Template Schemas
class ChallengeTemplateBase(BaseSchema):
    name: str
    account_size: Decimal
    fee_amount: Decimal
    profit_target_pct: Decimal
    max_drawdown_pct: Decimal
    daily_loss_pct: Decimal
    category: ChallengeCategory = ChallengeCategory.STOCKS
    status: ChallengeStatus = ChallengeStatus.ACTIVE

class ChallengeTemplateCreate(ChallengeTemplateBase):
    pass

class ChallengeTemplateUpdate(BaseSchema):
    name: Optional[str] = None
    account_size: Optional[Decimal] = None
    fee_amount: Optional[Decimal] = None
    profit_target_pct: Optional[Decimal] = None
    max_drawdown_pct: Optional[Decimal] = None
    daily_loss_pct: Optional[Decimal] = None
    category: Optional[ChallengeCategory] = None
    status: Optional[ChallengeStatus] = None

class ChallengeTemplateResponse(ChallengeTemplateBase):
    challenge_id: UUID

# Challenge Attempt Schemas
class ChallengeAttemptBase(BaseSchema):
    user_id: UUID
    challenge_id: UUID
    account_id: UUID
    state: ChallengeState = ChallengeState.ACTIVE

class ChallengeAttemptCreate(BaseSchema):
    user_id: UUID
    challenge_id: UUID
    account_id: UUID

class ChallengeAttemptUpdate(BaseSchema):
    state: Optional[ChallengeState] = None
    ended_at: Optional[datetime] = None
    metrics: Optional[Dict[str, Any]] = None

class ChallengeAttemptResponse(ChallengeAttemptBase):
    attempt_id: UUID
    started_at: datetime
    ended_at: Optional[datetime] = None
    metrics: Optional[Dict[str, Any]] = None

class ChallengeAttemptListResponse(BaseSchema):
    attempts: List[ChallengeAttemptResponse]
    total: int

# Trade Schemas
class TradeBase(BaseSchema):
    account_id: UUID
    user_id: UUID
    instrument: str
    side: TradeSide
    qty: Decimal
    entry_price: Decimal
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None

class TradeCreate(BaseSchema):
    account_id: UUID
    user_id: UUID
    instrument: str
    side: TradeSide
    qty: Decimal
    entry_price: Decimal
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None

class TradeUpdate(BaseSchema):
    exit_price: Optional[Decimal] = None
    pnl: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None

class TradeResponse(TradeBase):
    trade_id: UUID
    exit_price: Optional[Decimal] = None
    pnl: Optional[Decimal] = None
    timestamp: datetime

class TradeListResponse(BaseSchema):
    trades: List[TradeResponse]
    total: int

# Subscription Plan Schemas
class SubscriptionPlanBase(BaseSchema):
    name: str
    type: PlanType
    price: Decimal
    features: Optional[Dict[str, Any]] = None
    status: PlanStatus = PlanStatus.ACTIVE

class SubscriptionPlanCreate(SubscriptionPlanBase):
    pass

class SubscriptionPlanUpdate(BaseSchema):
    name: Optional[str] = None
    type: Optional[PlanType] = None
    price: Optional[Decimal] = None
    features: Optional[Dict[str, Any]] = None
    status: Optional[PlanStatus] = None

class SubscriptionPlanResponse(SubscriptionPlanBase):
    plan_id: UUID

# Subscription Schemas
class SubscriptionBase(BaseSchema):
    user_id: UUID
    plan_id: UUID
    start_date: datetime
    end_date: datetime
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE

class SubscriptionCreate(BaseSchema):
    user_id: UUID
    plan_id: UUID
    end_date: datetime

class SubscriptionUpdate(BaseSchema):
    status: Optional[SubscriptionStatus] = None
    end_date: Optional[datetime] = None

class SubscriptionResponse(SubscriptionBase):
    subscription_id: UUID

class SubscriptionListResponse(BaseSchema):
    subscriptions: List[SubscriptionResponse]
    total: int

# Challenge Selection Schemas
class ChallengeSelectionBase(BaseSchema):
    challenge_id: str
    amount: str
    price: str
    profit_target: str
    max_drawdown: str
    daily_limit: str
    category: SelectionChallengeCategory = SelectionChallengeCategory.STOCKS

class ChallengeSelectionCreate(ChallengeSelectionBase):
    class Config:
        json_schema_extra = {
            "example": {
                "challenge_id": "challenge_50k",
                "amount": "₹50,000",
                "price": "₹999",
                "profit_target": "₹5,000",
                "max_drawdown": "₹5,000",
                "daily_limit": "₹2,500"
            }
        }
    
    @validator('challenge_id')
    def validate_challenge_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Challenge ID cannot be empty')
        return v.strip()
    
    @validator('amount', 'price', 'profit_target', 'max_drawdown', 'daily_limit')
    def validate_amount_fields(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Amount fields cannot be empty')
        return v.strip()

class ChallengeSelectionUpdate(BaseSchema):
    status: Optional[str] = None
    activated_at: Optional[datetime] = None

class ChallengeSelectionResponse(ChallengeSelectionBase):
    selection_id: UUID
    user_id: UUID
    status: str
    created_at: datetime
    activated_at: Optional[datetime] = None

class ChallengeSelectionListResponse(BaseSchema):
    selections: List[ChallengeSelectionResponse]
    total: int

# Trading Challenge Schemas
class TradingChallengeBase(BaseSchema):
    target_amount: float
    max_drawdown_amount: float
    daily_loss_limit: float

class TradingChallengeCreate(TradingChallengeBase):
    selection_id: str
    initial_balance: float = 100000.0

class TradingChallengeUpdate(BaseSchema):
    current_balance: Optional[float] = None
    status: Optional[str] = None

class TradingChallengeResponse(TradingChallengeBase):
    challenge_id: UUID
    user_id: UUID
    selection_id: UUID
    current_balance: float
    peak_balance: float
    current_drawdown: float
    daily_loss: float
    status: str
    start_date: datetime
    end_date: Optional[datetime] = None
    is_profit_target_reached: bool
    is_drawdown_breached: bool
    is_daily_limit_breached: bool

class TradingChallengeListResponse(BaseSchema):
    challenges: List[TradingChallengeResponse]
    total: int

class TradingChallengeSummaryResponse(BaseSchema):
    total: int
    active: int
    completed: int
    failed: int
