#!/bin/bash
set -e

echo "Starting VCBL Chatbot Application..."

# 포트 설정
export PORT=${PORT:-8080}
echo "Starting on port: $PORT"

# 애플리케이션 디렉토리로 이동
cd /app/backend
export FLASK_APP=run.py

# 환경 변수 확인
echo "Environment variables:"
echo "PORT: $PORT"
echo "FLASK_ENV: $FLASK_ENV"

# Flask 애플리케이션 실행
echo "Starting Flask application..."
exec python run.py
