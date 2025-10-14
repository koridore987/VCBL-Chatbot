#!/bin/bash
set -e

echo "🧪 VCBL Chatbot 배포 테스트 스크립트"
echo "===================================="

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

print_step "배포 테스트 시작: $PROJECT_ID"

# 1. 서비스 상태 확인
print_step "Cloud Run 서비스 상태 확인 중..."
if gcloud run services describe $SERVICE_NAME --region $REGION &> /dev/null; then
    print_success "서비스가 존재합니다"
    
    # 서비스 URL 가져오기
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)')
    echo "서비스 URL: $SERVICE_URL"
    
    # 2. 헬스 체크
    print_step "헬스 체크 수행 중..."
    if curl -f -s "$SERVICE_URL/health" > /dev/null; then
        print_success "헬스 체크 통과"
    else
        print_warning "헬스 체크 실패 (서비스가 아직 준비되지 않았을 수 있음)"
    fi
    
    # 3. 로그 확인
    print_step "최근 로그 확인 중..."
    echo "최근 10개 로그:"
    gcloud run services logs read $SERVICE_NAME --region $REGION --limit=10
    
else
    print_error "서비스가 존재하지 않습니다"
    echo "먼저 배포를 수행하세요."
    exit 1
fi

# 4. 데이터베이스 연결 확인
print_step "데이터베이스 연결 확인 중..."
if gcloud sql instances describe vcbl-chatbot-db &> /dev/null; then
    print_success "Cloud SQL 인스턴스가 존재합니다"
else
    print_warning "Cloud SQL 인스턴스가 존재하지 않습니다"
fi

# 5. Secret Manager 확인
print_step "Secret Manager 시크릿 확인 중..."
SECRETS=("vcbl-db-password" "vcbl-openai-key" "vcbl-secret-key" "vcbl-jwt-secret")

for secret in "${SECRETS[@]}"; do
    if gcloud secrets describe $secret &> /dev/null; then
        print_success "시크릿 존재: $secret"
    else
        print_warning "시크릿 누락: $secret"
    fi
done

# 6. GitHub Actions 상태 확인
print_step "GitHub Actions 워크플로우 확인 중..."
echo "GitHub 저장소의 Actions 탭에서 최근 워크플로우 실행 상태를 확인하세요."
echo "URL: https://github.com/YOUR_USERNAME/YOUR_REPO/actions"

print_success "배포 테스트 완료!"
echo ""
echo "다음 단계:"
echo "1. 서비스 URL에 접속하여 애플리케이션 동작 확인"
echo "2. GitHub Actions에서 워크플로우 실행 상태 확인"
echo "3. Cloud Run 로그에서 오류 확인"
echo ""
echo "문제가 있다면 다음 명령어로 로그를 확인하세요:"
echo "gcloud run services logs read $SERVICE_NAME --region $REGION --limit=50"
