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
            'X-Service-Name': 'telegive-giveaway',
            'X-Service-Token': 'ch4nn3l_s3rv1c3_t0k3n_2025_s3cur3_r4nd0m_str1ng'
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
            # Use the correct Auth Service URL and endpoint
            auth_url = current_app.config.get('TELEGIVE_AUTH_URL', 'https://web-production-ddd7e.up.railway.app')
            url = f"{auth_url}/api/v1/bots/validate/{account_id}"
            
            logger.info(f"Validating account {account_id} at {url}")
            
            response = requests.get(
                url,
                headers=AuthService.get_service_headers(),
                timeout=10
            )
            
            if response.ok:
                data = response.json()
                logger.info(f"Account {account_id} validation successful: {data}")
                
                # Handle the correct response format from Auth Service
                if data.get('valid', False):
                    return {
                        'success': True,
                        'valid': True,
                        'account_id': data.get('bot_id'),
                        'username': data.get('bot_username'),
                        'name': data.get('bot_name')
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Account is not valid',
                        'error_code': 'ACCOUNT_INVALID'
                    }
            elif response.status_code == 404:
                logger.warning(f"Account {account_id} not found")
                return {
                    'success': False,
                    'error': 'Account not found',
                    'error_code': 'ACCOUNT_NOT_FOUND'
                }
            elif response.status_code == 403:
                logger.warning(f"Account {account_id} is inactive")
                return {
                    'success': False,
                    'error': 'Account inactive',
                    'error_code': 'ACCOUNT_INACTIVE'
                }
            else:
                logger.error(f"Account {account_id} validation failed: {response.status_code} - {response.text}")
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
            # Use the correct Auth Service URL
            auth_url = current_app.config.get('TELEGIVE_AUTH_URL', 'https://web-production-ddd7e.up.railway.app')
            url = f"{auth_url}/health"
            
            response = requests.get(url, timeout=5)
            if response.ok:
                # Try to get JSON response, fallback to status code check
                try:
                    data = response.json()
                    return data.get('status') == 'healthy' or data.get('alive', False)
                except:
                    return True  # If no JSON, but 200 OK, consider healthy
            return False
            
        except Exception as e:
            logger.error(f"Auth service health check failed: {e}")
            return False

