# Import all models to ensure they are registered with SQLAlchemy
from .user import User
from .account import Account
from .challenge_template import ChallengeTemplate
from .challenge_attempt import ChallengeAttempt
from .challenge_selection import ChallengeSelection
from .trading_challenge import TradingChallenge
from .trade import Trade
from .order import Order
from .position import Position
from .instrument import Instrument
from .subscription_plan import SubscriptionPlan
from .subscription import Subscription

__all__ = [
    "User",
    "Account", 
    "ChallengeTemplate",
    "ChallengeAttempt",
    "ChallengeSelection",
    "TradingChallenge",
    "Trade",
    "Order",
    "Position",
    "Instrument",
    "SubscriptionPlan",
    "Subscription"
]
