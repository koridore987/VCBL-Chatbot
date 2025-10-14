# Google Cloud Run 배포 가이드 (간소화 버전)

이 가이드는 VCBL Chatbot을 Google Cloud Run에 배포하는 전체 과정을 설명합니다.

## 📋 주요 변경사항 (2024년 10월)

이 프로젝트는 Cloud Run 배포를 위해 다음과 같이 최적화되었습니다:

### ✅ 개선된 점
1. **데이터베이스 연결**: Unix Socket 방식으로 단순화 (추가 의존성 없음)
2. **PostgreSQL 드라이버**: `psycopg2-binary`만 사용 (경량화)
3. **초기화 분리**: 마이그레이션과 Admin 생성을 Cloud Run Job으로 분리
4. **프론트엔드**: 상대 경로 사용으로 단일 빌드 지원
5. **Rate Limiting**: Memory storage 사용 (추가 인프라 불필요)

### 🏗️ 아키텍처
```
Cloud Run Service (앱 실행)
  ↓
Cloud SQL (PostgreSQL) - Unix Socket 연결
  ↓  
Secret Manager (민감 정보 저장)
  ↓
Cloud Run Jobs (마이그레이션 & Admin 생성)
```

---

## 🚀 빠른 시작

### 사전 준비

1. **Google Cloud 계정** 및 프로젝트 생성
2. **gcloud CLI** 설치 및 로그인
3. **프로젝트 설정**:
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   gcloud config set run/region asia-northeast3
   ```

---

## 📝 단계별 배포

### 1단계: Secret Manager 설정

모든 민감한 정보를 Secret Manager에 저장합니다.

```bash
# 스크립트 실행 (대화형)
./scripts/setup-secrets.sh
```

또는 수동으로:

```bash
# 1. SECRET_KEY 생성
python -c "import secrets; print(secrets.token_hex(32))" | \
  gcloud secrets create vcbl-secret-key --data-file=-

# 2. JWT_SECRET_KEY 생성
python -c "import secrets; print(secrets.token_hex(32))" | \
  gcloud secrets create vcbl-jwt-secret-key --data-file=-

# 3. 데이터베이스 비밀번호
echo -n "YOUR_DB_PASSWORD" | \
  gcloud secrets create vcbl-db-password --data-file=-

# 4. OpenAI API 키
echo -n "sk-YOUR_OPENAI_KEY" | \
  gcloud secrets create vcbl-openai-key --data-file=-

# 5-7. Super Admin 정보
echo -n "super" | gcloud secrets create vcbl-admin-student-id --data-file=-
echo -n "Super Administrator" | gcloud secrets create vcbl-admin-name --data-file=-
echo -n "YourSecurePassword123!" | gcloud secrets create vcbl-admin-password --data-file=-
```

### 2단계: Cloud SQL 인스턴스 생성

```bash
# PostgreSQL 15 인스턴스 생성
gcloud sql instances create vcbl-chatbot-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=asia-northeast3 \
  --storage-type=SSD \
  --storage-size=10GB \
  --storage-auto-increase \
  --backup-start-time=03:00 \
  --availability-type=zonal

# 데이터베이스 생성
gcloud sql databases create vcbl_chatbot \
  --instance=vcbl-chatbot-db

# 사용자 생성
gcloud sql users create vcbl_user \
  --instance=vcbl-chatbot-db \
  --password=YOUR_DB_PASSWORD
```

**⚠️ 주의**: `YOUR_DB_PASSWORD`는 Secret Manager의 `vcbl-db-password`와 동일해야 합니다.

### 3단계: 애플리케이션 배포

```bash
# Cloud Build로 배포
gcloud builds submit --config cloudbuild.yaml
```

이 명령은 다음을 수행합니다:
- Docker 이미지 빌드 (백엔드 + 프론트엔드)
- Container Registry에 푸시
- Cloud Run 서비스 배포

### 4단계: Cloud Run Jobs 생성

```bash
# Jobs 생성 (마이그레이션 & Admin)
./scripts/create-cloud-run-jobs.sh
```

또는 수동으로:

```bash
PROJECT_ID=$(gcloud config get-value project)
REGION=asia-northeast3

# 마이그레이션 Job
gcloud run jobs create vcbl-migrate \
  --image=gcr.io/$PROJECT_ID/vcbl-chatbot-backend \
  --region=$REGION \
  --set-env-vars="FLASK_ENV=production,CLOUD_SQL_INSTANCE=$PROJECT_ID:$REGION:vcbl-chatbot-db,DB_USER=vcbl_user,DB_NAME=vcbl_chatbot" \
  --set-secrets="DB_PASSWORD=vcbl-db-password:latest,SECRET_KEY=vcbl-secret-key:latest,JWT_SECRET_KEY=vcbl-jwt-secret:latest,OPENAI_API_KEY=vcbl-openai-key:latest" \
  --add-cloudsql-instances="$PROJECT_ID:$REGION:vcbl-chatbot-db" \
  --memory=1Gi \
  --cpu=1 \
  --max-retries=3 \
  --task-timeout=10m \
  --command="flask" \
  --args="db,upgrade"

