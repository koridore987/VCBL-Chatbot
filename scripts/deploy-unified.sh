#!/bin/bash

# ============================================
# VCBL Chatbot - 통합 배포 스크립트
# ============================================
# 이 스크립트는 Google Cloud에 VCBL Chatbot을 배포하기 위한
# 모든 설정과 환경변수를 자동으로 구성합니다.
# 
# 사용법:
#   ./deploy-unified.sh [--quick] [--full-setup]
#   --quick: 빠른 배포 (기존 설정 사용)
#   --full-setup: 완전한 초기 설정부터 배포까지

set -e  # 오류 발생 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수들
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 헤더 출력
echo "============================================"
echo "🚀 VCBL Chatbot - 통합 배포 스크립트"
echo "============================================"
echo ""

# ============================================
# 1. 명령행 인수 처리
# ============================================

QUICK_MODE=false
FULL_SETUP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --full-setup)
            FULL_SETUP=true
            shift
            ;;
        -h|--help)
            echo "사용법: $0 [옵션]"
            echo ""
            echo "옵션:"
            echo "  --quick        빠른 배포 (기존 설정 사용)"
            echo "  --full-setup   완전한 초기 설정부터 배포까지"
            echo "  -h, --help     도움말 표시"
            echo ""
            echo "예시:"
            echo "  $0 --quick        # 빠른 배포"
            echo "  $0 --full-setup   # 완전 설정"
            echo "  $0                # 대화형 모드"
            exit 0
            ;;
        *)
            log_error "알 수 없는 옵션: $1"
            echo "사용법: $0 [--quick] [--full-setup] [-h]"
            exit 1
            ;;
    esac
done

# ============================================
# 2. 사전 점검 및 설정
# ============================================

log_info "1. 사전 점검 및 설정 시작..."

# gcloud CLI 설치 확인
if ! command -v gcloud &> /dev/null; then
    log_error "gcloud CLI가 설치되지 않았습니다."
    echo "다음 명령어로 설치하세요:"
    echo "curl https://sdk.cloud.google.com | bash"
    exit 1
fi

# Docker 설치 확인
if ! command -v docker &> /dev/null; then
    log_error "Docker가 설치되지 않았습니다."
    echo "Docker를 설치하고 실행하세요."
    exit 1
fi

# gcloud 인증 확인
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    log_warning "gcloud 인증이 필요합니다."
    gcloud auth login
fi

log_success "사전 점검 완료"

# ============================================
# 공통 유틸: 서비스 계정 권한 보장
# ============================================

ensure_sa_roles() {
    local sa_email=$1
    local project_id=$2

    if [ -z "$sa_email" ] || [ -z "$project_id" ]; then
        return
    fi
    log_info "서비스 계정 권한 확인 중: $sa_email"
    # Secret Manager accessor
    gcloud projects add-iam-policy-binding "$project_id" \
        --member="serviceAccount:$sa_email" \
        --role="roles/secretmanager.secretAccessor" \
        --quiet >/dev/null 2>&1 || true

    # Cloud SQL client
    gcloud projects add-iam-policy-binding "$project_id" \
        --member="serviceAccount:$sa_email" \
        --role="roles/cloudsql.client" \
        --quiet >/dev/null 2>&1 || true
}

# ============================================
# 공통 유틸: buildx 보장 (멀티 플랫폼 빌드용)
# ============================================
ensure_buildx() {
    if ! docker buildx version >/dev/null 2>&1; then
        log_warning "Docker buildx를 사용할 수 없습니다. Docker Desktop 최신 버전이 필요합니다."
        return
    fi
    if ! docker buildx inspect vcbl-builder >/dev/null 2>&1; then
        docker buildx create --name vcbl-builder --use >/dev/null 2>&1 || true
        docker buildx inspect --bootstrap >/dev/null 2>&1 || true
    else
        docker buildx use vcbl-builder >/dev/null 2>&1 || true
        docker buildx inspect --bootstrap >/dev/null 2>&1 || true
    fi
}

