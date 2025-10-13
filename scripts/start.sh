#!/bin/bash
set -e

echo "Starting VCBL Chatbot Application..."

# Nginx 설정
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

# 데이터베이스 마이그레이션 (프로덕션 환경에서만)
if [ "$FLASK_ENV" = "production" ] && [ -n "$CLOUD_SQL_INSTANCE" ]; then
    echo "Running database migrations..."
    cd /app/backend
    export FLASK_APP=run.py
    flask db upgrade || echo "Migration failed or no migrations to apply"
fi

# Gunicorn으로 Flask 애플리케이션 시작
echo "Starting Gunicorn..."
cd /app/backend

# 워커 수 계산 (CPU 코어 수 * 2 + 1)
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

