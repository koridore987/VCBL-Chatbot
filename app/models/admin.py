"""
관리자 관련 모델 및 데이터베이스 함수들
"""
import sqlite3
import hashlib
from typing import List, Tuple, Optional
from datetime import datetime
from app import config

class AdminManager:
    """관리자 관리 클래스"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
    
    def get_connection(self):
        """데이터베이스 연결 반환"""
        return sqlite3.connect(self.db_path)
    
    def hash_password(self, password: str) -> str:
        """비밀번호 해시화"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """비밀번호 검증"""
        return self.hash_password(password) == password_hash
    
    def authenticate_admin(self, username: str, password: str) -> Optional[Tuple[int, str]]:
        """관리자 인증"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT id, password_hash, role FROM admin WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            
            if row and self.verify_password(password, row[1]):
                # 마지막 로그인 시간 업데이트
                cursor.execute(
                    "UPDATE admin SET last_login = ? WHERE id = ?",
                    (datetime.now().isoformat(), row[0])
                )
                conn.commit()
                return (row[0], row[2])  # (admin_id, role)
            return None
        finally:
            conn.close()
    
    def create_admin(self, username: str, password: str, role: str = 'admin') -> bool:
        """새 관리자 생성"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 중복 확인
            cursor.execute("SELECT id FROM admin WHERE username = ?", (username,))
            if cursor.fetchone():
                return False
            
            password_hash = self.hash_password(password)
            cursor.execute(
                "INSERT INTO admin (username, password_hash, role) VALUES (?, ?, ?)",
                (username, password_hash, role)
            )
            conn.commit()
            return True
        except sqlite3.Error:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_all_admins(self) -> List[Tuple[int, str, str, str, str]]:
        """모든 관리자 목록 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, username, role, created_at, last_login
                FROM admin
                ORDER BY created_at DESC
            """)
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_admin_by_id(self, admin_id: int) -> Optional[Tuple[int, str, str, str, str]]:
        """ID로 관리자 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, username, role, created_at, last_login
                FROM admin WHERE id = ?
            """, (admin_id,))
            return cursor.fetchone()
        finally:
            conn.close()
    
    def update_admin_password(self, admin_id: int, new_password: str) -> bool:
        """관리자 비밀번호 변경"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            password_hash = self.hash_password(new_password)
            cursor.execute(
                "UPDATE admin SET password_hash = ? WHERE id = ?",
                (password_hash, admin_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def delete_admin(self, admin_id: int, current_admin_id: int) -> bool:
        """관리자 삭제 (자기 자신은 삭제 불가)"""
        if admin_id == current_admin_id:
            return False
            
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM admin WHERE id = ?", (admin_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def check_super_admin_exists(self) -> bool:
        """super 관리자 존재 여부 확인"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM admin WHERE role = 'super'")
            return cursor.fetchone()[0] > 0
        finally:
            conn.close()