# ============================================
# 3. 배포 모드 선택
# ============================================

if [ "$QUICK_MODE" = true ]; then
    log_info "빠른 배포 모드 선택됨"
    DEPLOY_MODE="quick"
elif [ "$FULL_SETUP" = true ]; then
    log_info "완전 설정 모드 선택됨"
    DEPLOY_MODE="full"
else
    echo ""
    echo "배포 모드를 선택하세요:"
    echo "1) 빠른 배포 (기존 설정 사용)"
    echo "2) 완전 설정 (초기 설정부터 배포까지)"
    echo "3) 대화형 모드 (단계별 선택)"
    echo ""
    echo -n "선택 (1, 2, 또는 3): "
    read DEPLOY_CHOICE
    
    case $DEPLOY_CHOICE in
        1)
            DEPLOY_MODE="quick"
            ;;
        2)
            DEPLOY_MODE="full"
            ;;
        3)
            DEPLOY_MODE="interactive"
            ;;
        *)
            log_error "잘못된 선택입니다."
            exit 1
            ;;
    esac
fi

# ============================================
# 4. 프로젝트 설정
# ============================================

echo ""
log_info "2. 프로젝트 설정"

# 프로젝트 ID 설정
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -n "Google Cloud Project ID를 입력하세요: "
    read PROJECT_ID
    gcloud config set project $PROJECT_ID
else
    if [ "$DEPLOY_MODE" != "quick" ]; then
        echo -n "현재 프로젝트 ID ($PROJECT_ID)를 사용하시겠습니까? (y/n): "
        read use_current
        if [ "$use_current" != "y" ]; then
            echo -n "새로운 Google Cloud Project ID를 입력하세요: "
            read PROJECT_ID
            gcloud config set project $PROJECT_ID
        fi
    fi
fi

# 기본 설정값
REGION="${GCP_REGION:-asia-northeast3}"
SERVICE_NAME="${SERVICE_NAME:-vcbl-chatbot}"

if [ "$DEPLOY_MODE" != "quick" ]; then
    # 리전 설정
    echo -n "배포할 리전을 입력하세요 (기본값: $REGION): "
    read input_region
    REGION=${input_region:-$REGION}
    
    # 서비스 이름 설정
    echo -n "서비스 이름을 입력하세요 (기본값: $SERVICE_NAME): "
    read input_service
    SERVICE_NAME=${input_service:-$SERVICE_NAME}
fi

echo -e "${GREEN}Project ID: $PROJECT_ID${NC}"
echo -e "${GREEN}Region: $REGION${NC}"
echo -e "${GREEN}Service Name: $SERVICE_NAME${NC}"

# ============================================
# 5. 빠른 배포 모드
# ============================================

