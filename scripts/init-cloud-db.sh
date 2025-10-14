#!/bin/bash

# Cloud SQL 데이터베이스 초기화 스크립트
# PostgreSQL 데이터베이스를 설정하고 초기 데이터를 로드합니다

set -e

# 프로젝트 설정
PROJECT_ID=$(gcloud config get-value project)
REGION="asia-northeast3"
INSTANCE_NAME="vcbl-chatbot-db"
DATABASE_NAME="vcbl_chatbot"
USER_NAME="vcbl_user"

echo "🗄️ Cloud SQL 데이터베이스를 초기화합니다..."
echo "📋 프로젝트: $PROJECT_ID"
echo "🌏 리전: $REGION"
echo "🏷️ 인스턴스: $INSTANCE_NAME"

# Cloud SQL 인스턴스 상태 확인
echo "🔍 Cloud SQL 인스턴스 상태를 확인합니다..."
INSTANCE_STATUS=$(gcloud sql instances describe $INSTANCE_NAME --format="value(state)" 2>/dev/null || echo "NOT_FOUND")

if [ "$INSTANCE_STATUS" = "NOT_FOUND" ]; then
    echo "❌ Cloud SQL 인스턴스 '$INSTANCE_NAME'을 찾을 수 없습니다."
    echo "먼저 다음 명령어로 인스턴스를 생성하세요:"
    echo "gcloud sql instances create $INSTANCE_NAME --database-version=POSTGRES_15 --tier=db-f1-micro --region=$REGION"
    exit 1
fi

if [ "$INSTANCE_STATUS" != "RUNNABLE" ]; then
    echo "⏳ Cloud SQL 인스턴스가 시작 중입니다. 잠시 기다려주세요..."
    gcloud sql instances wait $INSTANCE_NAME --timeout=600
fi

# 데이터베이스 생성
echo "📊 데이터베이스를 생성합니다..."
gcloud sql databases create $DATABASE_NAME --instance=$INSTANCE_NAME 2>/dev/null || echo "데이터베이스가 이미 존재합니다."

# 사용자 생성 (비밀번호는 Secret Manager에서 가져옴)
echo "👤 데이터베이스 사용자를 생성합니다..."
DB_PASSWORD=$(gcloud secrets versions access latest --secret="vcbl-database-url" | grep -o '://[^:]*:\([^@]*\)' | cut -d: -f3 | cut -d@ -f1)

if [ -z "$DB_PASSWORD" ]; then
    echo "❌ 데이터베이스 비밀번호를 찾을 수 없습니다."
    echo "Secret Manager에서 vcbl-database-url 시크릿을 확인하세요."
    exit 1
fi

gcloud sql users create $USER_NAME --instance=$INSTANCE_NAME --password="$DB_PASSWORD" 2>/dev/null || echo "사용자가 이미 존재합니다."

# 연결 정보 출력
INSTANCE_CONNECTION_NAME="$PROJECT_ID:$REGION:$INSTANCE_NAME"
echo ""
echo "✅ 데이터베이스 초기화가 완료되었습니다!"
echo ""
echo "📝 연결 정보:"
echo "  - 인스턴스: $INSTANCE_NAME"
echo "  - 데이터베이스: $DATABASE_NAME"
echo "  - 사용자: $USER_NAME"
echo "  - 연결 이름: $INSTANCE_CONNECTION_NAME"
echo ""
echo "🔗 연결 문자열:"
echo "  postgresql+psycopg2://$USER_NAME:[PASSWORD]@/$DATABASE_NAME?host=/cloudsql/$INSTANCE_CONNECTION_NAME"
echo ""
echo "💡 다음 단계:"
echo "  1. 마이그레이션 실행: ./scripts/create-migration-job.sh"
echo "  2. 애플리케이션 배포: gcloud builds submit --config cloudbuild.yaml"
