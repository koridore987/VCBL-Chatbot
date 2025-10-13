"""
인증 관련 라우트
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import limiter
from app.services.auth_service import AuthService
from app.utils import validate_request, success_response, error_response
from app.validators import RegisterRequest, LoginRequest, ChangePasswordRequest
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
@validate_request(RegisterRequest)
def register(*, validated_data: RegisterRequest):
    """사용자 회원가입 (사전 등록된 학번으로만 가능)"""
    user, error = AuthService.register_user(
        student_id=validated_data.student_id,
        password=validated_data.password
    )
    
    if error:
        return error_response(error, 409 if '이미' in error else 400)
    
    return success_response({
        'message': '회원가입이 완료되었습니다',
        'user': user.to_dict()
    }, status_code=201)


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
@validate_request(LoginRequest)
def login(*, validated_data: LoginRequest):
    """사용자 로그인"""
    access_token, user, error = AuthService.login_user(
        student_id=validated_data.student_id,
        password=validated_data.password
    )
    
    if error:
        return error_response(error, 401 if '올바르지 않' in error else 403)
    
    return success_response({
        'access_token': access_token,
        'user': user.to_dict()
    })


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """현재 사용자 정보 조회"""
    user_id = int(get_jwt_identity())
    
    user, error = AuthService.get_current_user(user_id)
    
    if error:
        return error_response(error, 404)
    
    return success_response(user.to_dict())


@auth_bp.route('/password-reset-request', methods=['POST'])
@limiter.limit("3 per minute")
def password_reset_request():
    """비밀번호 재설정 요청"""
    data = request.get_json()
    student_id = data.get('student_id')
    
    if not student_id:
        return error_response('학번을 입력해주세요', 400)
    
    # 프로덕션에서는 실제 알림 시스템 사용
    logger.info(f"Password reset requested for: {student_id}")
    
    return success_response({
        'message': '비밀번호 재설정 요청이 관리자에게 전달되었습니다'
    })


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
@validate_request(ChangePasswordRequest)
def change_password(*, validated_data: ChangePasswordRequest):
    """비밀번호 변경"""
    user_id = int(get_jwt_identity())
    
    success, error = AuthService.change_password(
        user_id=user_id,
        old_password=validated_data.old_password,
        new_password=validated_data.new_password
    )
    
    if error:
        return error_response(error, 401 if '올바르지 않' in error else 400)
    
    return success_response({'message': '비밀번호가 변경되었습니다'})

