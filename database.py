import sqlite3
from datetime import datetime

def init_db():
    """
    데이터베이스를 초기화하고 필요한 테이블들을 생성합니다.
    """
    # chatbot.db 데이터베이스에 연결
    conn = sqlite3.connect('chatbot.db')
    cursor = conn.cursor()
    
    try:
        # user 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL
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
