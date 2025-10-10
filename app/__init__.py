"""
Flask 애플리케이션 팩토리
"""
from flask import Flask, render_template, redirect, url_for
from app.routes import auth, chat, admin
from app import config

def create_app():
    """Flask 애플리케이션 생성"""
    app = Flask(__name__)
    
    # config.py에서 설정 가져오기
    app.secret_key = config.SECRET_KEY
    app.config['DEBUG'] = config.DEBUG
    
    # 보안 설정
    app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS에서만 쿠키 전송
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # JavaScript에서 쿠키 접근 방지
    app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'  # CSRF 공격 방지
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 세션 타임아웃 1시간
    app.config['SESSION_COOKIE_NAME'] = 'vcbl_session'  # 세션 쿠키 이름 변경
    
    # 블루프린트 등록
    app.register_blueprint(auth.bp)
    app.register_blueprint(chat.bp)
    app.register_blueprint(admin.bp)
    
    # 에러 핸들러 등록
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('error.html', 
                             error_code=403, 
                             error_message="접근 권한이 없습니다. 로그인이 필요합니다."), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return render_template('error.html', 
                             error_code=404, 
                             error_message="페이지를 찾을 수 없습니다."), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.html', 
                             error_code=500, 
                             error_message="서버 내부 오류가 발생했습니다."), 500
    
    return app
