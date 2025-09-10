"""
Admin routes for database management and maintenance
"""

from flask import Blueprint, jsonify, request
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

# These will be set by the app after initialization
db = None

@admin_bp.route('/admin/init-db', methods=['POST'])
def init_database():
    """
    Initialize database tables
    This endpoint creates all necessary tables if they don't exist
    """
    try:
        # SQL to create the giveaways table
        create_giveaways_table = """
        CREATE TABLE IF NOT EXISTS giveaways (
            id BIGSERIAL PRIMARY KEY,
            account_id BIGINT NOT NULL,
            title VARCHAR(255) NOT NULL,
            main_body TEXT NOT NULL,
            winner_count INTEGER DEFAULT 1,
            participation_button_text VARCHAR(100) DEFAULT 'Participate',
            public_conclusion_message TEXT,
            winner_message TEXT,
            loser_message TEXT,
            messages_ready_for_finish BOOLEAN DEFAULT FALSE,
            status VARCHAR(20) DEFAULT 'active',
            message_id BIGINT,
            conclusion_message_id BIGINT,
            result_token VARCHAR(64) UNIQUE,
            media_file_id BIGINT,
            media_cleanup_status VARCHAR(20) DEFAULT 'pending',
            media_cleanup_timestamp TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            published_at TIMESTAMPTZ,
            finished_at TIMESTAMPTZ,
            CONSTRAINT check_status CHECK (status IN ('active', 'finished'))
        );
        """
        
        # SQL to create the giveaway_stats table
        create_stats_table = """
        CREATE TABLE IF NOT EXISTS giveaway_stats (
            id BIGSERIAL PRIMARY KEY,
            giveaway_id BIGINT NOT NULL REFERENCES giveaways(id) ON DELETE CASCADE,
            total_participants INTEGER DEFAULT 0,
            unique_participants INTEGER DEFAULT 0,
            winners_selected INTEGER DEFAULT 0,
            last_updated TIMESTAMPTZ DEFAULT NOW()
        );
        """
        
        # SQL to create the giveaway_publishing_log table
        create_log_table = """
        CREATE TABLE IF NOT EXISTS giveaway_publishing_log (
            id BIGSERIAL PRIMARY KEY,
            giveaway_id BIGINT NOT NULL REFERENCES giveaways(id) ON DELETE CASCADE,
            action VARCHAR(50) NOT NULL,
            telegram_message_id BIGINT,
            success BOOLEAN NOT NULL,
            error_message TEXT,
            response_data JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
        
        # Create indexes
        create_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_giveaways_account_id ON giveaways(account_id);",
            "CREATE INDEX IF NOT EXISTS idx_giveaways_status ON giveaways(status);",
            "CREATE INDEX IF NOT EXISTS idx_giveaways_created_at ON giveaways(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_giveaway_stats_giveaway_id ON giveaway_stats(giveaway_id);",
            "CREATE INDEX IF NOT EXISTS idx_giveaway_publishing_log_giveaway_id ON giveaway_publishing_log(giveaway_id);",
            "CREATE INDEX IF NOT EXISTS idx_giveaway_publishing_log_created_at ON giveaway_publishing_log(created_at);"
        ]
        
        # Execute table creation
        logger.info("Creating giveaways table...")
        db.session.execute(text(create_giveaways_table))
        
        logger.info("Creating giveaway_stats table...")
        db.session.execute(text(create_stats_table))
        
        logger.info("Creating giveaway_publishing_log table...")
        db.session.execute(text(create_log_table))
        
        # Create indexes
        logger.info("Creating indexes...")
        for index_sql in create_indexes:
            db.session.execute(text(index_sql))
        
        # Commit changes
        db.session.commit()
        
        logger.info("Database tables created successfully!")
        
        # Test the tables
        result = db.session.execute(text("SELECT COUNT(*) FROM giveaways"))
        giveaway_count = result.scalar()
        
        result = db.session.execute(text("SELECT COUNT(*) FROM giveaway_stats"))
        stats_count = result.scalar()
        
        result = db.session.execute(text("SELECT COUNT(*) FROM giveaway_publishing_log"))
        log_count = result.scalar()
        
        return jsonify({
            'success': True,
            'message': 'Database tables created successfully',
            'tables': {
                'giveaways': giveaway_count,
                'giveaway_stats': stats_count,
                'giveaway_publishing_log': log_count
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/admin/db-status', methods=['GET'])
def database_status():
    """
    Check database status and existing tables
    """
    try:
        # Check if tables exist
        tables_info = {}
        
        table_names = ['giveaways', 'giveaway_stats', 'giveaway_publishing_log']
        
        for table_name in table_names:
            try:
                result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                tables_info[table_name] = {'exists': True, 'count': count}
            except Exception as e:
                tables_info[table_name] = {'exists': False, 'error': str(e)}
        
        return jsonify({
            'database_connected': True,
            'tables': tables_info
        }), 200
        
    except Exception as e:
        logger.error(f"Database status check failed: {e}")
        return jsonify({
            'database_connected': False,
            'error': str(e)
        }), 500