if [ "$DEPLOY_MODE" = "quick" ]; then
    echo ""
    log_info "3. 빠른 배포 시작..."
    
    # Cloud SQL 인스턴스 정보 입력
    echo ""
    echo "Cloud SQL 인스턴스 연결 문자열을 입력하세요"
    echo "(형식: PROJECT_ID:REGION:INSTANCE_NAME)"
    read -p "Cloud SQL Instance: " CLOUD_SQL_INSTANCE
    
    # Docker 이미지 태그 (Artifact Registry 사용)
    IMAGE_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/vcbl-chatbot-repo/${SERVICE_NAME}:latest"

    # buildx 준비
    ensure_buildx

    # 1. 멀티 플랫폼 이미지 빌드 및 푸시 (amd64/arm64)
    echo ""
    log_info "1. 멀티 플랫폼 이미지 빌드/푸시 중 (linux/amd64, linux/arm64)..."
    docker buildx build --platform linux/amd64,linux/arm64 -t "$IMAGE_TAG" --push .
    log_success "이미지 빌드 및 푸시 완료 -> $IMAGE_TAG"
    
    # 2. 푸시는 빌드 시 자동으로 완료됨
    log_success "푸시 완료"
    
    # 3. Cloud Run에 배포
    echo ""
    log_info "3. Cloud Run에 배포 중..."
    
    # 배포용 서비스 계정 (없으면 기본 Compute SA 사용)
    DEPLOY_SA_EMAIL="vcbl-deployer@${PROJECT_ID}.iam.gserviceaccount.com"
    if ! gcloud iam service-accounts describe "$DEPLOY_SA_EMAIL" --project="$PROJECT_ID" >/dev/null 2>&1; then
        PROJECT_NUM=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
        DEPLOY_SA_EMAIL="${PROJECT_NUM}-compute@developer.gserviceaccount.com"
    fi

    ensure_sa_roles "$DEPLOY_SA_EMAIL" "$PROJECT_ID"

    gcloud run deploy "$SERVICE_NAME" \
        --image="$IMAGE_TAG" \
        --region="$REGION" \
        --platform=managed \
        --allow-unauthenticated \
        --memory=1Gi \
        --cpu=1 \
        --min-instances=0 \
        --max-instances=10 \
        --set-env-vars="FLASK_ENV=production" \
        --add-cloudsql-instances="$CLOUD_SQL_INSTANCE" \
        --set-secrets="SECRET_KEY=SECRET_KEY:latest,JWT_SECRET_KEY=JWT_SECRET_KEY:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,DATABASE_URL=DATABASE_URL:latest" \
        --service-account="$DEPLOY_SA_EMAIL" \
        --project="$PROJECT_ID"
    
    log_success "배포 완료!"
    
    # 서비스 URL 가져오기
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(status.url)")
    
    echo ""
    echo "======================================"
    echo -e "${GREEN}배포 성공!${NC}"
    echo "======================================"
    echo ""
    echo "서비스 URL: $SERVICE_URL"
    echo ""
    echo "다음 명령어로 로그 확인:"
    echo "gcloud run services logs read $SERVICE_NAME --region=$REGION --project=$PROJECT_ID"
    echo ""
    
    exit 0
fi

# ============================================
# 6. 완전 설정 모드
# ============================================

