"""
사용자 관리 서비스
사용자 CRUD 관련 비즈니스 로직
"""
from app import db, bcrypt
from app.models.user import User
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class UserService:
    """사용자 관리 서비스"""
    
    @staticmethod
    def pre_register_student(student_id: int, name: str, role: str = 'user') -> tuple:
        """
        학번 사전 등록 (관리자용)
        비밀번호 없이 학번과 이름만 등록
        
        Args:
            student_id: 학번 (10자리 정수)
            name: 이름
            role: 역할 (기본값: user)
            
        Returns:
            (user, error): 성공 시 사용자 객체, 실패 시 None과 에러 메시지
        """
        try:
            # 중복 확인
            if User.query.filter_by(student_id=student_id).first():
                return None, '이미 등록된 학번입니다'
            
            # 비밀번호 없이 사용자 생성 (password_hash를 빈 문자열로)
            user = User(
                student_id=student_id,
                password_hash='',  # 빈 문자열로 설정 (회원가입 전 상태)
                name=name,
                role=role,
                is_active=True
            )
            
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"Student pre-registered: {student_id} - {name}")
            return user, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Pre-register student error: {str(e)}")
            return None, '학번 등록 중 오류가 발생했습니다'
    
    @staticmethod
    def get_all_users() -> List[User]:
        """모든 사용자 조회"""
        try:
            return User.query.order_by(User.created_at.desc()).all()
        except Exception as e:
            logger.error(f"Get all users error: {str(e)}")
            return []
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """사용자 ID로 조회"""
        try:
            return User.query.get(user_id)
        except Exception as e:
            logger.error(f"Get user by id error: {str(e)}")
            return None
    
    @staticmethod
    def update_user_role(user_id: int, new_role: str) -> tuple:
        """
        사용자 역할 변경
        
        Args:
            user_id: 사용자 ID
            new_role: 새 역할 (user, admin, super)
            
        Returns:
            (user, error): 성공 시 사용자 객체, 실패 시 None과 에러 메시지
        """
        try:
            from app.constants import SUPER_ADMIN_CREDENTIALS
            
            user = User.query.get(user_id)
            
            if not user:
                return None, '사용자를 찾을 수 없습니다'
            
            # Super 관리자는 권한을 변경할 수 없음
            if user.student_id == SUPER_ADMIN_CREDENTIALS['STUDENT_ID']:
                return None, 'Super 관리자의 권한은 변경할 수 없습니다'
            
            # Super 역할로의 변경 방지
            if new_role == 'super':
                return None, 'Super 관리자는 시스템에 하나만 존재할 수 있습니다'
            
            user.role = new_role
            db.session.commit()
            
            logger.info(f"User role updated: {user_id} -> {new_role}")
            return user, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Update user role error: {str(e)}")
            return None, '역할 변경 중 오류가 발생했습니다'
    
    @staticmethod
    def toggle_user_activation(user_id: int, is_active: bool) -> tuple:
        """
        사용자 활성화 상태 변경
        
        Args:
            user_id: 사용자 ID
            is_active: 활성화 여부
            
        Returns:
            (user, error): 성공 시 사용자 객체, 실패 시 None과 에러 메시지
        """
        try:
            from app.constants import SUPER_ADMIN_CREDENTIALS
            
            user = User.query.get(user_id)
            
            if not user:
                return None, '사용자를 찾을 수 없습니다'
            
            # Super 관리자는 비활성화할 수 없음
            if user.student_id == SUPER_ADMIN_CREDENTIALS['STUDENT_ID']:
                return None, 'Super 관리자의 상태는 변경할 수 없습니다'
            
            user.is_active = is_active
            db.session.commit()
            
            logger.info(f"User activation toggled: {user_id} -> {is_active}")
            return user, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Toggle user activation error: {str(e)}")
            return None, '상태 변경 중 오류가 발생했습니다'
    
    @staticmethod
    def reset_user_password(user_id: int, new_password: str) -> tuple:
        """
        사용자 비밀번호 재설정 (관리자용)
        
        Args:
            user_id: 사용자 ID
            new_password: 새 비밀번호
            
        Returns:
            (success, error): 성공 여부와 에러 메시지
        """
        try:
            from app.constants import SUPER_ADMIN_CREDENTIALS
            
            user = User.query.get(user_id)
            
            if not user:
                return False, '사용자를 찾을 수 없습니다'
            
            # Super 관리자의 비밀번호는 재설정할 수 없음
            if user.student_id == SUPER_ADMIN_CREDENTIALS['STUDENT_ID']:
                return False, 'Super 관리자의 비밀번호는 재설정할 수 없습니다'
            
            user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
            db.session.commit()
            
            logger.info(f"Password reset for user: {user_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Reset password error: {str(e)}")
            return False, '비밀번호 재설정 중 오류가 발생했습니다'

