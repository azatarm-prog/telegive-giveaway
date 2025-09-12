"""
Debug route for giveaway creation to identify the exact error
"""

from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
import logging
import traceback

# Import services and utils
from services import AuthService
from utils import GiveawayValidator, TokenGenerator

logger = logging.getLogger(__name__)

debug_giveaway_bp = Blueprint('debug_giveaway', __name__)

# These will be set by the app after initialization
db = None
Giveaway = None
GiveawayStats = None

@debug_giveaway_bp.route('/debug/create-giveaway', methods=['POST'])
def debug_create_giveaway():
    """
    Debug version of giveaway creation with detailed error reporting
    """
    debug_info = {
        'step': 'initialization',
        'error': None,
        'traceback': None,
        'data_received': None,
        'validation_result': None,
        'auth_result': None,
        'token_generated': None,
        'model_created': None,
        'db_operation': None
    }
    
    try:
        # Step 1: Get request data
        debug_info['step'] = 'getting_request_data'
        data = request.get_json()
        debug_info['data_received'] = data
        
        if not data:
            debug_info['error'] = 'No request data received'
            return jsonify({
                'success': False,
                'error': 'Request body is required',
                'debug_info': debug_info
            }), 400
        
        # Step 2: Validate input data
        debug_info['step'] = 'validation'
        validation_result = GiveawayValidator.validate_giveaway_creation(data)
        debug_info['validation_result'] = validation_result
        
        if not validation_result['valid']:
            debug_info['error'] = 'Validation failed'
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'validation_errors': validation_result['errors'],
                'debug_info': debug_info
            }), 400
        
        account_id = data['account_id']
        
        # Step 3: Validate account
        debug_info['step'] = 'auth_validation'
        try:
            account_validation = AuthService.validate_account(account_id)
            debug_info['auth_result'] = account_validation
            
            if not account_validation.get('success', False):
                debug_info['error'] = 'Account validation failed'
                return jsonify({
                    'success': False,
                    'error': account_validation.get('error', 'Account validation failed'),
                    'debug_info': debug_info
                }), 400
        except Exception as e:
            debug_info['error'] = f'Auth service exception: {str(e)}'
            debug_info['traceback'] = traceback.format_exc()
            return jsonify({
                'success': False,
                'error': f'Account validation error: {str(e)}',
                'debug_info': debug_info
            }), 500
        
        # Step 4: Check for existing active giveaways
        debug_info['step'] = 'checking_existing_giveaways'
        try:
            existing_active = Giveaway.query.filter_by(
                account_id=account_id,
                status='active'
            ).first()
            
            if existing_active:
                debug_info['error'] = 'Active giveaway already exists'
                return jsonify({
                    'success': False,
                    'error': f'Account {account_id} already has an active giveaway',
                    'debug_info': debug_info
                }), 409
        except Exception as e:
            debug_info['error'] = f'Database query exception: {str(e)}'
            debug_info['traceback'] = traceback.format_exc()
            return jsonify({
                'success': False,
                'error': f'Database error: {str(e)}',
                'debug_info': debug_info
            }), 500
        
        # Step 5: Generate unique result token
        debug_info['step'] = 'token_generation'
        try:
            def check_token_exists(token):
                return Giveaway.query.filter_by(result_token=token).first() is not None
            
            result_token = TokenGenerator.generate_unique_result_token(check_token_exists)
            debug_info['token_generated'] = result_token
        except Exception as e:
            debug_info['error'] = f'Token generation exception: {str(e)}'
            debug_info['traceback'] = traceback.format_exc()
            return jsonify({
                'success': False,
                'error': f'Failed to generate unique result token: {str(e)}',
                'debug_info': debug_info
            }), 500
        
        # Step 6: Create giveaway model
        debug_info['step'] = 'model_creation'
        try:
            giveaway = Giveaway(
                account_id=account_id,
                title=GiveawayValidator.sanitize_input(data['title']),
                main_body=GiveawayValidator.sanitize_input(data['main_body']),
                winner_count=data.get('winner_count', 1),
                participation_button_text=GiveawayValidator.sanitize_input(
                    data.get('participation_button_text', 'Participate')
                ),
                media_file_id=data.get('media_file_id'),
                result_token=result_token
            )
            debug_info['model_created'] = True
        except Exception as e:
            debug_info['error'] = f'Model creation exception: {str(e)}'
            debug_info['traceback'] = traceback.format_exc()
            return jsonify({
                'success': False,
                'error': f'Model creation error: {str(e)}',
                'debug_info': debug_info
            }), 500
        
        # Step 7: Database operations
        debug_info['step'] = 'database_operations'
        try:
            db.session.add(giveaway)
            db.session.flush()  # Get the ID
            debug_info['db_operation'] = 'giveaway_added_and_flushed'
            
            # Create initial stats
            stats = GiveawayStats(giveaway_id=giveaway.id)
            db.session.add(stats)
            debug_info['db_operation'] = 'stats_added'
            
            db.session.commit()
            debug_info['db_operation'] = 'committed'
            
        except Exception as e:
            db.session.rollback()
            debug_info['error'] = f'Database operation exception: {str(e)}'
            debug_info['traceback'] = traceback.format_exc()
            return jsonify({
                'success': False,
                'error': f'Database operation error: {str(e)}',
                'debug_info': debug_info
            }), 500
        
        # Success!
        debug_info['step'] = 'success'
        return jsonify({
            'success': True,
            'giveaway': giveaway.to_dict(),
            'debug_info': debug_info
        }), 201
        
    except Exception as e:
        if db:
            db.session.rollback()
        debug_info['error'] = f'Unexpected exception: {str(e)}'
        debug_info['traceback'] = traceback.format_exc()
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}',
            'debug_info': debug_info
        }), 500

