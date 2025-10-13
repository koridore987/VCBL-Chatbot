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

# 데이터베이스 마이그레이션 실행
echo "Running database migrations..."
cd /app/backend
export FLASK_APP=run.py

if ! flask db upgrade; then
    echo "ERROR: Database migration failed!" >&2
    exit 1
fi
echo "✓ Database migrations completed."

# 초기 관리자 계정 생성 (존재하지 않을 경우에만)
echo "Checking for initial admin account..."
python << 'PYTHON_SCRIPT'
from app import create_app, db, bcrypt
from app.models.user import User
import sys

app = create_app()

with app.app_context():
    # Super 관리자가 이미 존재하는지 확인
    existing_super = User.query.filter_by(role='super').first()
    
    if existing_super:
        print(f"✓ Super 관리자가 이미 존재합니다: {existing_super.student_id} ({existing_super.name})")
    else:
        # 환경 변수에서 관리자 정보 가져오기 (없으면 기본값 사용)
        import os
        admin_student_id = os.getenv('ADMIN_STUDENT_ID', '9999000001')
        admin_name = os.getenv('ADMIN_NAME', 'Super Administrator')
        admin_password = os.getenv('ADMIN_PASSWORD', 'super1234')
        
        print(f"Creating initial super admin account: {admin_student_id}")
        
        # 비밀번호 해시 생성
        password_hash = bcrypt.generate_password_hash(admin_password).decode('utf-8')
        
        # Super 관리자 생성
        admin = User(
            student_id=admin_student_id,
            password_hash=password_hash,
            name=admin_name,
            role='super',
            is_active=True
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print("=" * 50)
        print("✅ Super 관리자가 생성되었습니다!")
        print("=" * 50)
        print(f"학번: {admin.student_id}")
        print(f"이름: {admin.name}")
        print(f"비밀번호: {admin_password}")
        print("=" * 50)
        print("⚠️  보안 경고: 프로덕션 환경에서는 반드시 비밀번호를 변경하세요!")
        print("=" * 50)

PYTHON_SCRIPT

# Gunicorn으로 Flask 애플리케이션 시작
echo "Starting Gunicorn..."
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
