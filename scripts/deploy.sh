#!/bin/bash

# ============================================
# Google Cloud Run 배포 스크립트
# ============================================

set -e

echo "======================================"
echo "VCBL Chatbot - Cloud Run Deployment"
echo "======================================"
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 설정값
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-asia-northeast3}"
SERVICE_NAME="${SERVICE_NAME:-vcbl-chatbot}"

# Project ID 확인
if [ -z "$PROJECT_ID" ]; then
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${YELLOW}GCP_PROJECT_ID가 설정되지 않았습니다.${NC}"
        echo -n "Google Cloud Project ID를 입력하세요: "
        read PROJECT_ID
    fi
fi

echo -e "${GREEN}Project ID: $PROJECT_ID${NC}"
echo -e "${GREEN}Region: $REGION${NC}"
echo -e "${GREEN}Service Name: $SERVICE_NAME${NC}"
echo ""

# 배포 방법 선택
echo "배포 방법을 선택하세요:"
echo "1) Cloud Build 사용 (GitHub 연동)"
echo "2) 로컬에서 빌드 후 배포"
echo ""
read -p "선택 (1 or 2): " DEPLOY_METHOD

if [ "$DEPLOY_METHOD" = "1" ]; then
    echo ""
    echo "Cloud Build 트리거 설정..."
    echo ""
    echo "다음 명령어로 GitHub 저장소를 연결하고 트리거를 생성하세요:"
    echo ""
    echo "gcloud builds triggers create github \\"
    echo "  --repo-name=YOUR_REPO_NAME \\"
    echo "  --repo-owner=YOUR_GITHUB_USERNAME \\"
    echo "  --branch-pattern='^main$' \\"
    echo "  --build-config=cloudbuild.yaml \\"
    echo "  --project=$PROJECT_ID"
    echo ""
    echo "또는 Google Cloud Console에서 수동으로 설정:"
    echo "https://console.cloud.google.com/cloud-build/triggers?project=$PROJECT_ID"
    
elif [ "$DEPLOY_METHOD" = "2" ]; then
    echo ""
    echo "로컬 빌드 및 배포 시작..."
    
    # Docker 이미지 태그
    IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"
    
    # 1. Docker 이미지 빌드
    echo ""
    echo "1. Docker 이미지 빌드 중..."
    docker build -t "$IMAGE_TAG" .
    echo -e "${GREEN}✓ 빌드 완료${NC}"
    
    # 2. GCR에 푸시
    echo ""
    echo "2. Google Container Registry에 푸시 중..."
    docker push "$IMAGE_TAG"
    echo -e "${GREEN}✓ 푸시 완료${NC}"
    
    # 3. Cloud Run에 배포
    echo ""
    echo "3. Cloud Run에 배포 중..."
    
    # Cloud SQL 인스턴스 정보 입력
    echo ""
    echo "Cloud SQL 인스턴스 연결 문자열을 입력하세요"
    echo "(형식: PROJECT_ID:REGION:INSTANCE_NAME)"
    read -p "Cloud SQL Instance: " CLOUD_SQL_INSTANCE
    
    gcloud run deploy "$SERVICE_NAME" \
        --image="$IMAGE_TAG" \
        --region="$REGION" \
        --platform=managed \
        --allow-unauthenticated \
        --memory=1Gi \
        --cpu=1 \
        --min-instances=0 \
        --max-instances=10 \
        --set-env-vars="FLASK_ENV=production,PORT=8080" \
        --add-cloudsql-instances="$CLOUD_SQL_INSTANCE" \
        --set-secrets="SECRET_KEY=SECRET_KEY:latest,JWT_SECRET_KEY=JWT_SECRET_KEY:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,DATABASE_URL=DATABASE_URL:latest" \
        --project="$PROJECT_ID"
    
    echo ""
    echo -e "${GREEN}✓ 배포 완료!${NC}"
    echo ""
    
    # 서비스 URL 가져오기
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(status.url)")
    
    echo "======================================"
    echo -e "${GREEN}배포 성공!${NC}"
    echo "======================================"
    echo ""
    echo "서비스 URL: $SERVICE_URL"
    echo ""
    echo "다음 명령어로 로그 확인:"
    echo "gcloud run services logs read $SERVICE_NAME --region=$REGION --project=$PROJECT_ID"
    echo ""
else
    echo -e "${RED}잘못된 선택입니다.${NC}"
    exit 1
fi

