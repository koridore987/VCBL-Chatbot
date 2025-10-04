"""
Flask 애플리케이션 팩토리
"""
from flask import Flask
from app.routes import auth, chat
import config

def create_app():
    """Flask 애플리케이션 생성"""
    app = Flask(__name__)
    
    # config.py에서 설정 가져오기
    app.secret_key = config.SECRET_KEY
    app.config['DEBUG'] = config.DEBUG
    
    # 블루프린트 등록
    app.register_blueprint(auth.bp)
    app.register_blueprint(chat.bp)
    
    return app
