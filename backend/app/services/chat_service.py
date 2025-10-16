"""
채팅 서비스
채팅 세션 및 메시지 관련 비즈니스 로직
"""
from app import db
from app.models.user import User
from app.models.video import Video
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.models.chat_prompt_template import ChatPromptTemplate
from app.models.event_log import EventLog
from app.services.openai_service import OpenAIService
from datetime import datetime
from typing import Optional, Tuple
import json
import logging

logger = logging.getLogger(__name__)


class ChatService:
    """채팅 관련 서비스"""
    
    @staticmethod
    def get_or_create_session(user_id: int, video_id: int) -> Tuple[Optional[ChatSession], Optional[str]]:
        """
        채팅 세션 조회 또는 생성
        
        Args:
            user_id: 사용자 ID
            video_id: 비디오 ID
            
        Returns:
            (session, error): 성공 시 세션 객체, 실패 시 None과 에러 메시지
        """
        try:
            # 비디오 존재 확인
            video = Video.query.get(video_id)
            if not video:
                return None, '비디오를 찾을 수 없습니다'
            
            # 기존 활성 세션 확인
            existing_session = ChatSession.query.filter_by(
                user_id=user_id,
                video_id=video_id,
                is_active=True
            ).first()
            
            if existing_session:
                return existing_session, None
            
            # 새 세션 생성
            session = ChatSession(
                user_id=user_id,
                video_id=video_id
            )
            
            db.session.add(session)
            db.session.commit()
            
            logger.info(f"New chat session created: user={user_id}, video={video_id}")
            return session, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Get or create session error: {str(e)}")
            return None, '세션 생성 중 오류가 발생했습니다'
    
    @staticmethod
    def get_session(session_id: int, user_id: int) -> Tuple[Optional[ChatSession], Optional[str]]:
        """
        채팅 세션 조회
        
        Args:
            session_id: 세션 ID
            user_id: 사용자 ID (권한 확인용)
            
        Returns:
            (session, error): 성공 시 세션 객체, 실패 시 None과 에러 메시지
        """
        try:
            session = ChatSession.query.get(session_id)
            
            if not session:
                return None, '세션을 찾을 수 없습니다'
            
            if session.user_id != user_id:
                logger.warning(f"Unauthorized session access: user={user_id}, session={session_id}")
                return None, '세션 접근 권한이 없습니다'
            
            return session, None
            
        except Exception as e:
            logger.error(f"Get session error: {str(e)}")
            return None, '세션 조회 중 오류가 발생했습니다'
    
    @staticmethod
    def send_message(session_id: int, user_id: int, message: str, 
                    openai_service: OpenAIService, daily_token_limit: int) -> Tuple[Optional[dict], Optional[str]]:
        """
        메시지 전송 및 AI 응답 생성
        
        Args:
            session_id: 세션 ID
            user_id: 사용자 ID
            message: 사용자 메시지
            openai_service: OpenAI 서비스 인스턴스
            daily_token_limit: 일일 토큰 제한
            
        Returns:
            (response_data, error): 성공 시 응답 데이터, 실패 시 None과 에러 메시지
        """
        try:
            # 세션 확인
            session = ChatSession.query.get(session_id)
            if not session or session.user_id != user_id:
                return None, '세션을 찾을 수 없습니다'
            
            # 사용자 확인
            user = User.query.get(user_id)
            if not user:
                return None, '사용자를 찾을 수 없습니다'
            
            # 일일 토큰 제한 확인
            if user.daily_token_usage >= daily_token_limit:
                logger.warning(f"Daily token limit exceeded: user={user_id}")
                return None, '일일 토큰 한도를 초과했습니다'
            
            # 시스템 프롬프트 및 constraints 가져오기
            system_prompt, constraints = ChatService._get_system_prompt(session.video_id, user.role)
            
            # OpenAI API 호출
            response_data = openai_service.chat_completion(
                session=session,
                user_message=message,
                system_prompt=system_prompt,
                constraints=constraints
            )
            
            # 사용자 메시지 저장
            user_msg = ChatMessage(
                session_id=session.id,
                role='user',
                content=message,
                total_tokens=0
            )
            db.session.add(user_msg)
            
            # AI 응답 메시지 저장
            assistant_msg = ChatMessage(
                session_id=session.id,
                role='assistant',
                content=response_data['content'],
                prompt_tokens=response_data['prompt_tokens'],
                completion_tokens=response_data['completion_tokens'],
                total_tokens=response_data['total_tokens']
            )
            db.session.add(assistant_msg)
            
            # 세션 업데이트
            session.total_tokens += response_data['total_tokens']
            session.total_cost += response_data['cost']
            
            if response_data.get('new_summary'):
                session.summary = response_data['new_summary']
                session.summary_updated_at = datetime.utcnow()
            
            # 사용자 토큰 사용량 업데이트
            user.daily_token_usage += response_data['total_tokens']
            user.total_token_usage += response_data['total_tokens']
            
            db.session.commit()
            
            logger.info(f"Message sent: session={session_id}, tokens={response_data['total_tokens']}")
            
            return {
                'message': assistant_msg.to_dict(),
                'session': {
                    'total_tokens': session.total_tokens,
                    'total_cost': session.total_cost,
                    'summary_updated': response_data.get('new_summary') is not None
                }
            }, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Send message error: {str(e)}")
            return None, f'메시지 전송 중 오류가 발생했습니다: {str(e)}'
    
    @staticmethod
    def _get_system_prompt(video_id: int = None, user_role: str = None) -> Tuple[str, dict]:
        """
        시스템 프롬프트 및 constraints 가져오기
        
        Returns:
            (system_prompt, constraints): 시스템 프롬프트와 OpenAI API constraints
        """
        try:
            # 전역 활성화된 페르소나 조회
            prompt_template = ChatPromptTemplate.query.filter_by(
                is_global_active=True,
                is_active=True
            ).first()
            
            if prompt_template:
                return prompt_template.system_prompt, prompt_template.get_constraints_dict()
            
            # 폴백 프롬프트
            logger.warning("No active persona found, using fallback prompt")
            return "당신은 학습을 돕는 AI 조교입니다. 학생들의 질문에 친절하고 명확하게 답변해주세요.", {}
            
        except Exception as e:
            logger.error(f"Get system prompt error: {str(e)}")
            return "당신은 학습을 돕는 AI 조교입니다. 학생들의 질문에 친절하고 명확하게 답변해주세요.", {}