if [ "$DEPLOY_MODE" = "full" ]; then
    echo ""
    log_info "3. 완전 설정 모드 시작..."
    
    # 필수 API 활성화
    log_info "필수 Google Cloud API 활성화..."
    APIS=(
        "cloudbuild.googleapis.com"
        "run.googleapis.com"
        "sqladmin.googleapis.com"
        "secretmanager.googleapis.com"
        "containerregistry.googleapis.com"
    )
    
    for api in "${APIS[@]}"; do
        log_info "API 활성화 중: $api"
        gcloud services enable $api --project=$PROJECT_ID
    done
    
    log_success "API 활성화 완료"
    
    # Secret Manager에 시크릿 저장
    echo ""
    log_info "4. Secret Manager에 시크릿 저장..."
    
    # 유틸: 시크릿 존재 여부
    secret_exists() {
        local secret_name=$1
        if gcloud secrets describe "$secret_name" --project="$PROJECT_ID" &>/dev/null; then
            return 0
        else
            return 1
        fi
    }

    # 유틸: 시크릿 생성 (값을 표준입력으로 전달)
    create_secret() {
        local secret_name=$1
        local secret_value=$2
        log_info "시크릿 $secret_name 생성 중..."
        echo -n "$secret_value" | gcloud secrets create "$secret_name" --data-file=- --project="$PROJECT_ID"
    }

    # Cloud SQL 인스턴스 먼저 입력 (나중 단계에서도 사용)
    echo ""
    log_warning "Cloud SQL 인스턴스가 필요합니다."
    echo "형식: PROJECT_ID:REGION:INSTANCE_NAME"
    echo -n "Cloud SQL 인스턴스 연결 문자열을 입력하세요: "
    read CLOUD_SQL_INSTANCE

    # SECRET_KEY
    if secret_exists "SECRET_KEY"; then
        log_success "시크릿 SECRET_KEY 이미 존재 — 입력 생략"
    else
        echo -n "SECRET_KEY (Flask 시크릿 키): "
        read -s SECRET_KEY
        echo ""
        create_secret "SECRET_KEY" "$SECRET_KEY"
    fi

    # JWT_SECRET_KEY
    if secret_exists "JWT_SECRET_KEY"; then
        log_success "시크릿 JWT_SECRET_KEY 이미 존재 — 입력 생략"
    else
        echo -n "JWT_SECRET_KEY (JWT 토큰 시크릿 키): "
        read -s JWT_SECRET_KEY
        echo ""
        create_secret "JWT_SECRET_KEY" "$JWT_SECRET_KEY"
    fi

    # OPENAI_API_KEY
    if secret_exists "OPENAI_API_KEY"; then
        log_success "시크릿 OPENAI_API_KEY 이미 존재 — 입력 생략"
    else
        echo -n "OPENAI_API_KEY (OpenAI API 키): "
        read -s OPENAI_API_KEY
        echo ""
        create_secret "OPENAI_API_KEY" "$OPENAI_API_KEY"
    fi

    # DATABASE_URL
    if secret_exists "DATABASE_URL"; then
        log_success "시크릿 DATABASE_URL 이미 존재 — 입력 생략"
    else
        echo -n "DB_PASSWORD (데이터베이스 비밀번호): "
        read -s DB_PASSWORD
        echo ""
        DB_USER="vcbl_user"
        DB_NAME="vcbl_chatbot"
        DATABASE_URL="postgresql+psycopg://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?host=/cloudsql/${CLOUD_SQL_INSTANCE}"
        create_secret "DATABASE_URL" "$DATABASE_URL"
    fi

    log_success "시크릿 저장 단계 완료"
    
    # Cloud Build 트리거 설정
    echo ""
    log_info "5. Cloud Build 트리거 설정..."
    
    # GitHub 저장소 정보 입력
    echo -n "GitHub 저장소 소유자 (예: username): "
    read GITHUB_OWNER
    
    echo -n "GitHub 저장소 이름: "
    read GITHUB_REPO
    
    # 트리거 생성 여부 확인
    echo -n "Cloud Build 트리거를 생성할까요? (y/n): "
    read CREATE_TRIGGER
    if [ "$CREATE_TRIGGER" = "y" ]; then
        log_info "Cloud Build 트리거 생성 중..."
        if gcloud builds triggers create github \
        --name="vcbl-chatbot-trigger" \
        --repo-name=$GITHUB_REPO \
        --repo-owner=$GITHUB_OWNER \
        --branch-pattern='^main$' \
        --build-config=cloudbuild.yaml \
        --project=$PROJECT_ID \
            --substitutions=_REGION=$REGION,_MEMORY=1Gi,_CPU=1,_MIN_INSTANCES=0,_MAX_INSTANCES=10,_CLOUD_SQL_INSTANCE=$CLOUD_SQL_INSTANCE; then
            log_success "Cloud Build 트리거 생성 완료"
        else
            log_warning "Cloud Build 트리거 생성 실패 — 콘솔에서 수동 설정하거나 스킵하세요."
        fi
    fi
    
    # 배포 방법 선택
    echo ""
    echo "배포 방법을 선택하세요:"
    echo "1) Cloud Build 트리거 사용 (GitHub push 시 자동 배포)"
    echo "2) 로컬에서 즉시 빌드 및 배포"
    echo ""
    echo -n "선택 (1 또는 2): "
    read DEPLOY_CHOICE
    
    if [ "$DEPLOY_CHOICE" = "2" ]; then
        log_info "6. 로컬 빌드 및 배포 시작..."
        
        # Docker 이미지 태그
        IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"
        
        # Docker 이미지 빌드
        log_info "Docker 이미지 빌드 중..."
        docker build -t "$IMAGE_TAG" .
        log_success "Docker 이미지 빌드 완료"
        
        # GCR에 푸시
        log_info "Google Container Registry에 푸시 중..."
        docker push "$IMAGE_TAG"
        log_success "이미지 푸시 완료"
        
        # Cloud Run에 배포
        log_info "Cloud Run에 배포 중..."
        gcloud run deploy "$SERVICE_NAME" \
            --image="$IMAGE_TAG" \
            --region="$REGION" \
            --platform=managed \
            --allow-unauthenticated \
            --memory=1Gi \
            --cpu=1 \
            --min-instances=0 \
            --max-instances=10 \
            --set-env-vars="FLASK_ENV=production" \
            --add-cloudsql-instances="$CLOUD_SQL_INSTANCE" \
            --set-secrets="SECRET_KEY=SECRET_KEY:latest,JWT_SECRET_KEY=JWT_SECRET_KEY:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,DATABASE_URL=DATABASE_URL:latest" \
            --project="$PROJECT_ID"
        
        log_success "Cloud Run 배포 완료"
    fi
