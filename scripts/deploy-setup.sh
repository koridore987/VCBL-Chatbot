#!/bin/bash
# Google Cloud Run 배포를 위한 초기 설정 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}VCBL Chatbot - Google Cloud Run 배포 설정${NC}"
echo "================================================"

# 프로젝트 ID 입력
read -p "Google Cloud 프로젝트 ID를 입력하세요: " PROJECT_ID
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}프로젝트 ID가 필요합니다.${NC}"
    exit 1
fi

# 리전 설정 (기본값: 서울)
REGION=${REGION:-asia-northeast3}
echo "리전: $REGION"

# 프로젝트 설정
echo -e "\n${YELLOW}1. 프로젝트 설정 중...${NC}"
gcloud config set project $PROJECT_ID

# API 활성화
echo -e "\n${YELLOW}2. 필요한 API 활성화 중...${NC}"
gcloud services enable \
    run.googleapis.com \
    sqladmin.googleapis.com \
    sql-component.googleapis.com \
    compute.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com

# 서비스 계정 생성
echo -e "\n${YELLOW}3. 서비스 계정 생성 중...${NC}"
SERVICE_ACCOUNT="vcbl-chatbot-sa@${PROJECT_ID}.iam.gserviceaccount.com"

if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT &>/dev/null; then
    gcloud iam service-accounts create vcbl-chatbot-sa \
        --display-name="VCBL Chatbot Service Account"
    echo "서비스 계정 생성됨: $SERVICE_ACCOUNT"
else
    echo "서비스 계정이 이미 존재합니다: $SERVICE_ACCOUNT"
fi

# 서비스 계정에 권한 부여
echo -e "\n${YELLOW}4. 서비스 계정 권한 부여 중...${NC}"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"

# Cloud SQL 인스턴스 생성
echo -e "\n${YELLOW}5. Cloud SQL PostgreSQL 인스턴스 생성${NC}"
SQL_INSTANCE="vcbl-postgres"

if ! gcloud sql instances describe $SQL_INSTANCE &>/dev/null; then
    read -p "Cloud SQL 인스턴스를 생성하시겠습니까? (y/n): " CREATE_SQL
    if [ "$CREATE_SQL" = "y" ]; then
        echo "Cloud SQL 인스턴스 생성 중... (5-10분 소요)"
        gcloud sql instances create $SQL_INSTANCE \
            --database-version=POSTGRES_15 \
            --tier=db-f1-micro \
            --region=$REGION \
            --storage-type=SSD \
            --storage-size=10GB \
            --storage-auto-increase \
            --backup-start-time=03:00 \
            --availability-type=zonal
        
        echo -e "${GREEN}Cloud SQL 인스턴스 생성 완료!${NC}"
    fi
else
    echo "Cloud SQL 인스턴스가 이미 존재합니다: $SQL_INSTANCE"
fi

# 데이터베이스 생성
echo -e "\n${YELLOW}6. 데이터베이스 생성${NC}"
DB_NAME="vcbl_chatbot"

if gcloud sql instances describe $SQL_INSTANCE &>/dev/null; then
    read -p "데이터베이스를 생성하시겠습니까? (y/n): " CREATE_DB
    if [ "$CREATE_DB" = "y" ]; then
        gcloud sql databases create $DB_NAME --instance=$SQL_INSTANCE || echo "데이터베이스가 이미 존재할 수 있습니다."
    fi
    
    # 데이터베이스 사용자 생성
    echo -e "\n${YELLOW}7. 데이터베이스 사용자 생성${NC}"
    read -p "DB 사용자 이름 (기본: vcbl_user): " DB_USER
    DB_USER=${DB_USER:-vcbl_user}
    
    read -sp "DB 비밀번호를 입력하세요: " DB_PASSWORD
    echo
    
    if [ -n "$DB_PASSWORD" ]; then
        gcloud sql users create $DB_USER \
            --instance=$SQL_INSTANCE \
            --password=$DB_PASSWORD || echo "사용자가 이미 존재할 수 있습니다."
    fi
fi

# Secret Manager에 비밀 저장
echo -e "\n${YELLOW}8. Secret Manager에 비밀 저장${NC}"

# SECRET_KEY
read -sp "SECRET_KEY를 입력하세요 (최소 32자): " SECRET_KEY
echo
if [ -n "$SECRET_KEY" ]; then
    echo -n "$SECRET_KEY" | gcloud secrets create vcbl-secret-key --data-file=- --replication-policy=automatic || \
    echo -n "$SECRET_KEY" | gcloud secrets versions add vcbl-secret-key --data-file=-
fi

# JWT_SECRET_KEY
read -sp "JWT_SECRET_KEY를 입력하세요 (최소 32자): " JWT_SECRET_KEY
echo
if [ -n "$JWT_SECRET_KEY" ]; then
    echo -n "$JWT_SECRET_KEY" | gcloud secrets create vcbl-jwt-secret-key --data-file=- --replication-policy=automatic || \
    echo -n "$JWT_SECRET_KEY" | gcloud secrets versions add vcbl-jwt-secret-key --data-file=-
fi

# DB_PASSWORD
if [ -n "$DB_PASSWORD" ]; then
    echo -n "$DB_PASSWORD" | gcloud secrets create vcbl-db-password --data-file=- --replication-policy=automatic || \
    echo -n "$DB_PASSWORD" | gcloud secrets versions add vcbl-db-password --data-file=-
fi

# OPENAI_API_KEY
read -sp "OPENAI_API_KEY를 입력하세요: " OPENAI_API_KEY
echo
if [ -n "$OPENAI_API_KEY" ]; then
    echo -n "$OPENAI_API_KEY" | gcloud secrets create vcbl-openai-api-key --data-file=- --replication-policy=automatic || \
    echo -n "$OPENAI_API_KEY" | gcloud secrets versions add vcbl-openai-api-key --data-file=-
fi

# REDIS_URL (선택사항)
read -p "Redis URL을 입력하세요 (기본: memory://): " REDIS_URL
REDIS_URL=${REDIS_URL:-memory://}
echo -n "$REDIS_URL" | gcloud secrets create vcbl-redis-url --data-file=- --replication-policy=automatic || \
echo -n "$REDIS_URL" | gcloud secrets versions add vcbl-redis-url --data-file=-

# Cloud Build 권한 부여
echo -e "\n${YELLOW}9. Cloud Build 권한 설정${NC}"
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUD_BUILD_SA" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUD_BUILD_SA" \
    --role="roles/iam.serviceAccountUser"

# 환경 정보 출력
echo -e "\n${GREEN}================================================${NC}"
echo -e "${GREEN}설정 완료!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "프로젝트 ID: $PROJECT_ID"
echo "리전: $REGION"
echo "Cloud SQL 인스턴스: $SQL_INSTANCE"
echo "Cloud SQL 연결 이름: ${PROJECT_ID}:${REGION}:${SQL_INSTANCE}"
echo "데이터베이스: $DB_NAME"
echo "DB 사용자: $DB_USER"
echo "서비스 계정: $SERVICE_ACCOUNT"
echo ""
echo -e "${YELLOW}다음 단계:${NC}"
echo "1. 데이터베이스 마이그레이션을 실행하세요:"
echo "   ./scripts/run-migration.sh"
echo ""
echo "2. 애플리케이션을 배포하세요:"
echo "   gcloud builds submit --config cloudbuild.yaml"
echo ""
echo -e "${YELLOW}또는 자동 배포를 설정하세요:${NC}"
echo "   GitHub 저장소와 Cloud Build를 연동하여 CI/CD 파이프라인 구축"

