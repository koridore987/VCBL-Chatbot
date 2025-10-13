from app import db
from datetime import datetime

class ChatPromptTemplate(db.Model):
    __tablename__ = 'chat_prompt_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    
    # Prompt content
    system_prompt = db.Column(db.Text, nullable=False)
    constraints = db.Column(db.Text)  # JSON format
    
    # Assignment
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=True)
    user_role = db.Column(db.String(20), nullable=True)  # 'user', 'admin', null (all)
    
    # Version management
    version = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False)
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'system_prompt': self.system_prompt,
            'constraints': self.constraints,
            'video_id': self.video_id,
            'user_role': self.user_role,
            'version': self.version,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

