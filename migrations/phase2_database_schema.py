"""
Phase 2 Database Schema Migration
=================================

This script handles the migration from Phase 1 to Phase 2 database schema.
It adds new tables and enhances existing ones for real-time trading functionality.

New Tables:
- account_ledger: Immutable journal for all financial transactions

Enhanced Tables:
- orders: Added margin, leverage, and real-time trading fields
- trades: Enhanced for better fill event tracking
- positions: Added proper status management and margin tracking
- accounts: Added comprehensive financial tracking and risk management
- users: Added ledger_entries relationship
- instruments: Added trades relationship

Run this script after backing up your database.
"""

import asyncio
import logging
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.database import async_engine, Base
from app.models import *  # Import all models

logger = logging.getLogger(__name__)

async def run_migration():
    """Run the Phase 2 database migration"""
    logger.info("🚀 Starting Phase 2 Database Schema Migration")
    
    try:
        async with async_engine.begin() as conn:
            # Create all new tables and update existing ones
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database schema updated successfully")
            
            # Add any custom migration logic here if needed
            # For example, data transformations or index optimizations
            
            logger.info("🎉 Phase 2 migration completed successfully!")
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

async def rollback_migration():
    """Rollback the migration (use with caution)"""
    logger.warning("⚠️  Rolling back Phase 2 migration")
    
    try:
        async with async_engine.begin() as conn:
            # Drop the new account_ledger table
            await conn.execute(text("DROP TABLE IF EXISTS account_ledger CASCADE"))
            logger.info("✅ Rollback completed")
            
    except Exception as e:
        logger.error(f"❌ Rollback failed: {e}")
        raise

async def verify_migration():
    """Verify that the migration was successful"""
    logger.info("🔍 Verifying migration...")
    
    try:
        async with async_engine.begin() as conn:
            # Check if account_ledger table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'account_ledger'
                );
            """))
            
            if result.scalar():
                logger.info("✅ account_ledger table exists")
            else:
                logger.error("❌ account_ledger table not found")
                return False
            
            # Check if new columns exist in orders table
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'orders' 
                AND column_name IN ('leverage', 'margin_required', 'margin_used', 'is_margin_order')
                ORDER BY column_name;
            """))
            
            columns = [row[0] for row in result.fetchall()]
            expected_columns = ['is_margin_order', 'leverage', 'margin_required', 'margin_used']
            
            if all(col in columns for col in expected_columns):
                logger.info("✅ Orders table enhanced successfully")
            else:
                logger.error(f"❌ Missing columns in orders table: {set(expected_columns) - set(columns)}")
                return False
            
            # Check if new columns exist in accounts table
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'accounts' 
                AND column_name IN ('equity', 'margin_used', 'margin_available', 'unrealized_pnl', 'realized_pnl')
                ORDER BY column_name;
            """))
            
            columns = [row[0] for row in result.fetchall()]
            expected_columns = ['equity', 'margin_available', 'margin_used', 'unrealized_pnl', 'realized_pnl']
            
            if all(col in columns for col in expected_columns):
                logger.info("✅ Accounts table enhanced successfully")
            else:
                logger.error(f"❌ Missing columns in accounts table: {set(expected_columns) - set(columns)}")
                return False
            
            logger.info("🎉 Migration verification completed successfully!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False

async def main():
    """Main migration function"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "migrate":
            await run_migration()
        elif command == "rollback":
            await rollback_migration()
        elif command == "verify":
            await verify_migration()
        else:
            print("Usage: python phase2_database_schema.py [migrate|rollback|verify]")
    else:
        # Default: run migration and verify
        await run_migration()
        await verify_migration()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
