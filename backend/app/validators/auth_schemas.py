"""
인증 관련 검증 스키마
"""
from pydantic import BaseModel, Field, field_validator
import re


class RegisterRequest(BaseModel):
    """회원가입 요청 검증"""
    student_id: int = Field(..., ge=1000000000, le=9999999999, description="학번 (10자리 정수)")
    password: str = Field(..., min_length=8, max_length=128, description="비밀번호")
    
    @field_validator('student_id')
    @classmethod
    def validate_student_id(cls, v):
        """학번은 10자리 정수, 관리자는 9999로 시작하므로 사용 불가"""
        if not (1000000000 <= v <= 9999999999):
            raise ValueError('학번은 10자리 정수여야 합니다')
        # 일반 사용자는 9999로 시작하는 학번 사용 불가
        if str(v).startswith('9999'):
            raise ValueError('해당 학번 범위는 관리자 전용입니다')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """비밀번호 강도 검증"""
        if len(v) < 8:
            raise ValueError('비밀번호는 최소 8자 이상이어야 합니다')
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('비밀번호는 최소 1개 이상의 영문자를 포함해야 합니다')
        if not re.search(r'[0-9]', v):
            raise ValueError('비밀번호는 최소 1개 이상의 숫자를 포함해야 합니다')
        return v


class LoginRequest(BaseModel):
    """로그인 요청 검증"""
    student_id: int = Field(..., ge=1000000000, le=9999999999, description="학번 (10자리 정수)")
    password: str = Field(..., min_length=1, max_length=128)


class ChangePasswordRequest(BaseModel):
    """비밀번호 변경 요청 검증"""
    old_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        """비밀번호 강도 검증"""
        if len(v) < 8:
            raise ValueError('비밀번호는 최소 8자 이상이어야 합니다')
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('비밀번호는 최소 1개 이상의 영문자를 포함해야 합니다')
        if not re.search(r'[0-9]', v):
            raise ValueError('비밀번호는 최소 1개 이상의 숫자를 포함해야 합니다')
        return v

