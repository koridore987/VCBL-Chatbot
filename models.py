"""
데이터베이스 모델 및 데이터베이스 관련 함수들
"""
import sqlite3
from typing import List, Tuple, Optional
import config

class DatabaseManager:
    """데이터베이스 관리 클래스"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
    
    def get_connection(self):
        """데이터베이스 연결 반환"""
        return sqlite3.connect(self.db_path)
    
    def get_user_by_username(self, username: str) -> Optional[int]:
        """사용자명으로 사용자 ID 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM user WHERE username = ?", (username,))
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            conn.close()
    
    def create_user(self, username: str) -> int:
        """새 사용자 생성"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO user (username) VALUES (?)", (username,))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def get_or_create_user(self, username: str) -> int:
        """사용자 조회 또는 생성"""
        user_id = self.get_user_by_username(username)
        if user_id:
            return user_id
        return self.create_user(username)
    
    def get_user_messages(self, user_id: int) -> List[Tuple[str, str, str]]:
        """사용자의 메시지 목록 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT sender, content, timestamp FROM message WHERE user_id = ? ORDER BY timestamp ASC",
                (user_id,)
            )
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_recent_messages(self, user_id: int, limit: int = None) -> List[Tuple[str, str]]:
        """최근 메시지 조회 (OpenAI 컨텍스트용)"""
        if limit is None:
            limit = config.MAX_RECENT_MESSAGES
            
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT sender, content FROM message WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
                (user_id, limit)
            )
            messages = cursor.fetchall()
            return messages[::-1]  # 시간순으로 정렬
        finally:
            conn.close()
    
    def save_message(self, user_id: int, sender: str, content: str) -> None:
        """메시지 저장"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO message (user_id, sender, content) VALUES (?, ?, ?)",
                (user_id, sender, content)
            )
            conn.commit()
        finally:
            conn.close()
