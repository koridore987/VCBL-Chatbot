"""
모듈 관련 라우트
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.module_service import ModuleService
from app.services.scaffolding_service import ScaffoldingService
from app.services.learning_progress_service import LearningProgressService
from app.utils import success_response, error_response, validate_request
from app.validators import ScaffoldingResponseRequest
try:
    from app.validators import BulkScaffoldingResponseRequest
except ImportError:
    BulkScaffoldingResponseRequest = None
import logging

logger = logging.getLogger(__name__)

modules_bp = Blueprint('modules', __name__)


@modules_bp.route('/', methods=['GET'])
@jwt_required()
def get_modules():
    """모든 모듈 조회"""
    user_id = int(get_jwt_identity())
    logger.info("GET /api/modules - fetching all active modules")
    
    modules = ModuleService.get_all_modules()
    progress_map = LearningProgressService.get_progress_map_for_user(user_id)
    logger.info(f"GET /api/modules - count={len(modules)}")
    
    response_payload = []
    for module in modules:
        module_data = module.to_dict()
        default_progress = {
            'status': 'not_started',
            'started_at': None,
            'last_activity_at': None,
            'completed_at': None,
            'survey_completed': False,
            'survey_completed_at': None,
            'total': 0,
            'completed': 0,
            'is_completed': False
        }
        merged_progress = {**default_progress, **progress_map.get(module.id, {})}
        merged_progress['is_completed'] = merged_progress['status'] == 'completed'
        module_data['learning_progress'] = merged_progress
        response_payload.append(module_data)
    
    return success_response(response_payload)


@modules_bp.route('/<int:module_id>', methods=['GET'])
@jwt_required()
def get_module(module_id):
    """모듈 상세 조회"""
    user_id = int(get_jwt_identity())
    
    module_data, error = ModuleService.get_module_with_scaffoldings(module_id, user_id)
    
    if error:
        return error_response(error, 404)
    
    # 모듈 조회 이벤트 로그
    ModuleService.log_module_event(
        user_id=user_id,
        module_id=module_id,
        event_type='module_view',
        event_data={},
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')
    )
    
    return success_response(module_data)


@modules_bp.route('/<int:module_id>/scaffoldings/<int:scaffolding_id>/respond', methods=['POST'])
@jwt_required()
@validate_request(ScaffoldingResponseRequest)
def respond_to_scaffolding(module_id, scaffolding_id, *, validated_data: ScaffoldingResponseRequest):
    """스캐폴딩 응답"""
    user_id = int(get_jwt_identity())
    
    response, error = ScaffoldingService.create_response(
        scaffolding_id=scaffolding_id,
        user_id=user_id,
        response_text=validated_data.response_text
    )
    
    if error:
        return error_response(error, 400)
    
    # 학습 진행 상황 업데이트
    try:
        LearningProgressService.mark_activity(user_id, module_id)
    except Exception as e:
        logger.error(f"Failed to mark learning activity: {str(e)}")
    
    return success_response(response.to_dict())


@modules_bp.route('/<int:module_id>/scaffoldings/respond-bulk', methods=['POST'])
@jwt_required()
def respond_to_scaffoldings_bulk(module_id):
    """스캐폴딩 일괄 응답"""
    if not BulkScaffoldingResponseRequest:
        return error_response('Bulk scaffolding response not supported', 400)
    
    user_id = int(get_jwt_identity())
    
    # Validate request data
    data = request.get_json()
    if not data or 'responses' not in data:
        return error_response('Invalid request data', 400)
    
    try:
        responses = []
        for response_data in data['responses']:
            response, error = ScaffoldingService.create_response(
                scaffolding_id=response_data['scaffolding_id'],
                user_id=user_id,
                response_text=response_data['response_text']
            )
            
            if error:
                return error_response(error, 400)
            
            responses.append(response.to_dict())
        
        # 학습 진행 상황 업데이트
        try:
            LearningProgressService.mark_activity(user_id, module_id)
        except Exception as e:
            logger.error(f"Failed to mark learning activity: {str(e)}")
        
        return success_response(responses)
        
    except Exception as e:
        logger.error(f"Bulk scaffolding response error: {str(e)}")
        return error_response('스캐폴딩 응답 처리 중 오류가 발생했습니다', 500)


@modules_bp.route('/<int:module_id>/event', methods=['POST'])
@jwt_required()
def log_module_event(module_id):
    """모듈 이벤트 로그"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    if not data or 'event_type' not in data:
        return error_response('이벤트 타입이 필요합니다', 400)
    
    event_type = data['event_type']
    event_data = data.get('event_data', {})
    
    ModuleService.log_module_event(
        user_id=user_id,
        module_id=module_id,
        event_type=event_type,
        event_data=event_data,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')
    )
    
    return success_response({'message': '이벤트가 기록되었습니다'})


@modules_bp.route('/<int:module_id>/survey-complete', methods=['POST'])
@jwt_required()
def mark_survey_completed(module_id):
    """설문 완료 처리"""
    user_id = int(get_jwt_identity())
    
    try:
        progress = LearningProgressService.mark_survey_completed(user_id, module_id)
        return success_response({
            'message': '설문 완료가 기록되었습니다',
            'learning_progress': progress.to_dict()
        })
    except Exception as e:
        logger.error(f"Mark survey completed error: {str(e)}")
        return error_response('설문 완료 처리 중 오류가 발생했습니다', 500)


@modules_bp.route('/<int:module_id>/complete', methods=['POST'])
@jwt_required()
def complete_learning(module_id):
    """학습 완료 처리"""
    user_id = int(get_jwt_identity())
    
    try:
        progress = LearningProgressService.mark_completed(user_id, module_id)
        return success_response({
            'message': '학습이 완료되었습니다',
            'learning_progress': progress.to_dict()
        })
    except Exception as e:
        logger.error(f"Complete learning error: {str(e)}")
        return error_response('학습 완료 처리 중 오류가 발생했습니다', 500)




