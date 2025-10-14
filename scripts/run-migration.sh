#!/bin/bash

# 데이터베이스 마이그레이션 실행 스크립트
# Cloud Run에서 실행되는 마이그레이션 작업

set -e

echo "🔄 데이터베이스 마이그레이션을 시작합니다..."

# 환경 변수 확인
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL 환경 변수가 설정되지 않았습니다."
    exit 1
fi

# Flask 애플리케이션 컨텍스트에서 마이그레이션 실행
cd /app/backend

# 마이그레이션 실행
python -c "
import os
import sys
sys.path.append('/app/backend')

from app import create_app
from flask_migrate import upgrade

app = create_app()
with app.app_context():
    print('마이그레이션을 실행합니다...')
    upgrade()
    print('✅ 마이그레이션이 완료되었습니다.')
"

echo "🎉 마이그레이션이 성공적으로 완료되었습니다!"
