#!/usr/bin/env python3
"""
Simple script to delete all positions from the database
This will clear all positions that the frontend displays
"""

import psycopg2
import sys

def delete_all_positions():
    """Delete all positions from the database using raw SQL"""
    
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
        
        # First, check how many positions exist
        cursor.execute("SELECT COUNT(*) FROM positions")
        total_count = cursor.fetchone()[0]
        print(f"📊 Found {total_count} total positions in database")
        
        if total_count == 0:
            print("✅ No positions found. Database is already clean!")
            cursor.close()
            conn.close()
            return True
        
        # Delete all positions
        print("🗑️  Deleting all positions...")
        cursor.execute("DELETE FROM positions")
        deleted_count = cursor.rowcount
        
        # Commit the transaction
        conn.commit()
        
        print(f"✅ Successfully deleted {deleted_count} positions")
        
        # Verify deletion
        cursor.execute("SELECT COUNT(*) FROM positions")
        remaining_count = cursor.fetchone()[0]
        
        if remaining_count == 0:
            print("🎯 All positions have been deleted successfully!")
            print("🎯 Frontend will now show 0 positions")
        else:
            print(f"⚠️  Warning: {remaining_count} positions still remain")
        
        # Close connections
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False
    except Exception as e:
        print(f"❌ Error deleting positions: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
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

