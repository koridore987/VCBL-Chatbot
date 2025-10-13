#!/bin/bash

# Google Cloud Run 배포 스크립트

# 환경 변수 설정
PROJECT_ID="your-project-id"  # 실제 프로젝트 ID로 변경
SERVICE_NAME="vcbl-chatbot"
REGION="asia-northeast3"  # 서울 리전

echo "🚀 VCBL Chatbot을 Google Cloud Run에 배포합니다..."

# 1. Docker 이미지 빌드
echo "📦 Docker 이미지를 빌드합니다..."
docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME:latest .

# 2. Container Registry에 푸시
echo "📤 이미지를 Container Registry에 푸시합니다..."
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:latest

# 3. Cloud Run에 배포
echo "🚀 Cloud Run에 배포합니다..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --set-env-vars "DATABASE_URL=sqlite:///app/data/vcbl_chatbot.db" \
  --set-env-vars "SECRET_KEY=your-secret-key-here" \
  --set-env-vars "OPENAI_API_KEY=your-openai-api-key-here"

echo "✅ 배포가 완료되었습니다!"
echo "🌐 서비스 URL: https://$SERVICE_NAME-$REGION.a.run.app"
