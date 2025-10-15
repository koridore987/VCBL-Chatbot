from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from dotenv import load_dotenv
import os

load_dotenv()

# Extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()
migrate = Migrate()
# Limiter는 key_func만 전달하고, 나머지 설정은 app.config에서 읽도록
# 라우트 데코레이터가 import 시점에 작동하도록 인스턴스 필요
limiter = Limiter(key_func=get_remote_address)

# OpenAI 서비스는 요청마다 g 객체에 캐시됨
def get_openai_service():
    """요청당 OpenAI 서비스 싱글턴"""
    if 'openai_service' not in g:
        from app.services.openai_service import OpenAIService
        from flask import current_app
        g.openai_service = OpenAIService(current_app.config)
    return g.openai_service


def create_app(config_name=None):
    """애플리케이션 팩토리"""
    app = Flask(__name__)
    
    # URL trailing slash 문제 해결
    app.url_map.strict_slashes = False
    
    # 설정 로드
    from app.config import get_config
    config = get_config(config_name)
    app.config.from_object(config)
    
    # 익스텐션 초기화
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    # CORS 설정 (보안 강화)
    CORS(app, 
         origins=app.config['CORS_ORIGINS'],
         supports_credentials=app.config['CORS_SUPPORTS_CREDENTIALS'],
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # Rate Limiter 초기화
    # Flask-Limiter는 init_app 시 app.config에서 자동으로 설정을 읽음:
    # - RATELIMIT_STORAGE_URL
    # - RATELIMIT_DEFAULT
    # - RATELIMIT_ENABLED
    if app.config.get('RATELIMIT_ENABLED', True):
        limiter.init_app(app)
    else:
        # Rate limiting 비활성화 시에도 init_app 호출 (데코레이터가 no-op으로 동작)
        limiter.enabled = False
        limiter.init_app(app)
    
    # 로거 설정
    from app.utils import setup_logger
    setup_logger(app)
    
    # 에러 핸들러 등록
    from app.utils import register_error_handlers
    register_error_handlers(app)
    
    # 블루프린트 등록
    from app.routes.auth import auth_bp
    from app.routes.videos import videos_bp
    from app.routes.chat import chat_bp
    from app.routes.admin import admin_bp
    from app.routes.logs import logs_bp
    from app.routes.surveys import surveys_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(videos_bp, url_prefix='/api/videos')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(logs_bp, url_prefix='/api/logs')
    app.register_blueprint(surveys_bp, url_prefix='/api/surveys')
    
    # 헬스 체크 엔드포인트
    @app.route('/health')
    def health_check():
        return {'status': 'healthy'}, 200
    
    # API 헬스 체크 (업스트림 확인용)
    @app.route('/api/health')
    def api_health_check():
        return {'status': 'ok'}, 200
    
    # CLI 명령어 등록
    from app.cli import cli as cli_group
    app.cli.add_command(cli_group)
    init_admin_cmd = cli_group.get_command(app, 'init-admin')
    if init_admin_cmd is not None:
        app.cli.add_command(init_admin_cmd, name='init-admin')
    
    return app
