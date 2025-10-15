"""
관리자 라우트
비디오, 사용자, 스캐폴딩, 프롬프트 관리
"""
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity
from app import db
from app.models.chat_prompt_template import ChatPromptTemplate
from app.services.user_service import UserService
from app.services.video_service import VideoService
from app.services.scaffolding_service import ScaffoldingService
from app.utils import (
    admin_required, super_admin_required, validate_request,
    success_response, error_response
)
from app.validators import (
    PreRegisterStudentRequest, UpdateUserRoleRequest, UpdateUserStatusRequest, ResetPasswordRequest,
    CreateVideoRequest, UpdateVideoRequest,
    CreateScaffoldingRequest, UpdateScaffoldingRequest,
    CreatePromptRequest, UpdatePromptRequest
)
import logging
import csv
import io

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)


# ==================== 사용자 관리 ====================

@admin_bp.route('/users/pre-register', methods=['POST'])
@admin_required
@validate_request(PreRegisterStudentRequest)
def pre_register_student(*, validated_data: PreRegisterStudentRequest):
    """학번 사전 등록 (관리자만)"""
    user, error = UserService.pre_register_student(
        student_id=validated_data.student_id,
        name=validated_data.name,
        role=validated_data.role
    )
    
    if error:
        return error_response(error, 409 if '이미 존재' in error else 400)
    
    return success_response(user.to_dict(), status_code=201)


@admin_bp.route('/users/bulk-register', methods=['POST'])
@admin_required
def bulk_register_students():
    """CSV 파일을 통한 학번 대량 등록"""
    if 'file' not in request.files:
        return error_response('파일이 없습니다', 400)
    
    file = request.files['file']
    
    if file.filename == '':
        return error_response('파일이 선택되지 않았습니다', 400)
    
    if not file.filename.endswith('.csv'):
        return error_response('CSV 파일만 업로드 가능합니다', 400)
    
    try:
        # CSV 파일 읽기 (UTF-8 with BOM 지원)
        stream = io.StringIO(file.stream.read().decode('utf-8-sig'), newline=None)
        csv_reader = csv.DictReader(stream)
        
        # 필수 컬럼 확인
        required_columns = ['student_id', 'name']
        if not all(col in csv_reader.fieldnames for col in required_columns):
            return error_response(
                f'CSV 파일에 필수 컬럼이 없습니다. 필수 컬럼: {", ".join(required_columns)}',
                400
            )
        
        success_count = 0
        error_count = 0
        errors = []
        
        for idx, row in enumerate(csv_reader, start=2):  # 헤더 다음부터 2행
            try:
                student_id = int(row['student_id'].strip())
                name = row['name'].strip()
                role = row.get('role', 'user').strip().lower()
                
                # 학번 형식 검증
                if len(str(student_id)) != 10:
                    errors.append(f'{idx}행: 학번은 10자리여야 합니다 ({student_id})')
                    error_count += 1
                    continue
                
                # role 검증
                if role not in ['user', 'admin']:
                    role = 'user'
                
                # 사용자 등록
                user, error = UserService.pre_register_student(
                    student_id=student_id,
                    name=name,
                    role=role
                )
                
                if error:
                    errors.append(f'{idx}행: {error} ({student_id})')
                    error_count += 1
                else:
                    success_count += 1
                    
            except ValueError as e:
                errors.append(f'{idx}행: 잘못된 학번 형식 ({row.get("student_id", "")})')
                error_count += 1
            except Exception as e:
                errors.append(f'{idx}행: {str(e)}')
                error_count += 1
        
        result = {
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors[:20]  # 최대 20개의 에러만 반환
        }
        
        if error_count > 0 and success_count == 0:
            return error_response('모든 학번 등록에 실패했습니다', 400, result)
        
        return success_response(result, status_code=201 if success_count > 0 else 200)
        
    except Exception as e:
        logger.error(f"Bulk register error: {str(e)}")
        return error_response(f'CSV 파일 처리 중 오류가 발생했습니다: {str(e)}', 500)


@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_admin_users(current_user):
    """모든 사용자 조회"""
    users = UserService.get_all_users()
    return success_response([user.to_dict() for user in users])


