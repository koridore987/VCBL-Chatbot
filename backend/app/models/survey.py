"""
설문조사 관련 데이터베이스 모델
"""
from datetime import datetime
from app import db


class Survey(db.Model):
    """설문조사 메타 정보"""
    __tablename__ = 'surveys'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_required = db.Column(db.Boolean, default=False, nullable=False)  # 필수 설문 여부
    show_after_registration = db.Column(db.Boolean, default=True, nullable=False)  # 회원가입 후 표시 여부
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 관계
    questions = db.relationship('SurveyQuestion', back_populates='survey', cascade='all, delete-orphan', lazy='dynamic')
    responses = db.relationship('SurveyResponse', back_populates='survey', cascade='all, delete-orphan', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'is_active': self.is_active,
            'is_required': self.is_required,
            'show_after_registration': self.show_after_registration,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'question_count': self.questions.count()
        }
    
    def to_dict_with_questions(self):
        """질문 목록을 포함한 딕셔너리"""
        data = self.to_dict()
        data['questions'] = [q.to_dict() for q in self.questions.order_by(SurveyQuestion.order).all()]
        return data


class SurveyQuestion(db.Model):
    """설문 문항"""
    __tablename__ = 'survey_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey('surveys.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False)  # 'multiple_choice', 'text', 'textarea'
    options = db.Column(db.JSON, nullable=True)  # 객관식인 경우 선택지 목록 (예: ["옵션1", "옵션2", ...])
    is_required = db.Column(db.Boolean, default=False, nullable=False)
    order = db.Column(db.Integer, default=0, nullable=False)  # 문항 순서
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 관계
    survey = db.relationship('Survey', back_populates='questions')
    responses = db.relationship('SurveyResponse', back_populates='question', cascade='all, delete-orphan', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'survey_id': self.survey_id,
            'question_text': self.question_text,
            'question_type': self.question_type,
            'options': self.options,
            'is_required': self.is_required,
            'order': self.order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SurveyResponse(db.Model):
    """설문 응답"""
    __tablename__ = 'survey_responses'
    
    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey('surveys.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('survey_questions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    response_text = db.Column(db.Text, nullable=True)  # 주관식 답변 또는 선택한 옵션
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 관계
    survey = db.relationship('Survey', back_populates='responses')
    question = db.relationship('SurveyQuestion', back_populates='responses')
    user = db.relationship('User', back_populates='survey_responses')
    
    # 복합 유니크 제약: 한 사용자가 같은 설문의 같은 질문에 중복 응답 방지
    __table_args__ = (
        db.UniqueConstraint('survey_id', 'question_id', 'user_id', name='unique_user_survey_question_response'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'survey_id': self.survey_id,
            'question_id': self.question_id,
            'user_id': self.user_id,
            'response_text': self.response_text,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_dict_with_details(self):
        """질문 정보를 포함한 딕셔너리"""
        data = self.to_dict()
        if self.question:
            data['question'] = self.question.to_dict()
        if self.user:
            data['user'] = {
                'id': self.user.id,
                'username': self.user.username,
                'student_id': self.user.student_id
            }
        return data

