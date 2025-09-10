"""
GiveawayValidator - Input validation utilities for giveaway data
"""

import re
from typing import Dict, List, Optional, Any
from flask import current_app

class GiveawayValidator:
    """Utility class for validating giveaway input data"""
    
    # Validation constants
    MIN_TITLE_LENGTH = 3
    MAX_TITLE_LENGTH = 255
    MIN_BODY_LENGTH = 10
    MAX_BODY_LENGTH = 4000
    MIN_WINNER_COUNT = 1
    MAX_BUTTON_TEXT_LENGTH = 100
    MIN_MESSAGE_LENGTH = 5
    MAX_MESSAGE_LENGTH = 4000
    
    @staticmethod
    def validate_giveaway_creation(data: Dict) -> Dict:
        """
        Validate giveaway creation data
        
        Args:
            data: Dictionary containing giveaway creation data
            
        Returns:
            Dict with validation results
        """
        errors = []
        
        # Required fields
        required_fields = ['account_id', 'title', 'main_body']
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Field '{field}' is required")
            elif isinstance(data[field], str) and not data[field].strip():
                errors.append(f"Field '{field}' cannot be empty")
        
        if errors:
            return {
                'valid': False,
                'errors': errors
            }
        
        # Account ID validation
        account_id_validation = GiveawayValidator.validate_account_id(data['account_id'])
        if not account_id_validation['valid']:
            errors.extend(account_id_validation['errors'])
        
        # Title validation
        title_validation = GiveawayValidator.validate_title(data['title'])
        if not title_validation['valid']:
            errors.extend(title_validation['errors'])
        
        # Main body validation
        body_validation = GiveawayValidator.validate_main_body(data['main_body'])
        if not body_validation['valid']:
            errors.extend(body_validation['errors'])
        
        # Winner count validation (optional, defaults to 1)
        winner_count = data.get('winner_count', 1)
        winner_count_validation = GiveawayValidator.validate_winner_count(winner_count)
        if not winner_count_validation['valid']:
            errors.extend(winner_count_validation['errors'])
        
        # Participation button text validation (optional)
        button_text = data.get('participation_button_text')
        if button_text is not None:
            button_validation = GiveawayValidator.validate_button_text(button_text)
            if not button_validation['valid']:
                errors.extend(button_validation['errors'])
        
        # Media file ID validation (optional)
        media_file_id = data.get('media_file_id')
        if media_file_id is not None:
            media_validation = GiveawayValidator.validate_media_file_id(media_file_id)
            if not media_validation['valid']:
                errors.extend(media_validation['errors'])
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    @staticmethod
    def validate_finish_messages(data: Dict) -> Dict:
        """
        Validate finish messages data
        
        Args:
            data: Dictionary containing finish messages
            
        Returns:
            Dict with validation results
        """
        errors = []
        
        # Required fields
        required_fields = ['public_conclusion_message', 'winner_message', 'loser_message']
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Field '{field}' is required")
            elif not data[field].strip():
                errors.append(f"Field '{field}' cannot be empty")
        
        if errors:
            return {
                'valid': False,
                'errors': errors
            }
        
        # Validate each message
        for field in required_fields:
            message_validation = GiveawayValidator.validate_message_content(data[field])
            if not message_validation['valid']:
                errors.extend([f"{field}: {error}" for error in message_validation['errors']])
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    @staticmethod
    def validate_account_id(account_id: Any) -> Dict:
        """Validate account ID"""
        if not isinstance(account_id, int):
            try:
                account_id = int(account_id)
            except (ValueError, TypeError):
                return {
                    'valid': False,
                    'errors': ['Account ID must be a valid integer']
                }
        
        if account_id <= 0:
            return {
                'valid': False,
                'errors': ['Account ID must be a positive integer']
            }
        
        return {'valid': True, 'errors': []}
    
    @staticmethod
    def validate_title(title: str) -> Dict:
        """Validate giveaway title"""
        if not isinstance(title, str):
            return {
                'valid': False,
                'errors': ['Title must be a string']
            }
        
        title = title.strip()
        
        if len(title) < GiveawayValidator.MIN_TITLE_LENGTH:
            return {
                'valid': False,
                'errors': [f'Title must be at least {GiveawayValidator.MIN_TITLE_LENGTH} characters long']
            }
        
        if len(title) > GiveawayValidator.MAX_TITLE_LENGTH:
            return {
                'valid': False,
                'errors': [f'Title cannot exceed {GiveawayValidator.MAX_TITLE_LENGTH} characters']
            }
        
        return {'valid': True, 'errors': []}
    
    @staticmethod
    def validate_main_body(main_body: str) -> Dict:
        """Validate giveaway main body"""
        if not isinstance(main_body, str):
            return {
                'valid': False,
                'errors': ['Main body must be a string']
            }
        
        main_body = main_body.strip()
        
        if len(main_body) < GiveawayValidator.MIN_BODY_LENGTH:
            return {
                'valid': False,
                'errors': [f'Main body must be at least {GiveawayValidator.MIN_BODY_LENGTH} characters long']
            }
        
        if len(main_body) > GiveawayValidator.MAX_BODY_LENGTH:
            return {
                'valid': False,
                'errors': [f'Main body cannot exceed {GiveawayValidator.MAX_BODY_LENGTH} characters']
            }
        
        return {'valid': True, 'errors': []}
    
    @staticmethod
    def validate_winner_count(winner_count: Any) -> Dict:
        """Validate winner count"""
        if not isinstance(winner_count, int):
            try:
                winner_count = int(winner_count)
            except (ValueError, TypeError):
                return {
                    'valid': False,
                    'errors': ['Winner count must be a valid integer']
                }
        
        if winner_count < GiveawayValidator.MIN_WINNER_COUNT:
            return {
                'valid': False,
                'errors': [f'Winner count must be at least {GiveawayValidator.MIN_WINNER_COUNT}']
            }
        
        max_winner_count = current_app.config.get('MAX_WINNER_COUNT', 100)
        if winner_count > max_winner_count:
            return {
                'valid': False,
                'errors': [f'Winner count cannot exceed {max_winner_count}']
            }
        
        return {'valid': True, 'errors': []}
    
    @staticmethod
    def validate_button_text(button_text: str) -> Dict:
        """Validate participation button text"""
        if not isinstance(button_text, str):
            return {
                'valid': False,
                'errors': ['Button text must be a string']
            }
        
        button_text = button_text.strip()
        
        if not button_text:
            return {
                'valid': False,
                'errors': ['Button text cannot be empty']
            }
        
        if len(button_text) > GiveawayValidator.MAX_BUTTON_TEXT_LENGTH:
            return {
                'valid': False,
                'errors': [f'Button text cannot exceed {GiveawayValidator.MAX_BUTTON_TEXT_LENGTH} characters']
            }
        
        return {'valid': True, 'errors': []}
    
    @staticmethod
    def validate_media_file_id(media_file_id: Any) -> Dict:
        """Validate media file ID"""
        if not isinstance(media_file_id, int):
            try:
                media_file_id = int(media_file_id)
            except (ValueError, TypeError):
                return {
                    'valid': False,
                    'errors': ['Media file ID must be a valid integer']
                }
        
        if media_file_id <= 0:
            return {
                'valid': False,
                'errors': ['Media file ID must be a positive integer']
            }
        
        return {'valid': True, 'errors': []}
    
    @staticmethod
    def validate_message_content(message: str) -> Dict:
        """Validate message content (for finish messages)"""
        if not isinstance(message, str):
            return {
                'valid': False,
                'errors': ['Message must be a string']
            }
        
        message = message.strip()
        
        if len(message) < GiveawayValidator.MIN_MESSAGE_LENGTH:
            return {
                'valid': False,
                'errors': [f'Message must be at least {GiveawayValidator.MIN_MESSAGE_LENGTH} characters long']
            }
        
        if len(message) > GiveawayValidator.MAX_MESSAGE_LENGTH:
            return {
                'valid': False,
                'errors': [f'Message cannot exceed {GiveawayValidator.MAX_MESSAGE_LENGTH} characters']
            }
        
        return {'valid': True, 'errors': []}
    
    @staticmethod
    def validate_result_token(token: str) -> Dict:
        """Validate result token format"""
        if not isinstance(token, str):
            return {
                'valid': False,
                'errors': ['Result token must be a string']
            }
        
        # Token should be alphanumeric and URL-safe
        if not re.match(r'^[A-Za-z0-9_-]+$', token):
            return {
                'valid': False,
                'errors': ['Result token contains invalid characters']
            }
        
        token_length = current_app.config.get('RESULT_TOKEN_LENGTH', 32)
        if len(token) != token_length:
            return {
                'valid': False,
                'errors': [f'Result token must be exactly {token_length} characters long']
            }
        
        return {'valid': True, 'errors': []}
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        Sanitize text input by removing potentially harmful content
        
        Args:
            text: Input text to sanitize
            
        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            return str(text)
        
        # Remove null bytes and control characters (except newlines and tabs)
        sanitized = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        # Trim whitespace
        sanitized = sanitized.strip()
        
        return sanitized

