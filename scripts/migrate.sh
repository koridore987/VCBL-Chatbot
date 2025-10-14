#!/bin/bash

# 로컬 마이그레이션 도구
# 개발 환경에서 데이터베이스 마이그레이션을 관리합니다

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

# 도움말 함수
show_help() {
    echo "VCBL Chatbot 마이그레이션 도구"
    echo ""
    echo "사용법:"
    echo "  $0 [명령어]"
    echo ""
    echo "명령어:"
    echo "  init        - 마이그레이션 초기화"
    echo "  create      - 새 마이그레이션 생성"
    echo "  upgrade     - 마이그레이션 실행"
    echo "  downgrade   - 마이그레이션 되돌리기"
    echo "  status      - 마이그레이션 상태 확인"
    echo "  history     - 마이그레이션 히스토리 보기"
    echo "  reset       - 데이터베이스 리셋 (주의!)"
    echo "  help        - 이 도움말 표시"
    echo ""
    echo "예시:"
    echo "  $0 create \"사용자 테이블 추가\""
    echo "  $0 upgrade"
    echo "  $0 status"
}

# 환경 확인
check_environment() {
    if [ ! -f "backend/requirements.txt" ]; then
        print_error "backend/requirements.txt 파일을 찾을 수 없습니다."
        print_info "프로젝트 루트 디렉토리에서 실행하세요."
        exit 1
    fi

    if [ ! -d "backend/migrations" ]; then
        print_error "마이그레이션 디렉토리를 찾을 수 없습니다."
        print_info "먼저 '$0 init' 명령어를 실행하세요."
        exit 1
    fi
}

# 마이그레이션 초기화
init_migration() {
    print_info "마이그레이션을 초기화합니다..."
    
    cd backend
    flask db init
    print_success "마이그레이션이 초기화되었습니다."
    cd ..
}

# 새 마이그레이션 생성
create_migration() {
    local message="$1"
    
    if [ -z "$message" ]; then
        print_error "마이그레이션 메시지를 입력하세요."
        print_info "사용법: $0 create \"메시지\""
        exit 1
    fi
    
    print_info "새 마이그레이션을 생성합니다: $message"
    
    cd backend
    flask db revision --message "$message"
    print_success "마이그레이션이 생성되었습니다."
    cd ..
}

# 마이그레이션 실행
upgrade_migration() {
    print_info "마이그레이션을 실행합니다..."
    
    cd backend
    flask db upgrade
    print_success "마이그레이션이 완료되었습니다."
    cd ..
}

# 마이그레이션 되돌리기
downgrade_migration() {
    print_warning "마이그레이션을 되돌립니다..."
    
    cd backend
    flask db downgrade
    print_success "마이그레이션이 되돌려졌습니다."
    cd ..
}

# 마이그레이션 상태 확인
show_status() {
    print_info "마이그레이션 상태를 확인합니다..."
    
    cd backend
    flask db current
    cd ..
}

# 마이그레이션 히스토리 보기
show_history() {
    print_info "마이그레이션 히스토리를 확인합니다..."
    
    cd backend
    flask db history
    cd ..
}

# 데이터베이스 리셋
reset_database() {
    print_warning "데이터베이스를 리셋합니다. 모든 데이터가 삭제됩니다!"
    
    if [ "$1" != "--force" ]; then
        read -p "정말로 계속하시겠습니까? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            print_info "취소되었습니다."
            exit 0
        fi
    fi
    
    print_info "데이터베이스를 리셋합니다..."
    
    cd backend
    flask db stamp base
    flask db upgrade
    print_success "데이터베이스가 리셋되었습니다."
    cd ..
}

# 메인 로직
case "${1:-help}" in
    "init")
        init_migration
        ;;
    "create")
        check_environment
        create_migration "$2"
        ;;
    "upgrade")
        check_environment
        upgrade_migration
        ;;
    "downgrade")
        check_environment
        downgrade_migration
        ;;
    "status")
        check_environment
        show_status
        ;;
    "history")
        check_environment
        show_history
        ;;
    "reset")
        check_environment
        reset_database "$2"
        ;;
    "help"|*)
        show_help
        ;;
esac
