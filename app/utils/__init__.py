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
        # chatbot_type 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chatbot_type (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                system_prompt TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # user 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                chatbot_type_id INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chatbot_type_id) REFERENCES chatbot_type (id)
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
        
        # video 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                video_url TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # activity_log 테이블 생성 (통합 학습 활동 로그)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                video_id INTEGER,
                content TEXT,
                metadata TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user (id),
                FOREIGN KEY (video_id) REFERENCES video (id)
            )
        ''')
        
        # qa_template 테이블 생성 (관리자 설정 질문/답변 - 향후 확장용)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qa_template (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                video_id INTEGER,
                order_index INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES video (id)
            )
        ''')
        
        # video_segments 테이블 생성 (비디오 구간 정의)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_segments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER NOT NULL,
                segment_index INTEGER NOT NULL,
                segment_name TEXT NOT NULL,
                start_time FLOAT NOT NULL,
                end_time FLOAT NOT NULL,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES video (id)
            )
        ''')
        
        # settings 테이블 생성 (시스템 설정)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # qa_responses 테이블 생성 (질문지 답변)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qa_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                answer TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (question_id) REFERENCES qa_template (id),
                UNIQUE(user_id, question_id)
            )
        ''')
        
        # student_numbers 테이블 생성 (학번 관리)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_numbers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_number TEXT UNIQUE NOT NULL,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 기본 챗봇 타입 생성 (없는 경우에만)
        cursor.execute("SELECT COUNT(*) FROM chatbot_type")
        chatbot_type_count = cursor.fetchone()[0]
        
        if chatbot_type_count == 0:
            default_chatbot_types = [
                ("기본 챗봇", "일반적인 대화를 위한 챗봇입니다.", "You are a helpful AI assistant. Please answer questions in a friendly and informative manner."),
                ("학습 도우미", "학습을 돕는 챗봇입니다.", "You are an educational AI assistant. Help users learn by explaining concepts clearly and providing examples."),
                ("연구 조수", "연구를 지원하는 챗봇입니다.", "You are a research assistant AI. Help users with research-related tasks, provide detailed information, and suggest relevant resources.")
            ]
            
            cursor.executemany(
                "INSERT INTO chatbot_type (name, description, system_prompt) VALUES (?, ?, ?)",
                default_chatbot_types
            )
            print("기본 챗봇 타입이 생성되었습니다.")
        
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
        
        # 기본 학번 생성 (없는 경우에만)
        cursor.execute("SELECT COUNT(*) FROM student_numbers")
        student_count = cursor.fetchone()[0]
        
        if student_count == 0:
            default_students = [
                ("2024000001", "관리자1"),
                ("2024000002", "관리자2"),
                ("2024000003", "관리자3")
            ]
            
            cursor.executemany(
                "INSERT INTO student_numbers (student_number, name) VALUES (?, ?)",
                default_students
            )
            print("기본 학번이 생성되었습니다.")
        
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