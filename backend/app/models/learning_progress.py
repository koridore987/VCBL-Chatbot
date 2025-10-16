from datetime import datetime

from app import db


class LearningProgress(db.Model):
  __tablename__ = 'learning_progress'

  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
  video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False, index=True)

  status = db.Column(db.String(20), nullable=False, default='not_started')  # not_started, in_progress, completed
  started_at = db.Column(db.DateTime)
  last_activity_at = db.Column(db.DateTime)
  completed_at = db.Column(db.DateTime)

  survey_completed = db.Column(db.Boolean, default=False)
  survey_completed_at = db.Column(db.DateTime)

  created_at = db.Column(db.DateTime, default=datetime.utcnow)
  updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  __table_args__ = (
    db.UniqueConstraint('user_id', 'video_id', name='uq_learning_progress_user_video'),
  )

  def to_dict(self):
    return {
      'id': self.id,
      'user_id': self.user_id,
      'video_id': self.video_id,
      'status': self.status,
      'started_at': self.started_at.isoformat() if self.started_at else None,
      'last_activity_at': self.last_activity_at.isoformat() if self.last_activity_at else None,
      'completed_at': self.completed_at.isoformat() if self.completed_at else None,
      'survey_completed': self.survey_completed,
      'survey_completed_at': self.survey_completed_at.isoformat() if self.survey_completed_at else None,
      'created_at': self.created_at.isoformat() if self.created_at else None,
      'updated_at': self.updated_at.isoformat() if self.updated_at else None,
    }
