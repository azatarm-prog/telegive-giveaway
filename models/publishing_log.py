"""
GiveawayPublishingLog model - For tracking publishing operations and audit trail
"""

from datetime import datetime, timezone
from sqlalchemy import Index
from sqlalchemy.dialects.postgresql import JSONB
from app import db

class GiveawayPublishingLog(db.Model):
    __tablename__ = 'giveaway_publishing_log'
    
    # Primary key
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    giveaway_id = db.Column(db.BigInteger, db.ForeignKey('giveaways.id'), nullable=False)
    
    # Operation details
    action = db.Column(db.String(50), nullable=False)  # publish, finish, update
    telegram_message_id = db.Column(db.BigInteger, default=None)
    success = db.Column(db.Boolean, nullable=False)
    error_message = db.Column(db.Text, default=None)
    response_data = db.Column(JSONB, default=None)
    
    # Timestamp
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Indexes
    __table_args__ = (
        Index('idx_giveaway_publishing_log_giveaway_id', 'giveaway_id'),
    )
    
    # Relationship
    giveaway = db.relationship('Giveaway', backref=db.backref('publishing_logs', cascade='all, delete-orphan'))
    
    def __init__(self, giveaway_id, action, success, **kwargs):
        super().__init__(
            giveaway_id=giveaway_id,
            action=action,
            success=success,
            **kwargs
        )
    
    def to_dict(self):
        """Convert log entry to dictionary"""
        return {
            'id': self.id,
            'giveaway_id': self.giveaway_id,
            'action': self.action,
            'telegram_message_id': self.telegram_message_id,
            'success': self.success,
            'error_message': self.error_message,
            'response_data': self.response_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def log_publish_attempt(cls, giveaway_id, success, telegram_message_id=None, error_message=None, response_data=None):
        """Log a publish attempt"""
        log_entry = cls(
            giveaway_id=giveaway_id,
            action='publish',
            success=success,
            telegram_message_id=telegram_message_id,
            error_message=error_message,
            response_data=response_data
        )
        db.session.add(log_entry)
        return log_entry
    
    @classmethod
    def log_finish_attempt(cls, giveaway_id, success, telegram_message_id=None, error_message=None, response_data=None):
        """Log a finish attempt"""
        log_entry = cls(
            giveaway_id=giveaway_id,
            action='finish',
            success=success,
            telegram_message_id=telegram_message_id,
            error_message=error_message,
            response_data=response_data
        )
        db.session.add(log_entry)
        return log_entry
    
    @classmethod
    def log_update_attempt(cls, giveaway_id, success, error_message=None, response_data=None):
        """Log an update attempt"""
        log_entry = cls(
            giveaway_id=giveaway_id,
            action='update',
            success=success,
            error_message=error_message,
            response_data=response_data
        )
        db.session.add(log_entry)
        return log_entry
    
    @classmethod
    def get_recent_logs(cls, giveaway_id, limit=10):
        """Get recent logs for a giveaway"""
        return cls.query.filter_by(giveaway_id=giveaway_id)\
                      .order_by(cls.created_at.desc())\
                      .limit(limit)\
                      .all()
    
    @classmethod
    def get_failed_operations(cls, giveaway_id):
        """Get failed operations for a giveaway"""
        return cls.query.filter_by(giveaway_id=giveaway_id, success=False)\
                      .order_by(cls.created_at.desc())\
                      .all()
    
    def __repr__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f'<GiveawayPublishingLog {self.id}: {self.action.upper()} - {status}>'

