"""
Debug routes for testing Auth Service integration
"""

from flask import Blueprint, jsonify, current_app
import requests
import logging

logger = logging.getLogger(__name__)

debug_bp = Blueprint('debug', __name__)

@debug_bp.route('/debug/auth-config', methods=['GET'])
def debug_auth_config():
    """Debug endpoint to check Auth Service configuration"""
    try:
        auth_url = current_app.config.get('TELEGIVE_AUTH_URL', 'NOT_SET')
        
        return jsonify({
            'auth_service_url': auth_url,
            'config_keys': list(current_app.config.keys()),
            'environment_check': {
                'TELEGIVE_AUTH_URL': auth_url
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

@debug_bp.route('/debug/auth-test/<int:account_id>', methods=['GET'])
def debug_auth_test(account_id):
    """Debug endpoint to test Auth Service directly"""
    try:
        auth_url = current_app.config.get('TELEGIVE_AUTH_URL', 'https://web-production-ddd7e.up.railway.app')
        test_url = f"{auth_url}/api/v1/bots/validate/{account_id}"
        
        logger.info(f"Testing Auth Service at: {test_url}")
        
        response = requests.get(
            test_url,
            headers={
                'Content-Type': 'application/json',
                'X-Service-Name': 'telegive-giveaway'
            },
            timeout=10
        )
        
        return jsonify({
            'test_url': test_url,
            'status_code': response.status_code,
            'response_headers': dict(response.headers),
            'response_body': response.text,
            'response_json': response.json() if response.headers.get('content-type', '').startswith('application/json') else None
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'error_type': type(e).__name__,
            'test_url': test_url if 'test_url' in locals() else 'URL_NOT_SET'
        }), 500

@debug_bp.route('/debug/auth-validate/<int:account_id>', methods=['GET'])
def debug_auth_validate(account_id):
    """Debug endpoint to test the AuthService.validate_account method"""
    try:
        from services.auth_service import AuthService
        
        result = AuthService.validate_account(account_id)
        
        return jsonify({
            'account_id': account_id,
            'validation_result': result,
            'auth_service_url': current_app.config.get('TELEGIVE_AUTH_URL')
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'error_type': type(e).__name__,
            'account_id': account_id
        }), 500

