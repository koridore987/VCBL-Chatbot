#!/bin/bash

# Secret Manager 설정 스크립트
# Cloud Run 배포에 필요한 모든 시크릿을 생성합니다.

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

print_info "프로젝트 ID: $PROJECT_ID"
echo ""
print_warning "이 스크립트는 Secret Manager에 민감한 정보를 저장합니다."
print_warning "각 시크릿 값을 신중하게 입력하세요."
echo ""

# =============================================================================
# 1. SECRET_KEY 생성
# =============================================================================

print_info "[1/7] SECRET_KEY 생성"
echo "Flask 세션 암호화용 키입니다. (최소 32자 권장)"
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)
print_success "자동 생성된 키: ${SECRET_KEY:0:16}..."

if gcloud secrets describe vcbl-secret-key &>/dev/null; then
    print_warning "vcbl-secret-key가 이미 존재합니다. 새 버전을 추가할까요? (y/N)"
    read -p "> " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        echo -n "$SECRET_KEY" | gcloud secrets versions add vcbl-secret-key --data-file=-
        print_success "새 버전이 추가되었습니다."
    else
        print_info "건너뜁니다."
    fi
else
    echo -n "$SECRET_KEY" | gcloud secrets create vcbl-secret-key --data-file=-
    print_success "vcbl-secret-key 생성 완료"
fi
echo ""

# =============================================================================
# 2. JWT_SECRET_KEY 생성
# =============================================================================

print_info "[2/7] JWT_SECRET_KEY 생성"
echo "JWT 토큰 서명용 키입니다. (최소 32자 권장)"
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)
print_success "자동 생성된 키: ${JWT_SECRET_KEY:0:16}..."

if gcloud secrets describe vcbl-jwt-secret-key &>/dev/null; then
    print_warning "vcbl-jwt-secret-key가 이미 존재합니다. 새 버전을 추가할까요? (y/N)"
    read -p "> " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        echo -n "$JWT_SECRET_KEY" | gcloud secrets versions add vcbl-jwt-secret-key --data-file=-
        print_success "새 버전이 추가되었습니다."
    else
        print_info "건너뜁니다."
    fi
else
    echo -n "$JWT_SECRET_KEY" | gcloud secrets create vcbl-jwt-secret-key --data-file=-
    print_success "vcbl-jwt-secret-key 생성 완료"
fi
echo ""

# =============================================================================
# 3. 데이터베이스 비밀번호
# =============================================================================

print_info "[3/7] 데이터베이스 비밀번호"
echo "Cloud SQL PostgreSQL 사용자(vcbl_user) 비밀번호를 입력하세요:"
read -sp "> " DB_PASSWORD
echo ""

if [ -z "$DB_PASSWORD" ]; then
    print_error "비밀번호가 입력되지 않았습니다."
    exit 1
fi

if gcloud secrets describe vcbl-db-password &>/dev/null; then
    print_warning "vcbl-db-password가 이미 존재합니다. 새 버전을 추가할까요? (y/N)"
    read -p "> " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        echo -n "$DB_PASSWORD" | gcloud secrets versions add vcbl-db-password --data-file=-
        print_success "새 버전이 추가되었습니다."
    else
        print_info "건너뜁니다."
    fi
else
    echo -n "$DB_PASSWORD" | gcloud secrets create vcbl-db-password --data-file=-
    print_success "vcbl-db-password 생성 완료"
fi
echo ""

# =============================================================================
# 4. OpenAI API 키
# =============================================================================

print_info "[4/7] OpenAI API 키"
echo "OpenAI API 키를 입력하세요 (sk-로 시작):"
read -sp "> " OPENAI_API_KEY
echo ""

if [ -z "$OPENAI_API_KEY" ]; then
    print_error "API 키가 입력되지 않았습니다."
    exit 1
fi

if gcloud secrets describe vcbl-openai-key &>/dev/null; then
    print_warning "vcbl-openai-key가 이미 존재합니다. 새 버전을 추가할까요? (y/N)"
    read -p "> " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        echo -n "$OPENAI_API_KEY" | gcloud secrets versions add vcbl-openai-key --data-file=-
        print_success "새 버전이 추가되었습니다."
    else
        print_info "건너뜁니다."
    fi
