"""
프롬프트 템플릿 관련 검증 스키마
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class CreatePromptRequest(BaseModel):
    """프롬프트 생성 요청 검증"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    system_prompt: str = Field(..., min_length=1, max_length=5000)
    constraints: Optional[str] = Field(None, max_length=2000)
    video_id: Optional[int] = Field(None, gt=0)
    user_role: Optional[str] = Field(None, pattern='^(user|admin|super)$')
    is_default: bool = Field(default=False)
    
    @field_validator('name', 'system_prompt')
    @classmethod
    def validate_required_fields(cls, v):
        if v:
            return v.strip()
        return v
    
    @field_validator('description', 'constraints', 'user_role')
    @classmethod
    def empty_string_to_none(cls, v):
        """빈 문자열을 None으로 변환"""
        if v == '' or (isinstance(v, str) and not v.strip()):
            return None
        return v.strip() if isinstance(v, str) else v
    
    @field_validator('video_id', mode='before')
    @classmethod
    def empty_video_id_to_none(cls, v):
        """빈 문자열이나 빈 값을 None으로 변환"""
        if v == '' or v is None:
            return None
        return v


class UpdatePromptRequest(BaseModel):
    """프롬프트 업데이트 요청 검증"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    system_prompt: Optional[str] = Field(None, min_length=1, max_length=5000)
    constraints: Optional[str] = Field(None, max_length=2000)
    video_id: Optional[int] = Field(None, gt=0)
    user_role: Optional[str] = Field(None, pattern='^(user|admin|super)$')
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    
    @field_validator('name', 'system_prompt')
    @classmethod
    def validate_fields(cls, v):
        if v:
            return v.strip()
        return v
    
    @field_validator('description', 'constraints', 'user_role')
    @classmethod
    def empty_string_to_none(cls, v):
        """빈 문자열을 None으로 변환"""
        if v == '' or (isinstance(v, str) and not v.strip()):
            return None
        return v.strip() if isinstance(v, str) else v
    
    @field_validator('video_id', mode='before')
    @classmethod
    def empty_video_id_to_none(cls, v):
        """빈 문자열이나 빈 값을 None으로 변환"""
        if v == '' or v is None:
            return None
        return v

