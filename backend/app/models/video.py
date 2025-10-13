from app import db
from datetime import datetime

class Video(db.Model):
    __tablename__ = 'videos'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    youtube_url = db.Column(db.String(500), nullable=False)
    youtube_id = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    duration = db.Column(db.Integer)  # in seconds
    thumbnail_url = db.Column(db.String(500))
    
    # Scaffolding settings
    scaffolding_mode = db.Column(db.String(20), default='both')  # 'prompt', 'chat', 'both', 'none'
    is_active = db.Column(db.Boolean, default=True)
    order_index = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    scaffoldings = db.relationship('Scaffolding', backref='video', lazy=True, cascade='all, delete-orphan')
    chat_sessions = db.relationship('ChatSession', backref='video', lazy=True, cascade='all, delete-orphan')
    event_logs = db.relationship('EventLog', backref='video', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'youtube_url': self.youtube_url,
            'youtube_id': self.youtube_id,
            'description': self.description,
            'duration': self.duration,
            'thumbnail_url': self.thumbnail_url,
            'scaffolding_mode': self.scaffolding_mode,
            'is_active': self.is_active,
            'order_index': self.order_index,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

