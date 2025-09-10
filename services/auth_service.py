"""
AuthService - Integration with Authentication Service
Handles account validation and authentication
"""

import requests
import logging
from typing import Dict, Optional
from flask import current_app

logger = logging.getLogger(__name__)

class AuthService:
    """Service for authentication and account validation"""
    
    @staticmethod
    def get_service_headers() -> Dict[str, str]:
        """Get standard headers for inter-service communication"""
        return {
            'Content-Type': 'application/json',
            'X-Service-Name': 'telegive-giveaway'
        }
    
    @staticmethod
    def validate_account(account_id: int) -> Dict:
        """
        Validate account exists and is active
        
        Args:
            account_id: Account ID to validate
            
        Returns:
            Dict with success status and account info
        """
        try:
            auth_url = current_app.config['TELEGIVE_AUTH_URL']
            url = f"{auth_url}/api/accounts/{account_id}/validate"
            
            response = requests.get(
                url,
                headers=AuthService.get_service_headers(),
                timeout=10
            )
            
            if response.ok:
                data = response.json()
                logger.info(f"Account {account_id} validation successful")
                return data
            else:
                logger.error(f"Account {account_id} validation failed: {response.status_code}")
                return {
                    'success': False,
                    'error': f'Account validation failed: {response.status_code}',
                    'error_code': 'ACCOUNT_VALIDATION_FAILED'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Auth service request failed: {e}")
            return {
                'success': False,
                'error': 'Auth service unavailable',
                'error_code': 'AUTH_SERVICE_UNAVAILABLE'
            }
        except Exception as e:
            logger.error(f"Unexpected error in account validation: {e}")
            return {
                'success': False,
                'error': 'Internal error during account validation',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def get_account_info(account_id: int) -> Dict:
        """
        Get detailed account information
        
        Args:
            account_id: Account ID
            
        Returns:
            Dict with account information
        """
        try:
            auth_url = current_app.config['TELEGIVE_AUTH_URL']
            url = f"{auth_url}/api/accounts/{account_id}"
            
            response = requests.get(
                url,
                headers=AuthService.get_service_headers(),
                timeout=10
            )
            
            if response.ok:
                data = response.json()
                logger.info(f"Account {account_id} info retrieved successfully")
                return data
            else:
                logger.error(f"Account {account_id} info retrieval failed: {response.status_code}")
                return {
                    'success': False,
                    'error': f'Account info retrieval failed: {response.status_code}',
                    'error_code': 'ACCOUNT_INFO_FAILED'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Auth service request failed: {e}")
            return {
                'success': False,
                'error': 'Auth service unavailable',
                'error_code': 'AUTH_SERVICE_UNAVAILABLE'
            }
        except Exception as e:
            logger.error(f"Unexpected error in account info retrieval: {e}")
            return {
                'success': False,
                'error': 'Internal error during account info retrieval',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def check_account_permissions(account_id: int, permission: str) -> Dict:
        """
        Check if account has specific permission
        
        Args:
            account_id: Account ID
            permission: Permission to check
            
        Returns:
            Dict with permission status
        """
        try:
            auth_url = current_app.config['TELEGIVE_AUTH_URL']
            url = f"{auth_url}/api/accounts/{account_id}/permissions/{permission}"
            
            response = requests.get(
                url,
                headers=AuthService.get_service_headers(),
                timeout=10
            )
            
            if response.ok:
                data = response.json()
                logger.info(f"Account {account_id} permission {permission} check successful")
                return data
            else:
                logger.error(f"Account {account_id} permission check failed: {response.status_code}")
                return {
                    'success': False,
                    'error': f'Permission check failed: {response.status_code}',
                    'error_code': 'PERMISSION_CHECK_FAILED'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Auth service request failed: {e}")
            return {
                'success': False,
                'error': 'Auth service unavailable',
                'error_code': 'AUTH_SERVICE_UNAVAILABLE'
            }
        except Exception as e:
            logger.error(f"Unexpected error in permission check: {e}")
            return {
                'success': False,
                'error': 'Internal error during permission check',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def is_service_healthy() -> bool:
        """
        Check if auth service is healthy
        
        Returns:
            Boolean indicating service health
        """
        try:
            auth_url = current_app.config['TELEGIVE_AUTH_URL']
            url = f"{auth_url}/health"
            
            response = requests.get(url, timeout=5)
            return response.ok and response.json().get('status') == 'healthy'
            
        except Exception as e:
            logger.error(f"Auth service health check failed: {e}")
            return False

