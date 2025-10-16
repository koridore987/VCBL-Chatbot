"""
스캐폴딩 관련 검증 스키마
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class CreateScaffoldingRequest(BaseModel):
    """스캐폴딩 생성 요청 검증"""
    title: str = Field(..., min_length=1, max_length=200)
    prompt_text: Optional[str] = Field(default='', max_length=2000)  # Allow empty prompt text
    order_index: int = Field(default=1, ge=1)
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if v:
            return v.strip()
        return v
    
    @field_validator('prompt_text')
    @classmethod
    def validate_prompt_text(cls, v):
        if v:
            return v.strip()
        return ''  # Return empty string if None or empty


class UpdateScaffoldingRequest(BaseModel):
    """스캐폴딩 업데이트 요청 검증"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    prompt_text: Optional[str] = Field(None, max_length=2000)  # Allow empty prompt text
    order_index: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if v:
            return v.strip()
        return v
    
    @field_validator('prompt_text')
    @classmethod
    def validate_prompt_text(cls, v):
        if v is not None:
            return v.strip()
        return v


class ScaffoldingResponseRequest(BaseModel):
    """스캐폴딩 응답 요청 검증"""
    response_text: str = Field(..., min_length=1, max_length=5000)
    
    @field_validator('response_text')
    @classmethod
    def validate_response_text(cls, v):
        v = v.strip()
        if not v:
            raise ValueError('응답 내용을 입력해주세요')
        return v


class ScaffoldingResponseItem(BaseModel):
    """개별 스캐폴딩 응답"""
    scaffolding_id: int = Field(..., gt=0)
    response_text: str = Field(..., max_length=5000)
    
    @field_validator('response_text')
    @classmethod
    def validate_response_text(cls, v):
        if v:
            return v.strip()
        return ''


class BulkScaffoldingResponseRequest(BaseModel):
    """여러 스캐폴딩 응답 일괄 저장 요청 검증"""
    responses: list[ScaffoldingResponseItem] = Field(..., min_length=1)
    
    @field_validator('responses')
    @classmethod
    def validate_responses(cls, v):
        if not v:
            raise ValueError('최소 하나 이상의 응답이 필요합니다')
        return v


class ReorderScaffoldingItem(BaseModel):
    """순서 변경을 위한 개별 스캐폴딩"""
    id: int = Field(..., gt=0)
    order_index: int = Field(..., ge=1)


class ReorderScaffoldingsRequest(BaseModel):
    """스캐폴딩 순서 재정렬 요청 검증"""
    scaffoldings: list[ReorderScaffoldingItem] = Field(..., min_length=1)
    
    @field_validator('scaffoldings')
    @classmethod
    def validate_scaffoldings(cls, v):
        if not v:
            raise ValueError('최소 하나 이상의 스캐폴딩이 필요합니다')
        
        # 순서가 중복되지 않는지 확인
        order_indices = [item.order_index for item in v]
        if len(order_indices) != len(set(order_indices)):
            raise ValueError('순서가 중복될 수 없습니다')
        
        return v