@admin_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@super_admin_required
@validate_request(UpdateUserRoleRequest)
def update_user_role(user_id, *, validated_data: UpdateUserRoleRequest):
    """사용자 역할 변경"""
    user, error = UserService.update_user_role(user_id, validated_data.role)
    
    if error:
        return error_response(error, 404 if '찾을 수 없' in error else 400)
    
    return success_response(user.to_dict())


@admin_bp.route('/users/<int:user_id>/activate', methods=['PUT'])
@admin_required
@validate_request(UpdateUserStatusRequest)
def toggle_user_activation(user_id, *, validated_data: UpdateUserStatusRequest):
    """사용자 활성화 상태 변경"""
    user, error = UserService.toggle_user_activation(user_id, validated_data.is_active)
    
    if error:
        return error_response(error, 404 if '찾을 수 없' in error else 400)
    
    return success_response(user.to_dict())


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@admin_required
@validate_request(ResetPasswordRequest)
def reset_user_password(user_id, *, validated_data: ResetPasswordRequest):
    """사용자 비밀번호 재설정"""
    success, error = UserService.reset_user_password(user_id, validated_data.new_password)
    
    if error:
        return error_response(error, 404 if '찾을 수 없' in error else 400)
    
    return success_response({'message': '비밀번호가 재설정되었습니다'})


# ==================== 비디오 관리 ====================

@admin_bp.route('/videos', methods=['GET'])
@admin_required
def get_admin_videos(current_user):
    """관리자용: 모든 비디오 조회 (비활성 포함)"""
    videos = VideoService.get_all_videos_for_admin()
    return success_response([video.to_dict() for video in videos])


@admin_bp.route('/videos', methods=['POST'])
@admin_required
@validate_request(CreateVideoRequest)
def create_video(current_user, *, validated_data: CreateVideoRequest):
    """비디오 생성"""
    video, error = VideoService.create_video(
        title=validated_data.title,
        youtube_url=validated_data.youtube_url,
        youtube_id=validated_data.youtube_id,
        description=validated_data.description,
        duration=validated_data.duration,
        thumbnail_url=validated_data.thumbnail_url,
        scaffolding_mode=validated_data.scaffolding_mode,
        order_index=validated_data.order_index,
        survey_url=validated_data.survey_url,
        intro_text=validated_data.intro_text
    )
    
    if error:
        return error_response(error, 400)
    
    return success_response(video.to_dict(), status_code=201)


@admin_bp.route('/videos/<int:video_id>', methods=['PUT'])
@admin_required
@validate_request(UpdateVideoRequest)
def update_video(current_user, video_id, *, validated_data: UpdateVideoRequest):
    """비디오 업데이트"""
    update_data = validated_data.model_dump(exclude_none=True)
    video, error = VideoService.update_video(video_id, **update_data)
    
    if error:
        return error_response(error, 404 if '찾을 수 없' in error else 400)
    
    return success_response(video.to_dict())


@admin_bp.route('/videos/<int:video_id>', methods=['DELETE'])
@admin_required
def delete_video(current_user, video_id):
    """비디오 삭제"""
    success, error = VideoService.delete_video(video_id)
    
    if error:
        return error_response(error, 404 if '찾을 수 없' in error else 400)
    
    return success_response({'message': '비디오가 삭제되었습니다'})


# ==================== 스캐폴딩 관리 ====================

@admin_bp.route('/videos/<int:video_id>/scaffoldings', methods=['POST'])
@admin_required
@validate_request(CreateScaffoldingRequest)
def create_scaffolding(current_user, video_id, *, validated_data: CreateScaffoldingRequest):
    """스캐폴딩 생성"""
    scaffolding, error = ScaffoldingService.create_scaffolding(
        video_id=video_id,
        title=validated_data.title,
        prompt_text=validated_data.prompt_text,
        order_index=validated_data.order_index
    )
    
    if error:
        return error_response(error, 400)
    
    return success_response(scaffolding.to_dict(), status_code=201)


