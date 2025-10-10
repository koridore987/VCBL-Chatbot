"""
Google Cloud Functions용 진입점
Google App Engine과 Cloud Run에서도 사용 가능
"""
import os
import sys
from flask import Flask

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 환경변수 설정
os.environ['FLASK_ENV'] = 'production'

# Flask 앱 import
from app import create_app

# Flask 앱 생성
app = create_app()

def main(request):
    """
    Google Cloud Functions 진입점
    Cloud Functions에서 사용할 때 호출되는 함수
    """
    return app(request.environ, lambda *args: None)

# App Engine과 Cloud Run에서 사용할 때
if __name__ == '__main__':
    # 개발 환경에서 테스트용
    app.run(debug=False, host='0.0.0.0', port=8080)
