#!/bin/bash

# ============================================
# 로컬 Docker 테스트 스크립트
# 프로덕션과 동일한 환경으로 로컬에서 테스트
# ============================================

set -e

echo "======================================"
echo "VCBL Chatbot - Local Docker Test"
echo "======================================"
echo ""

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}.env 파일이 없습니다. .env.example을 복사하세요.${NC}"
    echo ""
    read -p ".env.example을 .env로 복사하시겠습니까? (y/n): " response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        cp .env.example .env
        echo -e "${GREEN}.env 파일이 생성되었습니다. 필요한 값을 수정하세요.${NC}"
        echo ""
        read -p "계속하시겠습니까? (y/n): " continue_response
        if [[ ! "$continue_response" =~ ^[Yy]$ ]]; then
            exit 0
        fi
    else
        exit 1
    fi
fi

# Docker 이미지 빌드
echo "1. Docker 이미지 빌드 중..."
docker build -t vcbl-chatbot:local .
echo -e "${GREEN}✓ 빌드 완료${NC}"
echo ""

# 기존 컨테이너 중지 및 제거
echo "2. 기존 컨테이너 정리..."
docker stop vcbl-chatbot-test 2>/dev/null || true
docker rm vcbl-chatbot-test 2>/dev/null || true
echo -e "${GREEN}✓ 정리 완료${NC}"
echo ""

# 컨테이너 실행
echo "3. 컨테이너 실행 중..."
docker run -d \
    --name vcbl-chatbot-test \
    -p 8080:8080 \
    --env-file .env \
    vcbl-chatbot:local

echo -e "${GREEN}✓ 컨테이너 시작 완료${NC}"
echo ""

# 헬스 체크
echo "4. 헬스 체크 중..."
echo "애플리케이션 시작 대기 (최대 60초)..."

for i in {1..60}; do
    if curl -f http://localhost:8080/health >/dev/null 2>&1; then
        echo -e "${GREEN}✓ 애플리케이션 실행 중!${NC}"
        break
    fi
    
    if [ $i -eq 60 ]; then
        echo -e "${YELLOW}헬스 체크 타임아웃. 로그를 확인하세요:${NC}"
        echo "docker logs vcbl-chatbot-test"
        exit 1
    fi
    
    sleep 1
done

echo ""
echo "======================================"
echo -e "${GREEN}로컬 테스트 환경 실행 중!${NC}"
echo "======================================"
echo ""
echo "애플리케이션 URL: http://localhost:8080"
echo "API Health: http://localhost:8080/health"
echo ""
echo "유용한 명령어:"
echo "  - 로그 보기: docker logs -f vcbl-chatbot-test"
echo "  - 컨테이너 중지: docker stop vcbl-chatbot-test"
echo "  - 컨테이너 재시작: docker restart vcbl-chatbot-test"
echo "  - 컨테이너 제거: docker rm -f vcbl-chatbot-test"
echo ""

