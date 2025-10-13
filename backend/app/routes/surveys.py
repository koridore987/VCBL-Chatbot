"""
설문조사 관련 라우트
"""
from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
import logging
from app.utils.decorators import token_required, admin_required
from app.services.survey_service import SurveyService
from app.validators.survey_schemas import (
    survey_create_schema,
    survey_update_schema,
    question_create_schema,
    question_update_schema,
    question_reorder_schema,
    survey_responses_submit_schema
)
from app.utils.responses import success_response, error_response

surveys_bp = Blueprint('surveys', __name__, url_prefix='/api/surveys')
logger = logging.getLogger(__name__)


# ============================================================================
# 설문조사 관리 (관리자)
# ============================================================================

@surveys_bp.route('/', methods=['POST'])
@admin_required
def create_survey(current_user):
    """새 설문조사 생성 (관리자)"""
    try:
        data = survey_create_schema.load(request.json)
        
        survey = SurveyService.create_survey(
            title=data['title'],
            description=data.get('description'),
            is_required=data.get('is_required', False),
            show_after_registration=data.get('show_after_registration', True)
        )
        
        logger.info(f"Survey created: {survey.id} by admin {current_user.id}")
        return success_response(
            data=survey.to_dict(),
            message="설문조사가 생성되었습니다."
        ), 201
        
    except ValidationError as e:
        return error_response(message="입력 데이터가 올바르지 않습니다.", errors=e.messages), 400
    except Exception as e:
        logger.error(f"Error creating survey: {str(e)}")
        return error_response(message="설문조사 생성 중 오류가 발생했습니다."), 500


@surveys_bp.route('/<int:survey_id>', methods=['PUT'])
@admin_required
def update_survey(current_user, survey_id):
    """설문조사 수정 (관리자)"""
    try:
        data = survey_update_schema.load(request.json)
        
        survey = SurveyService.update_survey(survey_id, **data)
        if not survey:
            return error_response(message="설문조사를 찾을 수 없습니다."), 404
        
        logger.info(f"Survey updated: {survey_id} by admin {current_user.id}")
        return success_response(
            data=survey.to_dict(),
            message="설문조사가 수정되었습니다."
        )
        
    except ValidationError as e:
        return error_response(message="입력 데이터가 올바르지 않습니다.", errors=e.messages), 400
    except Exception as e:
        logger.error(f"Error updating survey {survey_id}: {str(e)}")
        return error_response(message="설문조사 수정 중 오류가 발생했습니다."), 500


@surveys_bp.route('/<int:survey_id>', methods=['DELETE'])
@admin_required
def delete_survey(current_user, survey_id):
    """설문조사 삭제 (관리자)"""
    try:
        success = SurveyService.delete_survey(survey_id)
        if not success:
            return error_response(message="설문조사를 찾을 수 없습니다."), 404
        
        logger.info(f"Survey deleted: {survey_id} by admin {current_user.id}")
        return success_response(message="설문조사가 삭제되었습니다.")
        
    except Exception as e:
        logger.error(f"Error deleting survey {survey_id}: {str(e)}")
        return error_response(message="설문조사 삭제 중 오류가 발생했습니다."), 500


@surveys_bp.route('/', methods=['GET'])
@admin_required
def get_all_surveys(current_user):
    """모든 설문조사 목록 조회 (관리자)"""
    try:
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        surveys = SurveyService.get_all_surveys(active_only=active_only)
        
        return success_response(
            data=[survey.to_dict() for survey in surveys]
        )
        
    except Exception as e:
        logger.error(f"Error fetching surveys: {str(e)}")
        return error_response(message="설문조사 목록 조회 중 오류가 발생했습니다."), 500


@surveys_bp.route('/<int:survey_id>', methods=['GET'])
@token_required
def get_survey(current_user, survey_id):
    """특정 설문조사 조회 (질문 포함)"""
    try:
        survey = SurveyService.get_survey(survey_id)
        if not survey:
            return error_response(message="설문조사를 찾을 수 없습니다."), 404
        
        # 관리자가 아닌 경우 활성화된 설문만 조회 가능
        if current_user.role not in ['admin', 'super'] and not survey.is_active:
            return error_response(message="접근 권한이 없습니다."), 403
        
        return success_response(data=survey.to_dict_with_questions())
        
    except Exception as e:
        logger.error(f"Error fetching survey {survey_id}: {str(e)}")
        return error_response(message="설문조사 조회 중 오류가 발생했습니다."), 500


