"""
TokenGenerator - Utility for generating secure tokens
"""

import secrets
import string
import hashlib
import time
from typing import Optional
from flask import current_app

class TokenGenerator:
    """Utility class for generating secure tokens and identifiers"""
    
    @staticmethod
    def generate_result_token(length: Optional[int] = None) -> str:
        """
        Generate a secure result token for giveaway result checking
        
        Args:
            length: Token length (uses config default if None)
            
        Returns:
            URL-safe token string
        """
        if length is None:
            length = current_app.config.get('RESULT_TOKEN_LENGTH', 32)
        
        # Generate URL-safe token
        token = secrets.token_urlsafe(length)
        
        # Ensure exact length by truncating or padding
        if len(token) > length:
            token = token[:length]
        elif len(token) < length:
            # Pad with additional random characters if needed
            additional_chars = length - len(token)
            alphabet = string.ascii_letters + string.digits + '-_'
            padding = ''.join(secrets.choice(alphabet) for _ in range(additional_chars))
            token += padding
        
        return token
    
    @staticmethod
    def generate_session_token(length: int = 64) -> str:
        """
        Generate a secure session token
        
        Args:
            length: Token length
            
        Returns:
            Hex token string
        """
        return secrets.token_hex(length // 2)
    
    @staticmethod
    def generate_api_key(length: int = 32) -> str:
        """
        Generate a secure API key
        
        Args:
            length: Key length
            
        Returns:
            URL-safe API key string
        """
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_unique_id(prefix: str = '', suffix: str = '') -> str:
        """
        Generate a unique identifier with optional prefix and suffix
        
        Args:
            prefix: Optional prefix for the ID
            suffix: Optional suffix for the ID
            
        Returns:
            Unique identifier string
        """
        # Use timestamp and random component for uniqueness
        timestamp = str(int(time.time() * 1000))  # Milliseconds
        random_part = secrets.token_hex(8)
        
        parts = [part for part in [prefix, timestamp, random_part, suffix] if part]
        return '_'.join(parts)
    
    @staticmethod
    def generate_verification_code(length: int = 6) -> str:
        """
        Generate a numeric verification code
        
        Args:
            length: Code length
            
        Returns:
            Numeric verification code
        """
        return ''.join(secrets.choice(string.digits) for _ in range(length))
    
    @staticmethod
    def generate_hash(data: str, algorithm: str = 'sha256') -> str:
        """
        Generate a hash of the given data
        
        Args:
            data: Data to hash
            algorithm: Hash algorithm to use
            
        Returns:
            Hex hash string
        """
        if algorithm == 'sha256':
            return hashlib.sha256(data.encode('utf-8')).hexdigest()
        elif algorithm == 'sha1':
            return hashlib.sha1(data.encode('utf-8')).hexdigest()
        elif algorithm == 'md5':
            return hashlib.md5(data.encode('utf-8')).hexdigest()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    @staticmethod
    def generate_secure_filename(original_filename: str) -> str:
        """
        Generate a secure filename based on the original filename
        
        Args:
            original_filename: Original filename
            
        Returns:
            Secure filename with timestamp and random component
        """
        # Extract file extension
        parts = original_filename.rsplit('.', 1)
        if len(parts) == 2:
            name, extension = parts
            extension = f".{extension}"
        else:
            name = original_filename
            extension = ""
        
        # Generate secure name
        timestamp = str(int(time.time()))
        random_part = secrets.token_hex(8)
        
        # Sanitize original name (keep only alphanumeric and basic chars)
        safe_name = ''.join(c for c in name if c.isalnum() or c in '-_')[:20]
        
        if safe_name:
            secure_name = f"{safe_name}_{timestamp}_{random_part}{extension}"
        else:
            secure_name = f"file_{timestamp}_{random_part}{extension}"
        
        return secure_name
    
    @staticmethod
    def validate_token_format(token: str, expected_length: Optional[int] = None) -> bool:
        """
        Validate token format
        
        Args:
            token: Token to validate
            expected_length: Expected token length
            
        Returns:
            Boolean indicating if token format is valid
        """
        if not isinstance(token, str):
            return False
        
        # Check length if specified
        if expected_length is not None and len(token) != expected_length:
            return False
        
        # Check if token contains only valid characters (URL-safe base64)
        valid_chars = set(string.ascii_letters + string.digits + '-_')
        return all(c in valid_chars for c in token)
    
    @staticmethod
    def generate_csrf_token() -> str:
        """
        Generate a CSRF token
        
        Returns:
            CSRF token string
        """
        return secrets.token_hex(32)
    
    @staticmethod
    def generate_nonce(length: int = 16) -> str:
        """
        Generate a cryptographic nonce
        
        Args:
            length: Nonce length in bytes
            
        Returns:
            Hex nonce string
        """
        return secrets.token_hex(length)
    
    @staticmethod
    def is_token_unique(token: str, check_function) -> bool:
        """
        Check if a token is unique using a provided check function
        
        Args:
            token: Token to check
            check_function: Function that returns True if token exists
            
        Returns:
            Boolean indicating if token is unique (not exists)
        """
        try:
            return not check_function(token)
        except Exception:
            # If check fails, assume token is not unique for safety
            return False
    
    @staticmethod
    def generate_unique_result_token(check_function, max_attempts: int = 10) -> str:
        """
        Generate a unique result token with collision checking
        
        Args:
            check_function: Function that returns True if token exists
            max_attempts: Maximum attempts to generate unique token
            
        Returns:
            Unique result token
            
        Raises:
            RuntimeError: If unable to generate unique token after max attempts
        """
        for attempt in range(max_attempts):
            token = TokenGenerator.generate_result_token()
            if TokenGenerator.is_token_unique(token, check_function):
                return token
        
        raise RuntimeError(f"Unable to generate unique token after {max_attempts} attempts")

