import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import user, account, challenge_template, challenge_attempt, trade, subscription_plan, subscription
from app.schemas import (
    UserCreate, UserUpdate, AccountCreate, AccountUpdate,
    ChallengeTemplateCreate, ChallengeTemplateUpdate,
    ChallengeAttemptCreate, ChallengeAttemptUpdate,
    TradeCreate, TradeUpdate,
    SubscriptionPlanCreate, SubscriptionPlanUpdate,
    SubscriptionCreate, SubscriptionUpdate
)

class TestUserCRUD:
    """Test User CRUD operations."""
    
    async def test_create_user(self, db_session: AsyncSession):
        """Test creating a user."""
        user_data = UserCreate(
            name="Test User",
            email="test@example.com",
            role="trader",
            status="active"
        )
        
        db_user = await user.create(db_session, obj_in=user_data)
        assert db_user.name == "Test User"
        assert db_user.email == "test@example.com"
        assert db_user.role == "trader"
        assert db_user.status == "active"
        assert db_user.user_id is not None
    
    async def test_get_user(self, db_session: AsyncSession):
        """Test getting a user by ID."""
        # Create user first
        user_data = UserCreate(
            name="Test User",
            email="test@example.com",
            role="trader",
            status="active"
        )
        db_user = await user.create(db_session, obj_in=user_data)
        
        # Get user by ID
        retrieved_user = await user.get(db_session, id=db_user.user_id)
        assert retrieved_user is not None
        assert retrieved_user.user_id == db_user.user_id
        assert retrieved_user.name == "Test User"
    
    async def test_get_user_by_email(self, db_session: AsyncSession):
        """Test getting a user by email."""
        # Create user first
        user_data = UserCreate(
            name="Test User",
            email="test@example.com",
            role="trader",
            status="active"
        )
        await user.create(db_session, obj_in=user_data)
        
        # Get user by email
        retrieved_user = await user.get_by_email(db_session, email="test@example.com")
        assert retrieved_user is not None
        assert retrieved_user.email == "test@example.com"
    
    async def test_update_user(self, db_session: AsyncSession):
        """Test updating a user."""
        # Create user first
        user_data = UserCreate(
            name="Test User",
            email="test@example.com",
            role="trader",
            status="active"
        )
        db_user = await user.create(db_session, obj_in=user_data)
        
        # Update user
        update_data = UserUpdate(name="Updated User")
        updated_user = await user.update(db_session, db_obj=db_user, obj_in=update_data)
        assert updated_user.name == "Updated User"
        assert updated_user.email == "test@example.com"  # Unchanged
    
    async def test_delete_user(self, db_session: AsyncSession):
        """Test deleting a user."""
        # Create user first
        user_data = UserCreate(
            name="Test User",
            email="test@example.com",
            role="trader",
            status="active"
        )
        db_user = await user.create(db_session, obj_in=user_data)
        
        # Delete user
        deleted_user = await user.remove(db_session, id=db_user.user_id)
        assert deleted_user is not None
        
        # Verify user is deleted
        retrieved_user = await user.get(db_session, id=db_user.user_id)
        assert retrieved_user is None
    
    async def test_get_users_with_filters(self, db_session: AsyncSession):
        """Test getting users with filters."""
        # Create multiple users
        user1_data = UserCreate(name="User 1", email="user1@example.com", role="trader", status="active")
        user2_data = UserCreate(name="User 2", email="user2@example.com", role="admin", status="active")
        
        await user.create(db_session, obj_in=user1_data)
        await user.create(db_session, obj_in=user2_data)
        
        # Get users by role
        traders = await user.get_by_role(db_session, role="trader")
        assert len(traders) == 1
        assert traders[0].role == "trader"
        
        admins = await user.get_by_role(db_session, role="admin")
        assert len(admins) == 1
        assert admins[0].role == "admin"

