#!/bin/bash

# Cloud Run Job 생성 스크립트
# 마이그레이션 및 관리자 생성을 위한 Job을 생성합니다.

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수 정의
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
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

# 환경 변수 확인
if [ -z "$PROJECT_ID" ]; then
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$PROJECT_ID" ]; then
        print_error "PROJECT_ID가 설정되지 않았습니다."
        print_info "사용법: PROJECT_ID=your-project-id $0"
        print_info "또는: gcloud config set project your-project-id"
        exit 1
    fi
fi

REGION=${REGION:-asia-northeast3}
IMAGE_NAME="gcr.io/$PROJECT_ID/vcbl-chatbot-backend"

print_info "프로젝트 ID: $PROJECT_ID"
print_info "리전: $REGION"
print_info "이미지: $IMAGE_NAME"
echo ""

# =============================================================================
# 1. 마이그레이션 Job 생성
# =============================================================================

print_info "마이그레이션 Job을 생성합니다..."

gcloud run jobs create vcbl-migrate \
  --image=$IMAGE_NAME \
  --region=$REGION \
  --set-env-vars="FLASK_ENV=production,CLOUD_SQL_INSTANCE=$PROJECT_ID:$REGION:vcbl-chatbot-db,DB_USER=vcbl_user,DB_NAME=vcbl_chatbot" \
  --set-secrets="DB_PASSWORD=vcbl-db-password:latest,SECRET_KEY=vcbl-secret-key:latest,JWT_SECRET_KEY=vcbl-jwt-secret:latest,OPENAI_API_KEY=vcbl-openai-key:latest" \
  --add-cloudsql-instances="$PROJECT_ID:$REGION:vcbl-chatbot-db" \
  --memory=1Gi \
  --cpu=1 \
  --max-retries=3 \
  --task-timeout=10m \
  --command="flask" \
  --args="db,upgrade" \
  || print_warning "마이그레이션 Job이 이미 존재하거나 생성 실패"

print_success "마이그레이션 Job 생성 완료 (또는 이미 존재함)"
echo ""

# =============================================================================
# 2. Super Admin 생성 Job 생성
# =============================================================================

print_info "Super Admin 생성 Job을 생성합니다..."

# Secret Manager에 관리자 정보가 있는지 확인
print_info "Secret Manager에 관리자 정보가 설정되어 있는지 확인하세요:"
print_info "  - vcbl-admin-student-id"
print_info "  - vcbl-admin-name"
print_info "  - vcbl-admin-password"
echo ""

read -p "Secret Manager에 관리자 정보를 설정하셨나요? (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    print_warning "먼저 Secret Manager에 관리자 정보를 설정하세요:"
    echo ""
    echo "  # 관리자 학번"
    echo "  echo -n 'super' | gcloud secrets create vcbl-admin-student-id --data-file=-"
    echo ""
    echo "  # 관리자 이름"
    echo "  echo -n 'Super Administrator' | gcloud secrets create vcbl-admin-name --data-file=-"
    echo ""
    echo "  # 관리자 비밀번호"
    echo "  echo -n 'YourSecurePassword123!' | gcloud secrets create vcbl-admin-password --data-file=-"
    echo ""
    print_info "설정 후 다시 실행하세요."
    exit 1
fi

gcloud run jobs create vcbl-init-admin \
  --image=$IMAGE_NAME \
  --region=$REGION \
  --set-env-vars="FLASK_ENV=production,CLOUD_SQL_INSTANCE=$PROJECT_ID:$REGION:vcbl-chatbot-db,DB_USER=vcbl_user,DB_NAME=vcbl_chatbot" \
  --set-secrets="DB_PASSWORD=vcbl-db-password:latest,SECRET_KEY=vcbl-secret-key:latest,JWT_SECRET_KEY=vcbl-jwt-secret:latest,OPENAI_API_KEY=vcbl-openai-key:latest,ADMIN_STUDENT_ID=vcbl-admin-student-id:latest,ADMIN_NAME=vcbl-admin-name:latest,ADMIN_PASSWORD=vcbl-admin-password:latest" \
  --add-cloudsql-instances="$PROJECT_ID:$REGION:vcbl-chatbot-db" \
  --memory=1Gi \
  --cpu=1 \
  --max-retries=3 \
  --task-timeout=10m \
  --command="flask" \
  --args="init-admin" \
  || print_warning "Admin 생성 Job이 이미 존재하거나 생성 실패"

print_success "Super Admin 생성 Job 생성 완료 (또는 이미 존재함)"
echo ""

# =============================================================================
# 사용법 안내
# =============================================================================

print_success "모든 Job이 생성되었습니다!"
echo ""
print_info "사용법:"
echo ""
echo "1. 마이그레이션 실행:"
echo "   gcloud run jobs execute vcbl-migrate --region=$REGION --wait"
echo ""
echo "2. Super Admin 생성:"
echo "   gcloud run jobs execute vcbl-init-admin --region=$REGION --wait"
echo ""
echo "3. Job 실행 로그 확인:"
echo "   gcloud run jobs executions logs read EXECUTION_NAME --region=$REGION"
echo ""
echo "4. Job 목록 확인:"
echo "   gcloud run jobs list --region=$REGION"
echo ""
print_info "배포 후 마이그레이션과 관리자 생성을 순서대로 실행하세요."