# Admin 생성 Job
gcloud run jobs create vcbl-init-admin \
  --image=gcr.io/$PROJECT_ID/vcbl-chatbot-backend \
  --region=$REGION \
  --set-env-vars="FLASK_ENV=production,CLOUD_SQL_INSTANCE=$PROJECT_ID:$REGION:vcbl-chatbot-db,DB_USER=vcbl_user,DB_NAME=vcbl_chatbot" \
  --set-secrets="DB_PASSWORD=vcbl-db-password:latest,SECRET_KEY=vcbl-secret-key:latest,JWT_SECRET_KEY=vcbl-jwt-secret:latest,OPENAI_API_KEY=vcbl-openai-key:latest,ADMIN_STUDENT_ID=vcbl-admin-student-id:latest,ADMIN_NAME=vcbl-admin-name:latest,ADMIN_PASSWORD=vcbl-admin-password:latest" \
  --add-cloudsql-instances="$PROJECT_ID:$REGION:vcbl-chatbot-db" \
  --memory=1Gi \
  --cpu=1 \
  --max-retries=3 \
  --task-timeout=10m \
  --command="flask" \
  --args="init-admin"
```

### 5단계: 초기화 실행

```bash
# 1. 마이그레이션 실행
gcloud run jobs execute vcbl-migrate \
  --region=asia-northeast3 \
  --wait

# 2. Super Admin 생성
gcloud run jobs execute vcbl-init-admin \
  --region=asia-northeast3 \
  --wait
```

### 6단계: 배포 확인

```bash
# 서비스 URL 확인
gcloud run services describe vcbl-chatbot \
  --region=asia-northeast3 \
  --format="value(status.url)"

# 헬스 체크
SERVICE_URL=$(gcloud run services describe vcbl-chatbot --region=asia-northeast3 --format="value(status.url)")
curl $SERVICE_URL/health

# 로그 확인
gcloud run services logs read vcbl-chatbot \
  --region=asia-northeast3 \
  --limit=50
```

---

## 🔄 업데이트 배포

코드 변경 후 재배포:

```bash
# 1. 애플리케이션 재배포
gcloud builds submit --config cloudbuild.yaml

# 2. 마이그레이션이 필요한 경우
gcloud run jobs execute vcbl-migrate --region=asia-northeast3 --wait
```

---

## 🛠️ 일반적인 작업

### 환경 변수 변경

```bash
# 환경 변수 업데이트
gcloud run services update vcbl-chatbot \
  --region=asia-northeast3 \
  --set-env-vars="NEW_VAR=value"

# Secret 업데이트
echo -n "new-value" | gcloud secrets versions add vcbl-secret-key --data-file=-
```

### 데이터베이스 직접 접속

```bash
gcloud sql connect vcbl-chatbot-db \
  --user=vcbl_user \
  --database=vcbl_chatbot
```

### 로그 실시간 모니터링

```bash
gcloud run services logs tail vcbl-chatbot \
  --region=asia-northeast3
```

---

## ❗ 문제 해결

### 앱이 시작되지 않는 경우

1. **로그 확인**:
   ```bash
   gcloud run services logs read vcbl-chatbot --region=asia-northeast3 --limit=100
   ```

2. **데이터베이스 연결 확인**:
   ```bash
   gcloud sql instances describe vcbl-chatbot-db
   ```

3. **Secret 확인**:
   ```bash
   gcloud secrets list --filter="name~vcbl-*"
   ```

### 마이그레이션 실패

```bash
# Job 실행 로그 확인
gcloud run jobs executions list \
  --region=asia-northeast3 \
  --job=vcbl-migrate

# 특정 실행 로그 보기
gcloud run jobs executions logs read EXECUTION_NAME \
  --region=asia-northeast3
```

### Admin이 생성되지 않음

```bash
# Admin Job 로그 확인
gcloud run jobs executions list \
  --region=asia-northeast3 \
  --job=vcbl-init-admin

# 재실행
gcloud run jobs execute vcbl-init-admin \
  --region=asia-northeast3 \
  --wait
```

---

## 💰 비용 최적화

### 현재 설정 (월 예상 비용)

- **Cloud Run**: ~$10-30 (최소 1 인스턴스)
- **Cloud SQL** (db-f1-micro): ~$7-15
- **Container Registry**: ~$1-5
- **Secret Manager**: ~$0.06 (7개 시크릿)
- **총계**: **~$18-50/월**

### 비용 절감 팁

1. **최소 인스턴스 0으로 설정** (콜드 스타트 허용):
   ```bash
   gcloud run services update vcbl-chatbot \
     --region=asia-northeast3 \
     --min-instances=0
   ```

2. **Cloud SQL 자동 정지** (개발/테스트용):
   ```bash
   gcloud sql instances patch vcbl-chatbot-db \
     --activation-policy=NEVER
   ```

3. **예산 알림 설정**:
   - Cloud Console → Billing → Budgets & alerts

---

## 🎯 프로덕션 체크리스트

배포 전 확인사항:

- [ ] Secret Manager의 모든 비밀번호가 강력한지 확인
- [ ] Cloud SQL 백업이 활성화되어 있는지 확인
- [ ] CORS_ORIGINS가 실제 도메인으로 설정되어 있는지 확인
- [ ] Admin 비밀번호가 기본값이 아닌지 확인
- [ ] 로그 모니터링 설정
- [ ] 예산 알림 설정

---

## 📚 추가 리소스

- [Cloud Run 문서](https://cloud.google.com/run/docs)
- [Cloud SQL 문서](https://cloud.google.com/sql/docs)
- [Secret Manager 문서](https://cloud.google.com/secret-manager/docs)
- [문제 해결 가이드](./4_TROUBLESHOOTING.md)

---

## 🆘 지원

문제가 발생하면:
1. 로그를 확인하세요
2. 이 문서의 문제 해결 섹션을 참조하세요
3. GitHub Issues에 문제를 등록하세요

