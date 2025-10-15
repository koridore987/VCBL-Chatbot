"""
비디오 관련 라우트
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.video_service import VideoService
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

videos_bp = Blueprint('videos', __name__)


@videos_bp.route('/', methods=['GET'])
@jwt_required()
def get_videos():
    """모든 비디오 조회"""
    user_id = int(get_jwt_identity())
    logger.info("GET /api/videos - fetching all active videos")
    
    videos = VideoService.get_all_videos()
    progress_map = LearningProgressService.get_progress_map_for_user(user_id)
    logger.info(f"GET /api/videos - count={len(videos)}")
    
    response_payload = []
    for video in videos:
        video_data = video.to_dict()
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
        merged_progress = {**default_progress, **progress_map.get(video.id, {})}
        merged_progress['is_completed'] = merged_progress['status'] == 'completed'
        video_data['learning_progress'] = merged_progress
        response_payload.append(video_data)
    
    return success_response(response_payload)


@videos_bp.route('/<int:video_id>', methods=['GET'])
@jwt_required()
def get_video(video_id):
    """비디오 상세 조회"""
    user_id = int(get_jwt_identity())
    
    video_data, error = VideoService.get_video_with_scaffoldings(video_id, user_id)
    
    if error:
        return error_response(error, 404)
    
    # 비디오 조회 이벤트 로그
    VideoService.log_video_event(
        user_id=user_id,
        video_id=video_id,
        event_type='video_view',
        event_data={},
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')
    )
    
    return success_response(video_data)


@videos_bp.route('/<int:video_id>/scaffoldings/<int:scaffolding_id>/respond', methods=['POST'])
@jwt_required()
@validate_request(ScaffoldingResponseRequest)
def respond_to_scaffolding(video_id, scaffolding_id, *, validated_data: ScaffoldingResponseRequest):
    """스캐폴딩 응답 저장"""
    user_id = int(get_jwt_identity())
    
    success, error = ScaffoldingService.save_response(
        scaffolding_id=scaffolding_id,
        video_id=video_id,
        user_id=user_id,
        response_text=validated_data.response_text
    )
    
    if error:
        return error_response(error, 404 if '찾을 수 없' in error else 400)
    
    # 스캐폴딩 응답 이벤트 로그
    VideoService.log_video_event(
        user_id=user_id,
        video_id=video_id,
        event_type='scaffolding_response',
        event_data={
            'scaffolding_id': scaffolding_id,
            'response_length': len(validated_data.response_text)
        },
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')
    )
    
    return success_response({'message': '응답이 저장되었습니다'})


@videos_bp.route('/<int:video_id>/scaffoldings/respond-all', methods=['POST'])
@jwt_required()
def respond_to_scaffoldings_bulk(video_id):
    """여러 스캐폴딩 응답 일괄 저장"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    if not data or 'responses' not in data:
        return error_response('응답 데이터가 필요합니다', 400)
    
    responses = data['responses']
    
    if not isinstance(responses, list):
        return error_response('응답은 배열 형식이어야 합니다', 400)
    
    try:
        # 각 응답 저장
        for response_data in responses:
            scaffolding_id = response_data.get('scaffolding_id')
            response_text = response_data.get('response_text', '')
            
            if scaffolding_id and response_text.strip():
                ScaffoldingService.save_response(
                    scaffolding_id=scaffolding_id,
                    video_id=video_id,
                    user_id=user_id,
                    response_text=response_text
                )
        
        # 전체 응답 완료 이벤트 로그
        VideoService.log_video_event(
            user_id=user_id,
            video_id=video_id,
            event_type='all_scaffolding_responses',
            event_data={
                'total_responses': len(responses)
            },
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        return success_response({'message': '모든 응답이 저장되었습니다'})
        
    except Exception as e:
        logger.error(f"Error saving all responses: {str(e)}")
        return error_response('응답 저장 중 오류가 발생했습니다', 500)


@videos_bp.route('/<int:video_id>/event', methods=['POST'])
@jwt_required()
def log_video_event(video_id):
    """비디오 이벤트 로그 기록"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    event_type = data.get('event_type')
    event_data = data.get('event_data', {})
    
    if not event_type:
        return error_response('이벤트 타입을 지정해주세요', 400)
    
    VideoService.log_video_event(
        user_id=user_id,
        video_id=video_id,
        event_type=event_type,
        event_data=event_data,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')
    )
    
    return success_response({'message': '이벤트가 기록되었습니다'})


@videos_bp.route('/<int:video_id>/survey-complete', methods=['POST'])
@jwt_required()
def mark_survey_completed(video_id):
    """설문 완료 확인"""
    user_id = int(get_jwt_identity())
    
    try:
        progress = LearningProgressService.mark_survey_completed(user_id, video_id)
    except Exception as e:
        logger.error(f"Failed to mark survey completion for user {user_id}, video {video_id}: {str(e)}")
        return error_response('설문 완료 처리 중 오류가 발생했습니다', 500)
    
    VideoService.log_video_event(
        user_id=user_id,
        video_id=video_id,
        event_type='survey_completion_confirmed',
        event_data={'source': 'manual_confirmation'},
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')
    )
    
    return success_response({
        'message': '설문 완료가 기록되었습니다',
        'learning_progress': progress.to_dict()
    })


@videos_bp.route('/<int:video_id>/complete', methods=['POST'])
@jwt_required()
def complete_learning(video_id):
    """학습 종료 처리"""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    survey_confirmed = bool(data.get('survey_confirmed', False))
    
    try:
        if survey_confirmed:
            LearningProgressService.mark_survey_completed(user_id, video_id)
        progress = LearningProgressService.mark_completed(user_id, video_id)
    except Exception as e:
        logger.error(f"Failed to complete learning for user {user_id}, video {video_id}: {str(e)}")
        return error_response('학습 종료 처리 중 오류가 발생했습니다', 500)
    
    VideoService.log_video_event(
        user_id=user_id,
        video_id=video_id,
        event_type='learning_session_completed',
        event_data={'survey_confirmed': survey_confirmed},
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')
    )
    
    return success_response({
        'message': '학습이 종료되었습니다',
        'learning_progress': progress.to_dict()
    })
