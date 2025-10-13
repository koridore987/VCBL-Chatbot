from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.event_log import EventLog
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from functools import wraps
import csv
import io
from datetime import datetime

logs_bp = Blueprint('logs', __name__)

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role not in ['admin', 'super']:
            return jsonify({'error': '관리자 권한이 필요합니다'}), 403
        
        return fn(*args, **kwargs)
    
    return wrapper


@logs_bp.route('/events', methods=['GET'])
@admin_required
def get_event_logs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    event_type = request.args.get('event_type')
    user_id = request.args.get('user_id', type=int)
    video_id = request.args.get('video_id', type=int)
    
    query = EventLog.query
    
    if event_type:
        query = query.filter_by(event_type=event_type)
    if user_id:
        query = query.filter_by(user_id=user_id)
    if video_id:
        query = query.filter_by(video_id=video_id)
    
    query = query.order_by(EventLog.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'logs': [log.to_dict() for log in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@logs_bp.route('/events/export', methods=['GET'])
@admin_required
def export_event_logs():
    event_type = request.args.get('event_type')
    user_id = request.args.get('user_id', type=int)
    video_id = request.args.get('video_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = EventLog.query
    
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
    
    logs = query.order_by(EventLog.created_at).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['ID', 'User ID', 'Video ID', 'Event Type', 'Event Data', 'IP Address', 'User Agent', 'Created At'])
    
    # Data
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


@logs_bp.route('/chat-sessions/export', methods=['GET'])
@admin_required
def export_chat_sessions():
    user_id = request.args.get('user_id', type=int)
    video_id = request.args.get('video_id', type=int)
    
    query = ChatSession.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    if video_id:
        query = query.filter_by(video_id=video_id)
    
    sessions = query.order_by(ChatSession.created_at).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Session ID', 'User ID', 'Video ID', 'Message ID', 'Role', 'Content', 
        'Prompt Tokens', 'Completion Tokens', 'Total Tokens', 'Created At'
    ])
    
    # Data
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


@logs_bp.route('/stats', methods=['GET'])
@admin_required
def get_stats():
    # User stats
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    
    # Token stats
    total_tokens = db.session.query(db.func.sum(User.total_token_usage)).scalar() or 0
    
    # Chat stats
    total_sessions = ChatSession.query.count()
    total_messages = ChatMessage.query.count()
    
    # Event stats
    total_events = EventLog.query.count()
    
    return jsonify({
        'users': {
            'total': total_users,
            'active': active_users
        },
        'tokens': {
            'total': total_tokens
        },
        'chat': {
            'sessions': total_sessions,
            'messages': total_messages
        },
        'events': {
            'total': total_events
        }
    }), 200

