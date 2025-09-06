import asyncio
import uuid
from app.db.database import AsyncSessionLocal
from app.models.challenge_selection import ChallengeSelection, ChallengeSelectionStatus

async def create_challenge_selection():
    """Create a test challenge selection for the existing user"""
    async with AsyncSessionLocal() as db:
        try:
            # Use one of the existing user IDs from the database
            user_id = uuid.UUID("69a7b340-8106-4577-8bd4-de9fe02f5cd6")  # Test User
            
            # Create a challenge selection
            challenge_selection = ChallengeSelection(
                selection_id=uuid.uuid4(),
                user_id=user_id,
                challenge_id="challenge_50k",  # Frontend challenge identifier
                amount="₹50,000",  # Challenge amount as string
                price="₹999",  # Challenge price
                profit_target="₹5,000",  # Profit target
                max_drawdown="₹5,000",  # Max drawdown
                daily_limit="₹2,500",  # Daily limit
                status=ChallengeSelectionStatus.ACTIVE
            )
            
            db.add(challenge_selection)
            await db.commit()
            
            print("Challenge selection created successfully!")
            print(f"Selection ID: {challenge_selection.selection_id}")
            print(f"User ID: {challenge_selection.user_id}")
            print(f"Challenge ID: {challenge_selection.challenge_id}")
            print(f"Amount: {challenge_selection.amount}")
            print(f"Status: {challenge_selection.status}")
            
        except Exception as e:
            await db.rollback()
            print(f"Error creating challenge selection: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(create_challenge_selection())
