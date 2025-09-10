"""
ChannelService - Integration with Channel Service
Handles channel permissions and validation
"""

import requests
import logging
from typing import Dict, Optional
from flask import current_app

logger = logging.getLogger(__name__)

class ChannelService:
    """Service for channel permissions and validation"""
    
    @staticmethod
    def get_service_headers() -> Dict[str, str]:
        """Get standard headers for inter-service communication"""
        return {
            'Content-Type': 'application/json',
            'X-Service-Name': 'telegive-giveaway'
        }
    
    @staticmethod
    def get_permissions(account_id: int) -> Dict:
        """
        Get channel permissions for account
        
        Args:
            account_id: Account ID
            
        Returns:
            Dict with permissions info
        """
        try:
            channel_url = current_app.config['TELEGIVE_CHANNEL_URL']
            url = f"{channel_url}/api/channels/{account_id}/permissions"
            
            response = requests.get(
                url,
                headers=ChannelService.get_service_headers(),
                timeout=10
            )
            
            if response.ok:
                data = response.json()
                logger.info(f"Channel permissions for account {account_id} retrieved successfully")
                return data
            else:
                logger.error(f"Channel permissions retrieval failed: {response.status_code}")
                return {
                    'success': False,
                    'error': f'Channel permissions retrieval failed: {response.status_code}',
                    'error_code': 'CHANNEL_PERMISSIONS_FAILED'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Channel service request failed: {e}")
            return {
                'success': False,
                'error': 'Channel service unavailable',
                'error_code': 'CHANNEL_SERVICE_UNAVAILABLE'
            }
        except Exception as e:
            logger.error(f"Unexpected error in channel permissions: {e}")
            return {
                'success': False,
                'error': 'Internal error during channel permissions check',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def can_post_messages(account_id: int) -> bool:
        """
        Check if account can post messages to channel
        
        Args:
            account_id: Account ID
            
        Returns:
            Boolean indicating if posting is allowed
        """
        permissions = ChannelService.get_permissions(account_id)
        
        if not permissions.get('success', False):
            return False
        
        channel_permissions = permissions.get('permissions', {})
        return channel_permissions.get('can_post_messages', False)
    
    @staticmethod
    def can_edit_messages(account_id: int) -> bool:
        """
        Check if account can edit messages in channel
        
        Args:
            account_id: Account ID
            
        Returns:
            Boolean indicating if editing is allowed
        """
        permissions = ChannelService.get_permissions(account_id)
        
        if not permissions.get('success', False):
            return False
        
        channel_permissions = permissions.get('permissions', {})
        return channel_permissions.get('can_edit_messages', False)
    
    @staticmethod
    def get_channel_info(account_id: int) -> Dict:
        """
        Get channel information for account
        
        Args:
            account_id: Account ID
            
        Returns:
            Dict with channel info
        """
        try:
            channel_url = current_app.config['TELEGIVE_CHANNEL_URL']
            url = f"{channel_url}/api/channels/{account_id}"
            
            response = requests.get(
                url,
                headers=ChannelService.get_service_headers(),
                timeout=10
            )
            
            if response.ok:
                data = response.json()
                logger.info(f"Channel info for account {account_id} retrieved successfully")
                return data
            else:
                logger.error(f"Channel info retrieval failed: {response.status_code}")
                return {
                    'success': False,
                    'error': f'Channel info retrieval failed: {response.status_code}',
                    'error_code': 'CHANNEL_INFO_FAILED'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Channel service request failed: {e}")
            return {
                'success': False,
                'error': 'Channel service unavailable',
                'error_code': 'CHANNEL_SERVICE_UNAVAILABLE'
            }
        except Exception as e:
            logger.error(f"Unexpected error in channel info retrieval: {e}")
            return {
                'success': False,
                'error': 'Internal error during channel info retrieval',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def validate_channel_setup(account_id: int) -> Dict:
        """
        Validate that channel is properly set up for giveaways
        
        Args:
            account_id: Account ID
            
        Returns:
            Dict with validation results
        """
        try:
            # Get channel permissions
            permissions_result = ChannelService.get_permissions(account_id)
            if not permissions_result.get('success', False):
                return permissions_result
            
            permissions = permissions_result.get('permissions', {})
            
            # Check required permissions
            required_permissions = ['can_post_messages', 'can_edit_messages']
            missing_permissions = []
            
            for perm in required_permissions:
                if not permissions.get(perm, False):
                    missing_permissions.append(perm)
            
            if missing_permissions:
                return {
                    'success': False,
                    'error': f'Missing required permissions: {", ".join(missing_permissions)}',
                    'error_code': 'INSUFFICIENT_PERMISSIONS',
                    'missing_permissions': missing_permissions
                }
            
            # Get channel info
            channel_info = ChannelService.get_channel_info(account_id)
            if not channel_info.get('success', False):
                return channel_info
            
            return {
                'success': True,
                'permissions': permissions,
                'channel_info': channel_info.get('channel', {})
            }
            
        except Exception as e:
            logger.error(f"Unexpected error in channel validation: {e}")
            return {
                'success': False,
                'error': 'Internal error during channel validation',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def is_service_healthy() -> bool:
        """
        Check if channel service is healthy
        
        Returns:
            Boolean indicating service health
        """
        try:
            channel_url = current_app.config['TELEGIVE_CHANNEL_URL']
            url = f"{channel_url}/health"
            
            response = requests.get(url, timeout=5)
            return response.ok and response.json().get('status') == 'healthy'
            
        except Exception as e:
            logger.error(f"Channel service health check failed: {e}")
            return False