# ============================================================================
# 설문 문항 관리 (관리자)
# ============================================================================

@surveys_bp.route('/<int:survey_id>/questions', methods=['POST'])
@admin_required
def add_question(current_user, survey_id):
    """설문 문항 추가 (관리자)"""
    try:
        data = question_create_schema.load(request.json)
        
        question = SurveyService.add_question(
            survey_id=survey_id,
            question_text=data['question_text'],
            question_type=data['question_type'],
            options=data.get('options'),
            is_required=data.get('is_required', False),
            order=data.get('order', 0)
        )
        
        if not question:
            return error_response(message="설문조사를 찾을 수 없습니다."), 404
        
        logger.info(f"Question added to survey {survey_id} by admin {current_user.id}")
        return success_response(
            data=question.to_dict(),
            message="문항이 추가되었습니다."
        ), 201
        
    except ValueError as e:
        return error_response(message=str(e)), 400
    except ValidationError as e:
        return error_response(message="입력 데이터가 올바르지 않습니다.", errors=e.messages), 400
    except Exception as e:
        logger.error(f"Error adding question to survey {survey_id}: {str(e)}")
        return error_response(message="문항 추가 중 오류가 발생했습니다."), 500


@surveys_bp.route('/<int:survey_id>/questions/<int:question_id>', methods=['PUT'])
@admin_required
def update_question(current_user, survey_id, question_id):
    """설문 문항 수정 (관리자)"""
    try:
        data = question_update_schema.load(request.json)
        
        # 문항이 해당 설문에 속하는지 확인
        question = SurveyService.get_question(question_id)
        if not question or question.survey_id != survey_id:
            return error_response(message="문항을 찾을 수 없습니다."), 404
        
        updated_question = SurveyService.update_question(question_id, **data)
        
        logger.info(f"Question {question_id} updated by admin {current_user.id}")
        return success_response(
            data=updated_question.to_dict(),
            message="문항이 수정되었습니다."
        )
        
    except ValidationError as e:
        return error_response(message="입력 데이터가 올바르지 않습니다.", errors=e.messages), 400
    except Exception as e:
        logger.error(f"Error updating question {question_id}: {str(e)}")
        return error_response(message="문항 수정 중 오류가 발생했습니다."), 500


@surveys_bp.route('/<int:survey_id>/questions/<int:question_id>', methods=['DELETE'])
@admin_required
def delete_question(current_user, survey_id, question_id):
    """설문 문항 삭제 (관리자)"""
    try:
        # 문항이 해당 설문에 속하는지 확인
        question = SurveyService.get_question(question_id)
        if not question or question.survey_id != survey_id:
            return error_response(message="문항을 찾을 수 없습니다."), 404
        
        success = SurveyService.delete_question(question_id)
        if not success:
            return error_response(message="문항을 찾을 수 없습니다."), 404
        
        logger.info(f"Question {question_id} deleted by admin {current_user.id}")
        return success_response(message="문항이 삭제되었습니다.")
        
    except Exception as e:
        logger.error(f"Error deleting question {question_id}: {str(e)}")
        return error_response(message="문항 삭제 중 오류가 발생했습니다."), 500


@surveys_bp.route('/<int:survey_id>/questions/reorder', methods=['POST'])
@admin_required
def reorder_questions(current_user, survey_id):
    """문항 순서 재정렬 (관리자)"""
    try:
        data = question_reorder_schema.load(request.json)
        
        success = SurveyService.reorder_questions(
            survey_id=survey_id,
            question_orders=data['question_orders']
        )
        
        if not success:
            return error_response(message="문항 순서 재정렬에 실패했습니다."), 400
        
        logger.info(f"Questions reordered for survey {survey_id} by admin {current_user.id}")
        return success_response(message="문항 순서가 변경되었습니다.")
        
    except ValidationError as e:
        return error_response(message="입력 데이터가 올바르지 않습니다.", errors=e.messages), 400
    except Exception as e:
        logger.error(f"Error reordering questions for survey {survey_id}: {str(e)}")
        return error_response(message="문항 순서 변경 중 오류가 발생했습니다."), 500


