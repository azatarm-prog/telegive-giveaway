"""
API routes for the Giveaway Management Service
"""

from .giveaways import giveaways_bp
from .health import health_bp

__all__ = ['giveaways_bp', 'health_bp']

