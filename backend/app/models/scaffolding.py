from app import db
from datetime import datetime

class Scaffolding(db.Model):
    __tablename__ = 'scaffoldings'
    
    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False, index=True)
    
    title = db.Column(db.String(255), nullable=False)
    prompt_text = db.Column(db.Text, nullable=True)  # Allow empty prompt text
    order_index = db.Column(db.Integer, default=0)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    responses = db.relationship('ScaffoldingResponse', backref='scaffolding', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'module_id': self.module_id,
            'title': self.title,
            'prompt_text': self.prompt_text,
            'order_index': self.order_index,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ScaffoldingResponse(db.Model):
    __tablename__ = 'scaffolding_responses'
    
    id = db.Column(db.Integer, primary_key=True)
    scaffolding_id = db.Column(db.Integer, db.ForeignKey('scaffoldings.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    response_text = db.Column(db.Text, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'scaffolding_id': self.scaffolding_id,
            'user_id': self.user_id,
            'response_text': self.response_text,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

