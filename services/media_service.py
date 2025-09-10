"""
MediaService - Integration with Media Service
Handles file management and media cleanup
"""

import requests
import logging
from typing import Dict, Optional
from flask import current_app

logger = logging.getLogger(__name__)

class MediaService:
    """Service for media file management and cleanup"""
    
    @staticmethod
    def get_service_headers() -> Dict[str, str]:
        """Get standard headers for inter-service communication"""
        return {
            'Content-Type': 'application/json',
            'X-Service-Name': 'telegive-giveaway'
        }
    
    @staticmethod
    def get_media_file(file_id: int) -> Dict:
        """
        Get media file information
        
        Args:
            file_id: Media file ID
            
        Returns:
            Dict with file information
        """
        try:
            media_url = current_app.config['TELEGIVE_MEDIA_URL']
            url = f"{media_url}/api/media/{file_id}"
            
            response = requests.get(
                url,
                headers=MediaService.get_service_headers(),
                timeout=10
            )
            
            if response.ok:
                data = response.json()
                logger.info(f"Media file {file_id} info retrieved successfully")
                return data
            else:
                logger.error(f"Media file retrieval failed: {response.status_code}")
                return {
                    'success': False,
                    'error': f'Media file retrieval failed: {response.status_code}',
                    'error_code': 'MEDIA_FILE_RETRIEVAL_FAILED'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Media service request failed: {e}")
            return {
                'success': False,
                'error': 'Media service unavailable',
                'error_code': 'MEDIA_SERVICE_UNAVAILABLE'
            }
        except Exception as e:
            logger.error(f"Unexpected error in media file retrieval: {e}")
            return {
                'success': False,
                'error': 'Internal error during media file retrieval',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def get_media_url(file_id: int) -> Dict:
        """
        Get media file URL for download/display
        
        Args:
            file_id: Media file ID
            
        Returns:
            Dict with file URL
        """
        try:
            media_url = current_app.config['TELEGIVE_MEDIA_URL']
            url = f"{media_url}/api/media/{file_id}/url"
            
            response = requests.get(
                url,
                headers=MediaService.get_service_headers(),
                timeout=10
            )
            
            if response.ok:
                data = response.json()
                logger.info(f"Media file {file_id} URL retrieved successfully")
                return data
            else:
                logger.error(f"Media URL retrieval failed: {response.status_code}")
                return {
                    'success': False,
                    'error': f'Media URL retrieval failed: {response.status_code}',
                    'error_code': 'MEDIA_URL_RETRIEVAL_FAILED'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Media service request failed: {e}")
            return {
                'success': False,
                'error': 'Media service unavailable',
                'error_code': 'MEDIA_SERVICE_UNAVAILABLE'
            }
        except Exception as e:
            logger.error(f"Unexpected error in media URL retrieval: {e}")
            return {
                'success': False,
                'error': 'Internal error during media URL retrieval',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def schedule_cleanup(file_id: int, delay_minutes: int = None) -> Dict:
        """
        Schedule media file cleanup after giveaway publishing
        
        Args:
            file_id: Media file ID
            delay_minutes: Delay before cleanup (uses config default if None)
            
        Returns:
            Dict with cleanup scheduling results
        """
        try:
            media_url = current_app.config['TELEGIVE_MEDIA_URL']
            url = f"{media_url}/api/media/{file_id}/schedule-cleanup"
            
            payload = {
                'delay_minutes': delay_minutes or current_app.config.get('CLEANUP_DELAY_MINUTES', 5)
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=MediaService.get_service_headers(),
                timeout=10
            )
            
            if response.ok:
                data = response.json()
                logger.info(f"Media file {file_id} cleanup scheduled successfully")
                return data
            else:
                logger.error(f"Media cleanup scheduling failed: {response.status_code}")
                return {
                    'success': False,
                    'error': f'Media cleanup scheduling failed: {response.status_code}',
                    'error_code': 'MEDIA_CLEANUP_SCHEDULING_FAILED'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Media service request failed: {e}")
            return {
                'success': False,
                'error': 'Media service unavailable',
                'error_code': 'MEDIA_SERVICE_UNAVAILABLE'
            }
        except Exception as e:
            logger.error(f"Unexpected error in media cleanup scheduling: {e}")
            return {
                'success': False,
                'error': 'Internal error during media cleanup scheduling',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def cancel_cleanup(file_id: int) -> Dict:
        """
        Cancel scheduled media file cleanup
        
        Args:
            file_id: Media file ID
            
        Returns:
            Dict with cleanup cancellation results
        """
        try:
            media_url = current_app.config['TELEGIVE_MEDIA_URL']
            url = f"{media_url}/api/media/{file_id}/cancel-cleanup"
            
            response = requests.post(
                url,
                headers=MediaService.get_service_headers(),
                timeout=10
            )
            
            if response.ok:
                data = response.json()
                logger.info(f"Media file {file_id} cleanup cancelled successfully")
                return data
            else:
                logger.error(f"Media cleanup cancellation failed: {response.status_code}")
                return {
                    'success': False,
                    'error': f'Media cleanup cancellation failed: {response.status_code}',
                    'error_code': 'MEDIA_CLEANUP_CANCELLATION_FAILED'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Media service request failed: {e}")
            return {
                'success': False,
                'error': 'Media service unavailable',
                'error_code': 'MEDIA_SERVICE_UNAVAILABLE'
            }
        except Exception as e:
            logger.error(f"Unexpected error in media cleanup cancellation: {e}")
            return {
                'success': False,
                'error': 'Internal error during media cleanup cancellation',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def get_cleanup_status(file_id: int) -> Dict:
        """
        Get media file cleanup status
        
        Args:
            file_id: Media file ID
            
        Returns:
            Dict with cleanup status
        """
        try:
            media_url = current_app.config['TELEGIVE_MEDIA_URL']
            url = f"{media_url}/api/media/{file_id}/cleanup-status"
            
            response = requests.get(
                url,
                headers=MediaService.get_service_headers(),
                timeout=10
            )
            
            if response.ok:
                data = response.json()
                logger.info(f"Media file {file_id} cleanup status retrieved")
                return data
            else:
                logger.error(f"Media cleanup status retrieval failed: {response.status_code}")
                return {
                    'success': False,
                    'error': f'Media cleanup status retrieval failed: {response.status_code}',
                    'error_code': 'MEDIA_CLEANUP_STATUS_FAILED'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Media service request failed: {e}")
            return {
                'success': False,
                'error': 'Media service unavailable',
                'error_code': 'MEDIA_SERVICE_UNAVAILABLE'
            }
        except Exception as e:
            logger.error(f"Unexpected error in media cleanup status: {e}")
            return {
                'success': False,
                'error': 'Internal error during media cleanup status retrieval',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def validate_media_file(file_id: int) -> Dict:
        """
        Validate that media file exists and is accessible
        
        Args:
            file_id: Media file ID
            
        Returns:
            Dict with validation results
        """
        try:
            file_info = MediaService.get_media_file(file_id)
            
            if not file_info.get('success', False):
                return file_info
            
            # Additional validation checks can be added here
            file_data = file_info.get('file', {})
            
            if not file_data.get('accessible', True):
                return {
                    'success': False,
                    'error': 'Media file is not accessible',
                    'error_code': 'MEDIA_FILE_NOT_ACCESSIBLE'
                }
            
            return {
                'success': True,
                'file': file_data,
                'validated': True
            }
            
        except Exception as e:
            logger.error(f"Unexpected error in media file validation: {e}")
            return {
                'success': False,
                'error': 'Internal error during media file validation',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def is_service_healthy() -> bool:
        """
        Check if media service is healthy
        
        Returns:
            Boolean indicating service health
        """
        try:
            media_url = current_app.config['TELEGIVE_MEDIA_URL']
            url = f"{media_url}/health"
            
            response = requests.get(url, timeout=5)
            return response.ok and response.json().get('status') == 'healthy'
            
        except Exception as e:
            logger.error(f"Media service health check failed: {e}")
            return False

