"""
비디오 관련 검증 스키마
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class CreateVideoRequest(BaseModel):
    """비디오 생성 요청 검증"""
    title: str = Field(..., min_length=1, max_length=200)
    youtube_url: str = Field(..., min_length=1, max_length=500)
    youtube_id: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=2000)
    duration: Optional[int] = Field(None, ge=0)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    scaffolding_mode: str = Field(default='none', pattern='^(none|prompt|chat)$')
    order_index: int = Field(default=0, ge=0)
    survey_url: Optional[str] = Field(None, max_length=500)
    intro_text: Optional[str] = Field(None, max_length=5000)
    
    @field_validator('title', 'youtube_url', 'youtube_id')
    @classmethod
    def validate_string_fields(cls, v):
        if v:
            return v.strip()
        return v


class UpdateVideoRequest(BaseModel):
    """비디오 업데이트 요청 검증"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    scaffolding_mode: Optional[str] = Field(None, pattern='^(none|prompt|chat)$')
    is_active: Optional[bool] = None
    learning_enabled: Optional[bool] = None
    order_index: Optional[int] = Field(None, ge=0)
    survey_url: Optional[str] = Field(None, max_length=500)
    intro_text: Optional[str] = Field(None, max_length=5000)
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if v:
            return v.strip()
        return v

