#!/bin/bash

# Google Cloud 초기 설정 스크립트
# PostgreSQL + Cloud SQL + Secret Manager + Cloud Run 배포를 위한 환경 설정

set -e

echo "🚀 VCBL Chatbot Google Cloud 배포 설정을 시작합니다..."

# 프로젝트 ID 확인
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Google Cloud 프로젝트가 설정되지 않았습니다."
    echo "다음 명령어로 프로젝트를 설정하세요:"
    echo "gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "📋 프로젝트 ID: $PROJECT_ID"

# 필요한 API 활성화
echo "🔧 필요한 Google Cloud API를 활성화합니다..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    cloudresourcemanager.googleapis.com

# Cloud SQL 인스턴스 생성
echo "🗄️ Cloud SQL PostgreSQL 인스턴스를 생성합니다..."
gcloud sql instances create vcbl-chatbot-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=asia-northeast3 \
    --storage-type=SSD \
    --storage-size=10GB \
    --storage-auto-increase \
    --backup \
    --enable-bin-log \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=3 \
    --maintenance-release-channel=production \
    --deletion-protection

# 데이터베이스 생성
echo "📊 데이터베이스를 생성합니다..."
gcloud sql databases create vcbl_chatbot --instance=vcbl-chatbot-db

# 사용자 생성
echo "👤 데이터베이스 사용자를 생성합니다..."
DB_PASSWORD=$(openssl rand -base64 32)
gcloud sql users create vcbl_user \
    --instance=vcbl-chatbot-db \
    --password="$DB_PASSWORD"

# Secret Manager에 시크릿 저장
echo "🔐 Secret Manager에 시크릿을 저장합니다..."

# 데이터베이스 URL 생성
INSTANCE_CONNECTION_NAME="$PROJECT_ID:asia-northeast3:vcbl-chatbot-db"
DATABASE_URL="postgresql+psycopg2://vcbl_user:$DB_PASSWORD@/vcbl_chatbot?host=/cloudsql/$INSTANCE_CONNECTION_NAME"

# 시크릿 생성
echo "$DATABASE_URL" | gcloud secrets create vcbl-database-url --data-file=-
echo "$OPENAI_API_KEY" | gcloud secrets create vcbl-openai-key --data-file=-
echo "$SECRET_KEY" | gcloud secrets create vcbl-secret-key --data-file=-
echo "$JWT_SECRET_KEY" | gcloud secrets create vcbl-jwt-secret --data-file=-

# 서비스 계정 생성 및 권한 부여
echo "🔑 서비스 계정을 생성하고 권한을 부여합니다..."
gcloud iam service-accounts create vcbl-deploy \
    --display-name="VCBL Chatbot Deploy Service Account"

# 필요한 권한 부여
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:vcbl-deploy@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:vcbl-deploy@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:vcbl-deploy@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

# Cloud Build 트리거 생성
echo "🔨 Cloud Build 트리거를 생성합니다..."
gcloud builds triggers create github \
    --repo-name=VCBL-Chatbot \
    --repo-owner=koridore987 \
    --branch-pattern="^main$" \
    --build-config=cloudbuild.yaml

echo "✅ 설정이 완료되었습니다!"
echo ""
echo "📝 다음 단계:"
echo "1. 환경 변수를 설정하세요:"
echo "   export OPENAI_API_KEY='your-openai-api-key'"
echo "   export SECRET_KEY='your-secret-key'"
echo "   export JWT_SECRET_KEY='your-jwt-secret-key'"
echo ""
echo "2. 이 스크립트를 다시 실행하세요:"
echo "   ./scripts/deploy-setup.sh"
echo ""
echo "3. 또는 수동으로 시크릿을 설정하세요:"
echo "   gcloud secrets versions add vcbl-openai-key --data-file=-"
echo "   gcloud secrets versions add vcbl-secret-key --data-file=-"
echo "   gcloud secrets versions add vcbl-jwt-secret --data-file=-"
