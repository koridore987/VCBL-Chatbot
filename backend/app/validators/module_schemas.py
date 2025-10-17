"""
모듈 관련 요청 스키마
"""
from pydantic import BaseModel, validator
from typing import Optional


class CreateModuleRequest(BaseModel):
    title: str
    youtube_url: str
    youtube_id: Optional[str] = None  # 자동 추출되므로 선택사항
    description: Optional[str] = None
    duration: Optional[int] = None
    thumbnail_url: Optional[str] = None
    scaffolding_mode: str = 'none'
    order_index: int = 0
    survey_url: Optional[str] = None
    intro_text: Optional[str] = None
    
    @validator('scaffolding_mode')
    def validate_scaffolding_mode(cls, v):
        valid_modes = ['none', 'prompt', 'chat']
        if v not in valid_modes:
            raise ValueError(f'유효하지 않은 학습 모드입니다. 허용된 값: {", ".join(valid_modes)}')
        return v


class UpdateModuleRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    scaffolding_mode: Optional[str] = None
    is_active: Optional[bool] = None
    learning_enabled: Optional[bool] = None
    order_index: Optional[int] = None
    survey_url: Optional[str] = None
    intro_text: Optional[str] = None
    
    @validator('scaffolding_mode')
    def validate_scaffolding_mode(cls, v):
        if v is not None:
            valid_modes = ['none', 'prompt', 'chat']
            if v not in valid_modes:
                raise ValueError(f'유효하지 않은 학습 모드입니다. 허용된 값: {", ".join(valid_modes)}')
        return v




