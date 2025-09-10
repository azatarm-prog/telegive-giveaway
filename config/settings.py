"""
Configuration settings for different environments
"""

import os
import secrets

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://localhost/telegive_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_timeout': 20,
        'pool_recycle': -1,
        'pool_pre_ping': True
    }
    
    # Service URLs
    TELEGIVE_AUTH_URL = os.getenv('TELEGIVE_AUTH_URL', 'http://localhost:8001')
    TELEGIVE_CHANNEL_URL = os.getenv('TELEGIVE_CHANNEL_URL', 'http://localhost:8002')
    TELEGIVE_PARTICIPANT_URL = os.getenv('TELEGIVE_PARTICIPANT_URL', 'http://localhost:8004')
    TELEGIVE_BOT_URL = os.getenv('TELEGIVE_BOT_URL', 'http://localhost:8005')
    TELEGIVE_MEDIA_URL = os.getenv('TELEGIVE_MEDIA_URL', 'http://localhost:8006')
    
    # External APIs
    TELEGRAM_API_BASE = os.getenv('TELEGRAM_API_BASE', 'https://api.telegram.org')
    
    # Application settings
    MAX_WINNER_COUNT = int(os.getenv('MAX_WINNER_COUNT', '100'))
    RESULT_TOKEN_LENGTH = int(os.getenv('RESULT_TOKEN_LENGTH', '32'))
    CLEANUP_DELAY_MINUTES = int(os.getenv('CLEANUP_DELAY_MINUTES', '5'))
    
    # Rate limiting settings
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'memory://')
    RATELIMIT_DEFAULT = "1000 per hour"
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # CORS settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Task scheduler settings
    SCHEDULER_TIMEZONE = os.getenv('SCHEDULER_TIMEZONE', 'UTC')
    ENABLE_CLEANUP_TASKS = os.getenv('ENABLE_CLEANUP_TASKS', 'true').lower() == 'true'
    
    # Health check settings
    HEALTH_CHECK_TIMEOUT = int(os.getenv('HEALTH_CHECK_TIMEOUT', '5'))
    
    @staticmethod
    def init_app(app):
        """Initialize application with this config"""
        pass

class DevelopmentConfig(Config):
    """Development environment configuration"""
    
    DEBUG = True
    TESTING = False
    
    # More verbose logging in development
    LOG_LEVEL = 'DEBUG'
    
    # Shorter cleanup delay for testing
    CLEANUP_DELAY_MINUTES = 1
    
    # Allow all origins in development
    CORS_ORIGINS = ['*']
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Development-specific initialization
        import logging
        logging.basicConfig(level=logging.DEBUG)

class ProductionConfig(Config):
    """Production environment configuration"""
    
    DEBUG = False
    TESTING = False
    
    # Production-specific settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'pool_timeout': 30,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    # Stricter rate limiting in production
    RATELIMIT_DEFAULT = "500 per hour"
    
    # Production logging
    LOG_LEVEL = 'INFO'
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Production-specific initialization
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Set up file logging
        if not app.debug and not app.testing:
            file_handler = RotatingFileHandler(
                'logs/telegive-giveaway.log',
                maxBytes=10240000,  # 10MB
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('Telegive Giveaway Service startup')

class TestingConfig(Config):
    """Testing environment configuration"""
    
    DEBUG = True
    TESTING = True
    
    # Use in-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF protection in testing
    WTF_CSRF_ENABLED = False
    
    # Disable cleanup tasks in testing
    ENABLE_CLEANUP_TASKS = False
    
    # Faster token generation for testing
    RESULT_TOKEN_LENGTH = 16
    
    # No rate limiting in tests
    RATELIMIT_ENABLED = False
    
    # Short timeouts for testing
    HEALTH_CHECK_TIMEOUT = 1
    CLEANUP_DELAY_MINUTES = 0
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Testing-specific initialization
        import logging
        logging.disable(logging.CRITICAL)

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])

