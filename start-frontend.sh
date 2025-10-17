#!/bin/bash

# ============================================
# VCBL Chatbot - 프론트엔드 개발 서버 시작
# ============================================
# 로컬에서 Vite 개발 서버를 실행합니다.

echo "🎨 프론트엔드 개발 서버 시작 중..."

# 프론트엔드 디렉토리로 이동
cd frontend

# 의존성 설치 (필요한 경우)
if [ ! -d "node_modules" ]; then
    echo "📦 의존성 설치 중..."
    npm install
fi

# Vite 개발 서버 시작
echo "🔥 Vite 개발 서버 시작 (핫 리로드 활성화)"
echo "📍 서버 주소: http://localhost:5173"
echo "🔄 파일 변경 시 자동으로 브라우저가 새로고침됩니다"
echo "⏹️  종료하려면 Ctrl+C를 누르세요"
echo ""

npm run dev
