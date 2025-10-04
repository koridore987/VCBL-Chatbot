"""
인증 관련 라우트 (로그인, 로그아웃)
"""
from flask import Blueprint, render_template, request, redirect, session, url_for
from models import DatabaseManager

# 블루프린트 생성
bp = Blueprint('auth', __name__)

# 데이터베이스 매니저
db_manager = DatabaseManager()

@bp.route('/', methods=['GET'])
def login_page():
    """로그인 페이지"""
    return render_template('login.html')

@bp.route('/login', methods=['POST'])
def login():
    """로그인 처리"""
    username = request.form.get('username', '').strip()
    if not username:
        return redirect(url_for('auth.login_page'))
    
    try:
        user_id = db_manager.get_or_create_user(username)
        session['user_id'] = user_id
        return redirect(url_for('chat.chat_page'))
    except Exception as e:
        return redirect(url_for('auth.login_page'))

@bp.route('/logout')
def logout():
    """로그아웃"""
    session.clear()
    return redirect(url_for('auth.login_page'))