else
    echo -n "$OPENAI_API_KEY" | gcloud secrets create vcbl-openai-key --data-file=-
    print_success "vcbl-openai-key 생성 완료"
fi
echo ""

# =============================================================================
# 5. Super Admin 학번
# =============================================================================

print_info "[5/7] Super Admin 학번"
echo "Super 관리자 학번을 입력하세요 (기본값: super):"
read -p "> " ADMIN_STUDENT_ID
ADMIN_STUDENT_ID=${ADMIN_STUDENT_ID:-super}

if gcloud secrets describe vcbl-admin-student-id &>/dev/null; then
    print_warning "vcbl-admin-student-id가 이미 존재합니다. 새 버전을 추가할까요? (y/N)"
    read -p "> " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        echo -n "$ADMIN_STUDENT_ID" | gcloud secrets versions add vcbl-admin-student-id --data-file=-
        print_success "새 버전이 추가되었습니다."
    else
        print_info "건너뜁니다."
    fi
else
    echo -n "$ADMIN_STUDENT_ID" | gcloud secrets create vcbl-admin-student-id --data-file=-
    print_success "vcbl-admin-student-id 생성 완료"
fi
echo ""

# =============================================================================
# 6. Super Admin 이름
# =============================================================================

print_info "[6/7] Super Admin 이름"
echo "Super 관리자 이름을 입력하세요 (기본값: Super Administrator):"
read -p "> " ADMIN_NAME
ADMIN_NAME=${ADMIN_NAME:-Super Administrator}

if gcloud secrets describe vcbl-admin-name &>/dev/null; then
    print_warning "vcbl-admin-name이 이미 존재합니다. 새 버전을 추가할까요? (y/N)"
    read -p "> " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        echo -n "$ADMIN_NAME" | gcloud secrets versions add vcbl-admin-name --data-file=-
        print_success "새 버전이 추가되었습니다."
    else
        print_info "건너뜁니다."
    fi
else
    echo -n "$ADMIN_NAME" | gcloud secrets create vcbl-admin-name --data-file=-
    print_success "vcbl-admin-name 생성 완료"
fi
echo ""

# =============================================================================
# 7. Super Admin 비밀번호
# =============================================================================

print_info "[7/7] Super Admin 비밀번호"
echo "Super 관리자 비밀번호를 입력하세요 (최소 8자):"
read -sp "> " ADMIN_PASSWORD
echo ""

if [ -z "$ADMIN_PASSWORD" ]; then
    print_error "비밀번호가 입력되지 않았습니다."
    exit 1
fi

if [ ${#ADMIN_PASSWORD} -lt 8 ]; then
    print_error "비밀번호는 최소 8자 이상이어야 합니다."
    exit 1
fi

if gcloud secrets describe vcbl-admin-password &>/dev/null; then
    print_warning "vcbl-admin-password가 이미 존재합니다. 새 버전을 추가할까요? (y/N)"
    read -p "> " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        echo -n "$ADMIN_PASSWORD" | gcloud secrets versions add vcbl-admin-password --data-file=-
        print_success "새 버전이 추가되었습니다."
    else
        print_info "건너뜁니다."
    fi
else
    echo -n "$ADMIN_PASSWORD" | gcloud secrets create vcbl-admin-password --data-file=-
    print_success "vcbl-admin-password 생성 완료"
fi
echo ""

# =============================================================================
# 완료
# =============================================================================

print_success "모든 시크릿이 생성되었습니다!"
echo ""
print_info "생성된 시크릿 목록:"
gcloud secrets list --filter="name~vcbl-*"
echo ""
print_info "다음 단계:"
echo "1. Cloud SQL 인스턴스가 생성되었는지 확인"
echo "2. Cloud Build로 애플리케이션 배포: gcloud builds submit --config cloudbuild.yaml"
echo "3. Cloud Run Jobs 생성: ./scripts/create-cloud-run-jobs.sh"
echo "4. 마이그레이션 실행 및 관리자 생성"

