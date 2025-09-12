"""
Giveaway management API routes
"""

from flask import Blueprint, request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
import logging

# Import services and utils (no circular dependency)
from services import AuthService, ChannelService, ParticipantService, BotService, MediaService
from utils import GiveawayValidator, TokenGenerator, StatusManager

logger = logging.getLogger(__name__)

giveaways_bp = Blueprint('giveaways', __name__)

# These will be set by the app after initialization
db = None
limiter = None
Giveaway = None
GiveawayStats = None
GiveawayPublishingLog = None

@giveaways_bp.route('/create', methods=['POST'])
def create_giveaway():
    """
    Create a new giveaway
    POST /api/giveaways/create
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required',
                'error_code': 'MISSING_REQUEST_BODY'
            }), 400
        
        # Validate input data
        validation_result = GiveawayValidator.validate_giveaway_creation(data)
        if not validation_result['valid']:
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'error_code': 'VALIDATION_FAILED',
                'validation_errors': validation_result['errors']
            }), 400
        
        account_id = data['account_id']
        
        # Validate account exists and is active
        logger.info(f"Validating account {account_id} for giveaway creation")
        try:
            account_validation = AuthService.validate_account(account_id)
            logger.info(f"Account validation result: {account_validation}")
            
            if not account_validation.get('success', False):
                logger.warning(f"Account validation failed for {account_id}: {account_validation}")
                return jsonify({
                    'success': False,
                    'error': account_validation.get('error', 'Account validation failed'),
                    'error_code': account_validation.get('error_code', 'ACCOUNT_VALIDATION_FAILED')
                }), 400
        except Exception as e:
            logger.error(f"Exception during account validation for {account_id}: {e}")
            return jsonify({
                'success': False,
                'error': f'Account validation error: {str(e)}',
                'error_code': 'ACCOUNT_VALIDATION_ERROR'
            }), 500
        
        # Check single active giveaway limit
        logger.info(f"Checking for existing active giveaways for account {account_id}")
        try:
            existing_active = Giveaway.query.filter_by(
                account_id=account_id,
                status='active'
            ).first()
            
            if existing_active:
                logger.warning(f"Account {account_id} already has active giveaway {existing_active.id}")
                return jsonify({
                    'success': False,
                    'error': f'Account {account_id} already has an active giveaway',
                    'error_code': 'SINGLE_ACTIVE_LIMIT_EXCEEDED',
                    'details': {
                        'active_giveaway_id': existing_active.id,
                        'account_id': account_id
                    }
                }), 409
        except Exception as e:
            logger.error(f"Database error checking active giveaways for {account_id}: {e}")
            return jsonify({
                'success': False,
                'error': f'Database error: {str(e)}',
                'error_code': 'DATABASE_ERROR'
            }), 500
        
        # Validate media file if provided
        media_file_id = data.get('media_file_id')
        if media_file_id:
            media_validation = MediaService.validate_media_file(media_file_id)
            if not media_validation.get('success', False):
                return jsonify({
                    'success': False,
                    'error': media_validation.get('error', 'Media file validation failed'),
                    'error_code': media_validation.get('error_code', 'MEDIA_VALIDATION_FAILED')
                }), 400
        
        # Generate unique result token
        def check_token_exists(token):
            return Giveaway.query.filter_by(result_token=token).first() is not None
        
        try:
            result_token = TokenGenerator.generate_unique_result_token(check_token_exists)
        except RuntimeError as e:
            logger.error(f"Failed to generate unique token: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to generate unique result token',
                'error_code': 'TOKEN_GENERATION_FAILED'
            }), 500
        
        # Create giveaway
        giveaway = Giveaway(
            account_id=account_id,
            title=GiveawayValidator.sanitize_input(data['title']),
            main_body=GiveawayValidator.sanitize_input(data['main_body']),
            winner_count=data.get('winner_count', 1),
            participation_button_text=GiveawayValidator.sanitize_input(
                data.get('participation_button_text', 'Participate')
            ),
            media_file_id=media_file_id,
            result_token=result_token
        )
        
        db.session.add(giveaway)
        db.session.flush()  # Get the ID
        
        # Create initial stats
        stats = GiveawayStats(giveaway_id=giveaway.id)
        db.session.add(stats)
        
        db.session.commit()
        
        logger.info(f"Giveaway {giveaway.id} created successfully for account {account_id}")
        
        return jsonify({
            'success': True,
            'giveaway': giveaway.to_dict()
        }), 201
        
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Database integrity error in giveaway creation: {e}")
        return jsonify({
            'success': False,
            'error': 'Database constraint violation',
            'error_code': 'INTEGRITY_ERROR'
        }), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error in giveaway creation: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception args: {e.args}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500

@giveaways_bp.route('/active/<int:account_id>', methods=['GET'])
def get_active_giveaway(account_id):
    """
    Get active giveaway for account
    GET /api/giveaways/active/{account_id}
    """
    try:
        # Validate account
        account_validation = AuthService.validate_account(account_id)
        if not account_validation.get('success', False):
            return jsonify({
                'success': False,
                'error': account_validation.get('error', 'Account validation failed'),
                'error_code': account_validation.get('error_code', 'ACCOUNT_VALIDATION_FAILED')
            }), 400
        
        # Get active giveaway
        giveaway = Giveaway.query.filter_by(
            account_id=account_id,
            status='active'
        ).first()
        
        if not giveaway:
            return jsonify({
                'success': False,
                'error': 'No active giveaway found for this account',
                'error_code': 'NO_ACTIVE_GIVEAWAY'
            }), 404
        
        # Get participant count
        participant_count = 0
        if giveaway.message_id:
            participant_stats = ParticipantService.get_participant_count(giveaway.id)
            if participant_stats.get('success', False):
                participant_count = participant_stats.get('total_participants', 0)
        
        giveaway_data = giveaway.to_dict()
        giveaway_data['participant_count'] = participant_count
        
        return jsonify({
            'success': True,
            'giveaway': giveaway_data
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in get active giveaway: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500

@giveaways_bp.route('/<int:giveaway_id>/publish', methods=['POST'])
def publish_giveaway(giveaway_id):
    """
    Publish giveaway to Telegram channel
    POST /api/giveaways/{id}/publish
    """
    try:
        # Get giveaway
        giveaway = Giveaway.query.get(giveaway_id)
        if not giveaway:
            return jsonify({
                'success': False,
                'error': 'Giveaway not found',
                'error_code': 'GIVEAWAY_NOT_FOUND'
            }), 404
        
        # Validate account
        account_validation = AuthService.validate_account(giveaway.account_id)
        if not account_validation.get('success', False):
            return jsonify({
                'success': False,
                'error': account_validation.get('error', 'Account validation failed'),
                'error_code': account_validation.get('error_code', 'ACCOUNT_VALIDATION_FAILED')
            }), 400
        
        # Check if giveaway can be published
        can_publish, error_message = StatusManager.can_publish(giveaway)
        if not can_publish:
            return jsonify({
                'success': False,
                'error': error_message,
                'error_code': 'CANNOT_PUBLISH'
            }), 400
        
        # Validate channel permissions
        channel_validation = ChannelService.validate_channel_setup(giveaway.account_id)
        if not channel_validation.get('success', False):
            return jsonify({
                'success': False,
                'error': channel_validation.get('error', 'Channel validation failed'),
                'error_code': channel_validation.get('error_code', 'CHANNEL_VALIDATION_FAILED')
            }), 400
        
        # Get media file URL if media is attached
        media_url = None
        if giveaway.media_file_id:
            media_result = MediaService.get_media_url(giveaway.media_file_id)
            if media_result.get('success', False):
                media_url = media_result.get('url')
            else:
                logger.warning(f"Failed to get media URL for file {giveaway.media_file_id}")
        
        # Prepare giveaway data for posting
        giveaway_data = giveaway.to_dict(include_sensitive=True)
        if media_url:
            giveaway_data['media_url'] = media_url
        
        # Post giveaway message via Bot Service
        posting_result = BotService.post_giveaway_message(giveaway.account_id, giveaway_data)
        
        # Log publishing attempt
        log_entry = GiveawayPublishingLog.log_publish_attempt(
            giveaway_id=giveaway.id,
            success=posting_result.get('success', False),
            telegram_message_id=posting_result.get('message_id'),
            error_message=posting_result.get('error'),
            response_data=posting_result
        )
        
        if not posting_result.get('success', False):
            db.session.add(log_entry)
            db.session.commit()
            return jsonify({
                'success': False,
                'error': posting_result.get('error', 'Message posting failed'),
                'error_code': posting_result.get('error_code', 'MESSAGE_POSTING_FAILED')
            }), 500
        
        # Update giveaway with message ID and published timestamp
        message_id = posting_result.get('message_id')
        published_at = datetime.now(timezone.utc)
        
        giveaway.mark_published(message_id, published_at)
        
        # Schedule media cleanup if media was used
        media_cleanup_triggered = False
        if giveaway.media_file_id:
            cleanup_result = MediaService.schedule_cleanup(giveaway.media_file_id)
            if cleanup_result.get('success', False):
                giveaway.media_cleanup_status = 'scheduled'
                giveaway.media_cleanup_timestamp = datetime.now(timezone.utc)
                media_cleanup_triggered = True
            else:
                logger.warning(f"Failed to schedule media cleanup for file {giveaway.media_file_id}")
        
        db.session.add(log_entry)
        db.session.commit()
        
        logger.info(f"Giveaway {giveaway.id} published successfully with message ID {message_id}")
        
        return jsonify({
            'success': True,
            'message_id': message_id,
            'published_at': published_at.isoformat(),
            'media_cleanup_triggered': media_cleanup_triggered
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error in giveaway publishing: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500

@giveaways_bp.route('/<int:giveaway_id>/finish-messages', methods=['PUT'])
def update_finish_messages(giveaway_id):
    """
    Update finish messages for giveaway
    PUT /api/giveaways/{id}/finish-messages
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required',
                'error_code': 'MISSING_REQUEST_BODY'
            }), 400
        
        # Get giveaway
        giveaway = Giveaway.query.get(giveaway_id)
        if not giveaway:
            return jsonify({
                'success': False,
                'error': 'Giveaway not found',
                'error_code': 'GIVEAWAY_NOT_FOUND'
            }), 404
        
        # Validate account
        account_validation = AuthService.validate_account(giveaway.account_id)
        if not account_validation.get('success', False):
            return jsonify({
                'success': False,
                'error': account_validation.get('error', 'Account validation failed'),
                'error_code': account_validation.get('error_code', 'ACCOUNT_VALIDATION_FAILED')
            }), 400
        
        # Check if finish messages can be updated
        can_update, error_message = StatusManager.can_update_finish_messages(giveaway)
        if not can_update:
            return jsonify({
                'success': False,
                'error': error_message,
                'error_code': 'CANNOT_UPDATE_FINISH_MESSAGES'
            }), 400
        
        # Validate finish messages
        validation_result = GiveawayValidator.validate_finish_messages(data)
        if not validation_result['valid']:
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'error_code': 'VALIDATION_FAILED',
                'validation_errors': validation_result['errors']
            }), 400
        
        # Update finish messages
        giveaway.set_finish_messages(
            public_conclusion_message=GiveawayValidator.sanitize_input(data['public_conclusion_message']),
            winner_message=GiveawayValidator.sanitize_input(data['winner_message']),
            loser_message=GiveawayValidator.sanitize_input(data['loser_message'])
        )
        
        db.session.commit()
        
        logger.info(f"Finish messages updated for giveaway {giveaway.id}")
        
        return jsonify({
            'success': True,
            'messages_ready': True,
            'finish_button_enabled': True
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error in finish messages update: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500

@giveaways_bp.route('/<int:giveaway_id>/finish', methods=['POST'])
def finish_giveaway(giveaway_id):
    """
    Finish giveaway and select winners
    POST /api/giveaways/{id}/finish
    """
    try:
        # Get giveaway
        giveaway = Giveaway.query.get(giveaway_id)
        if not giveaway:
            return jsonify({
                'success': False,
                'error': 'Giveaway not found',
                'error_code': 'GIVEAWAY_NOT_FOUND'
            }), 404
        
        # Validate account
        account_validation = AuthService.validate_account(giveaway.account_id)
        if not account_validation.get('success', False):
            return jsonify({
                'success': False,
                'error': account_validation.get('error', 'Account validation failed'),
                'error_code': account_validation.get('error_code', 'ACCOUNT_VALIDATION_FAILED')
            }), 400
        
        # Check if giveaway can be finished
        can_finish, error_message = StatusManager.can_finish(giveaway)
        if not can_finish:
            return jsonify({
                'success': False,
                'error': error_message,
                'error_code': 'CANNOT_FINISH'
            }), 400
        
        # Select winners via Participant Service
        winner_selection = ParticipantService.select_winners(giveaway.id, giveaway.winner_count)
        if not winner_selection.get('success', False):
            return jsonify({
                'success': False,
                'error': winner_selection.get('error', 'Winner selection failed'),
                'error_code': winner_selection.get('error_code', 'WINNER_SELECTION_FAILED')
            }), 500
        
        winners = winner_selection.get('winners', [])
        total_participants = winner_selection.get('total_participants', 0)
        
        # Get all participants for bulk messaging
        all_participants = []
        if total_participants > 0:
            participants_result = ParticipantService.get_participants(giveaway.id, page=1, limit=total_participants)
            if participants_result.get('success', False):
                all_participants = participants_result.get('participants', [])
        
        # Send bulk messages to participants
        bulk_messaging_result = BotService.send_bulk_messages(
            account_id=giveaway.account_id,
            giveaway_id=giveaway.id,
            winner_message=giveaway.winner_message,
            loser_message=giveaway.loser_message,
            winners=winners,
            participants=all_participants
        )
        
        messages_delivered = 0
        if bulk_messaging_result.get('success', False):
            messages_delivered = bulk_messaging_result.get('delivered', 0)
        else:
            logger.warning(f"Bulk messaging failed for giveaway {giveaway.id}: {bulk_messaging_result.get('error')}")
        
        # Post conclusion message to channel
        conclusion_result = BotService.post_conclusion_message(
            account_id=giveaway.account_id,
            giveaway_id=giveaway.id,
            conclusion_message=giveaway.public_conclusion_message,
            winners=winners
        )
        
        conclusion_message_id = None
        if conclusion_result.get('success', False):
            conclusion_message_id = conclusion_result.get('message_id')
        else:
            logger.warning(f"Conclusion message posting failed for giveaway {giveaway.id}: {conclusion_result.get('error')}")
        
        # Update giveaway status to finished
        finished_at = datetime.now(timezone.utc)
        giveaway.mark_finished(conclusion_message_id, finished_at)
        
        # Update stats
        stats = GiveawayStats.get_or_create(giveaway.id)
        stats.update_participants(total_participants)
        stats.update_winners(len(winners))
        stats.update_messages_delivered(messages_delivered)
        
        # Log finish attempt
        log_entry = GiveawayPublishingLog.log_finish_attempt(
            giveaway_id=giveaway.id,
            success=True,
            telegram_message_id=conclusion_message_id,
            response_data={
                'winners_selected': len(winners),
                'total_participants': total_participants,
                'messages_delivered': messages_delivered
            }
        )
        db.session.add(log_entry)
        
        db.session.commit()
        
        logger.info(f"Giveaway {giveaway.id} finished successfully with {len(winners)} winners")
        
        return jsonify({
            'success': True,
            'status': 'finished',
            'winners_selected': len(winners),
            'total_participants': total_participants,
            'messages_delivered': messages_delivered,
            'conclusion_message_id': conclusion_message_id,
            'finished_at': finished_at.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error in giveaway finishing: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500


@giveaways_bp.route('/history/<int:account_id>', methods=['GET'])
def get_giveaway_history(account_id):
    """
    Get giveaway history for account
    GET /api/giveaways/history/{account_id}
    """
    try:
        # Validate account
        account_validation = AuthService.validate_account(account_id)
        if not account_validation.get('success', False):
            return jsonify({
                'success': False,
                'error': account_validation.get('error', 'Account validation failed'),
                'error_code': account_validation.get('error_code', 'ACCOUNT_VALIDATION_FAILED')
            }), 400
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 10
        
        # Get giveaways with pagination
        giveaways_query = Giveaway.query.filter_by(account_id=account_id)\
                                       .order_by(Giveaway.created_at.desc())
        
        total_count = giveaways_query.count()
        giveaways = giveaways_query.offset((page - 1) * limit).limit(limit).all()
        
        # Convert to dict and add stats
        giveaway_list = []
        for giveaway in giveaways:
            giveaway_data = giveaway.to_dict()
            
            # Add participant count for finished giveaways
            if giveaway.status == 'finished':
                stats = GiveawayStats.query.filter_by(giveaway_id=giveaway.id).first()
                if stats:
                    giveaway_data['total_participants'] = stats.total_participants
                    giveaway_data['winner_count'] = stats.winner_count
            
            giveaway_list.append(giveaway_data)
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'giveaways': giveaway_list,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'pages': total_pages
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in giveaway history: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500

@giveaways_bp.route('/<int:giveaway_id>/stats', methods=['GET'])
def get_giveaway_stats(giveaway_id):
    """
    Get giveaway statistics
    GET /api/giveaways/{id}/stats
    """
    try:
        # Get giveaway
        giveaway = Giveaway.query.get(giveaway_id)
        if not giveaway:
            return jsonify({
                'success': False,
                'error': 'Giveaway not found',
                'error_code': 'GIVEAWAY_NOT_FOUND'
            }), 404
        
        # Validate account
        account_validation = AuthService.validate_account(giveaway.account_id)
        if not account_validation.get('success', False):
            return jsonify({
                'success': False,
                'error': account_validation.get('error', 'Account validation failed'),
                'error_code': account_validation.get('error_code', 'ACCOUNT_VALIDATION_FAILED')
            }), 400
        
        # Get or create stats
        stats = GiveawayStats.get_or_create(giveaway_id)
        
        # Update participant count if giveaway is active and published
        if giveaway.status == 'active' and giveaway.message_id:
            participant_result = ParticipantService.get_participation_stats(giveaway_id)
            if participant_result.get('success', False):
                participant_stats = participant_result.get('stats', {})
                stats.update_participants(
                    total_participants=participant_stats.get('total_participants', 0),
                    captcha_completed=participant_stats.get('captcha_completed_participants', 0)
                )
                db.session.commit()
        
        return jsonify({
            'success': True,
            'stats': stats.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in giveaway stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500

@giveaways_bp.route('/by-token/<string:result_token>', methods=['GET'])
def get_giveaway_by_token(result_token):
    """
    Get giveaway by result token
    GET /api/giveaways/by-token/{result_token}
    """
    try:
        # Validate token format
        token_validation = GiveawayValidator.validate_result_token(result_token)
        if not token_validation['valid']:
            return jsonify({
                'success': False,
                'error': 'Invalid result token format',
                'error_code': 'INVALID_TOKEN_FORMAT',
                'validation_errors': token_validation['errors']
            }), 400
        
        # Get giveaway by token
        giveaway = Giveaway.query.filter_by(result_token=result_token).first()
        if not giveaway:
            return jsonify({
                'success': False,
                'error': 'Giveaway not found',
                'error_code': 'GIVEAWAY_NOT_FOUND'
            }), 404
        
        # Return basic giveaway info with messages (for bot service)
        giveaway_data = {
            'id': giveaway.id,
            'title': giveaway.title,
            'status': giveaway.status,
            'winner_message': giveaway.winner_message,
            'loser_message': giveaway.loser_message
        }
        
        # Add finish info if giveaway is finished
        if giveaway.status == 'finished':
            giveaway_data['finished_at'] = giveaway.finished_at.isoformat() if giveaway.finished_at else None
            giveaway_data['public_conclusion_message'] = giveaway.public_conclusion_message
        
        return jsonify({
            'success': True,
            'giveaway': giveaway_data
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in get giveaway by token: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500

@giveaways_bp.route('/<int:giveaway_id>', methods=['GET'])
def get_giveaway(giveaway_id):
    """
    Get giveaway details
    GET /api/giveaways/{id}
    """
    try:
        # Get giveaway
        giveaway = Giveaway.query.get(giveaway_id)
        if not giveaway:
            return jsonify({
                'success': False,
                'error': 'Giveaway not found',
                'error_code': 'GIVEAWAY_NOT_FOUND'
            }), 404
        
        # Validate account
        account_validation = AuthService.validate_account(giveaway.account_id)
        if not account_validation.get('success', False):
            return jsonify({
                'success': False,
                'error': account_validation.get('error', 'Account validation failed'),
                'error_code': account_validation.get('error_code', 'ACCOUNT_VALIDATION_FAILED')
            }), 400
        
        # Get giveaway data
        giveaway_data = giveaway.to_dict(include_sensitive=True)
        
        # Add current participant count if published
        if giveaway.message_id:
            participant_result = ParticipantService.get_participant_count(giveaway.id)
            if participant_result.get('success', False):
                giveaway_data['current_participant_count'] = participant_result.get('total_participants', 0)
        
        # Add lifecycle info
        giveaway_data['lifecycle_stage'] = StatusManager.get_giveaway_lifecycle_stage(giveaway)
        giveaway_data['next_actions'] = StatusManager.get_next_actions(giveaway)
        
        return jsonify({
            'success': True,
            'giveaway': giveaway_data
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in get giveaway: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500

@giveaways_bp.route('/<int:giveaway_id>/logs', methods=['GET'])
def get_giveaway_logs(giveaway_id):
    """
    Get giveaway publishing logs
    GET /api/giveaways/{id}/logs
    """
    try:
        # Get giveaway
        giveaway = Giveaway.query.get(giveaway_id)
        if not giveaway:
            return jsonify({
                'success': False,
                'error': 'Giveaway not found',
                'error_code': 'GIVEAWAY_NOT_FOUND'
            }), 404
        
        # Validate account
        account_validation = AuthService.validate_account(giveaway.account_id)
        if not account_validation.get('success', False):
            return jsonify({
                'success': False,
                'error': account_validation.get('error', 'Account validation failed'),
                'error_code': account_validation.get('error_code', 'ACCOUNT_VALIDATION_FAILED')
            }), 400
        
        # Get logs
        limit = request.args.get('limit', 10, type=int)
        if limit < 1 or limit > 50:
            limit = 10
        
        logs = GiveawayPublishingLog.get_recent_logs(giveaway_id, limit)
        
        return jsonify({
            'success': True,
            'logs': [log.to_dict() for log in logs]
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in get giveaway logs: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500

@giveaways_bp.route('/<int:giveaway_id>/validate', methods=['GET'])
def validate_giveaway_state(giveaway_id):
    """
    Validate giveaway state and consistency
    GET /api/giveaways/{id}/validate
    """
    try:
        # Get giveaway
        giveaway = Giveaway.query.get(giveaway_id)
        if not giveaway:
            return jsonify({
                'success': False,
                'error': 'Giveaway not found',
                'error_code': 'GIVEAWAY_NOT_FOUND'
            }), 404
        
        # Validate account
        account_validation = AuthService.validate_account(giveaway.account_id)
        if not account_validation.get('success', False):
            return jsonify({
                'success': False,
                'error': account_validation.get('error', 'Account validation failed'),
                'error_code': account_validation.get('error_code', 'ACCOUNT_VALIDATION_FAILED')
            }), 400
        
        # Validate giveaway state
        validation_result = StatusManager.validate_giveaway_state(giveaway)
        
        return jsonify({
            'success': True,
            'validation': validation_result
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in giveaway validation: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500

# Error handlers for the blueprint
@giveaways_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'error_code': 'BAD_REQUEST'
    }), 400

@giveaways_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Resource not found',
        'error_code': 'NOT_FOUND'
    }), 404

@giveaways_bp.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded',
        'error_code': 'RATE_LIMIT_EXCEEDED'
    }), 429

