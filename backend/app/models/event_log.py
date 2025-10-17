from app import db
from datetime import datetime

class EventLog(db.Model):
    __tablename__ = 'event_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=True, index=True)
    
    event_type = db.Column(db.String(50), nullable=False, index=True)  # video_view, video_seek, chat_message, etc.
    event_data = db.Column(db.Text)  # JSON format
    
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'module_id': self.module_id,
            'event_type': self.event_type,
            'event_data': self.event_data,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

