"""
Migration: Add account_id columns to orders and positions tables
==============================================================

This migration adds the missing account_id foreign key columns to:
- orders table
- positions table

This is required for the execution engine to work properly.
"""

import asyncio
import sys
import os
from sqlalchemy import text

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import async_engine

async def migrate():
    """Add account_id columns to orders and positions tables"""
    print("🔄 Starting migration: Add account_id columns")
    
    try:
        async with async_engine.begin() as conn:
            # Check if account_id column exists in orders table
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'orders' AND column_name = 'account_id'
            """))
            
            if not result.fetchone():
                print("📝 Adding account_id column to orders table...")
                await conn.execute(text("""
                    ALTER TABLE orders 
                    ADD COLUMN account_id UUID REFERENCES accounts(account_id)
                """))
                print("✅ Added account_id to orders table")
            else:
                print("ℹ️ account_id already exists in orders table")
            
            # Check if account_id column exists in positions table
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'positions' AND column_name = 'account_id'
            """))
            
            if not result.fetchone():
                print("📝 Adding account_id column to positions table...")
                await conn.execute(text("""
                    ALTER TABLE positions 
                    ADD COLUMN account_id UUID REFERENCES accounts(account_id)
                """))
                print("✅ Added account_id to positions table")
            else:
                print("ℹ️ account_id already exists in positions table")
            
            # Add indexes for performance
            print("📝 Adding indexes...")
            try:
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_orders_account_id 
                    ON orders(account_id)
                """))
                print("✅ Added index on orders.account_id")
            except Exception as e:
                print(f"ℹ️ Index on orders.account_id may already exist: {e}")
            
            try:
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_positions_account_id 
                    ON positions(account_id)
                """))
                print("✅ Added index on positions.account_id")
            except Exception as e:
                print(f"ℹ️ Index on positions.account_id may already exist: {e}")
            
            print("🎉 Migration completed successfully!")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

async def main():
    """Main migration function"""
    await migrate()

if __name__ == "__main__":
    asyncio.run(main())
