"""
데이터베이스 모델 및 데이터베이스 관련 함수들
"""
import sqlite3
import hashlib
import threading
from typing import List, Tuple, Optional
from werkzeug.security import check_password_hash, generate_password_hash
from app import config

class DatabaseManager:
    """데이터베이스 관리 클래스 (PythonAnywhere 최적화)"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
        self._connection = None
        self._lock = threading.Lock()
    
    def get_connection(self):
        """최적화된 데이터베이스 연결 반환"""
        with self._lock:
            if self._connection is None:
                self._connection = sqlite3.connect(
                    self.db_path,
                    timeout=30.0,
                    check_same_thread=False
                )
                # PythonAnywhere 최적화 설정
                self._connection.execute("PRAGMA journal_mode=WAL")
                self._connection.execute("PRAGMA synchronous=NORMAL")
                self._connection.execute("PRAGMA cache_size=10000")
                self._connection.execute("PRAGMA temp_store=MEMORY")
                self._connection.execute("PRAGMA mmap_size=268435456")
                self._connection.execute("PRAGMA optimize")
            return self._connection
    
    def hash_password(self, password: str) -> str:
        """비밀번호 해시화 (솔트 포함)"""
        return generate_password_hash(password)

    def verify_password(self, password: str, password_hash: str, cursor=None, user_id: Optional[int] = None) -> bool:
        """
        저장된 해시와 평문 비밀번호 비교.
        legacy SHA-256 해시도 지원하며, 검증에 성공하면 PBKDF2 해시로 업그레이드합니다.
        """
        if password_hash.startswith('pbkdf2:'):
            return check_password_hash(password_hash, password)

        # 레거시 SHA-256
        legacy_match = hashlib.sha256(password.encode()).hexdigest() == password_hash
        if legacy_match and cursor is not None and user_id is not None:
            # 성공 시 즉시 PBKDF2로 업그레이드
            cursor.execute(
                "UPDATE user SET password_hash = ? WHERE id = ?",
                (self.hash_password(password), user_id)
            )
        return legacy_match
    
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
            
            if row and self.verify_password(password, row[1], cursor=cursor, user_id=row[0]):
                if not row[1].startswith('pbkdf2:'):
                    conn.commit()
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
    
    def create_user_by_student_number(self, student_number: str, password: str, name: str = None) -> int:
        """학번으로 새 사용자 생성 (이름 자동 채우기)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 학번 검증 및 이름 가져오기
            cursor.execute("SELECT id, name FROM student_numbers WHERE student_number = ?", (student_number,))
            student_info = cursor.fetchone()
            if not student_info:
                raise ValueError("등록되지 않은 학번입니다.")
            
            # 이미 등록된 학번인지 확인
            cursor.execute("SELECT id FROM user WHERE student_number = ?", (student_number,))
            if cursor.fetchone():
                raise ValueError("이미 등록된 학번입니다.")
            
            # 사용자명 생성 (학번 기반)
            username = f"student_{student_number}"
            
            # 학번에 등록된 이름이 있으면 사용, 없으면 파라미터로 받은 이름 사용
            student_name = student_info[1] if student_info[1] else name
            
            # 사용자 생성
            password_hash = self.hash_password(password)
            cursor.execute(
                "INSERT INTO user (username, password_hash, student_number, name, chatbot_type_id) VALUES (?, ?, ?, ?, ?)",
                (username, password_hash, student_number, student_name, 1)
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def verify_student_number(self, student_number: str) -> tuple:
        """학번 검증 및 정보 반환"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, name FROM student_numbers WHERE student_number = ?", (student_number,))
            result = cursor.fetchone()
            if result:
                return result  # (id, name)
            return None
        finally:
            conn.close()
    
    def check_student_registration(self, student_number: str) -> bool:
        """학번 등록 여부 확인"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM user WHERE student_number = ?", (student_number,))
            return cursor.fetchone() is not None
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
        except Exception as e:
            print(f"get_user_stats 오류: {e}")
            return 0, 0, 0, 0
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
