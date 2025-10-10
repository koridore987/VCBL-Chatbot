"""
채팅 관련 라우트
"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.models import DatabaseManager
from app.models.video import VideoManager
from app.models.activity_log import ActivityLogManager
from app.services import ChatService
from app.routes.auth import check_user_auth

# 블루프린트 생성
bp = Blueprint('chat', __name__, url_prefix='/chat')

# 서비스 인스턴스
db_manager = DatabaseManager()
video_manager = VideoManager()
activity_log_manager = ActivityLogManager()
chat_service = ChatService()

@bp.route('/')
def chat_page():
    """채팅 페이지"""
    user_id = check_user_auth(request)
    if not user_id:
        return redirect(url_for('auth.login_page'))
    
    messages = db_manager.get_user_messages(user_id)
    latest_video = video_manager.get_latest_video()
    
    # 현재 활동 모드 확인
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'activity_mode'")
    current_mode = cursor.fetchone()
    current_mode = current_mode[0] if current_mode else 'chatbot'
    
    # 질문지 모드인 경우 질문 목록 가져오기
    questions = []
    if current_mode == 'questionnaire':
        cursor.execute("SELECT id, question, order_index FROM qa_template ORDER BY order_index ASC")
        questions = cursor.fetchall()
    
    conn.close()
    
    return render_template('index.html', 
                         messages=messages, 
                         latest_video=latest_video,
                         current_mode=current_mode,
                         questions=questions)

@bp.route('/send_message', methods=['POST'])
def send_message():
    """메시지 전송 API"""
    user_id = check_user_auth(request)
    if not user_id:
        return jsonify({'error': '로그인이 필요합니다'}), 401
    
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

@bp.route('/log_activity', methods=['POST'])
def log_activity():
    """활동 로그 기록 API"""
    user_id = check_user_auth(request)
    if not user_id:
        return jsonify({'error': '로그인이 필요합니다'}), 401
    
    data = request.get_json()
    
    if not data or 'activity_type' not in data:
        return jsonify({'error': '활동 타입이 필요합니다'}), 400
    
    try:
        activity_type = data['activity_type']
        content = data.get('content', '')
        metadata = data.get('metadata', {})
        video_id = data.get('video_id')
        
        # 활동 로그 기록
        log_id = activity_log_manager.log_activity(
            user_id=user_id,
            activity_type=activity_type,
            content=content,
            metadata=metadata,
            video_id=video_id
        )
        
        return jsonify({'success': True, 'log_id': log_id})
        
    except Exception as e:
        return jsonify({'error': f'로그 기록 중 오류가 발생했습니다: {str(e)}'}), 500

@bp.route('/save_questionnaire', methods=['POST'])
def save_questionnaire():
    """질문지 답변 저장"""
    user_id = check_user_auth(request)
    if not user_id:
        return jsonify({'error': '로그인이 필요합니다'}), 401
    
    data = request.get_json()
    
    if not data or 'answers' not in data:
        return jsonify({'error': '답변 데이터가 필요합니다'}), 400
    
    answers = data['answers']
    
    try:
        # 답변 저장
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        for question_id, answer in answers.items():
            # 답변 저장 (기존 답변이 있으면 업데이트)
            cursor.execute("""
                INSERT OR REPLACE INTO qa_responses 
                (user_id, question_id, answer, created_at, updated_at) 
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (user_id, question_id, answer))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '답변이 저장되었습니다'})
    except Exception as e:
        return jsonify({'error': f'답변 저장 중 오류가 발생했습니다: {str(e)}'}), 500
