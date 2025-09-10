"""
GiveawayStats model - For performance tracking and statistics
"""

from datetime import datetime, timezone
from sqlalchemy import Index

# This will be set by the app
db = None

class GiveawayStats(db.Model):
    __tablename__ = 'giveaway_stats'
    
    # Primary key
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    giveaway_id = db.Column(db.BigInteger, db.ForeignKey('giveaways.id'), nullable=False)
    
    # Statistics
    total_participants = db.Column(db.Integer, default=0)
    captcha_completed_participants = db.Column(db.Integer, default=0)
    winner_count = db.Column(db.Integer, default=0)
    messages_delivered = db.Column(db.Integer, default=0)
    
    # Timestamp
    last_updated = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Indexes
    __table_args__ = (
        Index('idx_giveaway_stats_giveaway_id', 'giveaway_id'),
    )
    
    # Relationship
    giveaway = db.relationship('Giveaway', backref=db.backref('stats', uselist=False, cascade='all, delete-orphan'))
    
    def __init__(self, giveaway_id, **kwargs):
        super().__init__(giveaway_id=giveaway_id, **kwargs)
    
    def to_dict(self):
        """Convert stats to dictionary"""
        return {
            'id': self.id,
            'giveaway_id': self.giveaway_id,
            'total_participants': self.total_participants,
            'captcha_completed_participants': self.captcha_completed_participants,
            'winner_count': self.winner_count,
            'messages_delivered': self.messages_delivered,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    def update_participants(self, total_participants, captcha_completed=None):
        """Update participant counts"""
        self.total_participants = total_participants
        if captcha_completed is not None:
            self.captcha_completed_participants = captcha_completed
        self.last_updated = datetime.now(timezone.utc)
    
    def update_winners(self, winner_count):
        """Update winner count"""
        self.winner_count = winner_count
        self.last_updated = datetime.now(timezone.utc)
    
    def update_messages_delivered(self, messages_delivered):
        """Update messages delivered count"""
        self.messages_delivered = messages_delivered
        self.last_updated = datetime.now(timezone.utc)
    
    def refresh_stats(self):
        """Refresh the last updated timestamp"""
        self.last_updated = datetime.now(timezone.utc)
    
    @classmethod
    def get_or_create(cls, giveaway_id):
        """Get existing stats or create new ones"""
        stats = cls.query.filter_by(giveaway_id=giveaway_id).first()
        if not stats:
            stats = cls(giveaway_id=giveaway_id)
            db.session.add(stats)
            db.session.flush()  # Get the ID without committing
        return stats
    
    def __repr__(self):
        return f'<GiveawayStats {self.id}: Giveaway {self.giveaway_id} - {self.total_participants} participants>'

