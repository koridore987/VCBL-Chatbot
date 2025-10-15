#!/bin/bash

# ============================================
# Google Cloud 초기 설정 스크립트
# Cloud SQL, Secret Manager, Service Account 설정
# ============================================

set -e

echo "======================================"
echo "VCBL Chatbot - Google Cloud Setup"
echo "======================================"
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 설정값 (필요시 수정)
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-asia-northeast3}"
DB_INSTANCE_NAME="${DB_INSTANCE_NAME:-vcbl-chatbot-db}"
DB_NAME="${DB_NAME:-vcbl_chatbot}"
DB_USER="${DB_USER:-vcbl_user}"
SERVICE_NAME="${SERVICE_NAME:-vcbl-chatbot}"

# Project ID 확인
if [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}GCP_PROJECT_ID가 설정되지 않았습니다.${NC}"
    echo -n "Google Cloud Project ID를 입력하세요: "
    read PROJECT_ID
fi

echo -e "${GREEN}Project ID: $PROJECT_ID${NC}"
echo -e "${GREEN}Region: $REGION${NC}"
echo ""

# gcloud 설정
echo "1. gcloud 프로젝트 설정..."
gcloud config set project "$PROJECT_ID"

# 필요한 API 활성화
echo ""
echo "2. 필요한 Google Cloud API 활성화..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    compute.googleapis.com \
    vpcaccess.googleapis.com

echo -e "${GREEN}✓ API 활성화 완료${NC}"

# Cloud SQL 인스턴스 생성 (선택사항)
echo ""
echo "3. Cloud SQL 인스턴스 생성 (이미 존재하면 스킵)"
if gcloud sql instances describe "$DB_INSTANCE_NAME" --project="$PROJECT_ID" 2>/dev/null; then
    echo -e "${YELLOW}Cloud SQL 인스턴스가 이미 존재합니다: $DB_INSTANCE_NAME${NC}"
else
    echo "Cloud SQL 인스턴스를 생성하시겠습니까? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "데이터베이스 비밀번호를 입력하세요:"
        read -s DB_PASSWORD
        
        gcloud sql instances create "$DB_INSTANCE_NAME" \
            --database-version=POSTGRES_15 \
            --tier=db-f1-micro \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --root-password="$DB_PASSWORD"
        
        echo -e "${GREEN}✓ Cloud SQL 인스턴스 생성 완료${NC}"
        
        # 데이터베이스 생성
        gcloud sql databases create "$DB_NAME" \
            --instance="$DB_INSTANCE_NAME" \
            --project="$PROJECT_ID"
        
        # 사용자 생성
        gcloud sql users create "$DB_USER" \
            --instance="$DB_INSTANCE_NAME" \
            --password="$DB_PASSWORD" \
            --project="$PROJECT_ID"
        
        echo -e "${GREEN}✓ 데이터베이스 및 사용자 생성 완료${NC}"
    fi
fi

# Secret Manager에 시크릿 생성
echo ""
echo "4. Secret Manager 설정"
echo "다음 시크릿들을 생성합니다:"
echo "  - SECRET_KEY"
echo "  - JWT_SECRET_KEY"
echo "  - OPENAI_API_KEY"
echo "  - DATABASE_URL"

create_secret() {
    local SECRET_NAME=$1
    local SECRET_VALUE=$2
    
    if gcloud secrets describe "$SECRET_NAME" --project="$PROJECT_ID" 2>/dev/null; then
        echo -e "${YELLOW}시크릿이 이미 존재합니다: $SECRET_NAME${NC}"
        echo "덮어쓰시겠습니까? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            echo -n "$SECRET_VALUE" | gcloud secrets versions add "$SECRET_NAME" --data-file=- --project="$PROJECT_ID"
            echo -e "${GREEN}✓ 시크릿 업데이트: $SECRET_NAME${NC}"
        fi
    else
        echo -n "$SECRET_VALUE" | gcloud secrets create "$SECRET_NAME" --data-file=- --project="$PROJECT_ID"
        echo -e "${GREEN}✓ 시크릿 생성: $SECRET_NAME${NC}"
    fi
}

echo ""
echo "SECRET_KEY 입력 (Flask secret key):"
read -s SECRET_KEY
create_secret "SECRET_KEY" "$SECRET_KEY"

echo ""
echo "JWT_SECRET_KEY 입력:"
read -s JWT_SECRET_KEY
create_secret "JWT_SECRET_KEY" "$JWT_SECRET_KEY"

echo ""
echo "OPENAI_API_KEY 입력:"
read -s OPENAI_API_KEY
create_secret "OPENAI_API_KEY" "$OPENAI_API_KEY"

echo ""
echo "DATABASE_URL 입력 (예: postgresql+psycopg://user:pass@/db?host=/cloudsql/project:region:instance):"
read -s DATABASE_URL
create_secret "DATABASE_URL" "$DATABASE_URL"

# Cloud Run 서비스 계정에 시크릿 접근 권한 부여
echo ""
echo "5. Cloud Run 서비스 계정 권한 설정..."
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

for SECRET in "SECRET_KEY" "JWT_SECRET_KEY" "OPENAI_API_KEY" "DATABASE_URL"; do
    gcloud secrets add-iam-policy-binding "$SECRET" \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/secretmanager.secretAccessor" \
        --project="$PROJECT_ID" 2>/dev/null || true
done

echo -e "${GREEN}✓ 권한 설정 완료${NC}"

echo ""
echo "======================================"
echo -e "${GREEN}초기 설정 완료!${NC}"
echo "======================================"
echo ""
echo "다음 단계:"
echo "1. cloudbuild.yaml 파일에서 _CLOUD_SQL_INSTANCE 값을 다음으로 수정:"
echo "   ${PROJECT_ID}:${REGION}:${DB_INSTANCE_NAME}"
echo ""
echo "2. 배포 실행:"
echo "   ./scripts/deploy.sh"
echo ""

