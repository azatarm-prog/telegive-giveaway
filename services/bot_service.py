"""
BotService - Integration with Bot Service
Handles Telegram message posting and delivery
"""

import requests
import logging
from typing import Dict, List, Optional
from flask import current_app

logger = logging.getLogger(__name__)

class BotService:
    """Service for Telegram bot operations and message delivery"""
    
    @staticmethod
    def get_service_headers() -> Dict[str, str]:
        """Get standard headers for inter-service communication"""
        return {
            'Content-Type': 'application/json',
            'X-Service-Name': 'telegive-giveaway'
        }
    
    @staticmethod
    def post_giveaway_message(account_id: int, giveaway_data: Dict) -> Dict:
        """
        Post giveaway message to Telegram channel
        
        Args:
            account_id: Account ID
            giveaway_data: Giveaway data for the message
            
        Returns:
            Dict with posting results
        """
        try:
            bot_url = current_app.config['TELEGIVE_BOT_URL']
            url = f"{bot_url}/api/messages/giveaway"
            
            payload = {
                'account_id': account_id,
                'giveaway_id': giveaway_data.get('id'),
                'main_body': giveaway_data.get('main_body'),
                'winner_count': giveaway_data.get('winner_count'),
                'participation_button_text': giveaway_data.get('participation_button_text', 'Participate'),
                'result_token': giveaway_data.get('result_token'),
                'media_file_id': giveaway_data.get('media_file_id')
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=BotService.get_service_headers(),
                timeout=30
            )
            
            if response.ok:
                data = response.json()
                logger.info(f"Giveaway message posted for account {account_id}: message_id {data.get('message_id')}")
                return data
            else:
                logger.error(f"Giveaway message posting failed: {response.status_code}")
                return {
                    'success': False,
                    'error': f'Message posting failed: {response.status_code}',
                    'error_code': 'MESSAGE_POSTING_FAILED'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Bot service request failed: {e}")
            return {
                'success': False,
                'error': 'Bot service unavailable',
                'error_code': 'BOT_SERVICE_UNAVAILABLE'
            }
        except Exception as e:
            logger.error(f"Unexpected error in message posting: {e}")
            return {
                'success': False,
                'error': 'Internal error during message posting',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def post_conclusion_message(account_id: int, giveaway_id: int, conclusion_message: str, winners: List[Dict]) -> Dict:
        """
        Post giveaway conclusion message to Telegram channel
        
        Args:
            account_id: Account ID
            giveaway_id: Giveaway ID
            conclusion_message: Public conclusion message
            winners: List of winners
            
        Returns:
            Dict with posting results
        """
        try:
            bot_url = current_app.config['TELEGIVE_BOT_URL']
            url = f"{bot_url}/api/messages/conclusion"
            
            payload = {
                'account_id': account_id,
                'giveaway_id': giveaway_id,
                'conclusion_message': conclusion_message,
                'winners': winners
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=BotService.get_service_headers(),
                timeout=30
            )
            
            if response.ok:
                data = response.json()
                logger.info(f"Conclusion message posted for giveaway {giveaway_id}: message_id {data.get('message_id')}")
                return data
            else:
                logger.error(f"Conclusion message posting failed: {response.status_code}")
                return {
                    'success': False,
                    'error': f'Conclusion message posting failed: {response.status_code}',
                    'error_code': 'CONCLUSION_POSTING_FAILED'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Bot service request failed: {e}")
            return {
                'success': False,
                'error': 'Bot service unavailable',
                'error_code': 'BOT_SERVICE_UNAVAILABLE'
            }
        except Exception as e:
            logger.error(f"Unexpected error in conclusion posting: {e}")
            return {
                'success': False,
                'error': 'Internal error during conclusion posting',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def send_bulk_messages(account_id: int, giveaway_id: int, winner_message: str, loser_message: str, 
                          winners: List[Dict], participants: List[Dict]) -> Dict:
        """
        Send bulk messages to participants (winners and losers)
        
        Args:
            account_id: Account ID
            giveaway_id: Giveaway ID
            winner_message: Message for winners
            loser_message: Message for losers
            winners: List of winners
            participants: List of all participants
            
        Returns:
            Dict with delivery results
        """
        try:
            bot_url = current_app.config['TELEGIVE_BOT_URL']
            url = f"{bot_url}/api/messages/bulk"
            
            payload = {
                'account_id': account_id,
                'giveaway_id': giveaway_id,
                'winner_message': winner_message,
                'loser_message': loser_message,
                'winners': winners,
                'participants': participants
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=BotService.get_service_headers(),
                timeout=120  # Bulk messaging might take longer
            )
            
            if response.ok:
                data = response.json()
                logger.info(f"Bulk messages sent for giveaway {giveaway_id}: {data.get('delivered', 0)} delivered")
                return data
            else:
                logger.error(f"Bulk message sending failed: {response.status_code}")
                return {
                    'success': False,
                    'error': f'Bulk message sending failed: {response.status_code}',
                    'error_code': 'BULK_MESSAGING_FAILED'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Bot service request failed: {e}")
            return {
                'success': False,
                'error': 'Bot service unavailable',
                'error_code': 'BOT_SERVICE_UNAVAILABLE'
            }
        except Exception as e:
            logger.error(f"Unexpected error in bulk messaging: {e}")
            return {
                'success': False,
                'error': 'Internal error during bulk messaging',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def send_individual_message(account_id: int, user_id: int, message: str) -> Dict:
        """
        Send individual message to a user
        
        Args:
            account_id: Account ID
            user_id: User ID to send message to
            message: Message content
            
        Returns:
            Dict with sending results
        """
        try:
            bot_url = current_app.config['TELEGIVE_BOT_URL']
            url = f"{bot_url}/api/messages/individual"
            
            payload = {
                'account_id': account_id,
                'user_id': user_id,
                'message': message
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=BotService.get_service_headers(),
                timeout=10
            )
            
            if response.ok:
                data = response.json()
                logger.info(f"Individual message sent to user {user_id}")
                return data
            else:
                logger.error(f"Individual message sending failed: {response.status_code}")
                return {
                    'success': False,
                    'error': f'Individual message sending failed: {response.status_code}',
                    'error_code': 'INDIVIDUAL_MESSAGING_FAILED'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Bot service request failed: {e}")
            return {
                'success': False,
                'error': 'Bot service unavailable',
                'error_code': 'BOT_SERVICE_UNAVAILABLE'
            }
        except Exception as e:
            logger.error(f"Unexpected error in individual messaging: {e}")
            return {
                'success': False,
                'error': 'Internal error during individual messaging',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def get_message_info(account_id: int, message_id: int) -> Dict:
        """
        Get information about a posted message
        
        Args:
            account_id: Account ID
            message_id: Telegram message ID
            
        Returns:
            Dict with message information
        """
        try:
            bot_url = current_app.config['TELEGIVE_BOT_URL']
            url = f"{bot_url}/api/messages/{account_id}/{message_id}"
            
            response = requests.get(
                url,
                headers=BotService.get_service_headers(),
                timeout=10
            )
            
            if response.ok:
                data = response.json()
                logger.info(f"Message info retrieved for message {message_id}")
                return data
            else:
                logger.error(f"Message info retrieval failed: {response.status_code}")
                return {
                    'success': False,
                    'error': f'Message info retrieval failed: {response.status_code}',
                    'error_code': 'MESSAGE_INFO_FAILED'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Bot service request failed: {e}")
            return {
                'success': False,
                'error': 'Bot service unavailable',
                'error_code': 'BOT_SERVICE_UNAVAILABLE'
            }
        except Exception as e:
            logger.error(f"Unexpected error in message info retrieval: {e}")
            return {
                'success': False,
                'error': 'Internal error during message info retrieval',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def is_service_healthy() -> bool:
        """
        Check if bot service is healthy
        
        Returns:
            Boolean indicating service health
        """
        try:
            bot_url = current_app.config['TELEGIVE_BOT_URL']
            url = f"{bot_url}/health"
            
            response = requests.get(url, timeout=5)
            return response.ok and response.json().get('status') == 'healthy'
            
        except Exception as e:
            logger.error(f"Bot service health check failed: {e}")
            return False

