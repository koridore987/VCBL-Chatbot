from app import db
from datetime import datetime

class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False, index=True)
    
    # Summary carry-over
    summary = db.Column(db.Text)
    summary_updated_at = db.Column(db.DateTime)
    
    # Token tracking
    total_tokens = db.Column(db.Integer, default=0)
    total_cost = db.Column(db.Float, default=0.0)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = db.relationship('ChatMessage', backref='session', lazy=True, cascade='all, delete-orphan', order_by='ChatMessage.created_at')
    
    def to_dict(self, include_messages=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'video_id': self.video_id,
            'summary': self.summary,
            'summary_updated_at': self.summary_updated_at.isoformat() if self.summary_updated_at else None,
            'total_tokens': self.total_tokens,
            'total_cost': self.total_cost,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_messages:
            data['messages'] = [msg.to_dict() for msg in self.messages]
        return data

