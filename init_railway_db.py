#!/usr/bin/env python3
"""
Initialize Railway database remotely
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Railway database URL (from the deployment)
RAILWAY_DATABASE_URL = "postgresql://postgres:bNOtOvVTlHjQFCKGHGJJGKhYGKJLOqNe@junction.proxy.rlwy.net:31543/railway"

def create_tables():
    """Create tables directly using SQL DDL"""
    
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
    
    try:
        # Create engine
        engine = create_engine(RAILWAY_DATABASE_URL)
        
        with engine.connect() as conn:
            # Create tables
            logger.info("Creating giveaways table...")
            conn.execute(text(create_giveaways_table))
            
            logger.info("Creating giveaway_stats table...")
            conn.execute(text(create_stats_table))
            
            logger.info("Creating giveaway_publishing_log table...")
            conn.execute(text(create_log_table))
            
            # Create indexes
            logger.info("Creating indexes...")
            for index_sql in create_indexes:
                conn.execute(text(index_sql))
            
            # Commit changes
            conn.commit()
            
            logger.info("Database tables created successfully!")
            
            # Test the connection
            result = conn.execute(text("SELECT COUNT(*) FROM giveaways"))
            count = result.scalar()
            logger.info(f"Giveaways table is accessible, current count: {count}")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

if __name__ == '__main__':
    create_tables()

