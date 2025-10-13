#!/bin/bash
# Cloud SQL에 대해 데이터베이스 마이그레이션을 실행하는 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}VCBL Chatbot - 데이터베이스 마이그레이션${NC}"
echo "================================================"

# 프로젝트 ID 입력
read -p "Google Cloud 프로젝트 ID (기본: 현재 프로젝트): " PROJECT_ID
if [ -z "$PROJECT_ID" ]; then
    PROJECT_ID=$(gcloud config get-value project)
fi

REGION=${REGION:-asia-northeast3}
SQL_INSTANCE=${SQL_INSTANCE:-vcbl-postgres}
INSTANCE_CONNECTION="${PROJECT_ID}:${REGION}:${SQL_INSTANCE}"

echo "프로젝트: $PROJECT_ID"
echo "Cloud SQL 인스턴스: $INSTANCE_CONNECTION"

# Cloud SQL Proxy를 통한 로컬 연결 방법
echo -e "\n${YELLOW}옵션 1: Cloud SQL Proxy 사용 (권장)${NC}"
echo "1. Cloud SQL Proxy 다운로드:"
echo "   wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy"
echo "   chmod +x cloud_sql_proxy"
echo ""
echo "2. 백그라운드에서 실행:"
echo "   ./cloud_sql_proxy -instances=${INSTANCE_CONNECTION}=tcp:5432 &"
echo ""
echo "3. 마이그레이션 실행:"
echo "   cd backend"
echo "   export DATABASE_URL='postgresql://vcbl_user:YOUR_PASSWORD@127.0.0.1:5432/vcbl_chatbot'"
echo "   export FLASK_APP=run.py"
echo "   flask db upgrade"
echo ""

# Cloud Run Jobs를 통한 마이그레이션
echo -e "${YELLOW}옵션 2: Cloud Run Jobs 사용 (자동화)${NC}"
echo ""

read -p "Cloud Run Job을 생성/업데이트하시겠습니까? (y/n): " CREATE_JOB

if [ "$CREATE_JOB" = "y" ]; then
    JOB_NAME="vcbl-chatbot-migrate"
    IMAGE="gcr.io/${PROJECT_ID}/vcbl-chatbot:latest"
    
    echo -e "\n${YELLOW}마이그레이션 Job 생성 중...${NC}"
    
    # Job이 이미 존재하는지 확인
    if gcloud run jobs describe $JOB_NAME --region=$REGION &>/dev/null; then
        echo "기존 Job 업데이트 중..."
        gcloud run jobs update $JOB_NAME \
            --region=$REGION \
            --image=$IMAGE \
            --set-cloudsql-instances=$INSTANCE_CONNECTION \
            --set-env-vars="CLOUD_SQL_INSTANCE=${INSTANCE_CONNECTION},DB_USER=vcbl_user,DB_NAME=vcbl_chatbot,FLASK_ENV=production" \
            --set-secrets="DB_PASSWORD=vcbl-db-password:latest,SECRET_KEY=vcbl-secret-key:latest,JWT_SECRET_KEY=vcbl-jwt-secret-key:latest,OPENAI_API_KEY=vcbl-openai-api-key:latest" \
            --service-account="vcbl-chatbot-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
            --memory=1Gi \
            --cpu=1 \
            --max-retries=3 \
            --task-timeout=10m \
            --command="/bin/bash" \
            --args="-c,cd /app/backend && export FLASK_APP=run.py && flask db upgrade"
    else
        echo "새 Job 생성 중..."
        gcloud run jobs create $JOB_NAME \
            --region=$REGION \
            --image=$IMAGE \
            --set-cloudsql-instances=$INSTANCE_CONNECTION \
            --set-env-vars="CLOUD_SQL_INSTANCE=${INSTANCE_CONNECTION},DB_USER=vcbl_user,DB_NAME=vcbl_chatbot,FLASK_ENV=production" \
            --set-secrets="DB_PASSWORD=vcbl-db-password:latest,SECRET_KEY=vcbl-secret-key:latest,JWT_SECRET_KEY=vcbl-jwt-secret-key:latest,OPENAI_API_KEY=vcbl-openai-api-key:latest" \
            --service-account="vcbl-chatbot-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
            --memory=1Gi \
            --cpu=1 \
            --max-retries=3 \
            --task-timeout=10m \
            --command="/bin/bash" \
            --args="-c,cd /app/backend && export FLASK_APP=run.py && flask db upgrade"
    fi
    
    echo -e "\n${GREEN}마이그레이션 Job 생성/업데이트 완료!${NC}"
    
    # Job 실행 여부 확인
    read -p "지금 마이그레이션을 실행하시겠습니까? (y/n): " RUN_NOW
    if [ "$RUN_NOW" = "y" ]; then
        echo "마이그레이션 실행 중..."
        gcloud run jobs execute $JOB_NAME --region=$REGION --wait
        echo -e "${GREEN}마이그레이션 완료!${NC}"
    fi
fi

echo -e "\n${GREEN}================================================${NC}"
echo -e "${GREEN}설정이 완료되었습니다!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${YELLOW}다음 명령어로 배포하세요:${NC}"
echo "  gcloud builds submit --config cloudbuild.yaml"

