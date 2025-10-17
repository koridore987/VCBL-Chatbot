#!/bin/bash

# ============================================
# VCBL Chatbot - 통합 개발 환경 시작
# ============================================
# 백엔드와 프론트엔드를 동시에 실행합니다.

echo "🚀 통합 개발 환경 시작 중..."

# 터미널을 여러 개로 분할하여 실행
echo "📋 실행 방법:"
echo "1. 터미널을 2개 열어주세요"
echo "2. 첫 번째 터미널에서: ./start-backend.sh"
echo "3. 두 번째 터미널에서: ./start-frontend.sh"
echo ""
echo "또는 tmux를 사용하여 자동으로 분할할 수 있습니다:"

# tmux가 설치되어 있는지 확인
if command -v tmux &> /dev/null; then
    echo "🔧 tmux를 사용하여 자동 분할 실행..."
    
    # tmux 세션 생성
    tmux new-session -d -s vcbl-dev
    
    # 백엔드 창 생성
    tmux new-window -t vcbl-dev -n backend
    tmux send-keys -t vcbl-dev:backend "./start-backend.sh" Enter
    
    # 프론트엔드 창 생성
    tmux new-window -t vcbl-dev -n frontend
    tmux send-keys -t vcbl-dev:frontend "./start-frontend.sh" Enter
    
    # 세션에 연결
    tmux attach-session -t vcbl-dev
else
    echo "❌ tmux가 설치되어 있지 않습니다."
    echo "   설치하려면: brew install tmux"
    echo ""
    echo "📋 수동 실행 방법:"
    echo "1. 터미널 1: ./start-backend.sh"
    echo "2. 터미널 2: ./start-frontend.sh"
fi
