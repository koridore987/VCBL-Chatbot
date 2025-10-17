"""
채팅 관련 라우트
"""
from flask import Blueprint, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import get_openai_service
from app.services.chat_service import ChatService
from app.utils import validate_request, success_response, error_response
from app.validators import CreateSessionRequest, SendMessageRequest
import logging

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/sessions', methods=['POST'])
@jwt_required()
@validate_request(CreateSessionRequest)
def create_session(*, validated_data: CreateSessionRequest):
    """채팅 세션 생성 또는 조회"""
    user_id = int(get_jwt_identity())
    
    session, error = ChatService.get_or_create_session(
        user_id=user_id,
        module_id=validated_data.video_id
    )
    
    if error:
        return error_response(error, 404 if '찾을 수 없' in error else 400)
    
    return success_response(
        session.to_dict(include_messages=True),
        status_code=200 if session.messages else 201
    )


@chat_bp.route('/sessions/<int:session_id>', methods=['GET'])
@jwt_required()
def get_session(session_id):
    """채팅 세션 조회"""
    user_id = int(get_jwt_identity())
    
    session, error = ChatService.get_session(session_id, user_id)
    
    if error:
        return error_response(error, 403 if '권한' in error else 404)
    
    return success_response(session.to_dict(include_messages=True))


@chat_bp.route('/sessions/<int:session_id>/messages', methods=['POST'])
@jwt_required()
@validate_request(SendMessageRequest)
def send_message(session_id, *, validated_data: SendMessageRequest):
    """메시지 전송"""
    user_id = int(get_jwt_identity())
    
    # 요청당 캐시된 OpenAI 서비스 가져오기 (싱글턴 패턴)
    openai_service = get_openai_service()
    
    # 메시지 전송
    response_data, error = ChatService.send_message(
        session_id=session_id,
        user_id=user_id,
        message=validated_data.message,
        openai_service=openai_service,
        daily_token_limit=current_app.config['DAILY_TOKEN_LIMIT']
    )
    
    if error:
        if '한도를 초과' in error:
            return error_response(error, 429)
        elif '찾을 수 없' in error:
            return error_response(error, 404)
        else:
            return error_response(error, 500)
    
    return success_response(response_data)
