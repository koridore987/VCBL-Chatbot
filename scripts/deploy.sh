#!/bin/bash
# Google Cloud Run에 애플리케이션 배포

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}VCBL Chatbot - Cloud Run 배포${NC}"
echo "================================================"

# 프로젝트 ID 확인
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    read -p "Google Cloud 프로젝트 ID를 입력하세요: " PROJECT_ID
    gcloud config set project $PROJECT_ID
fi

echo "프로젝트: $PROJECT_ID"
echo ""

# Cloud Build를 사용한 배포
echo -e "${YELLOW}Cloud Build를 통해 배포합니다...${NC}"
echo ""

# Git 커밋 해시 가져오기 (선택사항)
if git rev-parse --git-dir > /dev/null 2>&1; then
    COMMIT_SHA=$(git rev-parse --short HEAD)
    echo "현재 커밋: $COMMIT_SHA"
fi

# 빌드 실행
echo -e "\n${YELLOW}빌드 및 배포 시작...${NC}"
gcloud builds submit --config cloudbuild.yaml

echo -e "\n${GREEN}================================================${NC}"
echo -e "${GREEN}배포 완료!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${YELLOW}서비스 URL 확인:${NC}"
gcloud run services describe vcbl-chatbot --region=asia-northeast3 --format="value(status.url)"
echo ""
echo -e "${YELLOW}로그 확인:${NC}"
echo "  gcloud run services logs read vcbl-chatbot --region=asia-northeast3"
echo ""
echo -e "${YELLOW}서비스 상태 확인:${NC}"
echo "  gcloud run services describe vcbl-chatbot --region=asia-northeast3"

