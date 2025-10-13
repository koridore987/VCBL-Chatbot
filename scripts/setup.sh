#!/bin/bash

# 의존성 설치 및 환경 설정 스크립트

echo "📦 VCBL Chatbot 의존성을 설치합니다..."
echo ""

# 백엔드 의존성 설치
echo "🐍 백엔드 의존성 설치 중..."
cd backend

# 가상환경 생성 (없는 경우)
if [ ! -d "venv" ]; then
    echo "가상환경을 생성합니다..."
    python3 -m venv venv
fi

# 가상환경 활성화
source venv/bin/activate

# 의존성 설치
echo "pip 패키지를 설치합니다..."
pip install --upgrade pip
pip install -r requirements.txt

# .env 파일 생성 (없는 경우)
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  .env 파일이 없습니다."
    if [ -f "../env.example" ]; then
        echo ".env 파일을 생성합니다..."
        cp ../env.example .env
        echo "✅ .env 파일이 생성되었습니다. 필요한 값을 수정해주세요."
        echo "   특히 SECRET_KEY와 OPENAI_API_KEY를 설정해야 합니다."
    fi
fi

echo "✅ 백엔드 의존성 설치 완료"

cd ..

# 프론트엔드 의존성 설치
echo ""
echo "📦 프론트엔드 의존성 설치 중..."
cd frontend

# .env 파일 생성 (없는 경우)
if [ ! -f ".env" ]; then
    echo "프론트엔드 .env 파일을 생성합니다..."
    echo "VITE_API_URL=http://localhost:8080/api" > .env
    echo "✅ 프론트엔드 .env 파일이 생성되었습니다."
fi

# npm 의존성 설치
echo "npm 패키지를 설치합니다..."
npm install

echo "✅ 프론트엔드 의존성 설치 완료"

cd ..

# 완료
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 모든 의존성 설치가 완료되었습니다!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "다음 단계:"
echo "1. backend/.env 파일에서 SECRET_KEY와 OPENAI_API_KEY를 설정하세요"
echo ""
echo "2. 데이터베이스 마이그레이션을 실행하세요:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   flask db init"
echo "   flask db migrate -m 'Initial migration'"
echo "   flask db upgrade"
echo "   cd .."
echo ""
echo "3. Super 관리자 계정을 생성하세요:"
echo "   ./scripts/create-admin.sh"
echo "   (기본 계정: super / super1234)"
echo ""
echo "4. 개발 서버를 시작하세요:"
echo "   ./start-dev.sh"
echo ""

