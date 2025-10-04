"""
챗봇 타입 관리 모델
"""
import sqlite3
from typing import List, Tuple, Optional
from datetime import datetime
from app import config

class ChatbotTypeManager:
    """챗봇 타입 관리 클래스"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
    
    def get_connection(self):
        """데이터베이스 연결"""
        return sqlite3.connect(self.db_path)
    
    def get_all_chatbot_types(self) -> List[Tuple]:
        """모든 챗봇 타입 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, name, description, system_prompt, created_at, updated_at
                FROM chatbot_type
                ORDER BY id ASC
            """)
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_chatbot_type(self, chatbot_type_id: int) -> Optional[Tuple]:
        """특정 챗봇 타입 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, name, description, system_prompt, created_at, updated_at
                FROM chatbot_type
                WHERE id = ?
            """, (chatbot_type_id,))
            return cursor.fetchone()
        finally:
            conn.close()
    
    def create_chatbot_type(self, name: str, description: str, system_prompt: str) -> int:
        """새로운 챗봇 타입 생성"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO chatbot_type (name, description, system_prompt)
                VALUES (?, ?, ?)
            """, (name, description, system_prompt))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()
    
    def update_chatbot_type(self, chatbot_type_id: int, name: str, description: str, system_prompt: str) -> bool:
        """챗봇 타입 업데이트"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE chatbot_type
                SET name = ?, description = ?, system_prompt = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (name, description, system_prompt, chatbot_type_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def delete_chatbot_type(self, chatbot_type_id: int) -> bool:
        """챗봇 타입 삭제"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 먼저 이 타입을 사용하는 사용자 수 확인
            cursor.execute("SELECT COUNT(*) FROM user WHERE chatbot_type_id = ?", (chatbot_type_id,))
            user_count = cursor.fetchone()[0]
            
            if user_count > 0:
                # 사용 중인 타입은 삭제 불가
                return False
            
            cursor.execute("DELETE FROM chatbot_type WHERE id = ?", (chatbot_type_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def get_chatbot_type_usage(self, chatbot_type_id: int) -> int:
        """특정 챗봇 타입을 사용하는 사용자 수 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM user WHERE chatbot_type_id = ?
            """, (chatbot_type_id,))
            return cursor.fetchone()[0]
        finally:
            conn.close()

