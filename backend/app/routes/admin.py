"""
관리자 라우트
비디오, 사용자, 스캐폴딩, 프롬프트 관리
"""
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity
from app import db
from app.models.chat_prompt_template import ChatPromptTemplate
from app.services.user_service import UserService
from app.services.module_service import ModuleService
from app.services.scaffolding_service import ScaffoldingService
from app.services.learning_progress_service import LearningProgressService
from app.utils import (
    admin_required, super_admin_required, validate_request,
    success_response, error_response
)
from app.validators import (
    PreRegisterStudentRequest, UpdateUserRoleRequest, UpdateUserStatusRequest, ResetPasswordRequest,
    CreateModuleRequest, UpdateModuleRequest,
    CreateScaffoldingRequest, UpdateScaffoldingRequest,
    CreatePromptRequest, UpdatePromptRequest
)
from app.validators.scaffolding_schemas import ReorderScaffoldingsRequest
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


# ==================== 모듈 관리 ====================

@admin_bp.route('/modules', methods=['GET'])
@admin_required
def get_admin_modules(current_user):
    """관리자용: 모든 모듈 조회 (비활성 포함)"""
    modules = ModuleService.get_all_modules_for_admin()
    return success_response([module.to_dict() for module in modules])


# ==================== 학습 진행 현황 ====================

@admin_bp.route('/progress', methods=['GET'])
@admin_required
def get_learning_progress(current_user):
    """학습 진행 현황 조회"""
    limit = request.args.get('limit', type=int) or 50
    recent_progress = LearningProgressService.get_recent_progress(limit=limit)
    status_counts = LearningProgressService.get_status_counts()
    
    return success_response({
        'recent': recent_progress,
        'status_counts': status_counts
    })


