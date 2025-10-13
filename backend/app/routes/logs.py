"""
로그 관련 라우트
이벤트 로그 및 통계 조회
"""
from flask import Blueprint, request, send_file
from app import db
from app.models.user import User
from app.models.event_log import EventLog
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.utils import admin_required, success_response, error_response, paginated_response
from datetime import datetime
import csv
import io
import logging

logger = logging.getLogger(__name__)

logs_bp = Blueprint('logs', __name__)


@logs_bp.route('/events', methods=['GET'])
@admin_required
def get_event_logs():
    """이벤트 로그 조회 (페이지네이션)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)  # 최대 100개로 제한
        event_type = request.args.get('event_type')
        user_id = request.args.get('user_id', type=int)
        video_id = request.args.get('video_id', type=int)
        
        query = EventLog.query
        
        # 필터링
        if event_type:
            query = query.filter_by(event_type=event_type)
        if user_id:
            query = query.filter_by(user_id=user_id)
        if video_id:
            query = query.filter_by(video_id=video_id)
        
        query = query.order_by(EventLog.created_at.desc())
        
        # 페이지네이션
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return paginated_response(
            items=[log.to_dict() for log in pagination.items],
            total=pagination.total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Get event logs error: {str(e)}")
        return error_response('로그 조회 중 오류가 발생했습니다', 500)


@logs_bp.route('/events/export', methods=['GET'])
@admin_required
def export_event_logs():
    """이벤트 로그 CSV 내보내기"""
    try:
        event_type = request.args.get('event_type')
        user_id = request.args.get('user_id', type=int)
        video_id = request.args.get('video_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = EventLog.query
        
        # 필터링
        if event_type:
            query = query.filter_by(event_type=event_type)
        if user_id:
            query = query.filter_by(user_id=user_id)
        if video_id:
            query = query.filter_by(video_id=video_id)
        if start_date:
            query = query.filter(EventLog.created_at >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(EventLog.created_at <= datetime.fromisoformat(end_date))
        
        # 최대 10000개로 제한
        logs = query.order_by(EventLog.created_at).limit(10000).all()
        
        # CSV 생성
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 헤더
        writer.writerow(['ID', 'User ID', 'Video ID', 'Event Type', 'Event Data', 'IP Address', 'User Agent', 'Created At'])
        
        # 데이터
        for log in logs:
            writer.writerow([
                log.id,
                log.user_id,
                log.video_id,
                log.event_type,
                log.event_data,
                log.ip_address,
                log.user_agent,
                log.created_at.isoformat()
            ])
        
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'event_logs_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        logger.error(f"Export event logs error: {str(e)}")
        return error_response('로그 내보내기 중 오류가 발생했습니다', 500)


@logs_bp.route('/chat-messages', methods=['GET'])
@admin_required
def get_chat_messages():
    """채팅 메시지 로그 조회 (페이지네이션)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        user_id = request.args.get('user_id', type=int)
        video_id = request.args.get('video_id', type=int)
        session_id = request.args.get('session_id', type=int)
        
        query = ChatMessage.query.join(ChatSession)
        
        # 필터링
        if user_id:
            query = query.filter(ChatSession.user_id == user_id)
        if video_id:
            query = query.filter(ChatSession.video_id == video_id)
        if session_id:
            query = query.filter(ChatMessage.session_id == session_id)
        
        query = query.order_by(ChatMessage.created_at.desc())
        
        # 페이지네이션
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 메시지와 세션 정보를 함께 반환
        items = []
        for message in pagination.items:
            message_dict = message.to_dict()
            message_dict['session'] = {
                'user_id': message.session.user_id,
                'video_id': message.session.video_id
            }
            items.append(message_dict)
        
        return paginated_response(
            items=items,
            total=pagination.total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Get chat messages error: {str(e)}")
        return error_response('채팅 메시지 조회 중 오류가 발생했습니다', 500)


@logs_bp.route('/timeline', methods=['GET'])
@admin_required
def get_activity_timeline():
    """채팅 세션과 비디오 이벤트를 통합한 타임라인 조회"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)
        user_id = request.args.get('user_id', type=int)
        video_id = request.args.get('video_id', type=int)
        
        # 채팅 세션 조회
        session_query = ChatSession.query
        if user_id:
            session_query = session_query.filter_by(user_id=user_id)
        if video_id:
            session_query = session_query.filter_by(video_id=video_id)
        
        session_query = session_query.order_by(ChatSession.updated_at.desc())
        pagination = session_query.paginate(page=page, per_page=per_page, error_out=False)
        
        sessions = []
        for session in pagination.items:
            session_dict = session.to_dict(include_messages=True)
            
            # 사용자 정보 추가
            user = User.query.get(session.user_id)
            if user:
                session_dict['user'] = {
                    'id': user.id,
                    'name': user.name,
                    'student_id': user.student_id
                }
            
            # 세션 시간 범위 내의 비디오 이벤트 가져오기
            event_query = EventLog.query.filter(
                EventLog.user_id == session.user_id,
                EventLog.video_id == session.video_id,
                EventLog.event_type != 'chat_message'  # chat_message 제외
            )
            
            # 세션 생성 시간부터 마지막 업데이트 시간까지의 이벤트만
            if session.created_at:
                event_query = event_query.filter(EventLog.created_at >= session.created_at)
            if session.updated_at:
                event_query = event_query.filter(EventLog.created_at <= session.updated_at)
            
            events = event_query.order_by(EventLog.created_at).all()
            session_dict['video_events'] = [event.to_dict() for event in events]
            
            sessions.append(session_dict)
        
        return paginated_response(
            items=sessions,
            total=pagination.total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Get activity timeline error: {str(e)}")
        return error_response('활동 타임라인 조회 중 오류가 발생했습니다', 500)


@logs_bp.route('/chat-sessions-grouped', methods=['GET'])
@admin_required
def get_chat_sessions_grouped():
    """채팅 세션별로 그룹화된 로그 조회 (페이지네이션)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)  # 세션 단위이므로 더 적은 수
        user_id = request.args.get('user_id', type=int)
        video_id = request.args.get('video_id', type=int)
        
        query = ChatSession.query
        
        # 필터링
        if user_id:
            query = query.filter_by(user_id=user_id)
        if video_id:
            query = query.filter_by(video_id=video_id)
        
        # 최근 세션부터
        query = query.order_by(ChatSession.updated_at.desc())
        
        # 페이지네이션
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 세션과 메시지를 함께 반환
        items = []
        for session in pagination.items:
            session_dict = session.to_dict(include_messages=True)
            # 사용자와 비디오 정보 추가
            user = User.query.get(session.user_id)
            if user:
                session_dict['user'] = {
                    'id': user.id,
                    'name': user.name,
                    'student_id': user.student_id
                }
            items.append(session_dict)
        
        return paginated_response(
            items=items,
            total=pagination.total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Get chat sessions grouped error: {str(e)}")
        return error_response('채팅 세션 조회 중 오류가 발생했습니다', 500)


@logs_bp.route('/chat-sessions/export', methods=['GET'])
@admin_required
def export_chat_sessions():
    """채팅 세션 CSV 내보내기"""
    try:
        user_id = request.args.get('user_id', type=int)
        video_id = request.args.get('video_id', type=int)
        
        query = ChatSession.query
        
        # 필터링
        if user_id:
            query = query.filter_by(user_id=user_id)
        if video_id:
            query = query.filter_by(video_id=video_id)
        
        # 최대 1000개 세션으로 제한
        sessions = query.order_by(ChatSession.created_at).limit(1000).all()
        
        # CSV 생성
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 헤더
        writer.writerow([
            'Session ID', 'User ID', 'Video ID', 'Message ID', 'Role', 'Content', 
            'Prompt Tokens', 'Completion Tokens', 'Total Tokens', 'Created At'
        ])
        
        # 데이터
        for session in sessions:
            for message in session.messages:
                writer.writerow([
                    session.id,
                    session.user_id,
                    session.video_id,
                    message.id,
                    message.role,
                    message.content,
                    message.prompt_tokens,
                    message.completion_tokens,
                    message.total_tokens,
                    message.created_at.isoformat()
                ])
        
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'chat_sessions_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        logger.error(f"Export chat sessions error: {str(e)}")
        return error_response('채팅 세션 내보내기 중 오류가 발생했습니다', 500)


@logs_bp.route('/stats', methods=['GET'])
@admin_required
def get_stats():
    """전체 통계 조회"""
    try:
        # 사용자 통계
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        
        # 토큰 통계 - User 테이블에서 집계
        total_tokens_from_users = db.session.query(db.func.sum(User.total_token_usage)).scalar() or 0
        daily_tokens_from_users = db.session.query(db.func.sum(User.daily_token_usage)).scalar() or 0
        
        # 토큰 통계 - ChatMessage 테이블에서 직접 집계 (더 정확함)
        total_tokens_from_messages = db.session.query(db.func.sum(ChatMessage.total_tokens)).scalar() or 0
        
        # 오늘 날짜의 메시지에서 토큰 집계
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        daily_tokens_from_messages = db.session.query(
            db.func.sum(ChatMessage.total_tokens)
        ).filter(
            ChatMessage.created_at >= today_start
        ).scalar() or 0
        
        # ChatMessage 기준 값 사용 (더 정확함)
        total_tokens = total_tokens_from_messages
        daily_tokens = daily_tokens_from_messages
        
        # 채팅 통계
        total_sessions = ChatSession.query.count()
        total_messages = ChatMessage.query.count()
        
        # 이벤트 통계
        total_events = EventLog.query.count()
        
        return success_response({
            'users': {
                'total': total_users,
                'active': active_users,
                'inactive': total_users - active_users
            },
            'tokens': {
                'total': total_tokens,
                'daily': daily_tokens,
                # 디버깅용 추가 정보
                'from_users': total_tokens_from_users,
                'from_messages': total_tokens_from_messages,
                'daily_from_users': daily_tokens_from_users,
                'daily_from_messages': daily_tokens_from_messages
            },
            'chat': {
                'sessions': total_sessions,
                'messages': total_messages,
                'average_messages_per_session': round(total_messages / total_sessions, 2) if total_sessions > 0 else 0
            },
            'events': {
                'total': total_events
            }
        })
        
    except Exception as e:
        logger.error(f"Get stats error: {str(e)}")
        return error_response('통계 조회 중 오류가 발생했습니다', 500)
