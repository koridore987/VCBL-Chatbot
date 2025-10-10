"""
Flask 애플리케이션 팩토리
"""
import os
from flask import Flask, render_template, redirect, url_for
from app.routes import auth, chat, admin
from app import config
from app.utils.csrf import ensure_csrf_token

# 환경변수 로드 (PythonAnywhere 배포용)
def load_env_vars():
    """환경변수 로드"""
    # .env 파일이 있으면 로드 (로컬 개발용)
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

def create_app():
    """Flask 애플리케이션 생성 (Google Cloud 최적화)"""
    # 환경변수 로드
    load_env_vars()
    
    app = Flask(__name__)
    
    # Google Cloud 환경변수에서 설정 가져오기
    app.secret_key = os.environ.get('SECRET_KEY', config.SECRET_KEY)
    app.config['DEBUG'] = os.environ.get('FLASK_ENV') != 'production'
    
    # Google Cloud 최적화 설정
    app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS 필수 (Google Cloud)
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # JavaScript에서 쿠키 접근 방지
    app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'  # CSRF 공격 방지 (엄격)
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 세션 타임아웃 1시간
    app.config['SESSION_COOKIE_NAME'] = 'vcbl_session'  # 세션 쿠키 이름 변경
    
    # 성능 최적화 설정
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False  # JSON 압축
    app.config['JSON_SORT_KEYS'] = False  # JSON 정렬 비활성화
    app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024  # 파일 업로드 제한 8MB
    
    # 블루프린트 등록
    app.register_blueprint(auth.bp)
    app.register_blueprint(chat.bp)
    app.register_blueprint(admin.bp)
    
    # Google Cloud 헬스체크 엔드포인트
    @app.route('/_ah/health')
    def health_check():
        """Google Cloud 헬스체크"""
        return 'OK', 200
    
    # 성능 모니터링 엔드포인트 (Google Cloud 최적화)
    @app.route('/api/performance')
    def performance_stats():
        """성능 통계 API (관리자만 접근 가능)"""
        from app.optimization.performance_monitor import performance_monitor
        from app.optimization.memory_optimizer import memory_optimizer
        
        stats = performance_monitor.get_performance_stats()
        stats['memory_usage_mb'] = memory_optimizer.get_memory_usage()
        stats['is_overloaded'] = performance_monitor.is_overloaded()
        stats['recommendations'] = performance_monitor.get_recommendations()
        
        return jsonify(stats)
    
    # 메모리 정리 스케줄러 (백그라운드)
    import threading
    import time
    
    def cleanup_scheduler():
        """주기적 메모리 정리"""
        while True:
            time.sleep(300)  # 5분마다
            from app.optimization.memory_optimizer import memory_optimizer
            memory_optimizer.cleanup_memory()
    
    # 백그라운드 스레드 시작 (개발 환경에서는 비활성화)
    if not config.DEBUG:
        cleanup_thread = threading.Thread(target=cleanup_scheduler, daemon=True)
        cleanup_thread.start()
    
    @app.context_processor
    def inject_csrf():
        return {'csrf_token': ensure_csrf_token}
    
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
