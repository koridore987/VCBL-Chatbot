"""
채팅 관련 검증 스키마
"""
from pydantic import BaseModel, Field, field_validator


class CreateSessionRequest(BaseModel):
    """채팅 세션 생성 요청 검증"""
    module_id: int = Field(..., gt=0, description="모듈 ID")


class SendMessageRequest(BaseModel):
    """메시지 전송 요청 검증"""
    message: str = Field(..., min_length=1, max_length=2000, description="메시지 내용")
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        """메시지 공백 제거 및 검증"""
        v = v.strip()
        if not v:
            raise ValueError('메시지 내용을 입력해주세요')
        return v

