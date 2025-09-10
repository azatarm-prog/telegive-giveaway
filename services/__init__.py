"""
Service integration classes for inter-service communication
"""

from .auth_service import AuthService
from .channel_service import ChannelService
from .participant_service import ParticipantService
from .bot_service import BotService
from .media_service import MediaService

__all__ = [
    'AuthService',
    'ChannelService', 
    'ParticipantService',
    'BotService',
    'MediaService'
]