class TestAccountCRUD:
    """Test Account CRUD operations."""
    
    async def test_create_account(self, db_session: AsyncSession):
        """Test creating an account."""
        # Create user first
        user_data = UserCreate(name="Test User", email="test@example.com", role="trader", status="active")
        db_user = await user.create(db_session, obj_in=user_data)
        
        account_data = AccountCreate(
            user_id=db_user.user_id,
            type="simulated",
            balance=Decimal("10000.00")
        )
        
        db_account = await account.create(db_session, obj_in=account_data)
        assert db_account.user_id == db_user.user_id
        assert db_account.type == "simulated"
        assert db_account.balance == Decimal("10000.00")
        assert db_account.account_id is not None
    
    async def test_get_accounts_by_user(self, db_session: AsyncSession):
        """Test getting accounts by user ID."""
        # Create user and accounts
        user_data = UserCreate(name="Test User", email="test@example.com", role="trader", status="active")
        db_user = await user.create(db_session, obj_in=user_data)
        
        account1_data = AccountCreate(user_id=db_user.user_id, type="simulated", balance=Decimal("10000.00"))
        account2_data = AccountCreate(user_id=db_user.user_id, type="copy", balance=Decimal("5000.00"))
        
        await account.create(db_session, obj_in=account1_data)
        await account.create(db_session, obj_in=account2_data)
        
        # Get accounts by user ID
        user_accounts = await account.get_by_user_id(db_session, user_id=db_user.user_id)
        assert len(user_accounts) == 2
    
    async def test_get_accounts_by_type(self, db_session: AsyncSession):
        """Test getting accounts by type."""
        # Create user and accounts
        user_data = UserCreate(name="Test User", email="test@example.com", role="trader", status="active")
        db_user = await user.create(db_session, obj_in=user_data)
        
        account1_data = AccountCreate(user_id=db_user.user_id, type="simulated", balance=Decimal("10000.00"))
        account2_data = AccountCreate(user_id=db_user.user_id, type="copy", balance=Decimal("5000.00"))
        
        await account.create(db_session, obj_in=account1_data)
        await account.create(db_session, obj_in=account2_data)
        
        # Get accounts by type
        simulated_accounts = await account.get_by_type(db_session, account_type="simulated")
        assert len(simulated_accounts) == 1
        assert simulated_accounts[0].type == "simulated"

class TestChallengeTemplateCRUD:
    """Test ChallengeTemplate CRUD operations."""
    
    async def test_create_challenge_template(self, db_session: AsyncSession):
        """Test creating a challenge template."""
        template_data = ChallengeTemplateCreate(
            name="Test Challenge",
            account_size=Decimal("50000.00"),
            fee_amount=Decimal("99.99"),
            profit_target_pct=Decimal("8.00"),
            max_drawdown_pct=Decimal("5.00"),
            daily_loss_pct=Decimal("3.00"),
            status="active"
        )
        
        db_template = await challenge_template.create(db_session, obj_in=template_data)
        assert db_template.name == "Test Challenge"
        assert db_template.account_size == Decimal("50000.00")
        assert db_template.status == "active"
    
    async def test_get_active_challenges(self, db_session: AsyncSession):
        """Test getting active challenge templates."""
        # Create active and archived challenges
        active_template = ChallengeTemplateCreate(
            name="Active Challenge",
            account_size=Decimal("50000.00"),
            fee_amount=Decimal("99.99"),
            profit_target_pct=Decimal("8.00"),
            max_drawdown_pct=Decimal("5.00"),
            daily_loss_pct=Decimal("3.00"),
            status="active"
        )
        
        archived_template = ChallengeTemplateCreate(
            name="Archived Challenge",
            account_size=Decimal("25000.00"),
            fee_amount=Decimal("49.99"),
            profit_target_pct=Decimal("6.00"),
            max_drawdown_pct=Decimal("4.00"),
            daily_loss_pct=Decimal("2.00"),
            status="archived"
        )
        
        await challenge_template.create(db_session, obj_in=active_template)
        await challenge_template.create(db_session, obj_in=archived_template)
        
        # Get active challenges only
        active_challenges = await challenge_template.get_active_challenges(db_session)
        assert len(active_challenges) == 1
        assert active_challenges[0].status == "active"

