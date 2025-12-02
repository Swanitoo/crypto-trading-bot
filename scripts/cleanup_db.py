#!/usr/bin/env python3
"""
Script to cleanup orphaned trades in the database
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database.models import init_db, Trade
from datetime import datetime

def cleanup_orphaned_trades():
    """Close all orphaned trades that are still marked as 'open' but have no active position"""
    db_session = init_db()

    try:
        # Get all open trades
        open_trades = db_session.query(Trade).filter(Trade.status == 'open').all()

        print(f"🔍 Found {len(open_trades)} open trades in database")

        if len(open_trades) == 0:
            print("✅ No orphaned trades to clean up")
            return

        # Display all open trades
        print("\n📊 Open trades:")
        for trade in open_trades:
            print(f"  - ID {trade.id}: {trade.pair} | Side: {trade.side} | Price: ${trade.price:.2f} | Time: {trade.timestamp}")

        # Ask for confirmation
        print(f"\n⚠️  This will close all {len(open_trades)} open trades with P&L = $0.00")
        confirm = input("Continue? (yes/no): ").lower().strip()

        if confirm != 'yes':
            print("❌ Cleanup cancelled")
            return

        # Close all orphaned trades
        closed_count = 0
        for trade in open_trades:
            trade.status = 'closed'
            trade.profit_loss = 0.0
            trade.profit_loss_percent = 0.0
            trade.notes = f"{trade.notes or ''} | Auto-closed: Orphaned trade (bot restart)".strip()
            closed_count += 1

        db_session.commit()

        print(f"\n✅ Successfully closed {closed_count} orphaned trades")

    except Exception as e:
        print(f"❌ Error cleaning up database: {e}")
        db_session.rollback()
    finally:
        db_session.close()

if __name__ == "__main__":
    print("🧹 Database Cleanup Tool\n")
    cleanup_orphaned_trades()
