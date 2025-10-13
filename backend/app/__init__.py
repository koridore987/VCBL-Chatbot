from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://localhost/vcbl_chatbot')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['JWT_SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_HEADER_TYPE'] = 'Bearer'
    
    # OpenAI Configuration
    app.config['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
    app.config['MODEL_NAME'] = os.getenv('MODEL_NAME', 'gpt-4o-mini')
    app.config['SUMMARY_TRIGGER_TOKENS'] = int(os.getenv('SUMMARY_TRIGGER_TOKENS', 3500))
    app.config['MAX_TOKENS_PER_REQUEST'] = int(os.getenv('MAX_TOKENS_PER_REQUEST', 4000))
    app.config['MAX_TOKENS_OUTPUT'] = int(os.getenv('MAX_TOKENS_OUTPUT', 1000))
    app.config['DAILY_TOKEN_LIMIT'] = int(os.getenv('DAILY_TOKEN_LIMIT', 50000))
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)
    CORS(app)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.videos import videos_bp
    from app.routes.chat import chat_bp
    from app.routes.admin import admin_bp
    from app.routes.logs import logs_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(videos_bp, url_prefix='/api/videos')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(logs_bp, url_prefix='/api/logs')
    
    return app

