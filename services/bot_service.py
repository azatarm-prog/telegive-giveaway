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
            'X-Service-Name': 'telegive-giveaway',
            'X-Service-Token': 'ch4nn3l_s3rv1c3_t0k3n_2025_s3cur3_r4nd0m_str1ng'
        }
    
    @staticmethod
    def get_bot_token(account_id: int) -> Dict:
        """
        Get bot token for account from Auth Service
        
        Args:
            account_id: Account ID
            
        Returns:
            Dict with bot token or error
        """
        try:
            # Use Auth Service to get bot token
            auth_url = current_app.config.get('TELEGIVE_AUTH_URL', 'https://web-production-ddd7e.up.railway.app')
            url = f"{auth_url}/api/accounts/{account_id}"
            
            logger.info(f"Getting bot token for account {account_id} from {url}")
            
            response = requests.get(
                url,
                headers=BotService.get_service_headers(),
                timeout=10
            )
            
            logger.info(f"Auth Service response status: {response.status_code}")
            
            if response.ok:
                data = response.json()
                
                # Extract the account from the response (actual format)
                account = data.get('account', {})
                if account:
                    bot_token = account.get('bot_token')
                    
                    if bot_token:
                        logger.info(f"Bot token retrieved successfully for account {account_id}")
                        return {
                            'success': True,
                            'bot_token': bot_token,
                            'bot_id': account.get('bot_id'),
                            'username': account.get('username')
                        }
                    else:
                        logger.warning(f"No bot token found for account {account_id}")
                        return {
                            'success': False,
                            'error': 'Bot token not found for account',
                            'error_code': 'BOT_TOKEN_NOT_FOUND'
                        }
                else:
                    logger.warning(f"No account data found for account {account_id}")
                    return {
                        'success': False,
                        'error': 'Account data not found',
                        'error_code': 'ACCOUNT_DATA_NOT_FOUND'
                    }
            elif response.status_code == 404:
                logger.warning(f"Account {account_id} not found in Auth Service")
                return {
                    'success': False,
                    'error': 'Account not found',
                    'error_code': 'ACCOUNT_NOT_FOUND'
                }
            else:
                error_text = response.text
                logger.error(f"Bot token retrieval failed: {response.status_code} - {error_text}")
                return {
                    'success': False,
                    'error': f'Auth Service error: {response.status_code}',
                    'error_code': 'AUTH_SERVICE_ERROR'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Auth service request failed: {e}")
            return {
                'success': False,
                'error': 'Auth service unavailable',
                'error_code': 'AUTH_SERVICE_UNAVAILABLE'
            }
        except Exception as e:
            logger.error(f"Unexpected error in bot token retrieval: {e}")
            return {
                'success': False,
                'error': 'Internal error during bot token retrieval',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def post_to_telegram_direct(bot_token: str, chat_id: str, message: str, reply_markup: Optional[Dict] = None) -> Dict:
        """
        Post message directly to Telegram using bot token
        
        Args:
            bot_token: Telegram bot token
            chat_id: Chat ID or channel username (e.g., @channelname)
            message: Message text
            reply_markup: Optional inline keyboard markup
            
        Returns:
            Dict with posting results
        """
        try:
            telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            if reply_markup:
                payload['reply_markup'] = reply_markup
            
            logger.info(f"Posting message to Telegram: chat_id={chat_id}, message_length={len(message)}")
            
            response = requests.post(
                telegram_url,
                json=payload,
                timeout=30
            )
            
            result = response.json()
            
            logger.info(f"Telegram API response: ok={result.get('ok')}, message_id={result.get('result', {}).get('message_id')}")
            
            if result.get('ok'):
                message_data = result.get('result', {})
                return {
                    'success': True,
                    'message_id': message_data.get('message_id'),
                    'date': message_data.get('date'),
                    'chat': message_data.get('chat', {}),
                    'telegram_response': result
                }
            else:
                error_description = result.get('description', 'Unknown Telegram API error')
                logger.error(f"Telegram API error: {error_description}")
                return {
                    'success': False,
                    'error': f'Telegram API error: {error_description}',
                    'error_code': 'TELEGRAM_API_ERROR',
                    'telegram_response': result
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Telegram API request failed: {e}")
            return {
                'success': False,
                'error': 'Telegram API unavailable',
                'error_code': 'TELEGRAM_API_UNAVAILABLE'
            }
        except Exception as e:
            logger.error(f"Unexpected error in Telegram posting: {e}")
            return {
                'success': False,
                'error': 'Internal error during Telegram posting',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def post_giveaway_message(account_id: int, giveaway_data: Dict) -> Dict:
        """
        Post giveaway message to Telegram channel using direct API
        
        Args:
            account_id: Account ID
            giveaway_data: Giveaway data for the message
            
        Returns:
            Dict with posting results
        """
        try:
            logger.info(f"🚀 Publishing giveaway {giveaway_data.get('id')} for account {account_id}")
            
            # 1. Get bot token from Auth Service
            token_result = BotService.get_bot_token(account_id)
            if not token_result.get('success'):
                logger.error(f"Failed to get bot token: {token_result.get('error')}")
                return token_result
            
            bot_token = token_result.get('bot_token')
            logger.info(f"✅ Bot token retrieved for account {account_id}")
            
            # 2. Get channel configuration (we need the channel username)
            from .channel_service import ChannelService
            channel_result = ChannelService.get_channel_config(account_id)
            if not channel_result.get('success'):
                logger.error(f"Failed to get channel config: {channel_result.get('error')}")
                return {
                    'success': False,
                    'error': 'Channel configuration failed',
                    'error_code': 'CHANNEL_CONFIG_FAILED'
                }
            
            channel_config = channel_result.get('config', {})
            channel_username = channel_config.get('username')
            if not channel_username:
                logger.error("Channel username not found in config")
                return {
                    'success': False,
                    'error': 'Channel username not found',
                    'error_code': 'CHANNEL_USERNAME_MISSING'
                }
            
            logger.info(f"✅ Channel config retrieved: {channel_username}")
            
            # 3. Create giveaway message
            message = BotService.create_giveaway_message(giveaway_data)
            
            # 4. Create inline keyboard for participation
            reply_markup = {
                'inline_keyboard': [[
                    {
                        'text': giveaway_data.get('participation_button_text', '🎁 Join Giveaway'),
                        'url': f"https://t.me/your_bot?start=join_{giveaway_data.get('result_token', giveaway_data.get('id'))}"
                    }
                ]]
            }
            
            # 5. Post to Telegram
            result = BotService.post_to_telegram_direct(
                bot_token=bot_token,
                chat_id=channel_username,
                message=message,
                reply_markup=reply_markup
            )
            
            if result.get('success'):
                logger.info(f"✅ Giveaway message posted successfully: message_id {result.get('message_id')}")
                return {
                    'success': True,
                    'message_id': result.get('message_id'),
                    'channel_username': channel_username,
                    'telegram_url': f"https://t.me/{channel_username.replace('@', '')}/{result.get('message_id')}",
                    'telegram_response': result.get('telegram_response')
                }
            else:
                logger.error(f"❌ Telegram posting failed: {result.get('error')}")
                return result
                
        except Exception as e:
            logger.error(f"Unexpected error in giveaway message posting: {e}")
            return {
                'success': False,
                'error': 'Internal error during giveaway message posting',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def create_giveaway_message(giveaway_data: Dict) -> str:
        """
        Create formatted giveaway message for Telegram
        
        Args:
            giveaway_data: Giveaway data
            
        Returns:
            Formatted message string
        """
        title = giveaway_data.get('title', 'Giveaway')
        main_body = giveaway_data.get('main_body', '')
        winner_count = giveaway_data.get('winner_count', 1)
        
        # Format the message
        message = f"🎁 <b>{title}</b>\n\n"
        
        if main_body:
            message += f"{main_body}\n\n"
        
        message += f"🏆 <b>Winners:</b> {winner_count}\n"
        message += f"⏰ <b>Status:</b> Active\n\n"
        message += "Click the button below to join the giveaway!"
        
        return message
    
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
        Check if auth service is healthy (for bot token access)
        
        Returns:
            Boolean indicating service health
        """
        try:
            # Check Auth Service health since we get bot tokens from there
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

