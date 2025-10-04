"""
관리자 관련 라우트
"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, make_response
from app.models import DatabaseManager
from app.models.admin import AdminManager
import hashlib
from app import config

# 블루프린트 생성
bp = Blueprint('admin', __name__, url_prefix='/admin')

# 매니저 인스턴스
db_manager = DatabaseManager()
admin_manager = AdminManager()

def check_admin_auth(request):
    """관리자 인증 확인"""
    admin_id = request.cookies.get('admin_id')
    admin_role = request.cookies.get('admin_role')
    
    if admin_id and admin_role:
        # 데이터베이스에서 관리자 존재 확인
        admin = admin_manager.get_admin_by_id(int(admin_id))
        if admin:
            return (int(admin_id), admin_role)
    return None

def require_auth(f):
    """인증 데코레이터"""
    def decorated_function(*args, **kwargs):
        auth = check_admin_auth(request)
        if not auth:
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def require_super(f):
    """Super 권한 데코레이터"""
    def decorated_function(*args, **kwargs):
        auth = check_admin_auth(request)
        if not auth:
            return redirect(url_for('admin.admin_login'))
        elif auth[1] != 'super':
            return redirect(url_for('admin.dashboard'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    """관리자 로그인"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        auth_result = admin_manager.authenticate_admin(username, password)
        if auth_result:
            admin_id, role = auth_result
            # 쿠키 설정
            response = make_response(redirect(url_for('admin.dashboard')))
            response.set_cookie('admin_id', str(admin_id), max_age=3600)  # 1시간
            response.set_cookie('admin_role', role, max_age=3600)
            return response
        else:
            return render_template('admin/login.html', error='잘못된 인증 정보입니다.')
    
    return render_template('admin/login.html')

@bp.route('/logout')
def admin_logout():
    """관리자 로그아웃"""
    response = make_response(redirect(url_for('admin.admin_login')))
    response.set_cookie('admin_id', '', expires=0)
    response.set_cookie('admin_role', '', expires=0)
    return response

@bp.route('/')
@require_auth
def dashboard():
    """관리자 대시보드"""
    
    # 사용자 목록 가져오기
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        # 사용자별 메시지 수 통계
        cursor.execute("""
            SELECT u.id, u.username, COUNT(m.id) as message_count,
                   MAX(m.timestamp) as last_message
            FROM user u
            LEFT JOIN message m ON u.id = m.user_id
            GROUP BY u.id, u.username
            ORDER BY last_message DESC
        """)
        users = cursor.fetchall()
        
        # 전체 통계
        cursor.execute("SELECT COUNT(*) FROM user")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM message")
        total_messages = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM message WHERE sender = 'user'")
        user_messages = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM message WHERE sender = 'bot'")
        bot_messages = cursor.fetchone()[0]
        
    finally:
        conn.close()
    
    return render_template('admin/dashboard.html', 
                         users=users,
                         total_users=total_users,
                         total_messages=total_messages,
                         user_messages=user_messages,
                         bot_messages=bot_messages)

@bp.route('/user/<int:user_id>')
def user_detail(user_id):
    """사용자 상세 정보 및 채팅 기록"""
    if not check_admin_auth(request):
        return redirect(url_for('admin.admin_login'))
    
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        # 사용자 정보
        cursor.execute("SELECT id, username FROM user WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return redirect(url_for('admin.dashboard'))
        
        # 사용자의 모든 메시지
        cursor.execute("""
            SELECT sender, content, timestamp
            FROM message
            WHERE user_id = ?
            ORDER BY timestamp ASC
        """, (user_id,))
        messages = cursor.fetchall()
        
    finally:
        conn.close()
    
    return render_template('admin/user_detail.html', user=user, messages=messages)

@bp.route('/admins')
@require_super
def admin_management():
    """관리자 계정 관리 (Super 권한 필요)"""
    admins = admin_manager.get_all_admins()
    return render_template('admin/admin_management.html', admins=admins)

@bp.route('/create_admin', methods=['POST'])
@require_super
def create_admin():
    """새 관리자 생성 (Super 권한 필요)"""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    role = request.form.get('role', 'admin').strip()
    
    if not username or not password:
        return redirect(url_for('admin.admin_management'))
    
    success = admin_manager.create_admin(username, password, role)
    if success:
        return redirect(url_for('admin.admin_management'))
    else:
        return redirect(url_for('admin.admin_management'))

@bp.route('/change_password/<int:admin_id>', methods=['POST'])
@require_super
def change_password(admin_id):
    """관리자 비밀번호 변경 (Super 권한 필요)"""
    new_password = request.form.get('new_password', '').strip()
    
    if not new_password:
        return redirect(url_for('admin.admin_management'))
    
    success = admin_manager.update_admin_password(admin_id, new_password)
    return redirect(url_for('admin.admin_management'))

@bp.route('/delete_admin/<int:admin_id>', methods=['POST'])
@require_super
def delete_admin(admin_id):
    """관리자 삭제 (Super 권한 필요)"""
    current_admin_id = check_admin_auth(request)[0]
    success = admin_manager.delete_admin(admin_id, current_admin_id)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': '삭제할 수 없습니다.'}), 400

@bp.route('/users')
@require_auth
def user_management():
    """회원 관리 페이지"""
    users = db_manager.get_all_users_with_stats()
    stats = db_manager.get_user_stats()
    total_users, active_users, total_messages, recent_users = stats
    
    return render_template('admin/user_management.html', 
                         users=users,
                         total_users=total_users,
                         active_users=active_users,
                         total_messages=total_messages,
                         recent_users=recent_users)

@bp.route('/delete_user/<int:user_id>', methods=['POST'])
@require_auth
def delete_user(user_id):
    """회원 삭제"""
    success = db_manager.delete_user(user_id)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': '삭제에 실패했습니다.'}), 400

@bp.route('/api/user/<int:user_id>/messages')
def user_messages_api(user_id):
    """사용자 메시지 API"""
    if not check_admin_auth(request):
        return jsonify({'error': '인증이 필요합니다'}), 401
    
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT sender, content, timestamp
            FROM message
            WHERE user_id = ?
            ORDER BY timestamp ASC
        """, (user_id,))
        messages = cursor.fetchall()
        
        # JSON 형태로 변환
        messages_data = []
        for sender, content, timestamp in messages:
            messages_data.append({
                'sender': sender,
                'content': content,
                'timestamp': timestamp
            })
        
        return jsonify({'messages': messages_data})
        
    finally:
        conn.close()
