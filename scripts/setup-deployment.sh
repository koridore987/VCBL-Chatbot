#!/bin/bash
set -e

echo "🚀 VCBL Chatbot 자동 배포 설정 스크립트"
echo "=========================================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수 정의
print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 입력 검증
if [ -z "$1" ]; then
    print_error "프로젝트 ID를 입력해주세요."
    echo "사용법: $0 <PROJECT_ID>"
    exit 1
fi

PROJECT_ID=$1
REGION="asia-northeast3"
SERVICE_NAME="vcbl-chatbot"

print_step "Google Cloud 프로젝트 설정: $PROJECT_ID"

# 1. Google Cloud CLI 확인
print_step "Google Cloud CLI 확인 중..."
if ! command -v gcloud &> /dev/null; then
    print_error "Google Cloud CLI가 설치되지 않았습니다."
    echo "설치 방법: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# 2. 프로젝트 설정
print_step "프로젝트 설정 중..."
gcloud config set project $PROJECT_ID

# 3. 필요한 API 활성화
print_step "필요한 API 활성화 중..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable iam.googleapis.com

print_success "API 활성화 완료"

# 4. 서비스 계정 생성
print_step "서비스 계정 생성 중..."
SERVICE_ACCOUNT_NAME="vcbl-deploy"
SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

# 서비스 계정이 이미 존재하는지 확인
if gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL &> /dev/null; then
    print_warning "서비스 계정이 이미 존재합니다: $SERVICE_ACCOUNT_EMAIL"
else
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="VCBL Chatbot Deploy Service Account"
    print_success "서비스 계정 생성 완료"
fi

# 5. 권한 부여
print_step "서비스 계정에 권한 부여 중..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/run.admin" \
    --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/iam.serviceAccountUser" \
    --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/cloudsql.client" \
    --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.admin" \
    --quiet

print_success "권한 부여 완료"

# 6. 서비스 계정 키 생성
print_step "서비스 계정 키 생성 중..."
KEY_FILE="vcbl-deploy-key.json"
gcloud iam service-accounts keys create $KEY_FILE \
    --iam-account=$SERVICE_ACCOUNT_EMAIL

print_success "서비스 계정 키 생성 완료: $KEY_FILE"

# 7. GitHub Secrets 설정 안내
print_step "GitHub Secrets 설정 안내"
echo ""
echo "다음 단계를 수행하세요:"
echo "1. GitHub 저장소로 이동"
echo "2. Settings > Secrets and variables > Actions"
echo "3. 다음 시크릿을 추가하세요:"
echo ""
echo "   GCP_PROJECT_ID: $PROJECT_ID"
echo ""
echo "   GCP_SA_KEY: (다음 명령어로 생성된 키를 Base64 인코딩하여 추가)"
echo "   cat $KEY_FILE | base64 -w 0"
echo ""

# 8. Secret Manager 설정 안내
print_step "Secret Manager 설정 안내"
echo ""
echo "다음 시크릿을 Secret Manager에 생성하세요:"
echo ""
echo "1. 데이터베이스 비밀번호:"
echo "   echo -n 'YOUR_DB_PASSWORD' | gcloud secrets create vcbl-db-password --data-file=-"
echo ""
echo "2. OpenAI API 키:"
echo "   echo -n 'YOUR_OPENAI_API_KEY' | gcloud secrets create vcbl-openai-key --data-file=-"
echo ""
echo "3. Flask 시크릿 키:"
echo "   echo -n 'YOUR_SECRET_KEY' | gcloud secrets create vcbl-secret-key --data-file=-"
echo ""
echo "4. JWT 시크릿 키:"
echo "   echo -n 'YOUR_JWT_SECRET_KEY' | gcloud secrets create vcbl-jwt-secret --data-file=-"
echo ""

# 9. Cloud SQL 설정 안내
print_step "Cloud SQL 설정 안내"
echo ""
echo "Cloud SQL 인스턴스를 생성하세요:"
echo ""
echo "gcloud sql instances create vcbl-chatbot-db \\"
echo "    --database-version=POSTGRES_15 \\"
echo "    --tier=db-f1-micro \\"
echo "    --region=$REGION \\"
echo "    --root-password=YOUR_ROOT_PASSWORD"
echo ""
echo "gcloud sql databases create vcbl_chatbot --instance=vcbl-chatbot-db"
echo ""
echo "gcloud sql users create vcbl_user \\"
echo "    --instance=vcbl-chatbot-db \\"
echo "    --password=YOUR_DB_PASSWORD"
echo ""

# 10. 마이그레이션 Job 생성 안내
print_step "데이터베이스 마이그레이션 Job 생성 안내"
echo ""
echo "데이터베이스 마이그레이션을 위한 Cloud Run Job을 생성하세요:"
echo ""
echo "gcloud run jobs create vcbl-migrate \\"
echo "    --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \\"
echo "    --region $REGION \\"
echo "    --set-env-vars FLASK_ENV=production \\"
echo "    --add-cloudsql-instances $PROJECT_ID:$REGION:vcbl-chatbot-db \\"
echo "    --set-secrets DB_PASSWORD=vcbl-db-password:latest,OPENAI_API_KEY=vcbl-openai-key:latest,SECRET_KEY=vcbl-secret-key:latest,JWT_SECRET_KEY=vcbl-jwt-secret:latest \\"
echo "    --command flask \\"
echo "    --args db,upgrade"
echo ""

print_success "설정 완료!"
echo ""
echo "다음 단계:"
echo "1. 위의 안내에 따라 GitHub Secrets 설정"
echo "2. Secret Manager에 시크릿 생성"
echo "3. Cloud SQL 인스턴스 생성"
echo "4. main 브랜치에 코드 push하여 자동 배포 테스트"
echo ""
echo "자세한 내용은 DEPLOYMENT_SETUP.md 파일을 참조하세요."
