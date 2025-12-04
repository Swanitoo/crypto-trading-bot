#!/usr/bin/env python3
"""
Script to reset the paper trading wallet to initial balance.
"""

import sys
import logging
from src.database.models import init_db, PaperWallet, Trade, Balance

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def reset_wallet(initial_balance: float = 100.0, confirm: bool = True):
    """Reset paper wallet to initial balance"""

    if confirm:
        logger.warning("⚠️  WARNING: This will reset your paper trading wallet!")
        logger.warning("   - All crypto balances will be cleared")
        logger.warning("   - USDT balance will be reset to initial amount")
        logger.warning(f"   - Initial balance: {initial_balance} USDT")
        logger.warning("")
        response = input("   Are you sure you want to continue? (yes/no): ")

        if response.lower() not in ['yes', 'y']:
            logger.info("❌ Operation cancelled")
            return False

    # Initialize database
    db_session = init_db()

    try:
        # Delete all wallet entries
        deleted = db_session.query(PaperWallet).delete()
        logger.info(f"🗑️  Deleted {deleted} wallet entries")

        # Create new USDT entry
        usdt_entry = PaperWallet(
            currency='USDT',
            balance=initial_balance,
            initial_balance=initial_balance
        )
        db_session.add(usdt_entry)
        db_session.commit()

        logger.info(f"✅ Paper wallet reset successfully!")
        logger.info(f"   New balance: {initial_balance} USDT")

        # Show statistics
        open_trades = db_session.query(Trade).filter(Trade.status == 'open').count()
        closed_trades = db_session.query(Trade).filter(Trade.status == 'closed').count()

        if open_trades > 0:
            logger.warning(f"\n⚠️  WARNING: You have {open_trades} open trade(s) in the database")
            logger.warning("   These positions may cause issues since the wallet has been reset")
            logger.warning("   Consider closing them manually or resetting the entire database")

        logger.info(f"\n📊 Database statistics:")
        logger.info(f"   Open trades: {open_trades}")
        logger.info(f"   Closed trades: {closed_trades}")

        return True

    except Exception as e:
        logger.error(f"❌ Error resetting wallet: {e}")
        db_session.rollback()
        return False

    finally:
        db_session.close()


def reset_all_data(confirm: bool = True):
    """Reset all data including trades, balances, and wallet"""

    if confirm:
        logger.warning("⚠️⚠️⚠️  DANGER: This will delete ALL data!")
        logger.warning("   - All trades (open and closed)")
        logger.warning("   - All balance snapshots")
        logger.warning("   - All AI analysis history")
        logger.warning("   - Paper trading wallet")
        logger.warning("   - Bot sessions")
        logger.warning("   - Price snapshots")
        logger.warning("")
        response = input("   Type 'DELETE ALL' to confirm: ")

        if response != 'DELETE ALL':
            logger.info("❌ Operation cancelled")
            return False

    # Initialize database
    db_session = init_db()

    try:
        from src.database.models import AIAnalysis, BotSession, PriceSnapshot

        # Delete everything
        deleted_trades = db_session.query(Trade).delete()
        deleted_balances = db_session.query(Balance).delete()
        deleted_ai = db_session.query(AIAnalysis).delete()
        deleted_wallet = db_session.query(PaperWallet).delete()
        deleted_sessions = db_session.query(BotSession).delete()
        deleted_snapshots = db_session.query(PriceSnapshot).delete()

        db_session.commit()

        logger.info("✅ All data deleted successfully!")
        logger.info(f"   Trades: {deleted_trades}")
        logger.info(f"   Balances: {deleted_balances}")
        logger.info(f"   AI Analysis: {deleted_ai}")
        logger.info(f"   Wallet: {deleted_wallet}")
        logger.info(f"   Sessions: {deleted_sessions}")
        logger.info(f"   Price snapshots: {deleted_snapshots}")

        return True

    except Exception as e:
        logger.error(f"❌ Error resetting data: {e}")
        db_session.rollback()
        return False

    finally:
        db_session.close()


def show_wallet_info():
    """Show current wallet information"""
    db_session = init_db()

    try:
        wallet_entries = db_session.query(PaperWallet).all()

        if not wallet_entries:
            logger.info("💰 Paper wallet is empty (not initialized yet)")
            return

        logger.info("\n💰 Current paper wallet:")
        logger.info("=" * 60)

        total_value = 0.0

        for entry in wallet_entries:
            logger.info(f"   {entry.currency}: {entry.balance:.8f}")

            if entry.currency == 'USDT':
                total_value += entry.balance
                if entry.initial_balance > 0:
                    logger.info(f"      Initial: {entry.initial_balance:.2f} USDT")
                    pnl = entry.balance - entry.initial_balance
                    pnl_percent = (pnl / entry.initial_balance) * 100
                    logger.info(f"      P&L: {pnl:+.2f} USDT ({pnl_percent:+.2f}%)")

        logger.info("=" * 60)
        logger.info(f"   Total value: ~{total_value:.2f} USDT")

        # Show open positions
        open_trades = db_session.query(Trade).filter(Trade.status == 'open').count()
        closed_trades = db_session.query(Trade).filter(Trade.status == 'closed').count()

        logger.info(f"\n📊 Trading statistics:")
        logger.info(f"   Open trades: {open_trades}")
        logger.info(f"   Closed trades: {closed_trades}")

    except Exception as e:
        logger.error(f"❌ Error fetching wallet info: {e}")

    finally:
        db_session.close()


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Manage paper trading wallet')
    parser.add_argument('action', choices=['reset', 'info', 'reset-all'],
                        help='Action to perform')
    parser.add_argument('--amount', type=float, default=100.0,
                        help='Initial balance for reset (default: 100 USDT)')
    parser.add_argument('--yes', action='store_true',
                        help='Skip confirmation prompt')

    args = parser.parse_args()

    logger.info("\n🤖 Paper Trading Wallet Manager")
    logger.info("=" * 60)

    if args.action == 'info':
        show_wallet_info()

    elif args.action == 'reset':
        reset_wallet(initial_balance=args.amount, confirm=not args.yes)

    elif args.action == 'reset-all':
        if reset_all_data(confirm=not args.yes):
            logger.info("\n💰 Initializing fresh wallet...")
            reset_wallet(initial_balance=args.amount, confirm=False)

    logger.info("")


if __name__ == '__main__':
    main()