fi

# ============================================
# 7. 대화형 모드
# ============================================

if [ "$DEPLOY_MODE" = "interactive" ]; then
    echo ""
    log_info "3. 대화형 모드 시작..."
    
    # 각 단계별로 선택할 수 있도록 구성
    echo "다음 중 실행할 작업을 선택하세요:"
    echo "1) API 활성화"
    echo "2) Secret Manager 설정"
    echo "3) Cloud Build 트리거 설정"
    echo "4) 로컬 빌드 및 배포"
    echo "5) 모든 작업 실행"
    echo ""
    echo -n "선택 (1-5): "
    read INTERACTIVE_CHOICE
    
    # 시크릿 생성 함수 (전역으로 정의)
    create_secret() {
        local secret_name=$1
        local secret_value=$2
        
        if gcloud secrets describe $secret_name --project=$PROJECT_ID &>/dev/null; then
            log_warning "시크릿 $secret_name이 이미 존재합니다. 업데이트합니다."
            echo -n "$secret_value" | gcloud secrets versions add $secret_name --data-file=- --project=$PROJECT_ID
        else
            log_info "시크릿 $secret_name 생성 중..."
            echo -n "$secret_value" | gcloud secrets create $secret_name --data-file=- --project=$PROJECT_ID
        fi
    }
    
    # API 활성화 함수
    enable_apis() {
        log_info "필수 Google Cloud API 활성화..."
        APIS=(
            "cloudbuild.googleapis.com"
            "run.googleapis.com"
            "sqladmin.googleapis.com"
            "secretmanager.googleapis.com"
            "containerregistry.googleapis.com"
        )
        
        for api in "${APIS[@]}"; do
            log_info "API 활성화 중: $api"
            gcloud services enable $api --project=$PROJECT_ID
        done
        log_success "API 활성화 완료"
    }
    
    # Secret Manager 설정 함수
    setup_secrets() {
        log_info "Secret Manager 설정..."
        
        # 필수 시크릿들 입력 받기
        echo ""
        log_warning "다음 시크릿들을 입력하세요 (보안을 위해 입력값이 화면에 표시되지 않습니다):"
        
        echo -n "SECRET_KEY (Flask 시크릿 키): "
        read -s SECRET_KEY
        echo ""
        
        echo -n "JWT_SECRET_KEY (JWT 토큰 시크릿 키): "
        read -s JWT_SECRET_KEY
        echo ""
        
        echo -n "OPENAI_API_KEY (OpenAI API 키): "
        read -s OPENAI_API_KEY
        echo ""
        
        echo -n "DB_PASSWORD (데이터베이스 비밀번호): "
        read -s DB_PASSWORD
        echo ""
        
        # Cloud SQL 인스턴스 설정
        echo ""
        log_warning "Cloud SQL 인스턴스가 필요합니다."
        echo "형식: PROJECT_ID:REGION:INSTANCE_NAME"
        echo -n "Cloud SQL 인스턴스 연결 문자열을 입력하세요: "
        read CLOUD_SQL_INSTANCE
        
        # 시크릿 저장
        create_secret "SECRET_KEY" "$SECRET_KEY"
        create_secret "JWT_SECRET_KEY" "$JWT_SECRET_KEY"
        create_secret "OPENAI_API_KEY" "$OPENAI_API_KEY"
        
        # DATABASE_URL 생성 및 저장
        DB_USER="vcbl_user"
        DB_NAME="vcbl_chatbot"
        DATABASE_URL="postgresql+psycopg://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?host=/cloudsql/${CLOUD_SQL_INSTANCE}"
        create_secret "DATABASE_URL" "$DATABASE_URL"
        
        log_success "시크릿 저장 완료"
    }
    
    # Cloud Build 트리거 설정 함수
    setup_trigger() {
        log_info "Cloud Build 트리거 설정..."
        
        # GitHub 저장소 정보 입력
        echo -n "GitHub 저장소 소유자 (예: username): "
        read GITHUB_OWNER
        
        echo -n "GitHub 저장소 이름: "
        read GITHUB_REPO
        
        # 트리거 생성 시도
        log_info "Cloud Build 트리거 생성 중..."
        
        if gcloud builds triggers create github \
            --name="vcbl-chatbot-trigger" \
            --repo-name=$GITHUB_REPO \
            --repo-owner=$GITHUB_OWNER \
            --branch-pattern='^main$' \
            --build-config=cloudbuild.yaml \
            --project=$PROJECT_ID \
            --substitutions=_REGION=$REGION,_MEMORY=1Gi,_CPU=1,_MIN_INSTANCES=0,_MAX_INSTANCES=10,_CLOUD_SQL_INSTANCE=$CLOUD_SQL_INSTANCE 2>/dev/null; then
            log_success "Cloud Build 트리거 생성 완료"
        else
            log_warning "Cloud Build 트리거 생성에 실패했습니다."
            echo ""
            echo "GitHub 저장소가 Cloud Build와 연결되지 않았을 수 있습니다."
            echo "다음 방법 중 하나를 선택하세요:"
            echo ""
            echo "1) Google Cloud Console에서 수동으로 GitHub 연결:"
            echo "   https://console.cloud.google.com/cloud-build/triggers?project=$PROJECT_ID"
            echo ""
            echo "2) GitHub 저장소 설정에서 Cloud Build 앱 설치:"
            echo "   https://github.com/$GITHUB_OWNER/$GITHUB_REPO/settings/installations"
            echo ""
            echo "3) 트리거 생성을 건너뛰고 로컬 배포만 진행"
            echo ""
            echo -n "트리거 생성을 건너뛰시겠습니까? (y/n): "
            read skip_trigger
            if [ "$skip_trigger" = "y" ]; then
                log_warning "Cloud Build 트리거 생성을 건너뜁니다."
                log_info "나중에 Google Cloud Console에서 수동으로 설정하세요."
            else
                log_error "트리거 생성이 필요합니다. 수동으로 설정 후 다시 시도하세요."
                exit 1
            fi
        fi
    }
    
    # 로컬 빌드 및 배포 함수
    deploy_local() {
        log_info "로컬 빌드 및 배포..."
        
        # Cloud SQL 인스턴스 정보 입력
        if [ -z "$CLOUD_SQL_INSTANCE" ]; then
            echo ""
            echo "Cloud SQL 인스턴스 연결 문자열을 입력하세요"
            echo "(형식: PROJECT_ID:REGION:INSTANCE_NAME)"
            read -p "Cloud SQL Instance: " CLOUD_SQL_INSTANCE
        fi
        
        # Docker 이미지 태그
        IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"
        
        # Docker 이미지 빌드
        log_info "Docker 이미지 빌드 중..."
        docker build -t "$IMAGE_TAG" .
        log_success "Docker 이미지 빌드 완료"
        
        # GCR에 푸시
        log_info "Google Container Registry에 푸시 중..."
        docker push "$IMAGE_TAG"
        log_success "이미지 푸시 완료"
        
        # Cloud Run에 배포
        log_info "Cloud Run에 배포 중..."
        gcloud run deploy "$SERVICE_NAME" \
            --image="$IMAGE_TAG" \
            --region="$REGION" \
            --platform=managed \
            --allow-unauthenticated \
            --memory=1Gi \
            --cpu=1 \
            --min-instances=0 \
            --max-instances=10 \
            --set-env-vars="FLASK_ENV=production,PORT=8080INIT_ADMIN_ON_START=true,ADMIN_STUDENT_ID=9999000001,ADMIN_NAME=Super Administrator,ADMIN_PASSWORD:ADMIN_PASSWORD:latest" \
            --add-cloudsql-instances="$CLOUD_SQL_INSTANCE" \
            --set-secrets="SECRET_KEY=SECRET_KEY:latest,JWT_SECRET_KEY=JWT_SECRET_KEY:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,DATABASE_URL=DATABASE_URL:latest" \
            --project="$PROJECT_ID"
        
        log_success "Cloud Run 배포 완료"
    }
    
    case $INTERACTIVE_CHOICE in
        1)
            enable_apis
            ;;
        2)
            setup_secrets
            ;;
        3)
            setup_trigger
            ;;
        4)
            deploy_local
            ;;
        5)
            # 모든 작업 실행
            enable_apis
            setup_secrets
            setup_trigger
            deploy_local
            ;;
    esac
