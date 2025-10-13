#!/bin/bash

# Create super admin account
# 경고: Super 관리자 계정은 시스템에 단 하나만 존재해야 합니다.
# 기본 계정: super / super1234
# 
# 사용법: ./create-admin.sh
# 또는: ./create-admin.sh <student_id> <name> <password>

# 기본값 설정
DEFAULT_STUDENT_ID="super"
DEFAULT_NAME="Super Administrator"
DEFAULT_PASSWORD="super1234"

# 인자가 제공되면 사용, 아니면 기본값 사용
STUDENT_ID=${1:-$DEFAULT_STUDENT_ID}
NAME=${2:-$DEFAULT_NAME}
PASSWORD=${3:-$DEFAULT_PASSWORD}

echo "=========================================="
echo "Super 관리자 계정 생성"
echo "=========================================="
echo "학번: $STUDENT_ID"
echo "이름: $NAME"
echo "=========================================="
echo ""
echo "⚠️  중요: Super 관리자는 시스템에 단 하나만 존재해야 합니다."
echo "⚠️  이 계정의 권한은 절대 변경할 수 없습니다."
echo ""

read -p "계속하시겠습니까? (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "취소되었습니다."
    exit 0
fi

# Use Flask shell to create admin
cd backend

python << END
import sys
from app import create_app, db, bcrypt
from app.models.user import User

app = create_app()

with app.app_context():
    # Check if super admin already exists
    existing_super = User.query.filter_by(role='super').first()
    
    if existing_super:
        print("❌ 오류: Super 관리자 계정이 이미 존재합니다.")
        print(f"   기존 계정: {existing_super.student_id} ({existing_super.name})")
        print("   Super 관리자는 시스템에 하나만 존재할 수 있습니다.")
        sys.exit(1)
    
    # Check if user with same student_id exists
    existing_user = User.query.filter_by(student_id='$STUDENT_ID').first()
    
    if existing_user:
        print(f"❌ 오류: 학번 '$STUDENT_ID'을(를) 가진 사용자가 이미 존재합니다.")
        sys.exit(1)
    
    # Create super admin
    password_hash = bcrypt.generate_password_hash('$PASSWORD').decode('utf-8')
    
    admin = User(
        student_id='$STUDENT_ID',
        password_hash=password_hash,
        name='$NAME',
        role='super',
        is_active=True
    )
    
    db.session.add(admin)
    db.session.commit()
    
    print("")
    print("========================================")
    print("✅ Super 관리자가 생성되었습니다!")
    print("========================================")
    print(f"학번: {admin.student_id}")
    print(f"이름: {admin.name}")
    print("권한: Super Administrator")
    print("========================================")
    print("")
    print("📝 주의사항:")
    print("  • 이 계정의 권한은 절대 변경할 수 없습니다.")
    print("  • 이 계정은 비활성화할 수 없습니다.")
    print("  • 비밀번호는 본인만 변경 가능합니다.")
    print("")
    sys.exit(0)
END

exit_code=$?
cd ..

if [ $exit_code -eq 0 ]; then
    echo "✨ 설정이 완료되었습니다. 로그인하여 사용하세요."
fi

exit $exit_code