@admin_bp.route('/modules', methods=['POST'])
@admin_required
@validate_request(CreateModuleRequest)
def create_module(current_user, *, validated_data: CreateModuleRequest):
    """모듈 생성"""
    module, error = ModuleService.create_module(
        title=validated_data.title,
        youtube_url=validated_data.youtube_url,
        youtube_id=validated_data.youtube_id,  # 선택사항이므로 None일 수 있음
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
    
    return success_response(module.to_dict(), status_code=201)


@admin_bp.route('/modules/<int:module_id>', methods=['PUT'])
@admin_required
@validate_request(UpdateModuleRequest)
def update_module(current_user, module_id, *, validated_data: UpdateModuleRequest):
    """모듈 업데이트"""
    update_data = validated_data.model_dump(exclude_none=True)
    module, error = ModuleService.update_module(module_id, **update_data)
    
    if error:
        return error_response(error, 404 if '찾을 수 없' in error else 400)
    
    return success_response(module.to_dict())


@admin_bp.route('/modules/<int:module_id>', methods=['DELETE'])
@admin_required
def delete_module(current_user, module_id):
    """모듈 삭제"""
    success, error = ModuleService.delete_module(module_id)
    
    if error:
        return error_response(error, 404 if '찾을 수 없' in error else 400)
    
    return success_response({'message': '모듈이 삭제되었습니다'})


# ==================== 스캐폴딩 관리 ====================

@admin_bp.route('/modules/<int:module_id>/scaffoldings', methods=['POST'])
@admin_required
@validate_request(CreateScaffoldingRequest)
def create_scaffolding(current_user, module_id, *, validated_data: CreateScaffoldingRequest):
    """스캐폴딩 생성"""
    scaffolding, error = ScaffoldingService.create_scaffolding(
        module_id=module_id,
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


@admin_bp.route('/videos/<int:video_id>/scaffoldings/reorder', methods=['PUT'])
@admin_required
@validate_request(ReorderScaffoldingsRequest)
def reorder_scaffoldings(current_user, video_id, *, validated_data: ReorderScaffoldingsRequest):
    """스캐폴딩 순서 재정렬"""
    reorder_data = [{'id': item.id, 'order_index': item.order_index} for item in validated_data.scaffoldings]
    
    success, error = ScaffoldingService.reorder_scaffoldings(video_id, reorder_data)
    
    if error:
        return error_response(error, 400)
    
    return success_response({'message': '순서가 변경되었습니다'})


# ==================== 페르소나 관리 ====================

@admin_bp.route('/personas', methods=['GET'])
@admin_required
def get_admin_personas(current_user):
    """모든 페르소나 조회"""
    personas = ChatPromptTemplate.query.order_by(ChatPromptTemplate.is_global_active.desc(), ChatPromptTemplate.created_at.desc()).all()
    return success_response([persona.to_dict() for persona in personas])


@admin_bp.route('/personas', methods=['POST'])
@admin_required
@validate_request(CreatePromptRequest)  # 별칭 사용 (하위 호환성)
def create_persona(current_user, *, validated_data: CreatePromptRequest):
    """페르소나 생성"""
    logger.info(f"Create persona request - validated data: {validated_data}")
    user_id = int(get_jwt_identity())
    
    try:
        # constraints를 JSON 문자열로 변환
        constraints_json = None
        if validated_data.constraints:
            import json
            constraints_json = json.dumps(validated_data.constraints)
        
        persona = ChatPromptTemplate(
            name=validated_data.name,
            description=validated_data.description,
            system_prompt=validated_data.system_prompt,
            constraints=constraints_json,
            is_global_active=False,  # 기본적으로 비활성 상태로 생성
            created_by=user_id
        )
        
        db.session.add(persona)
        db.session.commit()
        
        return success_response(persona.to_dict(), status_code=201)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Create persona error: {str(e)}")
        return error_response('페르소나 생성 중 오류가 발생했습니다', 500)


@admin_bp.route('/personas/<int:persona_id>', methods=['PUT'])
@admin_required
@validate_request(UpdatePromptRequest)  # 별칭 사용 (하위 호환성)
def update_persona(current_user, persona_id, *, validated_data: UpdatePromptRequest):
    """페르소나 업데이트"""
    try:
        persona = ChatPromptTemplate.query.get(persona_id)
        
        if not persona:
            return error_response('페르소나를 찾을 수 없습니다', 404)
        
        # 업데이트
        update_data = validated_data.model_dump(exclude_none=True)
        
        # constraints를 JSON 문자열로 변환
        if 'constraints' in update_data and update_data['constraints'] is not None:
            import json
            update_data['constraints'] = json.dumps(update_data['constraints'])
        
        for field, value in update_data.items():
            setattr(persona, field, value)
        
        persona.version += 1
        
        db.session.commit()
        
        return success_response(persona.to_dict())
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update persona error: {str(e)}")
        return error_response('페르소나 업데이트 중 오류가 발생했습니다', 500)


@admin_bp.route('/personas/<int:persona_id>/activate', methods=['PUT'])
@admin_required
def toggle_persona_activation(current_user, persona_id):
    """페르소나 전역 활성화 토글"""
    try:
        persona = ChatPromptTemplate.query.get(persona_id)
        
        if not persona:
            return error_response('페르소나를 찾을 수 없습니다', 404)
        
        # 현재 활성 페르소나 확인
        if persona.is_global_active:
            # 이미 활성화된 페르소나를 비활성화
            persona.is_global_active = False
        else:
            # 다른 모든 페르소나 비활성화
            ChatPromptTemplate.query.filter(ChatPromptTemplate.id != persona_id).update({'is_global_active': False})
            # 현재 페르소나 활성화
            persona.is_global_active = True
        
        db.session.commit()
        
        return success_response({
            'message': '페르소나가 활성화되었습니다' if persona.is_global_active else '페르소나가 비활성화되었습니다',
            'is_global_active': persona.is_global_active,
            'persona': persona.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Toggle persona activation error: {str(e)}")
        return error_response('페르소나 활성화 변경 중 오류가 발생했습니다', 500)


@admin_bp.route('/personas/<int:persona_id>', methods=['DELETE'])
@admin_required
def delete_persona(current_user, persona_id):
    """페르소나 삭제"""
    try:
        persona = ChatPromptTemplate.query.get(persona_id)
        
        if not persona:
            return error_response('페르소나를 찾을 수 없습니다', 404)
        
        # 활성화된 페르소나는 삭제 불가
        if persona.is_global_active:
            return error_response(
                '현재 활성화된 페르소나는 삭제할 수 없습니다. 다른 페르소나를 활성화한 후 삭제해주세요.',
                400,
                {'is_active': True}
            )
        
        db.session.delete(persona)
        db.session.commit()
        
        return success_response({'message': '페르소나가 삭제되었습니다'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete persona error: {str(e)}")
        return error_response('페르소나 삭제 중 오류가 발생했습니다', 500)


# ==================== 페르소나 테스트 채팅 ====================

@admin_bp.route('/personas/test', methods=['POST'])
@admin_required
def test_persona_chat(current_user):
    """페르소나 테스트 채팅 (임시 세션)"""
    from app.validators.prompt_schemas import TestChatRequest
    from app.services.openai_service import OpenAIService
    from flask import current_app
    
    try:
        # 요청 검증
        data = request.get_json()
        validated_data = TestChatRequest(**data)
        
        # 페르소나 조회
        persona = ChatPromptTemplate.query.get(validated_data.persona_id)
        if not persona:
            return error_response('페르소나를 찾을 수 없습니다', 404)
        
        # OpenAI 서비스 초기화
        openai_service = OpenAIService(current_app.config)
        
        # constraints 파싱
        constraints = persona.get_constraints_dict()
        
        # 임시 메시지 리스트 생성
        messages = [
            {"role": "system", "content": persona.system_prompt},
            {"role": "user", "content": validated_data.message}
        ]
        
        # OpenAI API 호출 파라미터 구성
        api_params = {
            'model': current_app.config['MODEL_NAME'],
            'messages': messages,
            'max_tokens': constraints.get('max_tokens', current_app.config.get('MAX_TOKENS_OUTPUT', 1000)),
            'temperature': constraints.get('temperature', 0.7)
        }
        
        # 추가 파라미터 적용
        if 'top_p' in constraints:
            api_params['top_p'] = constraints['top_p']
        if 'frequency_penalty' in constraints:
            api_params['frequency_penalty'] = constraints['frequency_penalty']
        if 'presence_penalty' in constraints:
            api_params['presence_penalty'] = constraints['presence_penalty']
        if 'stop' in constraints:
            api_params['stop'] = constraints['stop']
        if 'response_format' in constraints:
            api_params['response_format'] = constraints['response_format']
        
        # API 호출
        response = openai_service.client.chat.completions.create(**api_params)
        
        # 응답 추출
        assistant_message = response.choices[0].message.content
        
        return success_response({
            'message': assistant_message,
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
        })
        
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        logger.error(f"Test persona chat error: {str(e)}")
        return error_response(f'테스트 채팅 중 오류가 발생했습니다: {str(e)}', 500)


# ==================== 하위 호환성을 위한 별칭 ====================

# 기존 /prompts 엔드포인트도 유지 (하위 호환성)
# 주의: 이 함수들은 내부에서 다른 함수를 호출하지만, 데코레이터가 current_user를 이미 주입하므로
# 직접 호출하면 안 되고, 같은 로직을 실행해야 합니다.

@admin_bp.route('/prompts', methods=['GET'])
@admin_required
def get_admin_prompts_compat(current_user):
    """모든 프롬프트 조회 (하위 호환성)"""
    personas = ChatPromptTemplate.query.order_by(ChatPromptTemplate.is_global_active.desc(), ChatPromptTemplate.created_at.desc()).all()
    return success_response([persona.to_dict() for persona in personas])


@admin_bp.route('/prompts', methods=['POST'])
@admin_required
@validate_request(CreatePromptRequest)
def create_prompt_compat(current_user, *, validated_data: CreatePromptRequest):
    """프롬프트 생성 (하위 호환성)"""
    logger.info(f"Create prompt (compat) request - validated data: {validated_data}")
    user_id = int(get_jwt_identity())
    
    try:
        # constraints를 JSON 문자열로 변환
        constraints_json = None
        if validated_data.constraints:
            import json
            constraints_json = json.dumps(validated_data.constraints)
        
        persona = ChatPromptTemplate(
            name=validated_data.name,
            description=validated_data.description,
            system_prompt=validated_data.system_prompt,
            constraints=constraints_json,
            is_global_active=False,
            created_by=user_id
        )
        
        db.session.add(persona)
        db.session.commit()
        
        return success_response(persona.to_dict(), status_code=201)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Create prompt (compat) error: {str(e)}")
        return error_response('프롬프트 생성 중 오류가 발생했습니다', 500)


@admin_bp.route('/prompts/<int:prompt_id>', methods=['PUT'])
@admin_required
@validate_request(UpdatePromptRequest)
def update_prompt_compat(current_user, prompt_id, *, validated_data: UpdatePromptRequest):
    """프롬프트 업데이트 (하위 호환성)"""
    try:
        persona = ChatPromptTemplate.query.get(prompt_id)
        
        if not persona:
            return error_response('프롬프트를 찾을 수 없습니다', 404)
        
        # 업데이트
        update_data = validated_data.model_dump(exclude_none=True)
        
        # constraints를 JSON 문자열로 변환
        if 'constraints' in update_data and update_data['constraints'] is not None:
            import json
            update_data['constraints'] = json.dumps(update_data['constraints'])
        
        for field, value in update_data.items():
            setattr(persona, field, value)
        
        persona.version += 1
        
        db.session.commit()
        
        return success_response(persona.to_dict())
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update prompt (compat) error: {str(e)}")
        return error_response('프롬프트 업데이트 중 오류가 발생했습니다', 500)


@admin_bp.route('/prompts/<int:prompt_id>', methods=['DELETE'])
@admin_required
def delete_prompt_compat(current_user, prompt_id):
    """프롬프트 삭제 (하위 호환성)"""
    try:
        persona = ChatPromptTemplate.query.get(prompt_id)
        
        if not persona:
            return error_response('프롬프트를 찾을 수 없습니다', 404)
        
        # 활성화된 페르소나는 삭제 불가
        if persona.is_global_active:
            return error_response(
                '현재 활성화된 페르소나는 삭제할 수 없습니다. 다른 페르소나를 활성화한 후 삭제해주세요.',
                400,
                {'is_active': True}
            )
        
        db.session.delete(persona)
        db.session.commit()
        
        return success_response({'message': '프롬프트가 삭제되었습니다'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete prompt (compat) error: {str(e)}")
        return error_response('프롬프트 삭제 중 오류가 발생했습니다', 500)
