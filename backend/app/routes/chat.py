from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.video import Video
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.models.chat_prompt_template import ChatPromptTemplate
from app.services.openai_service import OpenAIService
from datetime import datetime
import json

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/sessions', methods=['POST'])
@jwt_required()
def create_session():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    video_id = data.get('video_id')
    
    if not video_id:
        return jsonify({'error': '비디오 ID가 필요합니다'}), 400
    
    video = Video.query.get(video_id)
    
    if not video:
        return jsonify({'error': '비디오를 찾을 수 없습니다'}), 404
    
    # Check if active session exists
    existing_session = ChatSession.query.filter_by(
        user_id=user_id,
        video_id=video_id,
        is_active=True
    ).first()
    
    if existing_session:
        return jsonify(existing_session.to_dict(include_messages=True)), 200
    
    # Create new session
    session = ChatSession(
        user_id=user_id,
        video_id=video_id
    )
    
    db.session.add(session)
    db.session.commit()
    
    return jsonify(session.to_dict(include_messages=True)), 201


@chat_bp.route('/sessions/<int:session_id>', methods=['GET'])
@jwt_required()
def get_session(session_id):
    user_id = get_jwt_identity()
    
    session = ChatSession.query.get(session_id)
    
    if not session or session.user_id != user_id:
        return jsonify({'error': '세션을 찾을 수 없습니다'}), 404
    
    return jsonify(session.to_dict(include_messages=True)), 200


@chat_bp.route('/sessions/<int:session_id>/messages', methods=['POST'])
@jwt_required()
def send_message(session_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    user_message = data.get('message')
    
    if not user_message:
        return jsonify({'error': '메시지를 입력해주세요'}), 400
    
    session = ChatSession.query.get(session_id)
    
    if not session or session.user_id != user_id:
        return jsonify({'error': '세션을 찾을 수 없습니다'}), 404
    
    user = User.query.get(user_id)
    
    # Check daily token limit
    if user.daily_token_usage >= current_app.config['DAILY_TOKEN_LIMIT']:
        return jsonify({'error': '일일 토큰 한도를 초과했습니다'}), 429
    
    # Initialize OpenAI service
    openai_service = OpenAIService(current_app.config)
    
    try:
        # Get system prompt
        system_prompt = get_system_prompt(session.video_id, user.role)
        
        # Process message with summary carry-over
        response_data = openai_service.chat_completion(
            session=session,
            user_message=user_message,
            system_prompt=system_prompt
        )
        
        # Save user message
        user_msg = ChatMessage(
            session_id=session.id,
            role='user',
            content=user_message,
            total_tokens=0
        )
        db.session.add(user_msg)
        
        # Save assistant message
        assistant_msg = ChatMessage(
            session_id=session.id,
            role='assistant',
            content=response_data['content'],
            prompt_tokens=response_data['prompt_tokens'],
            completion_tokens=response_data['completion_tokens'],
            total_tokens=response_data['total_tokens']
        )
        db.session.add(assistant_msg)
        
        # Update session
        session.total_tokens += response_data['total_tokens']
        session.total_cost += response_data['cost']
        
        if response_data.get('new_summary'):
            session.summary = response_data['new_summary']
            session.summary_updated_at = datetime.utcnow()
        
        # Update user token usage
        user.daily_token_usage += response_data['total_tokens']
        user.total_token_usage += response_data['total_tokens']
        
        db.session.commit()
        
        return jsonify({
            'message': assistant_msg.to_dict(),
            'session': {
                'total_tokens': session.total_tokens,
                'total_cost': session.total_cost,
                'summary_updated': response_data.get('new_summary') is not None
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


def get_system_prompt(video_id, user_role):
    # Try to find video-specific prompt
    prompt_template = ChatPromptTemplate.query.filter_by(
        video_id=video_id,
        is_active=True
    ).first()
    
    # Try to find role-specific prompt
    if not prompt_template:
        prompt_template = ChatPromptTemplate.query.filter_by(
            user_role=user_role,
            is_active=True
        ).first()
    
    # Use default prompt
    if not prompt_template:
        prompt_template = ChatPromptTemplate.query.filter_by(
            is_default=True,
            is_active=True
        ).first()
    
    if prompt_template:
        return prompt_template.system_prompt
    
    # Fallback system prompt
    return "당신은 학습을 돕는 AI 조교입니다. 학생들의 질문에 친절하고 명확하게 답변해주세요."

