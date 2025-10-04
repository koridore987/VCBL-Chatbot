"""
데이터베이스 모델 및 데이터베이스 관련 함수들
"""
import sqlite3
import hashlib
from typing import List, Tuple, Optional
from app import config

class DatabaseManager:
    """데이터베이스 관리 클래스"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
    
    def get_connection(self):
        """데이터베이스 연결 반환"""
        return sqlite3.connect(self.db_path)
    
    def hash_password(self, password: str) -> str:
        """비밀번호 해시화"""
        return hashlib.sha256(password.encode()).hexdigest()
    
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
    
    def authenticate_user(self, username: str, password: str) -> Optional[int]:
        """사용자 인증"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, password_hash FROM user WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            
            if row and self.hash_password(password) == row[1]:
                return row[0]  # user_id
            return None
        finally:
            conn.close()
    
    def create_user(self, username: str, password: str, chatbot_type_id: int = 1) -> int:
        """새 사용자 생성"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            password_hash = self.hash_password(password)
            cursor.execute(
                "INSERT INTO user (username, password_hash, chatbot_type_id) VALUES (?, ?, ?)",
                (username, password_hash, chatbot_type_id)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def get_or_create_user(self, username: str, password: str = None) -> int:
        """사용자 조회 또는 생성"""
        if password:
            # 인증 시도
            user_id = self.authenticate_user(username, password)
            if user_id:
                return user_id
            # 인증 실패 시 None 반환
            return None
        else:
            # 기존 방식 (비밀번호 없이 생성)
            user_id = self.get_user_by_username(username)
            if user_id:
                return user_id
            # 기본 비밀번호로 생성
            return self.create_user(username, "default123")
    
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
    
    def get_all_users_with_stats(self) -> List[Tuple[int, str, int, str, str]]:
        """모든 사용자와 통계 정보 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT u.id, u.username, 
                       COUNT(m.id) as message_count,
                       u.created_at,
                       MAX(m.timestamp) as last_activity
                FROM user u
                LEFT JOIN message m ON u.id = m.user_id
                GROUP BY u.id, u.username, u.created_at
                ORDER BY u.created_at DESC
            """)
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_user_stats(self) -> Tuple[int, int, int, int]:
        """사용자 통계 조회 (총 회원, 활성 회원, 총 메시지, 최근 가입자)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 총 회원 수
            cursor.execute("SELECT COUNT(*) FROM user")
            total_users = cursor.fetchone()[0]
            
            # 활성 회원 수 (메시지를 보낸 회원)
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM message WHERE sender = 'user'")
            active_users = cursor.fetchone()[0]
            
            # 총 메시지 수
            cursor.execute("SELECT COUNT(*) FROM message")
            total_messages = cursor.fetchone()[0]
            
            # 최근 7일 가입자 수
            cursor.execute("""
                SELECT COUNT(*) FROM user 
                WHERE created_at >= datetime('now', '-7 days')
            """)
            recent_users = cursor.fetchone()[0]
            
            return total_users, active_users, total_messages, recent_users
        finally:
            conn.close()
    
    def delete_user(self, user_id: int) -> bool:
        """사용자 삭제"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 먼저 사용자의 모든 메시지 삭제
            cursor.execute("DELETE FROM message WHERE user_id = ?", (user_id,))
            # 사용자 삭제
            cursor.execute("DELETE FROM user WHERE id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_all_chat_logs(self) -> List[Tuple]:
        """모든 채팅 로그 조회 (CSV/엑셀 내보내기용)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    m.id,
                    u.username,
                    c.name as chatbot_type,
                    m.sender,
                    m.content,
                    m.timestamp
                FROM message m
                JOIN user u ON m.user_id = u.id
                LEFT JOIN chatbot_type c ON u.chatbot_type_id = c.id
                ORDER BY m.timestamp ASC
            """)
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_chat_logs_by_user(self, user_id: int) -> List[Tuple]:
        """특정 사용자의 채팅 로그 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    m.id,
                    u.username,
                    c.name as chatbot_type,
                    m.sender,
                    m.content,
                    m.timestamp
                FROM message m
                JOIN user u ON m.user_id = u.id
                LEFT JOIN chatbot_type c ON u.chatbot_type_id = c.id
                WHERE m.user_id = ?
                ORDER BY m.timestamp ASC
            """, (user_id,))
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_chat_logs_by_date_range(self, start_date: str, end_date: str) -> List[Tuple]:
        """날짜 범위로 채팅 로그 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    m.id,
                    u.username,
                    c.name as chatbot_type,
                    m.sender,
                    m.content,
                    m.timestamp
                FROM message m
                JOIN user u ON m.user_id = u.id
                LEFT JOIN chatbot_type c ON u.chatbot_type_id = c.id
                WHERE DATE(m.timestamp) BETWEEN ? AND ?
                ORDER BY m.timestamp ASC
            """, (start_date, end_date))
            return cursor.fetchall()
        finally:
            conn.close()