fi

# ============================================
# 8. 배포 상태 확인
# ============================================

echo ""
log_info "배포 상태 확인..."

# 서비스 URL 가져오기
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --format="value(status.url)" 2>/dev/null || echo "")

if [ -n "$SERVICE_URL" ]; then
    log_success "배포 성공!"
    echo ""
    echo "============================================"
    echo "🎉 배포 완료!"
    echo "============================================"
    echo ""
    echo "서비스 URL: $SERVICE_URL"
    echo ""
    echo "다음 명령어로 로그 확인:"
    echo "gcloud run services logs read $SERVICE_NAME --region=$REGION --project=$PROJECT_ID"
    echo ""
    echo "다음 명령어로 서비스 상태 확인:"
    echo "gcloud run services describe $SERVICE_NAME --region=$REGION --project=$PROJECT_ID"
else
    log_warning "서비스 URL을 가져올 수 없습니다. 수동으로 확인하세요."
fi

# ============================================
# 9. 추가 설정 안내
# ============================================

echo ""
log_info "추가 설정 안내"
echo "============================================"
echo ""
echo "✅ 완료된 작업:"
if [ "$DEPLOY_MODE" = "full" ] || [ "$INTERACTIVE_CHOICE" = "5" ]; then
    echo "   - Google Cloud API 활성화"
    echo "   - Secret Manager에 시크릿 저장"
    echo "   - Cloud Build 트리거 생성"
fi
echo "   - Cloud Run 서비스 배포"
echo ""
echo "📋 추가로 확인해야 할 사항:"
echo "   1. Cloud SQL 인스턴스가 실행 중인지 확인"
echo "   2. 데이터베이스 마이그레이션 실행 (필요시)"
echo "   3. 도메인 설정 (필요시)"
echo "   4. SSL 인증서 설정 (HTTPS 사용시)"
echo "   5. 모니터링 및 알림 설정"
echo ""
echo "🔧 유용한 명령어들:"
echo "   - 서비스 로그: gcloud run services logs read $SERVICE_NAME --region=$REGION"
echo "   - 서비스 상태: gcloud run services describe $SERVICE_NAME --region=$REGION"
echo "   - 트리거 목록: gcloud builds triggers list"
echo "   - 빌드 히스토리: gcloud builds list"
echo ""

log_success "배포 스크립트 실행 완료!"