class TestTradeCRUD:
    """Test Trade CRUD operations."""
    
    async def test_create_trade(self, db_session: AsyncSession):
        """Test creating a trade."""
        # Create user and account first
        user_data = UserCreate(name="Test User", email="test@example.com", role="trader", status="active")
        db_user = await user.create(db_session, obj_in=user_data)
        
        account_data = AccountCreate(user_id=db_user.user_id, type="simulated", balance=Decimal("10000.00"))
        db_account = await account.create(db_session, obj_in=account_data)
        
        trade_data = TradeCreate(
            account_id=db_account.account_id,
            user_id=db_user.user_id,
            instrument="EURUSD",
            side="buy",
            qty=Decimal("1.0"),
            entry_price=Decimal("1.0850")
        )
        
        db_trade = await trade.create(db_session, obj_in=trade_data)
        assert db_trade.instrument == "EURUSD"
        assert db_trade.side == "buy"
        assert db_trade.qty == Decimal("1.0")
        assert db_trade.entry_price == Decimal("1.0850")
    
    async def test_get_trades_by_account(self, db_session: AsyncSession):
        """Test getting trades by account ID."""
        # Create user, account, and trades
        user_data = UserCreate(name="Test User", email="test@example.com", role="trader", status="active")
        db_user = await user.create(db_session, obj_in=user_data)
        
        account_data = AccountCreate(user_id=db_user.user_id, type="simulated", balance=Decimal("10000.00"))
        db_account = await account.create(db_session, obj_in=account_data)
        
        trade1_data = TradeCreate(
            account_id=db_account.account_id,
            user_id=db_user.user_id,
            instrument="EURUSD",
            side="buy",
            qty=Decimal("1.0"),
            entry_price=Decimal("1.0850")
        )
        
        trade2_data = TradeCreate(
            account_id=db_account.account_id,
            user_id=db_user.user_id,
            instrument="GBPUSD",
            side="sell",
            qty=Decimal("0.5"),
            entry_price=Decimal("1.2500")
        )
        
        await trade.create(db_session, obj_in=trade1_data)
        await trade.create(db_session, obj_in=trade2_data)
        
        # Get trades by account ID
        account_trades = await trade.get_by_account_id(db_session, account_id=db_account.account_id)
        assert len(account_trades) == 2
    
    async def test_get_open_trades(self, db_session: AsyncSession):
        """Test getting open trades."""
        # Create user, account, and trades
        user_data = UserCreate(name="Test User", email="test@example.com", role="trader", status="active")
        db_user = await user.create(db_session, obj_in=user_data)
        
        account_data = AccountCreate(user_id=db_user.user_id, type="simulated", balance=Decimal("10000.00"))
        db_account = await account.create(db_session, obj_in=account_data)
        
        # Create open trade (no exit price)
        open_trade_data = TradeCreate(
            account_id=db_account.account_id,
            user_id=db_user.user_id,
            instrument="EURUSD",
            side="buy",
            qty=Decimal("1.0"),
            entry_price=Decimal("1.0850")
        )
        
        # Create closed trade (with exit price)
        closed_trade_data = TradeCreate(
            account_id=db_account.account_id,
            user_id=db_user.user_id,
            instrument="GBPUSD",
            side="sell",
            qty=Decimal("0.5"),
            entry_price=Decimal("1.2500")
        )
        
        open_trade = await trade.create(db_session, obj_in=open_trade_data)
        closed_trade = await trade.create(db_session, obj_in=closed_trade_data)
        
        # Update closed trade with exit price
        await trade.update(db_session, db_obj=closed_trade, obj_in=TradeUpdate(exit_price=Decimal("1.2450")))
        
        # Get open trades
        open_trades = await trade.get_open_trades(db_session, account_id=db_account.account_id)
        assert len(open_trades) == 1
        assert open_trades[0].trade_id == open_trade.trade_id

