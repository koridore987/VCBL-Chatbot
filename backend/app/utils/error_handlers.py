"""
전역 에러 핸들러
"""
from flask import Flask
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError
from .responses import error_response
import logging

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask):
    """Flask 앱에 에러 핸들러 등록"""
    
    @app.errorhandler(400)
    def bad_request(e):
        """잘못된 요청"""
        return error_response('잘못된 요청입니다', 400)
    
    @app.errorhandler(401)
    def unauthorized(e):
        """인증 실패"""
        return error_response('인증이 필요합니다', 401)
    
    @app.errorhandler(403)
    def forbidden(e):
        """권한 없음"""
        return error_response('접근 권한이 없습니다', 403)
    
    @app.errorhandler(404)
    def not_found(e):
        """리소스를 찾을 수 없음"""
        return error_response('요청한 리소스를 찾을 수 없습니다', 404)
    
    @app.errorhandler(405)
    def method_not_allowed(e):
        """허용되지 않은 메서드"""
        return error_response('허용되지 않은 메서드입니다', 405)
    
    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        """요청 제한 초과"""
        return error_response('요청 횟수 제한을 초과했습니다. 잠시 후 다시 시도해주세요.', 429)
    
    @app.errorhandler(500)
    def internal_server_error(e):
        """내부 서버 오류"""
        logger.error(f"Internal server error: {str(e)}", exc_info=True)
        return error_response('서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.', 500)
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """HTTP 예외 처리"""
        logger.warning(f"HTTP exception: {e.code} - {e.description}")
        return error_response(e.description or '요청을 처리할 수 없습니다', e.code)
    
    @app.errorhandler(SQLAlchemyError)
    def handle_db_exception(e):
        """데이터베이스 예외 처리"""
        logger.error(f"Database error: {str(e)}", exc_info=True)
        return error_response('데이터베이스 오류가 발생했습니다', 500)
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        """Pydantic 검증 오류"""
        errors = []
        for error in e.errors():
            field = ' -> '.join(str(loc) for loc in error['loc'])
            message = error['msg']
            errors.append(f"{field}: {message}")
        
        logger.info(f"Validation error: {errors}")
        return error_response('입력 데이터가 올바르지 않습니다', 400, {'errors': errors})
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        """예상치 못한 오류"""
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        # 프로덕션 환경에서는 상세한 에러를 노출하지 않음
        if app.config.get('DEBUG'):
            return error_response(f'예상치 못한 오류: {str(e)}', 500)
        return error_response('서버 오류가 발생했습니다', 500)

