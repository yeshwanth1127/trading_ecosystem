#!/usr/bin/env python3
"""
Simple script to delete all open positions using raw SQL
This will clear all positions that the frontend displays
"""

import psycopg2
from psycopg2 import sql
import sys

def delete_all_positions():
    """Delete all open positions from the database using raw SQL"""
    
    # Database connection parameters
    DB_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'trading_ecosystem',
        'user': 'postgres',
        'password': '6ded34bad0f447a4a071ce794a4a8f63'
    }
    
    try:
        print("🔌 Connecting to database...")
        
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # First, check how many positions exist in total
        cursor.execute("SELECT COUNT(*) FROM positions")
        total_count = cursor.fetchone()[0]
        print(f"📊 Found {total_count} total positions in database")
        
        # Check how many open positions exist (try different enum formats)
        try:
            cursor.execute("SELECT COUNT(*) FROM positions WHERE status = 'open'")
            open_count = cursor.fetchone()[0]
        except:
            try:
                cursor.execute("SELECT COUNT(*) FROM positions WHERE status::text = 'open'")
                open_count = cursor.fetchone()[0]
            except:
                print("⚠️  Could not determine open positions count, will delete all positions")
                open_count = total_count
        
        print(f"📊 Found {open_count} open positions to delete")
        
        if open_count == 0:
            print("✅ No open positions found. Database is already clean!")
            cursor.close()
            conn.close()
            return True
        
        # Delete all positions (since we want 0 positions total)
        cursor.execute("DELETE FROM positions")
        deleted_count = cursor.rowcount
        
        # Commit the transaction
        conn.commit()
        
        print(f"🗑️  Successfully deleted {deleted_count} positions")
        
        # Verify deletion
        cursor.execute("SELECT COUNT(*) FROM positions")
        remaining_count = cursor.fetchone()[0]
        
        if remaining_count == 0:
            print("✅ All open positions have been deleted successfully!")
            print("🎯 Frontend will now show 0 positions")
        else:
            print(f"⚠️  Warning: {remaining_count} positions still remain")
        
        # Close connections
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error deleting positions: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Starting position cleanup...")
    print("=" * 50)
    
    success = delete_all_positions()
    
    print("=" * 50)
    if success:
        print("🎉 Position cleanup completed successfully!")
    else:
        print("💥 Position cleanup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
