"""
Health check routes for the Giveaway Management Service
"""

from flask import Blueprint, jsonify
from app import db
from services import AuthService, ChannelService, ParticipantService, BotService, MediaService
import logging

logger = logging.getLogger(__name__)

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    Returns service health status and external service connectivity
    """
    try:
        # Check database connectivity
        db_status = 'connected'
        try:
            db.session.execute('SELECT 1')
            db.session.commit()
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_status = 'disconnected'
        
        # Check external services
        external_services = {
            'auth_service': 'accessible' if AuthService.is_service_healthy() else 'inaccessible',
            'channel_service': 'accessible' if ChannelService.is_service_healthy() else 'inaccessible',
            'participant_service': 'accessible' if ParticipantService.is_service_healthy() else 'inaccessible',
            'bot_service': 'accessible' if BotService.is_service_healthy() else 'inaccessible',
            'media_service': 'accessible' if MediaService.is_service_healthy() else 'inaccessible'
        }
        
        # Determine overall health status
        overall_status = 'healthy'
        if db_status != 'connected':
            overall_status = 'unhealthy'
        elif any(status == 'inaccessible' for status in external_services.values()):
            overall_status = 'degraded'
        
        response = {
            'status': overall_status,
            'service': 'telegive-giveaway',
            'version': '1.0.0',
            'database': db_status,
            'external_services': external_services
        }
        
        # Return appropriate HTTP status code
        if overall_status == 'healthy':
            return jsonify(response), 200
        elif overall_status == 'degraded':
            return jsonify(response), 200  # Still operational
        else:
            return jsonify(response), 503  # Service unavailable
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'service': 'telegive-giveaway',
            'version': '1.0.0',
            'error': 'Health check failed',
            'database': 'unknown',
            'external_services': {}
        }), 503

@health_bp.route('/health/database', methods=['GET'])
def database_health():
    """
    Database-specific health check
    """
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        db.session.commit()
        
        # Test table access
        from models import Giveaway
        giveaway_count = Giveaway.query.count()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'giveaway_count': giveaway_count
        }), 200
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 503

@health_bp.route('/health/services', methods=['GET'])
def services_health():
    """
    External services health check
    """
    try:
        services_status = {}
        
        # Check each service
        services = {
            'auth_service': AuthService,
            'channel_service': ChannelService,
            'participant_service': ParticipantService,
            'bot_service': BotService,
            'media_service': MediaService
        }
        
        for service_name, service_class in services.items():
            try:
                is_healthy = service_class.is_service_healthy()
                services_status[service_name] = {
                    'status': 'accessible' if is_healthy else 'inaccessible',
                    'healthy': is_healthy
                }
            except Exception as e:
                logger.error(f"{service_name} health check failed: {e}")
                services_status[service_name] = {
                    'status': 'error',
                    'healthy': False,
                    'error': str(e)
                }
        
        # Determine overall status
        all_healthy = all(service['healthy'] for service in services_status.values())
        overall_status = 'healthy' if all_healthy else 'degraded'
        
        return jsonify({
            'status': overall_status,
            'services': services_status
        }), 200
        
    except Exception as e:
        logger.error(f"Services health check failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@health_bp.route('/health/ready', methods=['GET'])
def readiness_check():
    """
    Readiness check - indicates if service is ready to handle requests
    """
    try:
        # Check critical dependencies
        ready = True
        issues = []
        
        # Database must be accessible
        try:
            db.session.execute('SELECT 1')
            db.session.commit()
        except Exception as e:
            ready = False
            issues.append(f"Database not accessible: {e}")
        
        # Auth service must be accessible (critical for account validation)
        if not AuthService.is_service_healthy():
            ready = False
            issues.append("Auth service not accessible")
        
        if ready:
            return jsonify({
                'ready': True,
                'status': 'ready'
            }), 200
        else:
            return jsonify({
                'ready': False,
                'status': 'not_ready',
                'issues': issues
            }), 503
            
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return jsonify({
            'ready': False,
            'status': 'error',
            'error': str(e)
        }), 503

@health_bp.route('/health/live', methods=['GET'])
def liveness_check():
    """
    Liveness check - indicates if service is alive and responding
    """
    try:
        return jsonify({
            'alive': True,
            'status': 'alive',
            'service': 'telegive-giveaway'
        }), 200
        
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return jsonify({
            'alive': False,
            'status': 'error',
            'error': str(e)
        }), 500

