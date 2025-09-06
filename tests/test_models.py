import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Account, ChallengeTemplate, ChallengeAttempt, Trade, SubscriptionPlan, Subscription
from app.models.user import UserRole, UserStatus
from app.models.account import AccountType
from app.models.challenge_template import ChallengeStatus
from app.models.challenge_attempt import ChallengeState
from app.models.trade import TradeSide
from app.models.subscription_plan import PlanType, PlanStatus
from app.models.subscription import SubscriptionStatus

class TestUserModel:
    """Test User model functionality."""
    
    async def test_create_user(self, db_session: AsyncSession):
        """Test creating a user."""
        user = User(
            user_id=uuid4(),
            name="Test User",
            email="test@example.com",
            role=UserRole.TRADER,
            status=UserStatus.ACTIVE
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.name == "Test User"
        assert user.email == "test@example.com"
        assert user.role == UserRole.TRADER
        assert user.status == UserStatus.ACTIVE
        assert user.created_at is not None
    
    async def test_user_enum_values(self):
        """Test user enum values."""
        assert UserRole.TRADER == "trader"
        assert UserRole.ADMIN == "admin"
        assert UserStatus.ACTIVE == "active"
        assert UserStatus.BANNED == "banned"

class TestAccountModel:
    """Test Account model functionality."""
    
    async def test_create_account(self, db_session: AsyncSession):
        """Test creating an account."""
        user = User(
            user_id=uuid4(),
            name="Test User",
            email="test@example.com",
            role=UserRole.TRADER,
            status=UserStatus.ACTIVE
        )
        db_session.add(user)
        await db_session.commit()
        
        account = Account(
            account_id=uuid4(),
            user_id=user.user_id,
            type=AccountType.SIMULATED,
            balance=Decimal("10000.00")
        )
        
        db_session.add(account)
        await db_session.commit()
        await db_session.refresh(account)
        
        assert account.user_id == user.user_id
        assert account.type == AccountType.SIMULATED
        assert account.balance == Decimal("10000.00")
        assert account.created_at is not None
    
    async def test_account_enum_values(self):
        """Test account enum values."""
        assert AccountType.SIMULATED == "simulated"
        assert AccountType.COPY == "copy"
        assert AccountType.ALGO == "algo"

class TestChallengeTemplateModel:
    """Test ChallengeTemplate model functionality."""
    
    async def test_create_challenge_template(self, db_session: AsyncSession):
        """Test creating a challenge template."""
        template = ChallengeTemplate(
            challenge_id=uuid4(),
            name="Test Challenge",
            account_size=Decimal("50000.00"),
            fee_amount=Decimal("99.99"),
            profit_target_pct=Decimal("8.00"),
            max_drawdown_pct=Decimal("5.00"),
            daily_loss_pct=Decimal("3.00"),
            status=ChallengeStatus.ACTIVE
        )
        
        db_session.add(template)
        await db_session.commit()
        await db_session.refresh(template)
        
        assert template.name == "Test Challenge"
        assert template.account_size == Decimal("50000.00")
        assert template.fee_amount == Decimal("99.99")
        assert template.profit_target_pct == Decimal("8.00")
        assert template.max_drawdown_pct == Decimal("5.00")
        assert template.daily_loss_pct == Decimal("3.00")
        assert template.status == ChallengeStatus.ACTIVE
    
    async def test_challenge_status_enum_values(self):
        """Test challenge status enum values."""
        assert ChallengeStatus.ACTIVE == "active"
        assert ChallengeStatus.ARCHIVED == "archived"

class TestChallengeAttemptModel:
    """Test ChallengeAttempt model functionality."""
    
    async def test_create_challenge_attempt(self, db_session: AsyncSession):
        """Test creating a challenge attempt."""
        user = User(
            user_id=uuid4(),
            name="Test User",
            email="test@example.com",
            role=UserRole.TRADER,
            status=UserStatus.ACTIVE
        )
        db_session.add(user)
        
        account = Account(
            account_id=uuid4(),
            user_id=user.user_id,
            type=AccountType.SIMULATED,
            balance=Decimal("10000.00")
        )
        db_session.add(account)
        
        template = ChallengeTemplate(
            challenge_id=uuid4(),
            name="Test Challenge",
            account_size=Decimal("50000.00"),
            fee_amount=Decimal("99.99"),
            profit_target_pct=Decimal("8.00"),
            max_drawdown_pct=Decimal("5.00"),
            daily_loss_pct=Decimal("3.00"),
            status=ChallengeStatus.ACTIVE
        )
        db_session.add(template)
        
        await db_session.commit()
        
        attempt = ChallengeAttempt(
            attempt_id=uuid4(),
            user_id=user.user_id,
            challenge_id=template.challenge_id,
            account_id=account.account_id,
            state=ChallengeState.ACTIVE,
            metrics={"profit": "5.2", "drawdown": "2.1"}
        )
        
        db_session.add(attempt)
        await db_session.commit()
        await db_session.refresh(attempt)
        
        assert attempt.user_id == user.user_id
        assert attempt.challenge_id == template.challenge_id
        assert attempt.account_id == account.account_id
        assert attempt.state == ChallengeState.ACTIVE
        assert attempt.metrics == {"profit": "5.2", "drawdown": "2.1"}
        assert attempt.started_at is not None
    
    async def test_challenge_state_enum_values(self):
        """Test challenge state enum values."""
        assert ChallengeState.ACTIVE == "active"
        assert ChallengeState.PASSED == "passed"
        assert ChallengeState.FAILED == "failed"

class TestTradeModel:
    """Test Trade model functionality."""
    
    async def test_create_trade(self, db_session: AsyncSession):
        """Test creating a trade."""
        user = User(
            user_id=uuid4(),
            name="Test User",
            email="test@example.com",
            role=UserRole.TRADER,
            status=UserStatus.ACTIVE
        )
        db_session.add(user)
        
        account = Account(
            account_id=uuid4(),
            user_id=user.user_id,
            type=AccountType.SIMULATED,
            balance=Decimal("10000.00")
        )
        db_session.add(account)
        
        await db_session.commit()
        
        trade = Trade(
            trade_id=uuid4(),
            account_id=account.account_id,
            user_id=user.user_id,
            instrument="EURUSD",
            side=TradeSide.BUY,
            qty=Decimal("1.0"),
            entry_price=Decimal("1.0850"),
            stop_loss=Decimal("1.0800"),
            take_profit=Decimal("1.0900")
        )
        
        db_session.add(trade)
        await db_session.commit()
        await db_session.refresh(trade)
        
        assert trade.account_id == account.account_id
        assert trade.user_id == user.user_id
        assert trade.instrument == "EURUSD"
        assert trade.side == TradeSide.BUY
        assert trade.qty == Decimal("1.0")
        assert trade.entry_price == Decimal("1.0850")
        assert trade.stop_loss == Decimal("1.0800")
        assert trade.take_profit == Decimal("1.0900")
        assert trade.timestamp is not None
    
    async def test_trade_side_enum_values(self):
        """Test trade side enum values."""
        assert TradeSide.BUY == "buy"
        assert TradeSide.SELL == "sell"

class TestSubscriptionPlanModel:
    """Test SubscriptionPlan model functionality."""
    
    async def test_create_subscription_plan(self, db_session: AsyncSession):
        """Test creating a subscription plan."""
        plan = SubscriptionPlan(
            plan_id=uuid4(),
            name="Basic Copy Trading",
            type=PlanType.COPY_TRADE,
            price=Decimal("29.99"),
            features={"max_copiers": 10, "real_time_signals": True},
            status=PlanStatus.ACTIVE
        )
        
        db_session.add(plan)
        await db_session.commit()
        await db_session.refresh(plan)
        
        assert plan.name == "Basic Copy Trading"
        assert plan.type == PlanType.COPY_TRADE
        assert plan.price == Decimal("29.99")
        assert plan.features == {"max_copiers": 10, "real_time_signals": True}
        assert plan.status == PlanStatus.ACTIVE
    
    async def test_plan_enum_values(self):
        """Test plan enum values."""
        assert PlanType.COPY_TRADE == "copy_trade"
        assert PlanType.ALGO == "algo"
        assert PlanStatus.ACTIVE == "active"
        assert PlanStatus.ARCHIVED == "archived"

class TestSubscriptionModel:
    """Test Subscription model functionality."""
    
    async def test_create_subscription(self, db_session: AsyncSession):
        """Test creating a subscription."""
        user = User(
            user_id=uuid4(),
            name="Test User",
            email="test@example.com",
            role=UserRole.TRADER,
            status=UserStatus.ACTIVE
        )
        db_session.add(user)
        
        plan = SubscriptionPlan(
            plan_id=uuid4(),
            name="Basic Copy Trading",
            type=PlanType.COPY_TRADE,
            price=Decimal("29.99"),
            features={"max_copiers": 10, "real_time_signals": True},
            status=PlanStatus.ACTIVE
        )
        db_session.add(plan)
        
        await db_session.commit()
        
        subscription = Subscription(
            subscription_id=uuid4(),
            user_id=user.user_id,
            plan_id=plan.plan_id,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
            status=SubscriptionStatus.ACTIVE
        )
        
        db_session.add(subscription)
        await db_session.commit()
        await db_session.refresh(subscription)
        
        assert subscription.user_id == user.user_id
        assert subscription.plan_id == plan.plan_id
        assert subscription.status == SubscriptionStatus.ACTIVE
        assert subscription.start_date is not None
        assert subscription.end_date is not None
    
    async def test_subscription_status_enum_values(self):
        """Test subscription status enum values."""
        assert SubscriptionStatus.ACTIVE == "active"
        assert SubscriptionStatus.EXPIRED == "expired"
        assert SubscriptionStatus.CANCELLED == "cancelled"

class TestModelRelationships:
    """Test model relationships."""
    
    async def test_user_account_relationship(self, db_session: AsyncSession):
        """Test user-account relationship."""
        user = User(
            user_id=uuid4(),
            name="Test User",
            email="test@example.com",
            role=UserRole.TRADER,
            status=UserStatus.ACTIVE
        )
        db_session.add(user)
        await db_session.commit()
        
        account = Account(
            account_id=uuid4(),
            user_id=user.user_id,
            type=AccountType.SIMULATED,
            balance=Decimal("10000.00")
        )
        db_session.add(account)
        await db_session.commit()
        
        # Test relationship
        await db_session.refresh(user)
        assert len(user.accounts) == 1
        assert user.accounts[0].account_id == account.account_id
        
        await db_session.refresh(account)
        assert account.user.user_id == user.user_id
    
    async def test_user_trades_relationship(self, db_session: AsyncSession):
        """Test user-trades relationship."""
        user = User(
            user_id=uuid4(),
            name="Test User",
            email="test@example.com",
            role=UserRole.TRADER,
            status=UserStatus.ACTIVE
        )
        db_session.add(user)
        
        account = Account(
            account_id=uuid4(),
            user_id=user.user_id,
            type=AccountType.SIMULATED,
            balance=Decimal("10000.00")
        )
        db_session.add(account)
        
        await db_session.commit()
        
        trade = Trade(
            trade_id=uuid4(),
            account_id=account.account_id,
            user_id=user.user_id,
            instrument="EURUSD",
            side=TradeSide.BUY,
            qty=Decimal("1.0"),
            entry_price=Decimal("1.0850")
        )
        db_session.add(trade)
        await db_session.commit()
        
        # Test relationship
        await db_session.refresh(user)
        assert len(user.trades) == 1
        assert user.trades[0].trade_id == trade.trade_id
        
        await db_session.refresh(trade)
        assert trade.user.user_id == user.user_id
        assert trade.account.account_id == account.account_id
