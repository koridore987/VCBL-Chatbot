#!/bin/bash

# ============================================
# VCBL Chatbot - 백엔드 개발 서버 시작
# ============================================
# 로컬에서 Flask 개발 서버를 실행합니다.

set -e

echo "🚀 백엔드 개발 서버 시작 중..."

# 환경 변수 설정
export FLASK_APP=run.py
export FLASK_ENV=development
export FLASK_DEBUG=1

# .env 파일에서 환경 변수 로드
if [ -f .env ]; then
    echo "📄 .env 파일에서 환경 변수 로드 중..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  .env 파일이 없습니다. env.example을 복사하여 .env 파일을 생성하세요."
    echo "   cp env.example .env"
    exit 1
fi

# 데이터베이스 URL 설정 (로컬 개발용)
export DATABASE_URL=postgresql+psycopg://vcbl_user:${DB_PASSWORD:-vcbl_dev_password}@localhost:5433/vcbl_chatbot

# 데이터베이스와 Redis는 도커로 실행
echo "📦 데이터베이스와 Redis 컨테이너 시작 중..."
docker-compose up -d db redis

# 잠시 대기 (데이터베이스가 준비될 때까지)
echo "⏳ 데이터베이스 준비 중..."
sleep 5

# 백엔드 디렉토리로 이동
cd backend

# 가상환경 활성화
source venv/bin/activate

# 마이그레이션 실행
echo "🗄️ 데이터베이스 마이그레이션 실행 중..."
flask db upgrade

# Flask 개발 서버 시작 (핫 리로드 활성화)
echo "🔥 Flask 개발 서버 시작 (핫 리로드 활성화)"
echo "📍 서버 주소: http://localhost:5000"
echo "🔄 파일 변경 시 자동으로 서버가 재시작됩니다"
echo "⏹️  종료하려면 Ctrl+C를 누르세요"
echo ""

flask run --host=0.0.0.0 --port=5000 --reload
