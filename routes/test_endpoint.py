"""
Test endpoint to isolate Auth Service integration issues
"""

from flask import Blueprint, jsonify, request, current_app
from services.auth_service import AuthService
import logging

logger = logging.getLogger(__name__)

test_bp = Blueprint('test', __name__)

@test_bp.route('/test/auth/<int:account_id>', methods=['GET'])
def test_auth_integration(account_id):
    """Simple test endpoint to check Auth Service integration"""
    try:
        logger.info(f"Testing Auth Service integration for account {account_id}")
        
        # Get the Auth Service URL from config
        auth_url = current_app.config.get('TELEGIVE_AUTH_URL', 'NOT_SET')
        logger.info(f"Auth Service URL: {auth_url}")
        
        # Test the AuthService.validate_account method
        result = AuthService.validate_account(account_id)
        logger.info(f"Auth validation result: {result}")
        
        return jsonify({
            'success': True,
            'test_account_id': account_id,
            'auth_service_url': auth_url,
            'validation_result': result,
            'message': 'Auth Service integration test completed'
        }), 200
        
    except Exception as e:
        logger.error(f"Test endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'test_account_id': account_id
        }), 500

@test_bp.route('/test/config', methods=['GET'])
def test_config():
    """Test endpoint to check configuration"""
    try:
        config_info = {
            'TELEGIVE_AUTH_URL': current_app.config.get('TELEGIVE_AUTH_URL'),
            'TELEGIVE_CHANNEL_URL': current_app.config.get('TELEGIVE_CHANNEL_URL'),
            'TELEGIVE_BOT_URL': current_app.config.get('TELEGIVE_BOT_URL'),
            'TELEGIVE_PARTICIPANT_URL': current_app.config.get('TELEGIVE_PARTICIPANT_URL'),
            'TELEGIVE_MEDIA_URL': current_app.config.get('TELEGIVE_MEDIA_URL'),
            'SERVICE_NAME': current_app.config.get('SERVICE_NAME'),
            'SERVICE_PORT': current_app.config.get('SERVICE_PORT'),
            'DATABASE_URL': 'SET' if current_app.config.get('SQLALCHEMY_DATABASE_URI') else 'NOT_SET'
        }
        
        return jsonify({
            'success': True,
            'config': config_info,
            'message': 'Configuration check completed'
        }), 200
        
    except Exception as e:
        logger.error(f"Config test error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

