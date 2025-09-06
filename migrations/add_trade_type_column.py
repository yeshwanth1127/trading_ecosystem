"""
Migration: Add trade_type column to trades table
===============================================

This migration adds the missing trade_type column to the trades table.
"""

import asyncio
import sys
import os
from sqlalchemy import text

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import async_engine

async def migrate():
    """Add trade_type column to trades table"""
    print("🔄 Starting migration: Add trade_type column")
    
    try:
        async with async_engine.begin() as conn:
            # Check if trade_type column exists
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'trades' AND column_name = 'trade_type'
            """))
            
            if not result.fetchone():
                print("📝 Adding trade_type column to trades table...")
                await conn.execute(text("""
                    ALTER TABLE trades 
                    ADD COLUMN trade_type VARCHAR(20) DEFAULT 'FILL'
                """))
                print("✅ Added trade_type to trades table")
            else:
                print("ℹ️ trade_type already exists in trades table")
            
            print("🎉 Migration completed successfully!")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

async def main():
    """Main migration function"""
    await migrate()

if __name__ == "__main__":
    asyncio.run(main())
