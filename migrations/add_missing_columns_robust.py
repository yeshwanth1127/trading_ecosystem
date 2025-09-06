"""
Robust Migration: Add missing columns one by one
===============================================

This migration adds missing columns individually to avoid transaction failures.
"""

import asyncio
import sys
import os
from sqlalchemy import text

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import async_engine

async def add_column_if_not_exists(conn, table_name, column_name, column_def):
    """Add a column if it doesn't exist"""
    try:
        # Check if column exists
        result = await conn.execute(text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}' AND column_name = '{column_name}'
        """))
        
        if not result.fetchone():
            await conn.execute(text(f"""
                ALTER TABLE {table_name} 
                ADD COLUMN {column_name} {column_def}
            """))
            print(f"  ✅ Added {column_name} to {table_name}")
            return True
        else:
            print(f"  ℹ️ {column_name} already exists in {table_name}")
            return True
    except Exception as e:
        print(f"  ❌ Failed to add {column_name} to {table_name}: {e}")
        return False

async def migrate():
    """Add all missing columns individually"""
    print("🔄 Starting robust migration: Add missing columns")
    
    try:
        async with async_engine.begin() as conn:
            
            # ===== ORDERS TABLE =====
            print("📝 Updating orders table...")
            
            orders_columns = [
                ("time_in_force", "VARCHAR(10) DEFAULT 'gtc'"),
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
                await add_column_if_not_exists(conn, "orders", column_name, column_def)
            
            # ===== POSITIONS TABLE =====
            print("📝 Updating positions table...")
            
            positions_columns = [
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
                await add_column_if_not_exists(conn, "positions", column_name, column_def)
            
            # ===== TRADES TABLE =====
            print("📝 Updating trades table...")
            
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
                await add_column_if_not_exists(conn, "trades", column_name, column_def)
            
            # ===== ACCOUNTS TABLE =====
            print("📝 Updating accounts table...")
            
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
                await add_column_if_not_exists(conn, "accounts", column_name, column_def)
            
            print("🎉 Robust migration completed successfully!")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

async def main():
    """Main migration function"""
    await migrate()

if __name__ == "__main__":
    asyncio.run(main())
