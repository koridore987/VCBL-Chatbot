# VCBL Chatbot 배포 가이드

Google Cloud Run에 VCBL Chatbot을 배포하는 완전한 가이드입니다.

## 📋 사전 준비사항

### 1. Google Cloud 계정 및 프로젝트
- [Google Cloud Console](https://console.cloud.google.com/) 계정
- 결제 정보 등록 (무료 크레딧 사용 가능)
- 새 프로젝트 생성 또는 기존 프로젝트 선택

### 2. 필수 도구 설치
```bash
# Google Cloud CLI 설치
# Windows: https://cloud.google.com/sdk/docs/install-sdk
# macOS: brew install google-cloud-sdk
# Linux: curl https://sdk.cloud.google.com | bash

# 설치 확인
gcloud version

# 로그인
gcloud auth login
```

### 3. 프로젝트 설정
```bash
# 프로젝트 ID 설정 (YOUR_PROJECT_ID를 실제 프로젝트 ID로 변경)
gcloud config set project YOUR_PROJECT_ID

# 기본 리전 설정
gcloud config set run/region asia-northeast3
```

## 🚀 단계별 배포 가이드

### 1단계: 초기 설정

#### 1.1 프로젝트 설정 스크립트 실행
```bash
# 프로젝트 루트에서 실행
./scripts/deploy-setup.sh
```

이 스크립트는 다음 작업을 수행합니다:
- 필요한 API 활성화
- 서비스 계정 생성
- Cloud SQL 인스턴스 생성 (선택)
- Secret Manager 설정

#### 1.2 Secret Manager에 비밀 정보 저장
```bash
# SECRET_KEY (32자 이상)
echo -n "your-secret-key-here" | gcloud secrets create vcbl-secret-key --data-file=-

# JWT_SECRET_KEY (32자 이상)
echo -n "your-jwt-secret-key-here" | gcloud secrets create vcbl-jwt-secret-key --data-file=-

# 데이터베이스 비밀번호
echo -n "your-db-password" | gcloud secrets create vcbl-db-password --data-file=-

# OpenAI API 키
echo -n "sk-your-openai-api-key" | gcloud secrets create vcbl-openai-api-key --data-file=-

# Redis URL (선택)
echo -n "memory://" | gcloud secrets create vcbl-redis-url --data-file=-
```

### 2단계: 데이터베이스 설정

#### 2.1 Cloud SQL 인스턴스 생성 (아직 생성하지 않은 경우)
```bash
# Cloud SQL 인스턴스 생성
gcloud sql instances create vcbl-postgres \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=asia-northeast3 \
  --storage-type=SSD \
  --storage-size=10GB \
  --storage-auto-increase \
  --backup-start-time=03:00 \
  --availability-type=zonal
```

#### 2.2 데이터베이스 및 사용자 생성
```bash
# 데이터베이스 생성
gcloud sql databases create vcbl_chatbot --instance=vcbl-postgres

# 데이터베이스 사용자 생성
gcloud sql users create vcbl_user \
  --instance=vcbl-postgres \
  --password=your-db-password
```

### 3단계: 애플리케이션 배포

#### 3.1 첫 배포 실행
```bash
# Cloud Build를 통한 배포
gcloud builds submit --config cloudbuild.yaml
```

#### 3.2 배포 상태 확인
```bash
# 서비스 상태 확인
gcloud run services describe vcbl-chatbot --region=asia-northeast3

# 서비스 URL 확인
gcloud run services describe vcbl-chatbot --region=asia-northeast3 --format="value(status.url)"
```

### 4단계: 데이터베이스 마이그레이션

#### 4.1 마이그레이션 Job 생성
```bash
# 마이그레이션 Job 생성
./scripts/create-migration-job.sh
```

#### 4.2 마이그레이션 실행
```bash
# 마이그레이션 실행
gcloud run jobs execute vcbl-chatbot-migrate --region=asia-northeast3 --wait
```

### 5단계: 초기 관리자 계정 생성

#### 5.1 관리자 정보를 Secret Manager에 저장
```bash
# Super admin 학번
echo -n "2024000001" | gcloud secrets create vcbl-super-admin-id --data-file=-

# Super admin 이름
echo -n "관리자" | gcloud secrets create vcbl-super-admin-name --data-file=-

# Super admin 비밀번호
echo -n "SecurePass123!" | gcloud secrets create vcbl-super-admin-password --data-file=-
```

#### 5.2 관리자 계정 생성 Job 실행
```bash
# 관리자 생성 Job 생성 및 실행
gcloud run jobs create vcbl-init-admin \
  --image=gcr.io/YOUR_PROJECT_ID/vcbl-chatbot:latest \
  --set-cloudsql-instances=YOUR_PROJECT_ID:asia-northeast3:vcbl-postgres \
  --set-env-vars="CLOUD_SQL_INSTANCE=YOUR_PROJECT_ID:asia-northeast3:vcbl-postgres,DB_USER=vcbl_user,DB_NAME=vcbl_chatbot,FLASK_ENV=production" \
  --set-secrets="DB_PASSWORD=vcbl-db-password:latest,SECRET_KEY=vcbl-secret-key:latest,JWT_SECRET_KEY=vcbl-jwt-secret-key:latest,OPENAI_API_KEY=vcbl-openai-api-key:latest,VCBL_SUPER_ADMIN_ID=vcbl-super-admin-id:latest,VCBL_SUPER_ADMIN_NAME=vcbl-super-admin-name:latest,VCBL_SUPER_ADMIN_PASSWORD=vcbl-super-admin-password:latest" \
  --service-account="vcbl-chatbot-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --memory=1Gi \
  --cpu=1 \
  --max-retries=3 \
  --task-timeout=10m \
  --command="flask" \
  --args="init-superadmin" \
  --region=asia-northeast3

# Job 실행
gcloud run jobs execute vcbl-init-admin --region=asia-northeast3 --wait
```

### 6단계: 프론트엔드 환경 변수 설정

#### 6.1 프론트엔드 환경 변수 업데이트
```bash
# Cloud Run 서비스 URL 확인
SERVICE_URL=$(gcloud run services describe vcbl-chatbot --region=asia-northeast3 --format="value(status.url)")

# 프론트엔드 환경 변수 설정
echo "VITE_API_URL=${SERVICE_URL}/api" > frontend/.env.production
```

#### 6.2 프론트엔드 재배포
```bash
# 프론트엔드 포함 전체 재배포
gcloud builds submit --config cloudbuild.yaml
```

## ✅ 배포 확인

### 1. 서비스 상태 확인
```bash
# 서비스 URL 확인
gcloud run services describe vcbl-chatbot --region=asia-northeast3 --format="value(status.url)"

# 헬스 체크
curl https://YOUR_SERVICE_URL/health

# 준비 상태 체크
curl https://YOUR_SERVICE_URL/readiness
```

### 2. 로그 확인
```bash
# 최근 로그 확인
gcloud run services logs read vcbl-chatbot --region=asia-northeast3 --limit=50

# 실시간 로그 스트리밍
gcloud run services logs tail vcbl-chatbot --region=asia-northeast3
```

### 3. 데이터베이스 연결 확인
```bash
# 데이터베이스 상태 확인
gcloud run jobs create vcbl-check-db \
  --image=gcr.io/YOUR_PROJECT_ID/vcbl-chatbot:latest \
  --set-cloudsql-instances=YOUR_PROJECT_ID:asia-northeast3:vcbl-postgres \
  --set-env-vars="CLOUD_SQL_INSTANCE=YOUR_PROJECT_ID:asia-northeast3:vcbl-postgres,DB_USER=vcbl_user,DB_NAME=vcbl_chatbot,FLASK_ENV=production" \
  --set-secrets="DB_PASSWORD=vcbl-db-password:latest,SECRET_KEY=vcbl-secret-key:latest,JWT_SECRET_KEY=vcbl-jwt-secret-key:latest,OPENAI_API_KEY=vcbl-openai-api-key:latest" \
  --service-account="vcbl-chatbot-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --command="flask" \
  --args="check-db" \
  --region=asia-northeast3

gcloud run jobs execute vcbl-check-db --region=asia-northeast3 --wait
```

## 🔧 문제 해결

### 자주 발생하는 문제

#### 1. 배포 실패
```bash
# 빌드 로그 확인
gcloud builds log --stream

# 서비스 로그 확인
gcloud run services logs read vcbl-chatbot --region=asia-northeast3
```

#### 2. 데이터베이스 연결 실패
```bash
# Cloud SQL 인스턴스 상태 확인
gcloud sql instances describe vcbl-postgres

# 데이터베이스 연결 테스트
gcloud sql connect vcbl-postgres --user=vcbl_user --database=vcbl_chatbot
```

#### 3. Secret Manager 접근 실패
```bash
# 서비스 계정 권한 확인
gcloud projects get-iam-policy YOUR_PROJECT_ID

# Secret Manager 권한 부여
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:vcbl-chatbot-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## 📊 비용 최적화

### 1. Cloud Run 설정
- **최소 인스턴스**: 1개 (콜드 스타트 방지)
- **최대 인스턴스**: 10개 (비용 절약)
- **CPU**: 1 vCPU
- **메모리**: 2GB

### 2. Cloud SQL 설정
- **인스턴스 타입**: db-f1-micro (무료 티어)
- **스토리지**: 10GB (필요시 자동 증가)

### 3. 모니터링
```bash
# 비용 확인
gcloud billing budgets list

# 사용량 확인
gcloud logging read "resource.type=cloud_run_revision" --limit=10
```

## 🎯 다음 단계

배포가 완료되면 다음 작업을 수행하세요:

1. [유지관리 가이드](3_MAINTENANCE_GUIDE.md)를 확인하여 일상 관리 방법을 익히세요
2. [환경 변수 가이드](2_ENVIRONMENT_VARIABLES.md)를 참고하여 추가 설정을 조정하세요
3. [문제 해결 가이드](4_TROUBLESHOOTING.md)를 북마크하여 문제 발생 시 빠르게 해결하세요

## 📞 지원

문제가 발생하거나 질문이 있으시면:

1. [문제 해결 가이드](4_TROUBLESHOOTING.md)를 먼저 확인하세요
2. GitHub Issues에 문제를 등록하세요
3. 로그를 확인하여 구체적인 오류 메시지를 제공하세요
