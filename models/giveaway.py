"""
Giveaway model - Primary responsibility of the Giveaway Management Service
"""

from datetime import datetime, timezone
from sqlalchemy import Column, BigInteger, Integer, String, Text, Boolean, DateTime, CheckConstraint, Index
from flask_sqlalchemy import SQLAlchemy
import secrets

def create_giveaway_model(db):
    """Factory function to create Giveaway model with db instance"""
    
    class Giveaway(db.Model):
        __tablename__ = 'giveaways'
        
        # Primary key
        id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
        account_id = db.Column(db.BigInteger, nullable=False)
        
        # Giveaway content
        title = db.Column(db.String(255), nullable=False)  # Admin-only, not shown to users
        main_body = db.Column(db.Text, nullable=False)  # Shown to users in giveaway post
        winner_count = db.Column(db.Integer, default=1)
        participation_button_text = db.Column(db.String(100), default='Participate')
    
        # Finish messages (defined when finishing)
        public_conclusion_message = db.Column(db.Text, default=None)
        winner_message = db.Column(db.Text, default=None)
        loser_message = db.Column(db.Text, default=None)
        messages_ready_for_finish = db.Column(db.Boolean, default=False)
        
        # Status and lifecycle
        status = db.Column(db.String(20), default='active')
        message_id = db.Column(db.BigInteger, default=None)  # Telegram message ID
        conclusion_message_id = db.Column(db.BigInteger, default=None)  # Conclusion message ID
        result_token = db.Column(db.String(64), unique=True)  # For result checking
        
        # Media (managed by media service)
        media_file_id = db.Column(db.BigInteger, default=None)  # Reference to media service
        media_cleanup_status = db.Column(db.String(20), default='pending')
        media_cleanup_timestamp = db.Column(db.DateTime(timezone=True), default=None)
        
        # Timestamps
        created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
        published_at = db.Column(db.DateTime(timezone=True), default=None)
        finished_at = db.Column(db.DateTime(timezone=True), default=None)
        
        # Constraints
        __table_args__ = (
            CheckConstraint("status IN ('active', 'finished')", name='check_status'),
            Index('idx_giveaways_account_id', 'account_id'),
            Index('idx_giveaways_status', 'status'),
            Index('idx_giveaways_result_token', 'result_token'),
            # Unique constraint: Only one active giveaway per account
            Index('idx_giveaways_account_active', 'account_id', 
                  postgresql_where=db.text("status = 'active'"), unique=True),
        )
        
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            if not self.result_token:
                self.result_token = self.generate_result_token()
        
        @staticmethod
        def generate_result_token(length=32):
            """Generate a unique result token for the giveaway"""
            return secrets.token_urlsafe(length)[:length]
        
        def to_dict(self, include_sensitive=False):
            """Convert giveaway to dictionary"""
            data = {
                'id': self.id,
                'account_id': self.account_id,
                'title': self.title,
                'main_body': self.main_body,
                'winner_count': self.winner_count,
                'participation_button_text': self.participation_button_text,
                'status': self.status,
                'message_id': self.message_id,
                'conclusion_message_id': self.conclusion_message_id,
                'media_file_id': self.media_file_id,
                'media_cleanup_status': self.media_cleanup_status,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'published_at': self.published_at.isoformat() if self.published_at else None,
                'finished_at': self.finished_at.isoformat() if self.finished_at else None,
                'messages_ready_for_finish': self.messages_ready_for_finish
            }
            
            if include_sensitive:
                data.update({
                    'result_token': self.result_token,
                    'public_conclusion_message': self.public_conclusion_message,
                    'winner_message': self.winner_message,
                    'loser_message': self.loser_message,
                    'media_cleanup_timestamp': self.media_cleanup_timestamp.isoformat() if self.media_cleanup_timestamp else None
                })
            
            return data
        
        def can_publish(self):
            """Check if giveaway can be published"""
            return self.status == 'active' and self.message_id is None
        
        def can_finish(self):
            """Check if giveaway can be finished"""
            return (self.status == 'active' and 
                    self.message_id is not None and 
                    self.messages_ready_for_finish)
        
        def is_active(self):
            """Check if giveaway is active"""
            return self.status == 'active'
        
        def is_finished(self):
            """Check if giveaway is finished"""
            return self.status == 'finished'
        
        def mark_published(self, message_id, published_at=None):
            """Mark giveaway as published"""
            self.message_id = message_id
            self.published_at = published_at or datetime.now(timezone.utc)
        
        def mark_finished(self, conclusion_message_id=None, finished_at=None):
            """Mark giveaway as finished"""
            self.status = 'finished'
            self.conclusion_message_id = conclusion_message_id
            self.finished_at = finished_at or datetime.now(timezone.utc)
        
        def set_finish_messages(self, public_conclusion_message, winner_message, loser_message):
            """Set all finish messages and mark as ready"""
            self.public_conclusion_message = public_conclusion_message
            self.winner_message = winner_message
            self.loser_message = loser_message
            self.messages_ready_for_finish = True
        
        def __repr__(self):
            return f'<Giveaway {self.id}: {self.title} ({self.status})>'
    
    return Giveaway

