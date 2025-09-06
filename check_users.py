import asyncio
from app.db.database import AsyncSessionLocal
from app.models.user import User

async def check_users():
    """Check what users exist in the database"""
    async with AsyncSessionLocal() as db:
        try:
            from sqlalchemy import select
            stmt = select(User)
            result = await db.execute(stmt)
            users = result.scalars().all()
            
            print(f"Found {len(users)} users in the database:")
            print("=" * 50)
            
            for user in users:
                print(f"User ID: {user.user_id}")
                print(f"Name: {user.name}")
                print(f"Email: {user.email}")
                print(f"Created At: {user.created_at}")
                print("-" * 30)
                
        except Exception as e:
            print(f"Error checking users: {e}")

if __name__ == "__main__":
    asyncio.run(check_users())