@admin_bp.route('/scaffoldings/<int:scaffolding_id>', methods=['PUT'])
@admin_required
@validate_request(UpdateScaffoldingRequest)
def update_scaffolding(current_user, scaffolding_id, *, validated_data: UpdateScaffoldingRequest):
    """스캐폴딩 업데이트"""
    update_data = validated_data.model_dump(exclude_none=True)
    scaffolding, error = ScaffoldingService.update_scaffolding(scaffolding_id, **update_data)
    
    if error:
        return error_response(error, 404 if '찾을 수 없' in error else 400)
    
    return success_response(scaffolding.to_dict())


@admin_bp.route('/scaffoldings/<int:scaffolding_id>', methods=['DELETE'])
@admin_required
def delete_scaffolding(current_user, scaffolding_id):
    """스캐폴딩 삭제"""
    success, error = ScaffoldingService.delete_scaffolding(scaffolding_id)
    
    if error:
        return error_response(error, 404 if '찾을 수 없' in error else 400)
    
    return success_response({'message': '스캐폴딩이 삭제되었습니다'})


# ==================== 프롬프트 관리 ====================

@admin_bp.route('/prompts', methods=['GET'])
@admin_required
def get_admin_prompts(current_user):
    """모든 프롬프트 조회"""
    prompts = ChatPromptTemplate.query.all()
    return success_response([prompt.to_dict() for prompt in prompts])


@admin_bp.route('/prompts', methods=['POST'])
@admin_required
@validate_request(CreatePromptRequest)
def create_prompt(current_user, *, validated_data: CreatePromptRequest):
    """프롬프트 생성"""
    logger.info(f"Create prompt request - validated data: {validated_data}")
    user_id = int(get_jwt_identity())
    
    try:
        # 기본 프롬프트로 설정하는 경우 기존 기본 프롬프트 해제
        if validated_data.is_default:
            ChatPromptTemplate.query.filter_by(is_default=True).update({'is_default': False})
        
        prompt = ChatPromptTemplate(
            name=validated_data.name,
            description=validated_data.description,
            system_prompt=validated_data.system_prompt,
            constraints=validated_data.constraints,
            video_id=validated_data.video_id,
            user_role=validated_data.user_role,
            is_default=validated_data.is_default,
            created_by=user_id
        )
        
        db.session.add(prompt)
        db.session.commit()
        
        return success_response(prompt.to_dict(), status_code=201)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Create prompt error: {str(e)}")
        return error_response('프롬프트 생성 중 오류가 발생했습니다', 500)


@admin_bp.route('/prompts/<int:prompt_id>', methods=['PUT'])
@admin_required
@validate_request(UpdatePromptRequest)
def update_prompt(current_user, prompt_id, *, validated_data: UpdatePromptRequest):
    """프롬프트 업데이트"""
    try:
        prompt = ChatPromptTemplate.query.get(prompt_id)
        
        if not prompt:
            return error_response('프롬프트를 찾을 수 없습니다', 404)
        
        # 기본 프롬프트로 설정하는 경우
        if validated_data.is_default and not prompt.is_default:
            ChatPromptTemplate.query.filter_by(is_default=True).update({'is_default': False})
        
        # 업데이트
        update_data = validated_data.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(prompt, field, value)
        
        prompt.version += 1
        
        db.session.commit()
        
        return success_response(prompt.to_dict())
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update prompt error: {str(e)}")
        return error_response('프롬프트 업데이트 중 오류가 발생했습니다', 500)


@admin_bp.route('/prompts/<int:prompt_id>', methods=['DELETE'])
@admin_required
def delete_prompt(current_user, prompt_id):
    """프롬프트 삭제"""
    try:
        prompt = ChatPromptTemplate.query.get(prompt_id)
        
        if not prompt:
            return error_response('프롬프트를 찾을 수 없습니다', 404)
        
        if prompt.is_default:
            return error_response('기본 프롬프트는 삭제할 수 없습니다', 400)
        
        db.session.delete(prompt)
        db.session.commit()
        
        return success_response({'message': '프롬프트가 삭제되었습니다'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete prompt error: {str(e)}")
        return error_response('프롬프트 삭제 중 오류가 발생했습니다', 500)
