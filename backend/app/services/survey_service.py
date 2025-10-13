"""
설문조사 관련 비즈니스 로직
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.exc import IntegrityError
from app import db
from app.models.survey import Survey, SurveyQuestion, SurveyResponse
from app.models.user import User


class SurveyService:
    """설문조사 서비스"""
    
    @staticmethod
    def create_survey(title: str, description: str = None, is_required: bool = False, 
                     show_after_registration: bool = True) -> Survey:
        """새 설문조사 생성"""
        survey = Survey(
            title=title,
            description=description,
            is_required=is_required,
            show_after_registration=show_after_registration,
            is_active=True
        )
        db.session.add(survey)
        db.session.commit()
        return survey
    
    @staticmethod
    def update_survey(survey_id: int, **kwargs) -> Optional[Survey]:
        """설문조사 정보 수정"""
        survey = Survey.query.get(survey_id)
        if not survey:
            return None
        
        for key, value in kwargs.items():
            if hasattr(survey, key):
                setattr(survey, key, value)
        
        survey.updated_at = datetime.utcnow()
        db.session.commit()
        return survey
    
    @staticmethod
    def delete_survey(survey_id: int) -> bool:
        """설문조사 삭제"""
        survey = Survey.query.get(survey_id)
        if not survey:
            return False
        
        db.session.delete(survey)
        db.session.commit()
        return True
    
    @staticmethod
    def get_survey(survey_id: int, include_questions: bool = False) -> Optional[Survey]:
        """설문조사 조회"""
        survey = Survey.query.get(survey_id)
        return survey
    
    @staticmethod
    def get_all_surveys(active_only: bool = False) -> List[Survey]:
        """모든 설문조사 목록 조회"""
        query = Survey.query
        if active_only:
            query = query.filter_by(is_active=True)
        return query.order_by(Survey.created_at.desc()).all()
    
    @staticmethod
    def get_registration_surveys() -> List[Survey]:
        """회원가입 후 표시할 설문조사 목록"""
        return Survey.query.filter_by(
            is_active=True,
            show_after_registration=True
        ).order_by(Survey.created_at.desc()).all()
    
    # 질문 관리
    @staticmethod
    def add_question(survey_id: int, question_text: str, question_type: str,
                    options: Optional[List[str]] = None, is_required: bool = False,
                    order: int = 0) -> Optional[SurveyQuestion]:
        """설문 문항 추가"""
        survey = Survey.query.get(survey_id)
        if not survey:
            return None
        
        # question_type 검증
        valid_types = ['multiple_choice', 'text', 'textarea']
        if question_type not in valid_types:
            raise ValueError(f"Invalid question_type. Must be one of {valid_types}")
        
        # 객관식인 경우 options 필수
        if question_type == 'multiple_choice' and not options:
            raise ValueError("Options are required for multiple_choice questions")
        
        question = SurveyQuestion(
            survey_id=survey_id,
            question_text=question_text,
            question_type=question_type,
            options=options,
            is_required=is_required,
            order=order
        )
        db.session.add(question)
        db.session.commit()
        return question
    
    @staticmethod
    def update_question(question_id: int, **kwargs) -> Optional[SurveyQuestion]:
        """설문 문항 수정"""
        question = SurveyQuestion.query.get(question_id)
        if not question:
            return None
        
        for key, value in kwargs.items():
            if hasattr(question, key):
                setattr(question, key, value)
        
        question.updated_at = datetime.utcnow()
        db.session.commit()
        return question
    
    @staticmethod
    def delete_question(question_id: int) -> bool:
        """설문 문항 삭제"""
        question = SurveyQuestion.query.get(question_id)
        if not question:
            return False
        
        db.session.delete(question)
        db.session.commit()
        return True
    
    @staticmethod
    def get_question(question_id: int) -> Optional[SurveyQuestion]:
        """설문 문항 조회"""
        return SurveyQuestion.query.get(question_id)
    
    @staticmethod
    def get_survey_questions(survey_id: int) -> List[SurveyQuestion]:
        """특정 설문의 모든 문항 조회"""
        return SurveyQuestion.query.filter_by(survey_id=survey_id).order_by(SurveyQuestion.order).all()
    
    @staticmethod
    def reorder_questions(survey_id: int, question_orders: Dict[int, int]) -> bool:
        """문항 순서 재정렬
        
        Args:
            survey_id: 설문 ID
            question_orders: {question_id: order} 딕셔너리
        """
        try:
            for question_id, order in question_orders.items():
                question = SurveyQuestion.query.filter_by(
                    id=question_id,
                    survey_id=survey_id
                ).first()
                if question:
                    question.order = order
                    question.updated_at = datetime.utcnow()
            
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False
    
    # 응답 관리
    @staticmethod
    def submit_response(user_id: int, survey_id: int, question_id: int, 
                       response_text: str) -> Optional[SurveyResponse]:
        """설문 응답 제출 (단일 문항)"""
        # 설문과 문항 존재 여부 확인
        survey = Survey.query.get(survey_id)
        question = SurveyQuestion.query.get(question_id)
        user = User.query.get(user_id)
        
        if not survey or not question or not user:
            return None
        
        # 문항이 해당 설문에 속하는지 확인
        if question.survey_id != survey_id:
            return None
        
        try:
            # 기존 응답이 있으면 업데이트, 없으면 생성
            response = SurveyResponse.query.filter_by(
                user_id=user_id,
                survey_id=survey_id,
                question_id=question_id
            ).first()
            
            if response:
                response.response_text = response_text
                response.updated_at = datetime.utcnow()
            else:
                response = SurveyResponse(
                    user_id=user_id,
                    survey_id=survey_id,
                    question_id=question_id,
                    response_text=response_text
                )
                db.session.add(response)
            
            db.session.commit()
            return response
        except IntegrityError:
            db.session.rollback()
            return None
    
    @staticmethod
    def submit_survey_responses(user_id: int, survey_id: int, 
                               responses: List[Dict[str, Any]]) -> bool:
        """설문 전체 응답 제출
        
        Args:
            user_id: 사용자 ID
            survey_id: 설문 ID
            responses: [{"question_id": int, "response_text": str}, ...]
        """
        try:
            for response_data in responses:
                question_id = response_data.get('question_id')
                response_text = response_data.get('response_text')
                
                if not question_id or response_text is None:
                    continue
                
                SurveyService.submit_response(
                    user_id=user_id,
                    survey_id=survey_id,
                    question_id=question_id,
                    response_text=response_text
                )
            
            return True
        except Exception:
            db.session.rollback()
            return False
    
    @staticmethod
    def get_user_responses(user_id: int, survey_id: int) -> List[SurveyResponse]:
        """특정 사용자의 특정 설문에 대한 모든 응답 조회"""
        return SurveyResponse.query.filter_by(
            user_id=user_id,
            survey_id=survey_id
        ).all()
    
    @staticmethod
    def get_survey_all_responses(survey_id: int) -> List[SurveyResponse]:
        """특정 설문의 모든 응답 조회 (관리자용)"""
        return SurveyResponse.query.filter_by(survey_id=survey_id).all()
    
    @staticmethod
    def get_question_responses(question_id: int) -> List[SurveyResponse]:
        """특정 문항에 대한 모든 응답 조회"""
        return SurveyResponse.query.filter_by(question_id=question_id).all()
    
    @staticmethod
    def has_user_completed_survey(user_id: int, survey_id: int) -> bool:
        """사용자가 설문을 완료했는지 확인
        
        필수 문항을 모두 응답했는지 확인
        """
        survey = Survey.query.get(survey_id)
        if not survey:
            return False
        
        # 필수 문항 목록
        required_questions = SurveyQuestion.query.filter_by(
            survey_id=survey_id,
            is_required=True
        ).all()
        
        if not required_questions:
            # 필수 문항이 없으면 응답이 하나라도 있으면 완료로 간주
            response_count = SurveyResponse.query.filter_by(
                user_id=user_id,
                survey_id=survey_id
            ).count()
            return response_count > 0
        
        # 모든 필수 문항에 응답했는지 확인
        for question in required_questions:
            response = SurveyResponse.query.filter_by(
                user_id=user_id,
                survey_id=survey_id,
                question_id=question.id
            ).first()
            
            if not response or not response.response_text:
                return False
        
        return True
    
    @staticmethod
    def get_survey_statistics(survey_id: int) -> Dict[str, Any]:
        """설문 통계 조회"""
        survey = Survey.query.get(survey_id)
        if not survey:
            return {}
        
        questions = SurveyQuestion.query.filter_by(survey_id=survey_id).all()
        total_responses = db.session.query(SurveyResponse.user_id).filter_by(
            survey_id=survey_id
        ).distinct().count()
        
        question_stats = []
        for question in questions:
            responses = SurveyResponse.query.filter_by(question_id=question.id).all()
            
            stats = {
                'question_id': question.id,
                'question_text': question.question_text,
                'question_type': question.question_type,
                'response_count': len(responses)
            }
            
            # 객관식인 경우 선택지별 응답 수 집계
            if question.question_type == 'multiple_choice' and question.options:
                option_counts = {}
                for option in question.options:
                    option_counts[option] = 0
                
                for response in responses:
                    if response.response_text in option_counts:
                        option_counts[response.response_text] += 1
                
                stats['option_counts'] = option_counts
            
            question_stats.append(stats)
        
        return {
            'survey_id': survey_id,
            'survey_title': survey.title,
            'total_respondents': total_responses,
            'questions': question_stats
        }

