"""
인증 관련 라우트 (로그인, 로그아웃)
"""
from flask import Blueprint, render_template, request, redirect, url_for, make_response, session, flash
from app.models import DatabaseManager
import hashlib
import secrets
import time
import os
from datetime import datetime, timedelta
import bcrypt

# 블루프린트 생성
bp = Blueprint('auth', __name__)

# 데이터베이스 매니저
db_manager = DatabaseManager()

# 보안 설정
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 300  # 5분
SESSION_TIMEOUT = 3600  # 1시간

# 로그인 시도 추적 (실제 환경에서는 Redis 등 사용)
login_attempts = {}

def hash_user_id(user_id):
    """사용자 ID 해시화 (솔트 추가)"""
    salt = os.environ.get('SECRET_KEY', 'default_salt')
    return hashlib.sha256(f"{user_id}{salt}".encode()).hexdigest()

def hash_password(password):
    """비밀번호 해시화 (bcrypt 사용)"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """비밀번호 검증"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def is_account_locked(user_id):
    """계정 잠금 상태 확인"""
    if user_id in login_attempts:
        attempts, lockout_time = login_attempts[user_id]
        if attempts >= MAX_LOGIN_ATTEMPTS and time.time() < lockout_time:
            return True
    return False

def record_login_attempt(user_id, success):
    """로그인 시도 기록"""
    current_time = time.time()
    
    if user_id not in login_attempts:
        login_attempts[user_id] = [0, 0]
    
    attempts, lockout_time = login_attempts[user_id]
    
    if success:
        # 성공 시 시도 횟수 초기화
        login_attempts[user_id] = [0, 0]
    else:
        # 실패 시 시도 횟수 증가
        attempts += 1
        if attempts >= MAX_LOGIN_ATTEMPTS:
            lockout_time = current_time + LOCKOUT_DURATION
        login_attempts[user_id] = [attempts, lockout_time]

def generate_csrf_token():
    """CSRF 토큰 생성"""
    return secrets.token_hex(32)

def validate_csrf_token(token):
    """CSRF 토큰 검증"""
    return token and token == session.get('csrf_token')

def check_user_auth(request):
    """사용자 인증 확인 (보안 강화)"""
    # 세션 기반 인증으로 변경
    if 'user_id' in session and 'user_type' in session:
        # 세션 타임아웃 확인
        if 'last_activity' in session:
            last_activity = session['last_activity']
            if time.time() - last_activity > SESSION_TIMEOUT:
                session.clear()
                return None
        
        # 활동 시간 업데이트
        session['last_activity'] = time.time()
        return session['user_id']
    
    return None

@bp.route('/', methods=['GET'])
def login_page():
    """로그인 페이지 (보안 강화)"""
    # CSRF 토큰 생성
    csrf_token = generate_csrf_token()
    session['csrf_token'] = csrf_token
    
    error = request.args.get('error', '')
    return render_template('login.html', error=error, csrf_token=csrf_token)

@bp.route('/login', methods=['POST'])
def login():
    """로그인 처리 (보안 강화)"""
    # CSRF 토큰 검증
    csrf_token = request.form.get('csrf_token', '')
    if not validate_csrf_token(csrf_token):
        return redirect(url_for('auth.login_page', error='보안 토큰이 유효하지 않습니다.'))
    
    user_id = request.form.get('user_id', '').strip()
    password = request.form.get('password', '').strip()
    
    # 입력 검증
    if not user_id or not password:
        return redirect(url_for('auth.login_page', error='ID와 비밀번호를 모두 입력해주세요.'))
    
    # 길이 제한
    if len(user_id) > 50 or len(password) > 100:
        return redirect(url_for('auth.login_page', error='입력값이 너무 깁니다.'))
    
    # 계정 잠금 확인
    if is_account_locked(user_id):
        return redirect(url_for('auth.login_page', error='계정이 일시적으로 잠겼습니다. 5분 후 다시 시도해주세요.'))
    
    try:
        # 먼저 학습자로 로그인 시도
        student_id = db_manager.authenticate_user(user_id, password)
        if student_id:
            # 세션 생성
            session['user_id'] = student_id
            session['user_type'] = 'student'
            session['last_activity'] = time.time()
            session['csrf_token'] = generate_csrf_token()
            
            # 로그인 성공 기록
            record_login_attempt(user_id, True)
            
            # 보안 쿠키 설정
            response = make_response(redirect(url_for('chat.chat_page')))
            response.set_cookie('session_id', secrets.token_hex(32), 
                             max_age=SESSION_TIMEOUT, 
                             httponly=True, 
                             secure=True, 
                             samesite='Strict')
            return response
        
        # 학습자 로그인 실패 시 관리자로 로그인 시도
        from app.models.admin import AdminManager
        admin_manager = AdminManager()
        admin_id = admin_manager.authenticate_admin(user_id, password)
        if admin_id:
            # 세션 생성
            session['user_id'] = admin_id
            session['user_type'] = 'admin'
            session['last_activity'] = time.time()
            session['csrf_token'] = generate_csrf_token()
            
            # 로그인 성공 기록
            record_login_attempt(user_id, True)
            
            # 보안 쿠키 설정
            response = make_response(redirect(url_for('admin.dashboard')))
            response.set_cookie('session_id', secrets.token_hex(32), 
                             max_age=SESSION_TIMEOUT, 
                             httponly=True, 
                             secure=True, 
                             samesite='Strict')
            return response
        
        # 둘 다 실패 - 로그인 시도 기록
        record_login_attempt(user_id, False)
        
        # 일반적인 오류 메시지 (정보 누출 방지)
        return redirect(url_for('auth.login_page', error='ID 또는 비밀번호를 확인해주세요.'))
            
    except Exception as e:
        # 로그인 시도 기록
        record_login_attempt(user_id, False)
        
        # 보안을 위해 상세 오류 정보 숨김
        print(f"로그인 오류: {str(e)}")
        return redirect(url_for('auth.login_page', error='로그인 중 오류가 발생했습니다.'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """사용자 등록"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if not username or not password:
            return render_template('register.html', error='모든 필드를 입력해주세요.')
        
        if password != confirm_password:
            return render_template('register.html', error='비밀번호가 일치하지 않습니다.')
        
        try:
            # 사용자명 중복 확인
            if db_manager.get_user_by_username(username):
                return render_template('register.html', error='이미 존재하는 사용자명입니다.')
            
            # 새 사용자 생성
            user_id = db_manager.create_user(username, password)
            
            # 자동 로그인
            response = make_response(redirect(url_for('chat.chat_page')))
            response.set_cookie('username', username, max_age=86400)
            response.set_cookie('user_id_hash', hash_user_id(user_id), max_age=86400)
            return response
            
        except Exception as e:
            print(f"회원 등록 오류: {str(e)}")  # 디버깅을 위한 로그
            return render_template('register.html', error=f'등록 중 오류가 발생했습니다: {str(e)}')
    
    return render_template('register.html')

@bp.route('/logout')
def logout():
    """로그아웃 (보안 강화)"""
    # 세션 완전 삭제
    session.clear()
    
    # 보안 쿠키 삭제
    response = make_response(redirect(url_for('auth.login_page')))
    response.set_cookie('session_id', '', expires=0, httponly=True, secure=True, samesite='Strict')
    response.set_cookie('username', '', expires=0)
    response.set_cookie('user_id_hash', '', expires=0)
    response.set_cookie('user_type', '', expires=0)
    response.set_cookie('admin_username', '', expires=0)
    response.set_cookie('admin_id_hash', '', expires=0)
    
    return response
