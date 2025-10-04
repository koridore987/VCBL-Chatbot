"""
Flask 서버 실행 파일
"""
from app import create_app
from database import init_db
import config

# 데이터베이스 초기화
init_db()

# Flask 앱 생성
app = create_app()

if __name__ == '__main__':
    app.run(debug=config.DEBUG)
