"""
Migration: Add all missing columns from Phase 2 enhancements
===========================================================

This migration adds all the missing columns to make the database schema
match the enhanced models from Phase 2.
"""

import asyncio
import sys
import os
from sqlalchemy import text

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import async_engine

async def migrate():
    """Add all missing columns to match enhanced models"""
    print("🔄 Starting comprehensive migration: Add missing columns")
    
    try:
        async with async_engine.begin() as conn:
            
            # ===== ORDERS TABLE =====
            print("📝 Updating orders table...")
            
            # Add missing columns to orders table
            orders_columns = [
                ("time_in_force", "VARCHAR(10) DEFAULT 'gtc'"),
                ("filled_quantity", "NUMERIC(20,8) DEFAULT 0.0"),
                ("remaining_quantity", "NUMERIC(20,8)"),
                ("average_fill_price", "NUMERIC(20,8)"),
                ("filled_amount", "NUMERIC(20,8) DEFAULT 0.0"),
                ("remaining_amount", "NUMERIC(20,8)"),
                ("commission", "NUMERIC(20,8) DEFAULT 0.0"),
                ("commission_rate", "NUMERIC(8,6) DEFAULT 0.001"),
                ("leverage", "NUMERIC(8,2) DEFAULT 1.0"),
                ("margin_required", "NUMERIC(20,8) DEFAULT 0.0"),
                ("margin_used", "NUMERIC(20,8) DEFAULT 0.0"),
                ("is_margin_order", "BOOLEAN DEFAULT FALSE"),
                ("reduce_only", "BOOLEAN DEFAULT FALSE"),
                ("post_only", "BOOLEAN DEFAULT FALSE"),
                ("expired_at", "TIMESTAMP WITH TIME ZONE"),
                ("client_order_id", "VARCHAR(100)"),
                ("rejection_reason", "TEXT")
            ]
            
            for column_name, column_def in orders_columns:
                try:
                    await conn.execute(text(f"""
                        ALTER TABLE orders 
                        ADD COLUMN {column_name} {column_def}
                    """))
                    print(f"  ✅ Added {column_name} to orders")
                except Exception as e:
                    if "already exists" in str(e) or "duplicate column" in str(e):
                        print(f"  ℹ️ {column_name} already exists in orders")
                    else:
                        print(f"  ❌ Failed to add {column_name}: {e}")
            
            # ===== POSITIONS TABLE =====
            print("📝 Updating positions table...")
            
            # Add missing columns to positions table
            positions_columns = [
                ("account_id", "UUID REFERENCES accounts(account_id)"),
                ("mark_price", "NUMERIC(20,8)"),
                ("margin_required", "NUMERIC(20,8) DEFAULT 0.0"),
                ("margin_ratio", "NUMERIC(8,4) DEFAULT 0.0"),
                ("liquidation_price", "NUMERIC(20,8)"),
                ("stop_loss", "NUMERIC(20,8)"),
                ("take_profit", "NUMERIC(20,8)"),
                ("total_trades", "INTEGER DEFAULT 0"),
                ("total_volume", "NUMERIC(20,8) DEFAULT 0.0"),
                ("total_fees", "NUMERIC(20,8) DEFAULT 0.0"),
                ("notes", "TEXT"),
                ("extra_data", "TEXT")
            ]
            
            for column_name, column_def in positions_columns:
                try:
                    await conn.execute(text(f"""
                        ALTER TABLE positions 
                        ADD COLUMN {column_name} {column_def}
                    """))
                    print(f"  ✅ Added {column_name} to positions")
                except Exception as e:
                    if "already exists" in str(e) or "duplicate column" in str(e):
                        print(f"  ℹ️ {column_name} already exists in positions")
                    else:
                        print(f"  ❌ Failed to add {column_name}: {e}")
            
            # ===== TRADES TABLE =====
            print("📝 Updating trades table...")
            
            # Add missing columns to trades table
            trades_columns = [
                ("order_id", "UUID REFERENCES orders(order_id)"),
                ("price", "NUMERIC(20,8)"),
                ("amount", "NUMERIC(20,8)"),
                ("commission_rate", "NUMERIC(8,6) DEFAULT 0.001"),
                ("funding_fee", "NUMERIC(20,8) DEFAULT 0.0"),
                ("leverage", "NUMERIC(8,2) DEFAULT 1.0"),
                ("margin_used", "NUMERIC(20,8) DEFAULT 0.0"),
                ("realized_pnl", "NUMERIC(20,8) DEFAULT 0.0"),
                ("unrealized_pnl", "NUMERIC(20,8) DEFAULT 0.0"),
                ("is_maker", "BOOLEAN DEFAULT FALSE"),
                ("execution_id", "VARCHAR(100)"),
                ("liquidity", "VARCHAR(20) DEFAULT 'taker'"),
                ("executed_at", "TIMESTAMP WITH TIME ZONE"),
                ("notes", "TEXT"),
                ("extra_data", "TEXT")
            ]
            
            for column_name, column_def in trades_columns:
                try:
                    await conn.execute(text(f"""
                        ALTER TABLE trades 
                        ADD COLUMN {column_name} {column_def}
                    """))
                    print(f"  ✅ Added {column_name} to trades")
                except Exception as e:
                    if "already exists" in str(e) or "duplicate column" in str(e):
                        print(f"  ℹ️ {column_name} already exists in trades")
                    else:
                        print(f"  ❌ Failed to add {column_name}: {e}")
            
            # ===== ACCOUNTS TABLE =====
            print("📝 Updating accounts table...")
            
            # Add missing columns to accounts table
            accounts_columns = [
                ("status", "VARCHAR(20) DEFAULT 'active'"),
                ("equity", "NUMERIC(20,8) DEFAULT 0.0"),
                ("margin_used", "NUMERIC(20,8) DEFAULT 0.0"),
                ("margin_available", "NUMERIC(20,8) DEFAULT 0.0"),
                ("unrealized_pnl", "NUMERIC(20,8) DEFAULT 0.0"),
                ("realized_pnl", "NUMERIC(20,8) DEFAULT 0.0"),
                ("max_leverage", "NUMERIC(8,2) DEFAULT 1.0"),
                ("margin_call_threshold", "NUMERIC(8,4) DEFAULT 0.8"),
                ("liquidation_threshold", "NUMERIC(8,4) DEFAULT 0.5"),
                ("is_margin_enabled", "BOOLEAN DEFAULT FALSE"),
                ("auto_liquidation", "BOOLEAN DEFAULT TRUE"),
                ("last_updated", "TIMESTAMP WITH TIME ZONE DEFAULT NOW()")
            ]
            
            for column_name, column_def in accounts_columns:
                try:
                    await conn.execute(text(f"""
                        ALTER TABLE accounts 
                        ADD COLUMN {column_name} {column_def}
                    """))
                    print(f"  ✅ Added {column_name} to accounts")
                except Exception as e:
                    if "already exists" in str(e) or "duplicate column" in str(e):
                        print(f"  ℹ️ {column_name} already exists in accounts")
                    else:
                        print(f"  ❌ Failed to add {column_name}: {e}")
            
            # ===== CREATE ACCOUNT_LEDGER TABLE =====
            print("📝 Creating account_ledger table...")
            
            try:
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS account_ledger (
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
                print("  ✅ Created account_ledger table")
            except Exception as e:
                if "already exists" in str(e):
                    print("  ℹ️ account_ledger table already exists")
                else:
                    print(f"  ❌ Failed to create account_ledger: {e}")
            
            # ===== ADD INDEXES =====
            print("📝 Adding indexes...")
            
            indexes = [
                ("idx_orders_account_status", "orders(account_id, status)"),
                ("idx_orders_user_status", "orders(user_id, status)"),
                ("idx_orders_created_at", "orders(created_at)"),
                ("idx_orders_client_order_id", "orders(client_order_id)"),
                ("idx_positions_account_status", "positions(account_id, status)"),
                ("idx_positions_user_status", "positions(user_id, status)"),
                ("idx_trades_order_id", "trades(order_id)"),
                ("idx_trades_execution_id", "trades(execution_id)"),
                ("idx_ledger_user_account_type", "account_ledger(user_id, account_id, entry_type)"),
                ("idx_ledger_created_at", "account_ledger(created_at)")
            ]
            
            for index_name, index_def in indexes:
                try:
                    await conn.execute(text(f"""
                        CREATE INDEX IF NOT EXISTS {index_name} ON {index_def}
                    """))
                    print(f"  ✅ Added index {index_name}")
                except Exception as e:
                    print(f"  ℹ️ Index {index_name} may already exist: {e}")
            
            print("🎉 Comprehensive migration completed successfully!")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

async def main():
    """Main migration function"""
    await migrate()

if __name__ == "__main__":
    asyncio.run(main())
