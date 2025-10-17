"""
애플리케이션 설정 관리
- 로컬 개발: .env 파일 사용
- 프로덕션: Google Cloud Secret Manager 사용
"""
import os
from datetime import timedelta


def get_ratelimit_storage_url(require_distributed: bool = False) -> str:
    """
    Rate limiting 스토리지 백엔드를 반환합니다.

    Cloud Run과 같은 분산 환경에서는 인메모리 스토리지를 사용할 수 없으므로
    production 환경에서는 외부 Redis(또는 호환 서비스)를 강제합니다.
    """
    url = os.getenv('RATELIMIT_STORAGE_URL') or os.getenv('REDIS_URL') or 'memory://'

    if require_distributed and url.startswith('memory://'):
        raise ValueError(
            "프로덕션 환경에서는 분산 Rate Limiting을 위해 RATELIMIT_STORAGE_URL "
            "또는 REDIS_URL 환경 변수를 Redis와 같은 외부 저장소로 설정해야 합니다."
        )

    return url


def get_database_url():
    """
    데이터베이스 URL을 반환합니다.
    
    우선순위:
    1. DATABASE_URL 환경 변수 (명시적 설정)
    2. CLOUD_SQL_INSTANCE (Cloud Run/GCP 환경)
    3. SQLite (로컬 개발 환경 - Docker Compose PostgreSQL 권장)
    """
    # 1. DATABASE_URL이 명시적으로 설정된 경우 사용
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return database_url
    
    # 2. Cloud SQL 인스턴스 연결 (Unix 소켓 사용)
    instance_connection_name = os.getenv('CLOUD_SQL_INSTANCE')
    if instance_connection_name:
        db_user = os.getenv('DB_USER', 'vcbl_user')
        db_password = os.getenv('DB_PASSWORD')
        db_name = os.getenv('DB_NAME', 'vcbl_chatbot')
        
        if not db_password:
            raise ValueError(
                "DB_PASSWORD 환경 변수가 설정되지 않았습니다. "
                "Cloud SQL 연결에 필수입니다."
            )
        
        # Cloud Run에서는 Unix 소켓을 통해 Cloud SQL에 연결
        # 형식: postgresql+psycopg://USER:PASSWORD@/DATABASE?host=/cloudsql/INSTANCE_CONNECTION_NAME
        # URL 인코딩 처리
        import urllib.parse
        encoded_password = urllib.parse.quote_plus(db_password)
        return f"postgresql+psycopg://{db_user}:{encoded_password}@/{db_name}?host=/cloudsql/{instance_connection_name}"
    
    # 3. 기본 연결이 명시되지 않은 경우 오류 발생
    raise ValueError(
        "DATABASE_URL 환경 변수가 설정되지 않았습니다. "
        "로컬 개발: docker-compose.yml에서 자동 주입, "
        "프로덕션: Secret Manager에서 주입되어야 합니다."
    )


class Config:
    """기본 설정"""
    
    # 데이터베이스
    SQLALCHEMY_DATABASE_URI = get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # PostgreSQL 연결 풀 설정 (다중 작업 지원)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # 연결 유효성 검사
        'pool_recycle': 300,    # 5분마다 연결 재사용
        'pool_size': 10,        # 기본 연결 풀 크기
        'max_overflow': 20,     # 추가 연결 허용 수
        'pool_timeout': 30,     # 연결 대기 시간 (초)
    }
    
    # 보안
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY 환경 변수가 설정되지 않았습니다. 보안을 위해 필수입니다.")
    
    # JWT 설정
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES_DAYS', 7)))
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # CORS 설정 (로컬 개발용 기본값)
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:3000').split(',')
    CORS_SUPPORTS_CREDENTIALS = True
    
    # OpenAI 설정
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
    
    MODEL_NAME = os.getenv('MODEL_NAME', 'gpt-4o-mini')
    SUMMARY_TRIGGER_TOKENS = int(os.getenv('SUMMARY_TRIGGER_TOKENS', 3500))
    MAX_TOKENS_PER_REQUEST = int(os.getenv('MAX_TOKENS_PER_REQUEST', 4000))
    MAX_TOKENS_OUTPUT = int(os.getenv('MAX_TOKENS_OUTPUT', 1000))
    OPENAI_TIMEOUT = int(os.getenv('OPENAI_TIMEOUT', 30))  # 초
    OPENAI_MAX_RETRIES = int(os.getenv('OPENAI_MAX_RETRIES', 3))
    
    # 토큰 제한
    DAILY_TOKEN_LIMIT = int(os.getenv('DAILY_TOKEN_LIMIT', 50000))
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = get_ratelimit_storage_url()
    RATELIMIT_STRATEGY = 'fixed-window'
    RATELIMIT_DEFAULT = '100 per minute'
    
    # 로깅
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 입력 검증 제한
    MAX_MESSAGE_LENGTH = 2000
    MAX_NAME_LENGTH = 100
    MAX_STUDENT_ID_LENGTH = 50
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128


class DevelopmentConfig(Config):
    """개발 환경 설정"""
    DEBUG = True
    TESTING = False
    RATELIMIT_ENABLED = False  # 개발 중에는 Rate Limiting 비활성화


class ProductionConfig(Config):
    """프로덕션 환경 설정"""
    DEBUG = False
    TESTING = False
    RATELIMIT_ENABLED = True
    # 초기화 시점에 검증/설정 (app/__init__.py에서 수행)
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL') or os.getenv('REDIS_URL') or 'memory://'
    
    # 프로덕션에서는 HTTPS만 허용
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class TestingConfig(Config):
    """테스트 환경 설정"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    RATELIMIT_ENABLED = False
    
    # 테스트용 간단한 키
    SECRET_KEY = 'test-secret-key'
    JWT_SECRET_KEY = 'test-jwt-secret-key'
    OPENAI_API_KEY = 'test-openai-key'


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """설정 객체 반환"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    return config_by_name.get(config_name, DevelopmentConfig)
