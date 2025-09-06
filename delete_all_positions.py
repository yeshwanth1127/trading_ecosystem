#!/usr/bin/env python3
"""
Simple script to delete all open positions from the database
This will clear all positions that the frontend displays
"""

import asyncio
import sys
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Import the existing database configuration
from app.config.settings import settings

async def delete_all_positions():
    """Delete all open positions from the database"""
    
    # Use the existing database configuration
    DATABASE_URL = settings.database_url
    
    try:
        # Create async engine
        engine = create_async_engine(DATABASE_URL, echo=True)
        
        async with engine.begin() as conn:
            # First, let's see how many positions we have
            result = await conn.execute(text("SELECT COUNT(*) FROM positions WHERE status = 'open'"))
            count = result.scalar()
            print(f"📊 Found {count} open positions to delete")
            
            if count == 0:
                print("✅ No open positions found. Database is already clean!")
                return
            
            # Delete all open positions
            delete_result = await conn.execute(
                text("DELETE FROM positions WHERE status = 'open'")
            )
            
            deleted_count = delete_result.rowcount
            print(f"🗑️  Successfully deleted {deleted_count} open positions")
            
            # Verify deletion
            result = await conn.execute(text("SELECT COUNT(*) FROM positions WHERE status = 'open'"))
            remaining_count = result.scalar()
            
            if remaining_count == 0:
                print("✅ All open positions have been deleted successfully!")
                print("🎯 Frontend will now show 0 positions")
            else:
                print(f"⚠️  Warning: {remaining_count} positions still remain")
        
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ Error deleting positions: {e}")
        return False
    
    return True

async def main():
    """Main function"""
    print("🚀 Starting position cleanup...")
    print("=" * 50)
    
    success = await delete_all_positions()
    
    print("=" * 50)
    if success:
        print("🎉 Position cleanup completed successfully!")
    else:
        print("💥 Position cleanup failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
