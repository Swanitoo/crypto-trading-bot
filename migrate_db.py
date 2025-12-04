#!/usr/bin/env python3
"""
Script to migrate database to latest schema.
Adds new tables without losing existing data.
"""

import sys
import logging
from src.database.models import init_db, PaperWallet, BotSession, PriceSnapshot

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def migrate_database():
    """Migrate database to latest schema"""

    logger.info("🔄 Migrating database to latest schema...")

    try:
        # Initialize database (creates missing tables)
        db_session = init_db()

        logger.info("✅ Database migrated successfully!")
        logger.info("   New tables added:")
        logger.info("   - bot_sessions (session tracking)")
        logger.info("   - price_snapshots (price history)")
        logger.info("   - paper_wallet (persistent wallet)")

        # Check if wallet exists
        wallet_count = db_session.query(PaperWallet).count()
        session_count = db_session.query(BotSession).count()
        snapshot_count = db_session.query(PriceSnapshot).count()

        logger.info(f"\n📊 Database statistics:")
        logger.info(f"   Wallet entries: {wallet_count}")
        logger.info(f"   Bot sessions: {session_count}")
        logger.info(f"   Price snapshots: {snapshot_count}")

        db_session.close()

        return True

    except Exception as e:
        logger.error(f"❌ Error migrating database: {e}")
        return False


if __name__ == '__main__':
    logger.info("\n🤖 Database Migration Tool")
    logger.info("=" * 60)

    success = migrate_database()

    if success:
        logger.info("\n✅ Migration complete! You can now start the bot.")
    else:
        logger.info("\n❌ Migration failed. Check the error above.")
        sys.exit(1)
