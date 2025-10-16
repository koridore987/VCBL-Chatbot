from app import db
from datetime import datetime
import json

class ChatPromptTemplate(db.Model):
    """
    챗봇 페르소나 모델
    전역 활성화를 통해 한 번에 하나의 페르소나만 활성화 가능
    """
    __tablename__ = 'chat_prompt_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    
    # Persona content
    system_prompt = db.Column(db.Text, nullable=False)
    constraints = db.Column(db.Text)  # JSON format for OpenAI API parameters
    
    # Global activation (only one can be active at a time)
    is_global_active = db.Column(db.Boolean, default=False, index=True)
    
    # Version management
    version = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    
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
            'is_global_active': self.is_global_active,
            'version': self.version,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_constraints_dict(self):
        """Get constraints as a dictionary"""
        if not self.constraints:
            return {}
        try:
            return json.loads(self.constraints)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_constraints_dict(self, constraints_dict):
        """Set constraints from a dictionary"""
        if constraints_dict:
            self.constraints = json.dumps(constraints_dict)
        else:
            self.constraints = None

