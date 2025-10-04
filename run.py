"""
Flask 서버 실행 파일
"""
from app import create_app
from app.utils import init_db
from app import config

# 데이터베이스 초기화
init_db()

# Flask 앱 생성
app = create_app()

if __name__ == '__main__':
    app.run(debug=config.DEBUG, port=8080, host='0.0.0.0')
