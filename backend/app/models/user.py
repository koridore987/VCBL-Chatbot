from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.BigInteger, unique=True, nullable=False, index=True)  # 10자리 정수 학번
    password_hash = db.Column(db.String(255), nullable=True)  # 사전등록시에는 비어있음
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # super, admin, user
    is_active = db.Column(db.Boolean, default=True)
    
    # Token usage tracking
    daily_token_usage = db.Column(db.Integer, default=0)
    total_token_usage = db.Column(db.Integer, default=0)
    last_token_reset = db.Column(db.DateTime, default=datetime.utcnow)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chat_sessions = db.relationship('ChatSession', backref='user', lazy=True, cascade='all, delete-orphan')
    event_logs = db.relationship('EventLog', backref='user', lazy=True, cascade='all, delete-orphan')
    scaffolding_responses = db.relationship('ScaffoldingResponse', backref='user', lazy=True, cascade='all, delete-orphan')
    survey_responses = db.relationship('SurveyResponse', back_populates='user', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'name': self.name,
            'role': self.role,
            'is_active': self.is_active,
            'daily_token_usage': self.daily_token_usage,
            'total_token_usage': self.total_token_usage,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

