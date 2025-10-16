"""
챗봇 페르소나 관련 검증 스키마
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
import json


class CreatePersonaRequest(BaseModel):
    """페르소나 생성 요청 검증"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    system_prompt: str = Field(..., min_length=1, max_length=5000)
    constraints: Optional[Dict[str, Any]] = Field(None, description="OpenAI API 파라미터")
    
    @field_validator('name', 'system_prompt')
    @classmethod
    def validate_required_fields(cls, v):
        if v:
            return v.strip()
        return v
    
    @field_validator('description')
    @classmethod
    def empty_string_to_none(cls, v):
        """빈 문자열을 None으로 변환"""
        if v == '' or (isinstance(v, str) and not v.strip()):
            return None
        return v.strip() if isinstance(v, str) else v
    
    @field_validator('constraints', mode='before')
    @classmethod
    def validate_constraints(cls, v):
        """constraints를 딕셔너리로 변환"""
        if v is None or v == '':
            return None
        
        # 이미 딕셔너리인 경우
        if isinstance(v, dict):
            return v
        
        # 문자열인 경우 JSON 파싱
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                raise ValueError('constraints는 유효한 JSON 형식이어야 합니다')
        
        return v


class UpdatePersonaRequest(BaseModel):
    """페르소나 업데이트 요청 검증"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    system_prompt: Optional[str] = Field(None, min_length=1, max_length=5000)
    constraints: Optional[Dict[str, Any]] = Field(None, description="OpenAI API 파라미터")
    is_active: Optional[bool] = None
    
    @field_validator('name', 'system_prompt')
    @classmethod
    def validate_fields(cls, v):
        if v:
            return v.strip()
        return v
    
    @field_validator('description')
    @classmethod
    def empty_string_to_none(cls, v):
        """빈 문자열을 None으로 변환"""
        if v == '' or (isinstance(v, str) and not v.strip()):
            return None
        return v.strip() if isinstance(v, str) else v
    
    @field_validator('constraints', mode='before')
    @classmethod
    def validate_constraints(cls, v):
        """constraints를 딕셔너리로 변환"""
        if v is None or v == '':
            return None
        
        # 이미 딕셔너리인 경우
        if isinstance(v, dict):
            return v
        
        # 문자열인 경우 JSON 파싱
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                raise ValueError('constraints는 유효한 JSON 형식이어야 합니다')
        
        return v


class TestChatRequest(BaseModel):
    """페르소나 테스트 채팅 요청 검증"""
    message: str = Field(..., min_length=1, max_length=2000)
    persona_id: int = Field(..., gt=0)
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        return v.strip() if v else v


# 하위 호환성을 위한 별칭
CreatePromptRequest = CreatePersonaRequest
UpdatePromptRequest = UpdatePersonaRequest

