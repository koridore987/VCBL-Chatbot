"""
인증 관련 라우트 (로그인, 로그아웃)
"""
from flask import Blueprint, render_template, request, redirect, url_for, make_response
from app.models import DatabaseManager
import hashlib

# 블루프린트 생성
bp = Blueprint('auth', __name__)

# 데이터베이스 매니저
db_manager = DatabaseManager()

def hash_user_id(user_id):
    """사용자 ID 해시화"""
    return hashlib.sha256(str(user_id).encode()).hexdigest()

def check_user_auth(request):
    """사용자 인증 확인"""
    username = request.cookies.get('username')
    user_id_hash = request.cookies.get('user_id_hash')
    
    if username and user_id_hash:
        # 사용자 ID 조회
        user_id = db_manager.get_user_by_username(username)
        if user_id and user_id_hash == hash_user_id(user_id):
            return user_id
    return None

@bp.route('/', methods=['GET'])
def login_page():
    """로그인 페이지"""
    error = request.args.get('error', '')
    return render_template('login.html', error=error)

@bp.route('/login', methods=['POST'])
def login():
    """로그인 처리"""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    
    if not username or not password:
        return redirect(url_for('auth.login_page', error='사용자명과 비밀번호를 모두 입력해주세요.'))
    
    try:
        user_id = db_manager.authenticate_user(username, password)
        if user_id:
            # 쿠키 설정
            response = make_response(redirect(url_for('chat.chat_page')))
            response.set_cookie('username', username, max_age=86400)  # 24시간
            response.set_cookie('user_id_hash', hash_user_id(user_id), max_age=86400)
            return response
        else:
            return redirect(url_for('auth.login_page', error='잘못된 사용자명 또는 비밀번호입니다.'))
    except Exception as e:
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
    """로그아웃"""
    response = make_response(redirect(url_for('auth.login_page')))
    response.set_cookie('username', '', expires=0)
    response.set_cookie('user_id_hash', '', expires=0)
    return response
