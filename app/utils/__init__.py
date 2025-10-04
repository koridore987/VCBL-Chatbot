import sqlite3
from datetime import datetime
from app import config

def init_db():
    """
    데이터베이스를 초기화하고 필요한 테이블들을 생성합니다.
    """
    # config.py에서 데이터베이스 경로 가져오기
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # user 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # message 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS message (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                sender TEXT CHECK(sender IN ('user', 'bot')) NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')
        
        # admin 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT CHECK(role IN ('super', 'admin')) NOT NULL DEFAULT 'admin',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
        ''')
        
        # 기본 super 관리자 생성 (없는 경우에만)
        cursor.execute("SELECT COUNT(*) FROM admin WHERE role = 'super'")
        super_count = cursor.fetchone()[0]
        
        if super_count == 0:
            import hashlib
            default_password = "super123"
            password_hash = hashlib.sha256(default_password.encode()).hexdigest()
            cursor.execute(
                "INSERT INTO admin (username, password_hash, role) VALUES (?, ?, ?)",
                ("super", password_hash, "super")
            )
            print("기본 super 관리자가 생성되었습니다. (ID: super, PW: super123)")
        
        # 변경사항 저장
        conn.commit()
        print("데이터베이스가 성공적으로 초기화되었습니다.")
        
    except sqlite3.Error as e:
        print(f"데이터베이스 초기화 중 오류가 발생했습니다: {e}")
        conn.rollback()
        
    finally:
        # 연결 종료
        conn.close()

if __name__ == "__main__":
    # 스크립트가 직접 실행될 때 데이터베이스 초기화
    init_db()