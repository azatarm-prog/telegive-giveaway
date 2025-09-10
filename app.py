"""
Giveaway Management Service - Main Flask Application
Repository: telegive-giveaway
Port: 8003
Purpose: Giveaway creation, publishing, and lifecycle management
"""

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import logging
from datetime import datetime, timezone
import secrets

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://localhost/telegive_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_timeout': 20,
    'pool_recycle': -1,
    'pool_pre_ping': True
}

# Service URLs
app.config['TELEGIVE_AUTH_URL'] = os.getenv('TELEGIVE_AUTH_URL', 'http://localhost:8001')
app.config['TELEGIVE_CHANNEL_URL'] = os.getenv('TELEGIVE_CHANNEL_URL', 'http://localhost:8002')
app.config['TELEGIVE_PARTICIPANT_URL'] = os.getenv('TELEGIVE_PARTICIPANT_URL', 'http://localhost:8004')
app.config['TELEGIVE_BOT_URL'] = os.getenv('TELEGIVE_BOT_URL', 'http://localhost:8005')
app.config['TELEGIVE_MEDIA_URL'] = os.getenv('TELEGIVE_MEDIA_URL', 'http://localhost:8006')

# External APIs
app.config['TELEGRAM_API_BASE'] = os.getenv('TELEGRAM_API_BASE', 'https://api.telegram.org')

# Service configuration
app.config['SERVICE_NAME'] = os.getenv('SERVICE_NAME', 'giveaway-service')
app.config['SERVICE_PORT'] = int(os.getenv('SERVICE_PORT', '8003'))
app.config['MAX_WINNER_COUNT'] = int(os.getenv('MAX_WINNER_COUNT', '100'))
app.config['RESULT_TOKEN_LENGTH'] = int(os.getenv('RESULT_TOKEN_LENGTH', '32'))
app.config['CLEANUP_DELAY_MINUTES'] = int(os.getenv('CLEANUP_DELAY_MINUTES', '5'))

# Initialize extensions
db = SQLAlchemy(app)
CORS(app, origins="*")

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per hour"]
)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create model classes using factory functions
from models.giveaway import create_giveaway_model
from models.giveaway_stats import create_giveaway_stats_model
from models.publishing_log import create_publishing_log_model

# Create model classes with db instance
Giveaway = create_giveaway_model(db)
GiveawayStats = create_giveaway_stats_model(db)
GiveawayPublishingLog = create_publishing_log_model(db)

# Import routes
import routes.giveaways
import routes.health

# Set dependencies in routes to avoid circular imports
routes.giveaways.db = db
routes.giveaways.limiter = limiter
routes.giveaways.Giveaway = Giveaway
routes.giveaways.GiveawayStats = GiveawayStats
routes.giveaways.GiveawayPublishingLog = GiveawayPublishingLog

# Import blueprints after dependencies are set
from routes.giveaways import giveaways_bp
from routes.health import health_bp

# Register blueprints
app.register_blueprint(giveaways_bp, url_prefix='/api/giveaways')
app.register_blueprint(health_bp)

# Apply rate limiting to the giveaways blueprint
limiter.limit("100 per hour")(giveaways_bp)

# Error handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'error_code': 'BAD_REQUEST'
    }), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Resource not found',
        'error_code': 'NOT_FOUND'
    }), 404

@app.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded',
        'error_code': 'RATE_LIMIT_EXCEEDED'
    }), 429

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'error_code': 'INTERNAL_ERROR'
    }), 500

# Request logging middleware
@app.before_request
def log_request():
    logger.info(f"{request.method} {request.path} - {request.remote_addr}")

@app.after_request
def log_response(response):
    logger.info(f"Response: {response.status_code}")
    return response

# Database initialization
def create_tables():
    """Create all database tables"""
    with app.app_context():
        db.create_all()
        logger.info("Database tables created successfully")

if __name__ == '__main__':
    # Get configuration from environment
    port = int(os.getenv('PORT', app.config['SERVICE_PORT']))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Giveaway Management Service on port {port}")
    
    # Run the application
    app.run(
        host='0.0.0.0',  # Listen on all interfaces for deployment
        port=port,
        debug=debug,
        threaded=True
    )

