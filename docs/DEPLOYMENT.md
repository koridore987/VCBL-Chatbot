# Cloud Run 배포 가이드

## 사전 준비

### 1. GCP 프로젝트 설정

```bash
# GCP 프로젝트 ID 설정
export PROJECT_ID="your-project-id"

# 프로젝트 설정
gcloud config set project $PROJECT_ID

# 필요한 API 활성화
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable sqladmin.googleapis.com
```

### 2. Cloud SQL (PostgreSQL) 설정

```bash
# Cloud SQL 인스턴스 생성
gcloud sql instances create vcbl-chatbot-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=asia-northeast3

# 데이터베이스 생성
gcloud sql databases create vcbl_chatbot \
  --instance=vcbl-chatbot-db

# 사용자 생성
gcloud sql users create vcbl \
  --instance=vcbl-chatbot-db \
  --password=your-secure-password
```

### 3. Service Account 생성

```bash
# Service Account 생성
gcloud iam service-accounts create vcbl-chatbot-sa \
  --display-name="VCBL Chatbot Service Account"

# 권한 부여
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:vcbl-chatbot-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"

# 키 생성 (GitHub Actions용)
gcloud iam service-accounts keys create key.json \
  --iam-account=vcbl-chatbot-sa@$PROJECT_ID.iam.gserviceaccount.com
```

## GitHub Secrets 설정

Repository > Settings > Secrets and variables > Actions에서 다음 secrets 추가:

```bash
GCP_PROJECT_ID=your-project-id
GCP_SA_KEY=<key.json 파일 내용 전체>
CLOUD_RUN_REGION=asia-northeast3
DATABASE_URL=postgresql://vcbl:password@/vcbl_chatbot?host=/cloudsql/PROJECT_ID:REGION:vcbl-chatbot-db
SECRET_KEY=<강력한 랜덤 문자열>
OPENAI_API_KEY=<OpenAI API 키>
```

## 수동 배포

### 1. Docker 이미지 빌드 및 푸시

```bash
# 이미지 빌드
docker build -t gcr.io/$PROJECT_ID/vcbl-chatbot:latest .

# GCR 인증
gcloud auth configure-docker

# 이미지 푸시
docker push gcr.io/$PROJECT_ID/vcbl-chatbot:latest
```

### 2. Cloud Run 배포

```bash
gcloud run deploy vcbl-chatbot \
  --image gcr.io/$PROJECT_ID/vcbl-chatbot:latest \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated \
  --add-cloudsql-instances $PROJECT_ID:asia-northeast3:vcbl-chatbot-db \
  --set-env-vars "DATABASE_URL=postgresql://vcbl:password@/vcbl_chatbot?host=/cloudsql/$PROJECT_ID:asia-northeast3:vcbl-chatbot-db" \
  --set-env-vars "SECRET_KEY=your-secret-key" \
  --set-env-vars "OPENAI_API_KEY=your-openai-key" \
  --set-env-vars "MODEL_NAME=gpt-4o-mini" \
  --set-env-vars "SUMMARY_TRIGGER_TOKENS=3500" \
  --set-env-vars "MAX_TOKENS_PER_REQUEST=4000" \
  --set-env-vars "MAX_TOKENS_OUTPUT=1000" \
  --set-env-vars "DAILY_TOKEN_LIMIT=50000" \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 1
```

### 3. 데이터베이스 초기화

```bash
# Cloud Run 인스턴스에 접속
gcloud run services proxy vcbl-chatbot --region=asia-northeast3

# 다른 터미널에서
curl http://localhost:8080/api/admin/init-db

# 또는 Cloud Console에서 직접 실행
```

## 자동 배포 (GitHub Actions)

### main 브랜치 푸시 시 자동 배포

```bash
git add .
git commit -m "Deploy to production"
git push origin main
```

GitHub Actions가 자동으로:
1. Docker 이미지 빌드
2. GCR에 푸시
3. Cloud Run에 배포
4. 서비스 URL 출력

## 모니터링

### Cloud Run 로그 확인

```bash
gcloud run services logs read vcbl-chatbot \
  --region=asia-northeast3 \
  --limit=50
```

### 메트릭 확인

```bash
# Cloud Console에서 확인
https://console.cloud.google.com/run/detail/asia-northeast3/vcbl-chatbot/metrics
```

## 비용 최적화

### 1. Cloud Run 설정

```bash
# 최소 인스턴스를 0으로 설정 (트래픽 없을 때 요금 없음)
gcloud run services update vcbl-chatbot \
  --min-instances=0 \
  --region=asia-northeast3
```

### 2. Cloud SQL 설정

```bash
# 자동 백업 설정
gcloud sql instances patch vcbl-chatbot-db \
  --backup-start-time=03:00
```

## 문제 해결

### 배포 실패 시

```bash
# Cloud Build 로그 확인
gcloud builds list --limit=5

# 특정 빌드 로그 확인
gcloud builds log <BUILD_ID>
```

### 데이터베이스 연결 실패

```bash
# Cloud SQL Proxy로 로컬에서 테스트
cloud_sql_proxy -instances=$PROJECT_ID:asia-northeast3:vcbl-chatbot-db=tcp:5432

# 다른 터미널에서
psql -h localhost -U vcbl -d vcbl_chatbot
```

## 보안 강화

### 1. VPC Connector 설정 (선택사항)

```bash
gcloud compute networks vpc-access connectors create vcbl-connector \
  --region=asia-northeast3 \
  --range=10.8.0.0/28

gcloud run services update vcbl-chatbot \
  --vpc-connector=vcbl-connector \
  --region=asia-northeast3
```

### 2. Secret Manager 사용

```bash
# Secret 생성
echo -n "your-secret-key" | gcloud secrets create secret-key --data-file=-

# Cloud Run에서 사용
gcloud run services update vcbl-chatbot \
  --update-secrets=SECRET_KEY=secret-key:latest \
  --region=asia-northeast3
```

## 스케일링 설정

```bash
# 동시성 설정
gcloud run services update vcbl-chatbot \
  --concurrency=80 \
  --region=asia-northeast3

# CPU 할당 설정
gcloud run services update vcbl-chatbot \
  --cpu-throttling \
  --region=asia-northeast3
```

