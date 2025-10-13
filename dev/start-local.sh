#!/bin/bash

# 로컬 개발 환경 시작 스크립트
# 사용법: ./dev/start-local.sh

set -e

echo "🚀 VCBL Chatbot 로컬 개발 환경을 시작합니다..."
echo ""

# 프로젝트 루트로 이동
cd "$(dirname "$0")/.."

# .env 파일 확인
if [ ! -f "backend/.env" ]; then
    echo "⚠️  backend/.env 파일이 없습니다."
    echo "backend/env.example을 복사하여 .env 파일을 생성하세요:"
    echo "  cp backend/env.example backend/.env"
    echo ""
    exit 1
fi

if [ ! -f "frontend/.env" ]; then
    echo "⚠️  frontend/.env 파일이 없습니다."
    echo "frontend/env.example을 복사하여 .env 파일을 생성하세요:"
    echo "  cp frontend/env.example frontend/.env"
    echo ""
    exit 1
fi

# 백엔드 가상환경 확인
if [ ! -d "backend/venv" ]; then
    echo "❌ backend/venv 가상환경이 없습니다."
    echo "다음 명령어로 설정을 먼저 실행하세요:"
    echo "  ./scripts/setup.sh"
    exit 1
fi

# 백엔드 시작
echo "📦 백엔드 서버를 시작합니다..."
cd backend
source venv/bin/activate
export FLASK_APP=run.py
export FLASK_ENV=development
python run.py > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# 백엔드 시작 대기
echo "⏳ 백엔드 서버 시작 대기 중..."
sleep 3

# 백엔드 상태 확인
if ! ps -p $BACKEND_PID > /dev/null; then
    echo "❌ 백엔드 서버 시작 실패!"
    echo "로그를 확인하세요: tail -f backend.log"
    exit 1
fi

# 프론트엔드 시작
echo "🎨 프론트엔드 개발 서버를 시작합니다..."
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# 프론트엔드 시작 대기
echo "⏳ 프론트엔드 서버 시작 대기 중..."
sleep 3

echo ""
echo "✅ 개발 환경이 시작되었습니다!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📱 프론트엔드: http://localhost:5173"
echo "🔧 백엔드:     http://localhost:8080"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 로그 확인:"
echo "  - 백엔드:     tail -f backend.log"
echo "  - 프론트엔드: tail -f frontend.log"
echo ""
echo "🛑 종료하려면 Ctrl+C를 누르세요."

# 종료 시 프로세스 정리
cleanup() {
    echo ""
    echo "🛑 개발 환경을 종료합니다..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo "✅ 종료 완료"
    exit
}

trap cleanup INT TERM

# 프로세스가 종료될 때까지 대기
wait

