"""
설문조사 관련 요청/응답 스키마
"""
from marshmallow import Schema, fields, validate, validates, ValidationError


class SurveyCreateSchema(Schema):
    """설문조사 생성 스키마"""
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    description = fields.Str(required=False, allow_none=True)
    is_required = fields.Bool(required=False, load_default=False)
    show_after_registration = fields.Bool(required=False, load_default=True)


class SurveyUpdateSchema(Schema):
    """설문조사 수정 스키마"""
    title = fields.Str(required=False, validate=validate.Length(min=1, max=200))
    description = fields.Str(required=False, allow_none=True)
    is_required = fields.Bool(required=False)
    show_after_registration = fields.Bool(required=False)
    is_active = fields.Bool(required=False)


class QuestionCreateSchema(Schema):
    """설문 문항 생성 스키마"""
    question_text = fields.Str(required=True, validate=validate.Length(min=1))
    question_type = fields.Str(
        required=True,
        validate=validate.OneOf(['multiple_choice', 'text', 'textarea'])
    )
    options = fields.List(fields.Str(), required=False, allow_none=True)
    is_required = fields.Bool(required=False, load_default=False)
    order = fields.Int(required=False, load_default=0)
    
    @validates('options')
    def validate_options(self, value):
        """객관식 문항인 경우 옵션이 있어야 함"""
        # question_type은 다른 필드이므로 여기서 직접 검증하기 어려움
        # 서비스 레이어에서 추가 검증 필요
        if value is not None and len(value) == 0:
            raise ValidationError("Options list cannot be empty if provided")


class QuestionUpdateSchema(Schema):
    """설문 문항 수정 스키마"""
    question_text = fields.Str(required=False, validate=validate.Length(min=1))
    question_type = fields.Str(
        required=False,
        validate=validate.OneOf(['multiple_choice', 'text', 'textarea'])
    )
    options = fields.List(fields.Str(), required=False, allow_none=True)
    is_required = fields.Bool(required=False)
    order = fields.Int(required=False)


class QuestionReorderSchema(Schema):
    """문항 순서 재정렬 스키마"""
    question_orders = fields.Dict(
        keys=fields.Int(),
        values=fields.Int(),
        required=True
    )


class ResponseSubmitSchema(Schema):
    """단일 응답 제출 스키마"""
    question_id = fields.Int(required=True)
    response_text = fields.Str(required=True, validate=validate.Length(min=1))


class SurveyResponsesSubmitSchema(Schema):
    """설문 전체 응답 제출 스키마"""
    responses = fields.List(
        fields.Nested(ResponseSubmitSchema),
        required=True,
        validate=validate.Length(min=1)
    )


# 응답 스키마 인스턴스 생성
survey_create_schema = SurveyCreateSchema()
survey_update_schema = SurveyUpdateSchema()
question_create_schema = QuestionCreateSchema()
question_update_schema = QuestionUpdateSchema()
question_reorder_schema = QuestionReorderSchema()
response_submit_schema = ResponseSubmitSchema()
survey_responses_submit_schema = SurveyResponsesSubmitSchema()

