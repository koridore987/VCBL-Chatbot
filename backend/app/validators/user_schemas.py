"""
사용자 관리 관련 검증 스키마
"""
from pydantic import BaseModel, Field, field_validator


class PreRegisterStudentRequest(BaseModel):
    """학번 사전 등록 요청 검증"""
    student_id: int = Field(..., ge=1000000000, le=9999999999, description="학번 (10자리 정수)")
    name: str = Field(..., min_length=1, max_length=100, description="이름")
    role: str = Field(default='user', pattern='^(user|admin)$', description="역할")
    
    @field_validator('student_id')
    @classmethod
    def validate_student_id(cls, v):
        """학번 검증"""
        if not (1000000000 <= v <= 9999999999):
            raise ValueError('학번은 10자리 정수여야 합니다')
        return v
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """이름 공백 제거"""
        return v.strip()


class UpdateUserRoleRequest(BaseModel):
    """사용자 역할 변경 요청 검증"""
    role: str = Field(..., pattern='^(user|admin|super)$')


class UpdateUserStatusRequest(BaseModel):
    """사용자 상태 변경 요청 검증"""
    is_active: bool = Field(...)


class ResetPasswordRequest(BaseModel):
    """비밀번호 재설정 요청 검증"""
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        """비밀번호 강도 검증"""
        import re
        if len(v) < 8:
            raise ValueError('비밀번호는 최소 8자 이상이어야 합니다')
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('비밀번호는 최소 1개 이상의 영문자를 포함해야 합니다')
        if not re.search(r'[0-9]', v):
            raise ValueError('비밀번호는 최소 1개 이상의 숫자를 포함해야 합니다')
        return v

