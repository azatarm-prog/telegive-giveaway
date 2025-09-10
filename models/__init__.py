"""
Database models for Giveaway Management Service
"""

# Import factory functions instead of model classes directly
from .giveaway import create_giveaway_model
from .giveaway_stats import create_giveaway_stats_model
from .publishing_log import create_publishing_log_model

# Models will be created by factory functions after db is initialized
Giveaway = None
GiveawayStats = None
GiveawayPublishingLog = None

__all__ = ['create_giveaway_model', 'create_giveaway_stats_model', 'create_publishing_log_model']

