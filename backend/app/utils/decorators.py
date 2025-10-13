"""
공통 데코레이터
권한 검증 및 요청 검증 데코레이터
"""
from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError
from app.models.user import User
from .responses import error_response
import logging

logger = logging.getLogger(__name__)


def token_required(fn):
    """인증된 사용자 (토큰 필요)"""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            logger.warning(f"User not found: {user_id}")
            return error_response('사용자를 찾을 수 없습니다', 404)
        
        if not user.is_active:
            logger.warning(f"Inactive user attempted access: {user_id}")
            return error_response('비활성화된 계정입니다', 403)
        
        # current_user를 함수 인자로 전달
        return fn(current_user=user, *args, **kwargs)
    
    return wrapper


def admin_required(fn):
    """관리자 권한 필요"""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            logger.warning(f"User not found: {user_id}")
            return error_response('사용자를 찾을 수 없습니다', 404)
        
        if not user.is_active:
            logger.warning(f"Inactive user attempted access: {user_id}")
            return error_response('비활성화된 계정입니다', 403)
        
        if user.role not in ['admin', 'super']:
            logger.warning(f"Unauthorized access attempt by user: {user_id}")
            return error_response('관리자 권한이 필요합니다', 403)
        
        # current_user를 함수 인자로 전달
        return fn(current_user=user, *args, **kwargs)
    
    return wrapper


def super_admin_required(fn):
    """최고 관리자 권한 필요"""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            logger.warning(f"User not found: {user_id}")
            return error_response('사용자를 찾을 수 없습니다', 404)
        
        if not user.is_active:
            logger.warning(f"Inactive user attempted access: {user_id}")
            return error_response('비활성화된 계정입니다', 403)
        
        if user.role != 'super':
            logger.warning(f"Unauthorized super admin access attempt by user: {user_id}")
            return error_response('최고 관리자 권한이 필요합니다', 403)
        
        # current_user를 함수 인자로 전달
        return fn(current_user=user, *args, **kwargs)
    
    return wrapper


def validate_request(schema):
    """
    요청 데이터 검증 데코레이터
    
    사용 예시:
    @validate_request(LoginRequest)
    def login(validated_data):
        # validated_data는 검증된 Pydantic 모델 인스턴스
        pass
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                data = request.get_json()
                if data is None:
                    return error_response('요청 본문이 비어있습니다', 400)
                
                logger.info(f"Request data before validation: {data}")
                
                # Pydantic 검증
                validated_data = schema(**data)
                
                # 검증된 데이터를 kwargs로 전달 (URL 파라미터와 충돌 방지)
                kwargs['validated_data'] = validated_data
                return fn(*args, **kwargs)
                
            except ValidationError as e:
                # Pydantic 검증 오류
                errors = []
                for error in e.errors():
                    field = ' -> '.join(str(loc) for loc in error['loc'])
                    message = error['msg']
                    errors.append(f"{field}: {message}")
                
                logger.info(f"Validation error: {errors}")
                return error_response('입력 데이터가 올바르지 않습니다', 400, {'errors': errors})
            
            except Exception as e:
                logger.error(f"Unexpected error in validation: {str(e)}")
                return error_response('요청 처리 중 오류가 발생했습니다', 500)
        
        return wrapper
    return decorator

