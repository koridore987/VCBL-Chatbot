"""
인증 서비스
사용자 인증 관련 비즈니스 로직
"""
from app import db, bcrypt
from app.models.user import User
from flask_jwt_extended import create_access_token
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """인증 관련 서비스"""
    
    @staticmethod
    def register_user(student_id: int, password: str) -> tuple:
        """
        사용자 회원가입
        관리자가 사전에 등록한 학번으로만 가입 가능
        
        Args:
            student_id: 학번 (10자리 정수)
            password: 비밀번호
            
        Returns:
            (user, error): 성공 시 사용자 객체, 실패 시 None과 에러 메시지
        """
        try:
            # 사전 등록된 학번인지 확인 (비밀번호가 없는 상태)
            user = User.query.filter_by(student_id=student_id).first()
            
            if not user:
                return None, '사전 등록되지 않은 학번입니다. 관리자에게 문의하세요.'
            
            # 이미 비밀번호가 설정되어 있으면 이미 가입된 것
            if user.password_hash:
                return None, '이미 가입이 완료된 학번입니다'
            
            # 비밀번호 해시 설정
            user.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            db.session.commit()
            
            logger.info(f"User registration completed: {student_id}")
            return user, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {str(e)}")
            return None, '회원가입 처리 중 오류가 발생했습니다'
    
    @staticmethod
    def login_user(student_id: int, password: str, token_expires_days: int = 7) -> tuple:
        """
        사용자 로그인
        
        Args:
            student_id: 학번
            password: 비밀번호
            token_expires_days: 토큰 만료 기간(일)
            
        Returns:
            (access_token, user, error): 성공 시 토큰과 사용자 객체, 실패 시 None과 에러 메시지
        """
        try:
            # 사용자 조회
            user = User.query.filter_by(student_id=student_id).first()
            
            if not user or not bcrypt.check_password_hash(user.password_hash, password):
                logger.warning(f"Failed login attempt for: {student_id}")
                return None, None, '학번 또는 비밀번호가 올바르지 않습니다'
            
            if not user.is_active:
                logger.warning(f"Inactive user login attempt: {student_id}")
                return None, None, '비활성화된 계정입니다'
            
            # 일일 토큰 사용량 리셋
            if user.last_token_reset.date() < datetime.utcnow().date():
                user.daily_token_usage = 0
                user.last_token_reset = datetime.utcnow()
                db.session.commit()
            
            # JWT 토큰 생성
            access_token = create_access_token(
                identity=str(user.id),
                expires_delta=timedelta(days=token_expires_days)
            )
            
            logger.info(f"User logged in: {student_id}")
            return access_token, user, None
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return None, None, '로그인 처리 중 오류가 발생했습니다'
    
    @staticmethod
    def change_password(user_id: int, old_password: str, new_password: str) -> tuple:
        """
        비밀번호 변경
        
        Args:
            user_id: 사용자 ID
            old_password: 현재 비밀번호
            new_password: 새 비밀번호
            
        Returns:
            (success, error): 성공 여부와 에러 메시지
        """
        try:
            user = User.query.get(user_id)
            
            if not user:
                return False, '사용자를 찾을 수 없습니다'
            
            if not bcrypt.check_password_hash(user.password_hash, old_password):
                logger.warning(f"Invalid old password for user: {user_id}")
                return False, '현재 비밀번호가 올바르지 않습니다'
            
            # 새 비밀번호 설정
            user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
            db.session.commit()
            
            logger.info(f"Password changed for user: {user_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Password change error: {str(e)}")
            return False, '비밀번호 변경 중 오류가 발생했습니다'
    
    @staticmethod
    def get_current_user(user_id) -> tuple:
        """
        현재 사용자 정보 조회
        
        Args:
            user_id: 사용자 ID (문자열 또는 정수)
            
        Returns:
            (user, error): 성공 시 사용자 객체, 실패 시 None과 에러 메시지
        """
        try:
            # JWT identity는 문자열이므로 정수로 변환
            user_id = int(user_id)
            user = User.query.get(user_id)
            
            if not user:
                return None, '사용자를 찾을 수 없습니다'
            
            return user, None
            
        except Exception as e:
            logger.error(f"Get user error: {str(e)}")
            return None, '사용자 정보 조회 중 오류가 발생했습니다'