# ============================================================================
# 설문 응답 (사용자)
# ============================================================================

@surveys_bp.route('/registration', methods=['GET'])
@token_required
def get_registration_surveys(current_user):
    """회원가입 후 표시할 설문조사 목록"""
    try:
        surveys = SurveyService.get_registration_surveys()
        
        # 각 설문에 대해 완료 여부 추가
        result = []
        for survey in surveys:
            survey_data = survey.to_dict_with_questions()
            survey_data['is_completed'] = SurveyService.has_user_completed_survey(
                current_user.id,
                survey.id
            )
            result.append(survey_data)
        
        return success_response(data=result)
        
    except Exception as e:
        logger.error(f"Error fetching registration surveys: {str(e)}")
        return error_response(message="설문조사 목록 조회 중 오류가 발생했습니다."), 500


@surveys_bp.route('/<int:survey_id>/responses', methods=['POST'])
@token_required
def submit_survey_responses(current_user, survey_id):
    """설문 응답 제출"""
    try:
        data = survey_responses_submit_schema.load(request.json)
        
        # 설문 존재 여부 확인
        survey = SurveyService.get_survey(survey_id)
        if not survey:
            return error_response(message="설문조사를 찾을 수 없습니다."), 404
        
        if not survey.is_active:
            return error_response(message="비활성화된 설문조사입니다."), 400
        
        success = SurveyService.submit_survey_responses(
            user_id=current_user.id,
            survey_id=survey_id,
            responses=data['responses']
        )
        
        if not success:
            return error_response(message="응답 제출에 실패했습니다."), 400
        
        logger.info(f"Survey {survey_id} responses submitted by user {current_user.id}")
        return success_response(message="응답이 제출되었습니다.")
        
    except ValidationError as e:
        return error_response(message="입력 데이터가 올바르지 않습니다.", errors=e.messages), 400
    except Exception as e:
        logger.error(f"Error submitting survey responses: {str(e)}")
        return error_response(message="응답 제출 중 오류가 발생했습니다."), 500


@surveys_bp.route('/<int:survey_id>/responses/my', methods=['GET'])
@token_required
def get_my_responses(current_user, survey_id):
    """내 설문 응답 조회"""
    try:
        responses = SurveyService.get_user_responses(current_user.id, survey_id)
        
        return success_response(
            data=[response.to_dict_with_details() for response in responses]
        )
        
    except Exception as e:
        logger.error(f"Error fetching user responses: {str(e)}")
        return error_response(message="응답 조회 중 오류가 발생했습니다."), 500


# ============================================================================
# 설문 응답 관리 및 통계 (관리자)
# ============================================================================

@surveys_bp.route('/<int:survey_id>/responses', methods=['GET'])
@admin_required
def get_survey_responses(current_user, survey_id):
    """설문 응답 조회 (관리자)"""
    try:
        responses = SurveyService.get_survey_all_responses(survey_id)
        
        return success_response(
            data=[response.to_dict_with_details() for response in responses]
        )
        
    except Exception as e:
        logger.error(f"Error fetching survey responses: {str(e)}")
        return error_response(message="응답 조회 중 오류가 발생했습니다."), 500


@surveys_bp.route('/<int:survey_id>/statistics', methods=['GET'])
@admin_required
def get_survey_statistics(current_user, survey_id):
    """설문 통계 조회 (관리자)"""
    try:
        statistics = SurveyService.get_survey_statistics(survey_id)
        
        if not statistics:
            return error_response(message="설문조사를 찾을 수 없습니다."), 404
        
        return success_response(data=statistics)
        
    except Exception as e:
        logger.error(f"Error fetching survey statistics: {str(e)}")
        return error_response(message="통계 조회 중 오류가 발생했습니다."), 500