class TestSubscriptionPlanCRUD:
    """Test SubscriptionPlan CRUD operations."""
    
    async def test_create_subscription_plan(self, db_session: AsyncSession):
        """Test creating a subscription plan."""
        plan_data = SubscriptionPlanCreate(
            name="Basic Copy Trading",
            type="copy_trade",
            price=Decimal("29.99"),
            features={"max_copiers": 10, "real_time_signals": True},
            status="active"
        )
        
        db_plan = await subscription_plan.create(db_session, obj_in=plan_data)
        assert db_plan.name == "Basic Copy Trading"
        assert db_plan.type == "copy_trade"
        assert db_plan.price == Decimal("29.99")
        assert db_plan.features == {"max_copiers": 10, "real_time_signals": True}
    
    async def test_get_active_plans(self, db_session: AsyncSession):
        """Test getting active subscription plans."""
        # Create active and archived plans
        active_plan = SubscriptionPlanCreate(
            name="Active Plan",
            type="copy_trade",
            price=Decimal("29.99"),
            features={},
            status="active"
        )
        
        archived_plan = SubscriptionPlanCreate(
            name="Archived Plan",
            type="algo",
            price=Decimal("19.99"),
            features={},
            status="archived"
        )
        
        await subscription_plan.create(db_session, obj_in=active_plan)
        await subscription_plan.create(db_session, obj_in=archived_plan)
        
        # Get active plans only
        active_plans = await subscription_plan.get_active_plans(db_session)
        assert len(active_plans) == 1
        assert active_plans[0].status == "active"

class TestSubscriptionCRUD:
    """Test Subscription CRUD operations."""
    
    async def test_create_subscription(self, db_session: AsyncSession):
        """Test creating a subscription."""
        # Create user and plan first
        user_data = UserCreate(name="Test User", email="test@example.com", role="trader", status="active")
        db_user = await user.create(db_session, obj_in=user_data)
        
        plan_data = SubscriptionPlanCreate(
            name="Basic Plan",
            type="copy_trade",
            price=Decimal("29.99"),
            features={},
            status="active"
        )
        db_plan = await subscription_plan.create(db_session, obj_in=plan_data)
        
        subscription_data = SubscriptionCreate(
            user_id=db_user.user_id,
            plan_id=db_plan.plan_id,
            end_date=datetime.utcnow() + timedelta(days=30)
        )
        
        db_subscription = await subscription.create(db_session, obj_in=subscription_data)
        assert db_subscription.user_id == db_user.user_id
        assert db_subscription.plan_id == db_plan.plan_id
        assert db_subscription.status == "active"
    
    async def test_get_user_active_subscription(self, db_session: AsyncSession):
        """Test getting user's active subscription."""
        # Create user and plan
        user_data = UserCreate(name="Test User", email="test@example.com", role="trader", status="active")
        db_user = await user.create(db_session, obj_in=user_data)
        
        plan_data = SubscriptionPlanCreate(
            name="Basic Plan",
            type="copy_trade",
            price=Decimal("29.99"),
            features={},
            status="active"
        )
        db_plan = await subscription_plan.create(db_session, obj_in=plan_data)
        
        # Create active subscription
        subscription_data = SubscriptionCreate(
            user_id=db_user.user_id,
            plan_id=db_plan.plan_id,
            end_date=datetime.utcnow() + timedelta(days=30)
        )
        
        await subscription.create(db_session, obj_in=subscription_data)
        
        # Get user's active subscription
        active_subscription = await subscription.get_user_active_subscription(db_session, user_id=db_user.user_id)
        assert active_subscription is not None
        assert active_subscription.user_id == db_user.user_id
        assert active_subscription.status == "active"
