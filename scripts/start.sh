#!/bin/bash
set -e

echo "Starting VCBL Chatbot Application..."

# Cloud Run 환경 감지
if [ -n "$K_SERVICE" ]; then
    echo "🚀 Running on Google Cloud Run"
    export CLOUD_RUN=true
else
    echo "🏠 Running locally"
    export CLOUD_RUN=false
fi

# Nginx 설정 (Cloud Run에서는 필요 없음)
if [ "$CLOUD_RUN" = "false" ]; then
    echo "Configuring Nginx..."
    # PORT 환경 변수가 없으면 기본값 8080 사용
    export PORT=${PORT:-8080}

    # Nginx 설정 파일에서 포트 치환
    if [ -f /etc/nginx/sites-available/default ]; then
        sed -i "s/listen 8080/listen $PORT/g" /etc/nginx/sites-available/default
    fi

    # Nginx 시작
    echo "Starting Nginx..."
    nginx
fi

# 데이터베이스 연결 확인
echo "Checking database connection..."
cd /app/backend
export FLASK_APP=run.py

# 데이터베이스 연결 테스트
if ! python << 'PYTHON_SCRIPT'
from app import create_app, db
from sqlalchemy import text
import sys

app = create_app()

with app.app_context():
    try:
        # 간단한 쿼리로 연결 테스트
        db.session.execute(text('SELECT 1'))
        print("✓ 데이터베이스 연결: 성공")
    except Exception as e:
        print(f"✗ 데이터베이스 연결 실패: {e}", file=sys.stderr)
        sys.exit(1)
PYTHON_SCRIPT
then
    echo "ERROR: Database connection failed!" >&2
    exit 1
fi

# 데이터베이스 마이그레이션 상태 확인 (실행하지 않음)
echo "Checking database migration status..."
if flask db current > /dev/null 2>&1; then
    echo "✓ Database schema is ready."
else
    echo "⚠️  Warning: Database migrations may not be applied."
    echo "⚠️  Please run migrations using Cloud Run Job or manually."
    echo "⚠️  Command: gcloud run jobs execute vcbl-migrate --region=your-region --wait"
fi

# Super 관리자 존재 확인 (생성하지 않음)
echo "Checking for super admin account..."
python << 'PYTHON_SCRIPT'
from app import create_app
from app.models.user import User

app = create_app()

with app.app_context():
    try:
        existing_super = User.query.filter_by(role='super').first()
        
        if existing_super:
            print(f"✓ Super 관리자가 존재합니다: {existing_super.student_id} ({existing_super.name})")
        else:
            print("⚠️  Warning: No super admin account found.")
            print("⚠️  Please create one using Cloud Run Job or manually.")
            print("⚠️  Command: gcloud run jobs execute vcbl-init-admin --region=your-region --wait")
            print("⚠️  Or use CLI: flask init-admin")
    except Exception as e:
        print(f"⚠️  Warning: Could not check super admin account: {e}")
        print("⚠️  This might be due to missing database tables.")
        print("⚠️  Please run database migrations first.")
PYTHON_SCRIPT

echo ""
echo "=" * 50
echo "✅ Application startup checks completed."
echo "=" * 50
echo ""

# Gunicorn으로 Flask 애플리케이션 시작
echo "Starting Gunicorn..."

# Cloud Run 환경에 따른 설정
if [ "$CLOUD_RUN" = "true" ]; then
    # Cloud Run: 단일 워커, 높은 동시성
    echo "🚀 Cloud Run configuration: Single worker with high concurrency"
    exec gunicorn \
        --bind 0.0.0.0:8080 \
        --workers 1 \
        --threads 8 \
        --worker-class gthread \
        --worker-tmp-dir /dev/shm \
        --timeout 300 \
        --keep-alive 5 \
        --log-level info \
        --access-logfile - \
        --error-logfile - \
        run:app
else
    # 로컬 환경: 다중 워커
    echo "🏠 Local configuration: Multiple workers"
    WORKERS=${WORKERS:-$(( $(nproc) * 2 + 1 ))}
    echo "Starting with $WORKERS workers"
    
    exec gunicorn \
        --bind 0.0.0.0:5000 \
        --workers $WORKERS \
        --threads 4 \
        --worker-class gthread \
        --worker-tmp-dir /dev/shm \
        --timeout 300 \
        --keep-alive 5 \
        --log-level info \
        --access-logfile - \
        --error-logfile - \
        run:app
fi
