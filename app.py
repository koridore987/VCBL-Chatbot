from flask import Flask
from database import init_db
from routes import init_routes

# 데이터베이스 초기화
init_db()

# Flask 앱 생성
app = Flask(__name__)
app.secret_key = 'your_super_secret_key_123!@#'  # 세션을 위한 시크릿키 설정

# 라우트 등록
init_routes(app)

if __name__ == '__main__':
    app.run(debug=True)
