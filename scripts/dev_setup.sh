#!/bin/bash

# ============================================
# VCBL Chatbot - 로컬 개발 환경 설정
# ============================================
# Docker 없이 로컬에서 직접 개발할 수 있도록 환경을 설정합니다.

set -e

echo "🚀 VCBL Chatbot 로컬 개발 환경 설정 시작..."

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. 환경 변수 파일 확인
echo -e "${BLUE}1. 환경 변수 파일 설정...${NC}"
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        cp env.example .env
        echo -e "${GREEN}✓ .env 파일이 생성되었습니다${NC}"
        echo -e "${YELLOW}⚠️  .env 파일을 열어서 OPENAI_API_KEY를 설정하세요${NC}"
    else
        echo -e "${YELLOW}❌ env.example 파일이 없습니다${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ .env 파일이 이미 존재합니다${NC}"
fi

# 2. 백엔드 가상환경 설정
echo -e "${BLUE}2. 백엔드 Python 환경 설정...${NC}"
cd backend

# Python 버전 확인
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}❌ Python3가 설치되어 있지 않습니다${NC}"
    echo "   macOS: brew install python3"
    echo "   Ubuntu: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

# 가상환경 생성
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Python 가상환경이 생성되었습니다${NC}"
else
    echo -e "${GREEN}✓ Python 가상환경이 이미 존재합니다${NC}"
fi

# 가상환경 활성화 및 의존성 설치
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ Python 의존성이 설치되었습니다${NC}"

cd ..

# 3. 프론트엔드 환경 설정
echo -e "${BLUE}3. 프론트엔드 Node.js 환경 설정...${NC}"
cd frontend

# Node.js 버전 확인
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}❌ Node.js가 설치되어 있지 않습니다${NC}"
    echo "   macOS: brew install node"
    echo "   Ubuntu: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs"
    exit 1
fi

# npm 의존성 설치
if [ ! -d "node_modules" ]; then
    npm install
    echo -e "${GREEN}✓ Node.js 의존성이 설치되었습니다${NC}"
else
    echo -e "${GREEN}✓ Node.js 의존성이 이미 설치되어 있습니다${NC}"
fi

cd ..

# 4. 데이터베이스 설정 (Docker 사용)
echo -e "${BLUE}4. 데이터베이스 설정...${NC}"
echo "   데이터베이스는 Docker로 실행합니다 (PostgreSQL + Redis)"
echo "   다음 명령어로 데이터베이스를 시작하세요:"
echo -e "${YELLOW}   docker-compose -f docker-compose.dev.yml up -d${NC}"

echo ""
echo "======================================"
echo -e "${GREEN}🎉 로컬 개발 환경 설정 완료!${NC}"
echo "======================================"
echo ""
echo "📋 다음 단계:"
echo "1. 데이터베이스 시작: docker-compose -f docker-compose.dev.yml up -d"
echo "2. 백엔드 서버 시작: cd backend && source venv/bin/activate && python run.py"
echo "3. 프론트엔드 서버 시작: cd frontend && npm run dev"
echo ""
echo "🔧 또는 Docker Compose로 전체 실행: docker-compose up"
