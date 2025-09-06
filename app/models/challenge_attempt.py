from sqlalchemy import Column, String, Enum, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum
import uuid

class ChallengeState(str, enum.Enum):
    ACTIVE = "active"
    PASSED = "passed"
    FAILED = "failed"

class ChallengeAttempt(Base):
    __tablename__ = "challenge_attempts"
    
    attempt_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    challenge_id = Column(UUID(as_uuid=True), ForeignKey("challenge_templates.challenge_id"), nullable=False, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.account_id"), nullable=False, index=True)
    state = Column(Enum(ChallengeState), nullable=False, default=ChallengeState.ACTIVE)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    metrics = Column(JSON, nullable=True)  # Store PnL, drawdown, daily loss logs
    
    # Relationships
    user = relationship("User", back_populates="challenge_attempts")
    challenge_template = relationship("ChallengeTemplate", back_populates="challenge_attempts")
    account = relationship("Account", back_populates="challenge_attempts")
    
    def __repr__(self):
        return f"<ChallengeAttempt(attempt_id={self.attempt_id}, user_id={self.user_id}, state={self.state})>"
