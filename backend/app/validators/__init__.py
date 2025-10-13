"""
입력 검증 스키마
Pydantic을 사용한 요청 데이터 검증
"""
from .auth_schemas import RegisterRequest, LoginRequest, ChangePasswordRequest
from .chat_schemas import CreateSessionRequest, SendMessageRequest
from .video_schemas import CreateVideoRequest, UpdateVideoRequest
from .scaffolding_schemas import (
    CreateScaffoldingRequest, UpdateScaffoldingRequest, 
    ScaffoldingResponseRequest, BulkScaffoldingResponseRequest
)
from .prompt_schemas import CreatePromptRequest, UpdatePromptRequest
from .user_schemas import (
    PreRegisterStudentRequest, UpdateUserRoleRequest, 
    UpdateUserStatusRequest, ResetPasswordRequest
)

__all__ = [
    'RegisterRequest',
    'LoginRequest',
    'ChangePasswordRequest',
    'CreateSessionRequest',
    'SendMessageRequest',
    'CreateVideoRequest',
    'UpdateVideoRequest',
    'CreateScaffoldingRequest',
    'UpdateScaffoldingRequest',
    'ScaffoldingResponseRequest',
    'BulkScaffoldingResponseRequest',
    'CreatePromptRequest',
    'UpdatePromptRequest',
    'PreRegisterStudentRequest',
    'UpdateUserRoleRequest',
    'UpdateUserStatusRequest',
    'ResetPasswordRequest',
]

