#!/bin/bash

# Cloud Run Job을 사용한 마이그레이션 실행 스크립트
# Google Cloud에서 데이터베이스 마이그레이션을 안전하게 실행합니다

set -e

# 프로젝트 설정
PROJECT_ID=$(gcloud config get-value project)
REGION="asia-northeast3"
JOB_NAME="vcbl-migration-job"
SERVICE_NAME="vcbl-chatbot"

echo "🔄 Cloud Run Job을 사용한 마이그레이션을 설정합니다..."
echo "📋 프로젝트: $PROJECT_ID"
echo "🌏 리전: $REGION"

# Cloud Run Job 생성
echo "🔨 Cloud Run Job을 생성합니다..."
gcloud run jobs create $JOB_NAME \
    --image=gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --region=$REGION \
    --memory=2Gi \
    --cpu=2 \
    --timeout=1800 \
    --max-retries=3 \
    --parallelism=1 \
    --task-count=1 \
    --add-cloudsql-instances=$PROJECT_ID:$REGION:vcbl-chatbot-db \
    --set-secrets=DATABASE_URL=vcbl-database-url:latest,OPENAI_API_KEY=vcbl-openai-key:latest,SECRET_KEY=vcbl-secret-key:latest,JWT_SECRET_KEY=vcbl-jwt-secret:latest \
    --set-env-vars=FLASK_ENV=production \
    --command="/app/scripts/run-migration.sh" \
    --args=""

echo "✅ Cloud Run Job이 생성되었습니다."

# Job 실행
echo "🚀 마이그레이션 Job을 실행합니다..."
gcloud run jobs execute $JOB_NAME --region=$REGION --wait

echo "🎉 마이그레이션이 완료되었습니다!"

# Job 상태 확인
echo "📊 Job 상태를 확인합니다..."
gcloud run jobs describe $JOB_NAME --region=$REGION --format="value(status.conditions[0].type,status.conditions[0].status)"

echo ""
echo "💡 추가 명령어:"
echo "  - Job 삭제: gcloud run jobs delete $JOB_NAME --region=$REGION"
echo "  - Job 로그: gcloud logging read 'resource.type=\"cloud_run_job\" AND resource.labels.job_name=\"$JOB_NAME\"' --limit=50"
