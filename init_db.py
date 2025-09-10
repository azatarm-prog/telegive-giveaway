"""
Database initialization script for Giveaway Management Service
"""

from app import app, db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize the database with all tables and constraints"""
    try:
        with app.app_context():
            # Create all tables
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Create custom indexes and constraints if needed
            # (Most are handled by the model definitions)
            
            logger.info("Database initialization completed successfully")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

def drop_database():
    """Drop all database tables (for development/testing)"""
    try:
        with app.app_context():
            db.drop_all()
            logger.info("Database tables dropped successfully")
            
    except Exception as e:
        logger.error(f"Database drop failed: {e}")
        raise

def reset_database():
    """Reset the database (drop and recreate)"""
    try:
        drop_database()
        init_database()
        logger.info("Database reset completed successfully")
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        raise

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'init':
            init_database()
        elif command == 'drop':
            drop_database()
        elif command == 'reset':
            reset_database()
        else:
            print("Usage: python init_db.py [init|drop|reset]")
            sys.exit(1)
    else:
        # Default action
        init_database()

