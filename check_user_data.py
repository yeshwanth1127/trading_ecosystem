import asyncio
from app.db.database import AsyncSessionLocal
from app.models.challenge_selection import ChallengeSelection

async def check_user_data():
    """Check challenge selection data for the actual user"""
    async with AsyncSessionLocal() as db:
        try:
            # Check for the actual user (yeshwanth sh)
            actual_user_id = "1b9efe4b-5885-4ae5-a9fa-072a9a84fd1c"
            
            # Get all challenge selections for this user
            from sqlalchemy import select
            stmt = select(ChallengeSelection).where(ChallengeSelection.user_id == actual_user_id)
            result = await db.execute(stmt)
            selections = result.scalars().all()
            
            print(f"Found {len(selections)} challenge selections for user {actual_user_id}")
            
            for selection in selections:
                print(f"Selection ID: {selection.selection_id}")
                print(f"Challenge ID: {selection.challenge_id}")
                print(f"Amount: {selection.amount}")
                print(f"Status: {selection.status}")
                print(f"Created At: {selection.created_at}")
                print("---")
                
        except Exception as e:
            print(f"Error checking user data: {e}")

if __name__ == "__main__":
    asyncio.run(check_user_data())
