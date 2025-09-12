"""
Debug endpoint for giveaway creation
"""

from flask import Blueprint, request, jsonify, current_app
import logging
from services import AuthService
from utils import GiveawayValidator, TokenGenerator
from models import Giveaway, GiveawayStats
from app import db

logger = logging.getLogger(__name__)

debug_create_bp = Blueprint('debug_create', __name__)

@debug_create_bp.route('/debug/create-step-by-step', methods=['POST'])
def debug_create_giveaway():
    """Debug giveaway creation step by step"""
    try:
        # Step 1: Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'step': 'request_data',
                'success': False,
                'error': 'No request data'
            }), 400
        
        logger.info(f"Step 1 - Request data: {data}")
        
        # Step 2: Validate input
        validation_result = GiveawayValidator.validate_giveaway_creation(data)
        if not validation_result['valid']:
            return jsonify({
                'step': 'input_validation',
                'success': False,
                'error': validation_result['errors']
            }), 400
        
        logger.info("Step 2 - Input validation: PASSED")
        
        # Step 3: Account validation
        account_id = data['account_id']
        try:
            account_validation = AuthService.validate_account(account_id)
            logger.info(f"Step 3 - Account validation result: {account_validation}")
            
            if not account_validation.get('success', False):
                return jsonify({
                    'step': 'account_validation',
                    'success': False,
                    'error': account_validation.get('error', 'Account validation failed')
                }), 400
        except Exception as e:
            logger.error(f"Step 3 - Account validation exception: {e}")
            return jsonify({
                'step': 'account_validation',
                'success': False,
                'error': f'Account validation error: {str(e)}'
            }), 500
        
        logger.info("Step 3 - Account validation: PASSED")
        
        # Step 4: Check existing giveaways
        try:
            existing_active = Giveaway.query.filter_by(
                account_id=account_id,
                status='active'
            ).first()
            
            if existing_active:
                return jsonify({
                    'step': 'existing_giveaway_check',
                    'success': False,
                    'error': f'Account already has active giveaway: {existing_active.id}'
                }), 409
        except Exception as e:
            logger.error(f"Step 4 - Database query exception: {e}")
            return jsonify({
                'step': 'existing_giveaway_check',
                'success': False,
                'error': f'Database query error: {str(e)}'
            }), 500
        
        logger.info("Step 4 - Existing giveaway check: PASSED")
        
        # Step 5: Generate token
        try:
            result_token = TokenGenerator.generate_result_token()
            logger.info(f"Step 5 - Generated token: {result_token}")
        except Exception as e:
            logger.error(f"Step 5 - Token generation exception: {e}")
            return jsonify({
                'step': 'token_generation',
                'success': False,
                'error': f'Token generation error: {str(e)}'
            }), 500
        
        logger.info("Step 5 - Token generation: PASSED")
        
        # Step 6: Create giveaway object (without saving)
        try:
            giveaway = Giveaway(
                account_id=account_id,
                title=GiveawayValidator.sanitize_input(data['title']),
                main_body=GiveawayValidator.sanitize_input(data['main_body']),
                winner_count=data.get('winner_count', 1),
                participation_button_text=GiveawayValidator.sanitize_input(
                    data.get('participation_button_text', 'Participate')
                ),
                media_file_id=None,  # Skip media for debug
                result_token=result_token
            )
            logger.info("Step 6 - Giveaway object created")
        except Exception as e:
            logger.error(f"Step 6 - Giveaway object creation exception: {e}")
            return jsonify({
                'step': 'giveaway_object_creation',
                'success': False,
                'error': f'Giveaway object creation error: {str(e)}'
            }), 500
        
        logger.info("Step 6 - Giveaway object creation: PASSED")
        
        # Step 7: Database operations
        try:
            db.session.add(giveaway)
            db.session.flush()  # Get the ID
            logger.info(f"Step 7a - Giveaway added to session, ID: {giveaway.id}")
            
            # Create initial stats
            stats = GiveawayStats(giveaway_id=giveaway.id)
            db.session.add(stats)
            logger.info("Step 7b - Stats object added to session")
            
            db.session.commit()
            logger.info("Step 7c - Database commit successful")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Step 7 - Database operation exception: {e}")
            return jsonify({
                'step': 'database_operations',
                'success': False,
                'error': f'Database operation error: {str(e)}'
            }), 500
        
        logger.info("Step 7 - Database operations: PASSED")
        
        return jsonify({
            'success': True,
            'message': 'All steps completed successfully',
            'giveaway_id': giveaway.id,
            'steps_completed': [
                'request_data',
                'input_validation', 
                'account_validation',
                'existing_giveaway_check',
                'token_generation',
                'giveaway_object_creation',
                'database_operations'
            ]
        }), 201
        
    except Exception as e:
        logger.error(f"Unexpected error in debug create: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'step': 'unexpected_error',
            'success': False,
            'error': f'Unexpected error: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500

