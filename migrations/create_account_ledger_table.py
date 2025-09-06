"""
Migration: Create account_ledger table
======================================

This migration creates the account_ledger table for the immutable financial journal.
"""

import asyncio
import sys
import os
from sqlalchemy import text

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import async_engine

async def migrate():
    """Create account_ledger table"""
    print("🔄 Starting migration: Create account_ledger table")
    
    try:
        async with async_engine.begin() as conn:
            # Check if account_ledger table exists
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'account_ledger'
            """))
            
            if not result.fetchone():
                print("📝 Creating account_ledger table...")
                await conn.execute(text("""
                    CREATE TABLE account_ledger (
                        entry_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES users(user_id),
                        account_id UUID NOT NULL REFERENCES accounts(account_id),
                        order_id UUID REFERENCES orders(order_id),
                        trade_id UUID REFERENCES trades(trade_id),
                        position_id UUID REFERENCES positions(position_id),
                        entry_type VARCHAR(20) NOT NULL,
                        status VARCHAR(20) NOT NULL DEFAULT 'completed',
                        amount NUMERIC(20,8) NOT NULL,
                        balance_before NUMERIC(20,8) NOT NULL,
                        balance_after NUMERIC(20,8) NOT NULL,
                        currency VARCHAR(10) NOT NULL DEFAULT 'USD',
                        exchange_rate NUMERIC(15,8),
                        description TEXT,
                        reference_id VARCHAR(100),
                        extra_data TEXT,
                        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                        processed_at TIMESTAMP WITH TIME ZONE
                    )
                """))
                print("✅ Created account_ledger table")
                
                # Add indexes
                print("📝 Adding indexes...")
                await conn.execute(text("""
                    CREATE INDEX idx_ledger_user_account_type ON account_ledger(user_id, account_id, entry_type)
                """))
                await conn.execute(text("""
                    CREATE INDEX idx_ledger_created_at ON account_ledger(created_at)
                """))
                print("✅ Added indexes")
            else:
                print("ℹ️ account_ledger table already exists")
            
            print("🎉 Migration completed successfully!")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

async def main():
    """Main migration function"""
    await migrate()

if __name__ == "__main__":
    asyncio.run(main())
