"""
채팅 관련 라우트
"""
from flask import Blueprint, render_template, request, redirect, session, url_for, jsonify
from models import DatabaseManager
from services import ChatService

# 블루프린트 생성
bp = Blueprint('chat', __name__, url_prefix='/chat')

# 서비스 인스턴스
db_manager = DatabaseManager()
chat_service = ChatService()

@bp.route('/')
def chat_page():
    """채팅 페이지"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    
    user_id = session['user_id']
    messages = db_manager.get_user_messages(user_id)
    return render_template('index.html', messages=messages)

@bp.route('/send_message', methods=['POST'])
def send_message():
    """메시지 전송 API"""
    if 'user_id' not in session:
        return jsonify({'error': '로그인이 필요합니다'}), 401
    
    user_id = session['user_id']
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({'error': '메시지가 필요합니다'}), 400
    
    message = data['message']
    
    try:
        # 사용자 메시지 저장
        db_manager.save_message(user_id, 'user', message)
        
        # 봇 답변 생성
        bot_reply = chat_service.generate_response(user_id, message)
        
        # 봇 답변 저장
        db_manager.save_message(user_id, 'bot', bot_reply)
        
        return jsonify({'reply': bot_reply})
        
    except Exception as e:
        return jsonify({'error': f'오류가 발생했습니다: {str(e)}'}), 500
