#!/bin/bash
set -e

echo "Starting database migration..."

# 애플리케이션 디렉토리로 이동
cd /app/backend
export FLASK_APP=run.py

# 환경 변수 확인
echo "Environment variables:"
echo "FLASK_ENV: $FLASK_ENV"
echo "CLOUD_SQL_INSTANCE: $CLOUD_SQL_INSTANCE"
echo "DB_USER: $DB_USER"
echo "DB_NAME: $DB_NAME"

# 데이터베이스 마이그레이션 실행
echo "Running database migrations..."
flask db upgrade

echo "Database migration completed successfully!"
