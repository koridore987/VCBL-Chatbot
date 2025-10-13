"""
로깅 설정
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
import os


def setup_logger(app):
    """
    애플리케이션 로거 설정
    
    Args:
        app: Flask 애플리케이션
    """
    # 로그 레벨 설정
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    log_format = app.config.get('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 로거 설정
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # 파일 핸들러 추가 (프로덕션 환경)
    if not app.config.get('DEBUG'):
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'app.log'),
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setLevel(getattr(logging, log_level))
        file_handler.setFormatter(logging.Formatter(log_format))
        
        app.logger.addHandler(file_handler)
    
    # SQLAlchemy 로깅 레벨 설정 (너무 많은 쿼리 로그 방지)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    app.logger.info(f"Logger initialized with level: {log_level}")

