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

# Gunicorn 바인딩 포트 설정 (Cloud Run은 $PORT 제공)
export PORT=${PORT:-8080}
echo "Gunicorn will bind to 0.0.0.0:${PORT}"

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
printf '%0.s=' {1..50}; echo
echo "✅ Application startup checks completed."
printf '%0.s=' {1..50}; echo
echo ""

# Gunicorn으로 Flask 애플리케이션 시작
echo "Starting Gunicorn..."

# Cloud Run은 단일 프로세스가 권장되므로 워커 수 최소화
if [ "$CLOUD_RUN" = "true" ]; then
    WORKERS=${WORKERS:-1}
    THREADS=${THREADS:-8}
else
    WORKERS=${WORKERS:-$(( $(nproc) * 2 + 1 ))}
    THREADS=${THREADS:-4}
fi

echo "Using $WORKERS workers and $THREADS threads"

exec gunicorn \
    --bind "0.0.0.0:${PORT}" \
    --workers "$WORKERS" \
    --threads "$THREADS" \
    --worker-class gthread \
    --worker-tmp-dir /dev/shm \
    --timeout 300 \
    --keep-alive 5 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    run:app
