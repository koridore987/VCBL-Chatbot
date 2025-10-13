# Google Cloud Run 배포 가이드

이 문서는 VCBL Chatbot을 Google Cloud Run에 PostgreSQL과 함께 배포하는 방법을 설명합니다.

## 목차

1. [사전 준비](#사전-준비)
2. [빠른 시작](#빠른-시작)
3. [상세 배포 단계](#상세-배포-단계)
4. [로컬 개발 환경](#로컬-개발-환경)
5. [문제 해결](#문제-해결)
6. [비용 최적화](#비용-최적화)

---

## 사전 준비

### 필수 요구사항

1. **Google Cloud 계정**
   - GCP 프로젝트 생성
   - 결제 계정 연결

2. **로컬 도구 설치**
   ```bash
   # Google Cloud SDK 설치
   # macOS
   brew install --cask google-cloud-sdk
   
   # Linux
   curl https://sdk.cloud.google.com | bash
   
   # 설치 후 초기화
   gcloud init
   ```

3. **OpenAI API 키**
   - https://platform.openai.com/api-keys 에서 생성

4. **도메인 (선택사항)**
   - 커스텀 도메인을 사용하려는 경우

---

## 빠른 시작

### 1단계: 초기 설정 실행

```bash
# 저장소 클론 (이미 클론했다면 생략)
cd vcbl-chatbot

# 배포 설정 스크립트 실행
./scripts/deploy-setup.sh
```

이 스크립트는 다음 작업을 수행합니다:
- 필요한 GCP API 활성화
- 서비스 계정 생성 및 권한 부여
- Cloud SQL PostgreSQL 인스턴스 생성
- 데이터베이스 및 사용자 생성
- Secret Manager에 비밀 저장

### 2단계: 데이터베이스 마이그레이션

```bash
./scripts/run-migration.sh
```

### 3단계: 애플리케이션 배포

```bash
./scripts/deploy.sh
```

또는 직접:

```bash
gcloud builds submit --config cloudbuild.yaml
```

### 4단계: 배포 확인

```bash
# 서비스 URL 확인
gcloud run services describe vcbl-chatbot \
  --region=asia-northeast3 \
  --format="value(status.url)"

# 헬스 체크
curl https://YOUR-SERVICE-URL/health
```

---

## 상세 배포 단계

### 1. Google Cloud 프로젝트 설정

```bash
# 프로젝트 ID 설정
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# 필요한 API 활성화
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com
```

### 2. Cloud SQL PostgreSQL 인스턴스 생성

```bash
# 인스턴스 생성 (5-10분 소요)
gcloud sql instances create vcbl-postgres \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=asia-northeast3 \
  --storage-type=SSD \
  --storage-size=10GB \
  --storage-auto-increase \
  --backup-start-time=03:00

# 데이터베이스 생성
gcloud sql databases create vcbl_chatbot \
  --instance=vcbl-postgres

# 사용자 생성
gcloud sql users create vcbl_user \
  --instance=vcbl-postgres \
  --password=YOUR_SECURE_PASSWORD
```

### 3. Secret Manager 설정

```bash
# SECRET_KEY 생성 및 저장
python3 -c "import secrets; print(secrets.token_hex(32))" | \
  gcloud secrets create vcbl-secret-key \
  --data-file=- \
  --replication-policy=automatic

# JWT_SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))" | \
  gcloud secrets create vcbl-jwt-secret-key \
  --data-file=- \
  --replication-policy=automatic

# DB_PASSWORD
echo -n "YOUR_DB_PASSWORD" | \
  gcloud secrets create vcbl-db-password \
  --data-file=- \
  --replication-policy=automatic

# OPENAI_API_KEY
echo -n "YOUR_OPENAI_API_KEY" | \
  gcloud secrets create vcbl-openai-api-key \
  --data-file=- \
  --replication-policy=automatic

# REDIS_URL (메모리 기반 사용 시)
echo -n "memory://" | \
  gcloud secrets create vcbl-redis-url \
  --data-file=- \
  --replication-policy=automatic
```

### 4. 서비스 계정 생성 및 권한 부여

```bash
# 서비스 계정 생성
gcloud iam service-accounts create vcbl-chatbot-sa \
  --display-name="VCBL Chatbot Service Account"

# Cloud SQL 클라이언트 권한
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:vcbl-chatbot-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"

# Secret Manager 접근 권한
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:vcbl-chatbot-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 5. Cloud Build 권한 설정

```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

### 6. 데이터베이스 마이그레이션

#### 옵션 A: Cloud SQL Proxy 사용 (로컬)

```bash
# Cloud SQL Proxy 다운로드
wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
chmod +x cloud_sql_proxy

# Proxy 실행
./cloud_sql_proxy -instances=${PROJECT_ID}:asia-northeast3:vcbl-postgres=tcp:5432 &

# 마이그레이션 실행
cd backend
export DATABASE_URL='postgresql://vcbl_user:YOUR_PASSWORD@127.0.0.1:5432/vcbl_chatbot'
export SECRET_KEY='temp-key-for-migration'
export OPENAI_API_KEY='temp-key-for-migration'
export FLASK_APP=run.py
flask db upgrade
```

#### 옵션 B: Cloud Run Jobs 사용 (권장)

```bash
# 마이그레이션 Job 생성 및 실행
./scripts/run-migration.sh
```

### 7. 애플리케이션 배포

```bash
# Cloud Build를 통한 배포
gcloud builds submit --config cloudbuild.yaml

# 또는 스크립트 사용
./scripts/deploy.sh
```

### 8. 관리자 계정 생성

```bash
# Cloud Run 서비스에 직접 접속하여 생성
gcloud run services proxy vcbl-chatbot --region=asia-northeast3 &

# 관리자 생성 스크립트 실행
cd backend
export DATABASE_URL='postgresql://vcbl_user:YOUR_PASSWORD@127.0.0.1:5432/vcbl_chatbot'
python -c "
from app import create_app, db, bcrypt
from app.models.user import User

app = create_app('production')
with app.app_context():
    admin = User(
        student_id='2024000001',
        name='Admin',
        hashed_password=bcrypt.generate_password_hash('admin_password').decode('utf-8'),
        is_admin=True
    )
    db.session.add(admin)
    db.session.commit()
    print('관리자 계정 생성 완료!')
"
```

---

## 로컬 개발 환경

### Docker Compose 사용 (권장)

```bash
# .env 파일 생성
cp backend/env.example backend/.env
# backend/.env 파일을 편집하여 실제 값 입력

# Docker Compose로 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f app

# 서비스 중지
docker-compose down

# 볼륨 포함 완전 제거
docker-compose down -v
```

### 직접 실행

```bash
# 백엔드
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# .env 파일 설정
cp env.example .env
# .env 파일 편집

# 데이터베이스 마이그레이션
export FLASK_APP=run.py
flask db upgrade

# 개발 서버 실행
python run.py

# 프론트엔드 (새 터미널)
cd frontend
npm install
cp env.example .env
# .env 파일에서 VITE_API_URL 설정
npm run dev
```

---

## 환경 변수 설정

### Cloud Run 환경 변수

`cloudbuild.yaml`에 정의되어 있으며, 다음을 포함합니다:

```yaml
# 직접 설정되는 환경 변수
CLOUD_SQL_INSTANCE: ${PROJECT_ID}:asia-northeast3:vcbl-postgres
DB_USER: vcbl_user
DB_NAME: vcbl_chatbot
FLASK_ENV: production

# Secret Manager에서 가져오는 비밀
SECRET_KEY: vcbl-secret-key:latest
JWT_SECRET_KEY: vcbl-jwt-secret-key:latest
DB_PASSWORD: vcbl-db-password:latest
OPENAI_API_KEY: vcbl-openai-api-key:latest
REDIS_URL: vcbl-redis-url:latest
```

### 환경 변수 업데이트

```bash
# 환경 변수 직접 수정
gcloud run services update vcbl-chatbot \
  --region=asia-northeast3 \
  --update-env-vars="NEW_VAR=value"

# Secret 업데이트
echo -n "new-secret-value" | \
  gcloud secrets versions add vcbl-secret-key --data-file=-
```

---

## 모니터링 및 로깅

### 로그 확인

```bash
# 최근 로그 확인
gcloud run services logs read vcbl-chatbot \
  --region=asia-northeast3 \
  --limit=50

# 실시간 로그 스트리밍
gcloud run services logs tail vcbl-chatbot \
  --region=asia-northeast3
```

### 메트릭 확인

```bash
# 서비스 상태
gcloud run services describe vcbl-chatbot \
  --region=asia-northeast3

# Cloud Console에서 확인
# https://console.cloud.google.com/run
```

### 알림 설정

Google Cloud Console에서 다음을 설정할 수 있습니다:
- CPU/메모리 사용량 알림
- 오류율 알림
- 응답 시간 알림

---

## 문제 해결

### 일반적인 문제

#### 1. 데이터베이스 연결 실패

```bash
# Cloud SQL 인스턴스 상태 확인
gcloud sql instances describe vcbl-postgres

# Cloud SQL 연결 테스트
gcloud sql connect vcbl-postgres --user=vcbl_user
```

#### 2. Secret Manager 접근 오류

```bash
# 서비스 계정 권한 확인
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --format="table(bindings.role)" \
  --filter="bindings.members:vcbl-chatbot-sa@"

# Secret 존재 확인
gcloud secrets list
```

#### 3. 빌드 실패

```bash
# 빌드 로그 확인
gcloud builds list --limit=5

# 특정 빌드 로그 확인
gcloud builds log BUILD_ID
```

#### 4. 500 에러

```bash
# 애플리케이션 로그 확인
gcloud run services logs read vcbl-chatbot \
  --region=asia-northeast3 \
  --limit=100

# 환경 변수 확인
gcloud run services describe vcbl-chatbot \
  --region=asia-northeast3 \
  --format="yaml(spec.template.spec.containers[0].env)"
```

### 디버깅 모드

임시로 디버그 모드를 활성화하려면:

```bash
gcloud run services update vcbl-chatbot \
  --region=asia-northeast3 \
  --update-env-vars="LOG_LEVEL=DEBUG"
```

---

## 보안 권장사항

### 1. Secret 관리

- ❌ 절대 코드에 직접 비밀 키 입력하지 않기
- ✅ Secret Manager 사용
- ✅ 정기적으로 비밀 키 교체

### 2. IAM 권한

- ✅ 최소 권한 원칙 적용
- ✅ 서비스 계정별로 필요한 권한만 부여
- ❌ 과도한 권한 부여 금지

### 3. 네트워크 보안

```bash
# VPC Connector 사용 (선택사항)
gcloud compute networks vpc-access connectors create vcbl-connector \
  --region=asia-northeast3 \
  --range=10.8.0.0/28

# Cloud Run 서비스에 연결
gcloud run services update vcbl-chatbot \
  --region=asia-northeast3 \
  --vpc-connector=vcbl-connector \
  --vpc-egress=private-ranges-only
```

### 4. Cloud SQL 보안

- ✅ Private IP 사용 고려
- ✅ SSL/TLS 연결 강제
- ✅ 정기적인 백업 확인
- ✅ 자동 백업 활성화

---

## 비용 최적화

### 리소스 크기 조정

```bash
# 메모리 및 CPU 조정
gcloud run services update vcbl-chatbot \
  --region=asia-northeast3 \
  --memory=1Gi \
  --cpu=1
```

### 인스턴스 제한

```bash
# 최소/최대 인스턴스 설정
gcloud run services update vcbl-chatbot \
  --region=asia-northeast3 \
  --min-instances=0 \
  --max-instances=10
```

### Cloud SQL 티어 조정

```bash
# 개발/스테이징 환경: db-f1-micro
# 프로덕션 (소규모): db-g1-small
# 프로덕션 (중규모): db-n1-standard-1

gcloud sql instances patch vcbl-postgres \
  --tier=db-f1-micro
```

### 비용 모니터링

- Cloud Console의 Billing 페이지에서 확인
- 예산 알림 설정
- 정기적인 리소스 사용량 검토

### 예상 비용 (월 기준)

**소규모 운영 (학생 100명 이하)**
- Cloud Run: $0-5
- Cloud SQL (db-f1-micro): $7-10
- 네트워크: $0-2
- 총: **$10-20/월**

**중규모 운영 (학생 500명)**
- Cloud Run: $10-30
- Cloud SQL (db-g1-small): $25-35
- 네트워크: $2-5
- 총: **$40-70/월**

*실제 비용은 사용량에 따라 달라질 수 있습니다.*

---

## CI/CD 파이프라인

### GitHub와 Cloud Build 연동

1. **Cloud Build GitHub App 설치**
   ```bash
   # GCP Console에서 설정
   # https://console.cloud.google.com/cloud-build/triggers
   ```

2. **트리거 생성**
   ```bash
   gcloud builds triggers create github \
     --repo-name=vcbl-chatbot \
     --repo-owner=YOUR_GITHUB_USERNAME \
     --branch-pattern="^main$" \
     --build-config=cloudbuild.yaml
   ```

3. **자동 배포**
   - `main` 브랜치에 푸시하면 자동으로 빌드 및 배포

---

## 롤백 및 버전 관리

### 이전 버전으로 롤백

```bash
# 리비전 목록 확인
gcloud run revisions list \
  --service=vcbl-chatbot \
  --region=asia-northeast3

# 특정 리비전으로 트래픽 전환
gcloud run services update-traffic vcbl-chatbot \
  --region=asia-northeast3 \
  --to-revisions=REVISION_NAME=100
```

### 점진적 배포 (Blue-Green)

```bash
# 새 버전에 10% 트래픽
gcloud run services update-traffic vcbl-chatbot \
  --region=asia-northeast3 \
  --to-revisions=NEW_REVISION=10,OLD_REVISION=90

# 문제 없으면 100% 전환
gcloud run services update-traffic vcbl-chatbot \
  --region=asia-northeast3 \
  --to-latest
```

---

## 추가 리소스

- [Google Cloud Run 문서](https://cloud.google.com/run/docs)
- [Cloud SQL for PostgreSQL](https://cloud.google.com/sql/docs/postgres)
- [Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Cloud Build](https://cloud.google.com/build/docs)

---

## 지원

문제가 발생하면 다음을 확인하세요:

1. 로그 확인: `gcloud run services logs read vcbl-chatbot --region=asia-northeast3`
2. 서비스 상태: `gcloud run services describe vcbl-chatbot --region=asia-northeast3`
3. Cloud SQL 상태: `gcloud sql instances describe vcbl-postgres`
4. Issue 생성: GitHub 저장소의 Issues 탭

---

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

