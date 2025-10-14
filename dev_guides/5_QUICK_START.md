# 빠른 시작 가이드

VCBL Chatbot을 빠르게 시작하는 체크리스트와 필수 명령어 모음입니다.

## ⚡ 5분 로컬 환경 설정

### ✅ 체크리스트: 로컬 개발 환경 (5분)

#### 1. 사전 준비 (1분)
- [ ] Docker 설치 확인: `docker --version`
- [ ] Node.js 설치 확인: `node --version` (v18 이상)
- [ ] Python 설치 확인: `python --version` (v3.11 이상)

#### 2. PostgreSQL 시작 (1분)
```bash
# PostgreSQL 데이터베이스 시작
docker-compose up -d db

# 데이터베이스 상태 확인
docker-compose ps db
```

#### 3. 환경 변수 설정 (1분)
```bash
# 백엔드 환경 변수
cp backend/env.example backend/.env

# 프론트엔드 환경 변수
cp frontend/env.example frontend/.env

# .env 파일 편집 (SECRET_KEY, OPENAI_API_KEY 설정)
# backend/.env에서 DATABASE_URL을 postgresql://vcbl_user:vcbl_dev_password@localhost:5432/vcbl_chatbot로 설정
```

#### 4. 의존성 설치 (1분)
```bash
# 백엔드 의존성
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 프론트엔드 의존성
cd ../frontend
npm install
```

#### 5. 데이터베이스 초기화 (1분)
```bash
# 마이그레이션 실행
cd backend
source venv/bin/activate
flask db upgrade

# 관리자 계정 생성
flask init-superadmin
# 또는
./scripts/create-admin.sh
```

#### 6. 개발 서버 실행 (1분)
```bash
# 백엔드 서버 (터미널 1)
cd backend
source venv/bin/activate
python run.py

# 프론트엔드 서버 (터미널 2)
cd frontend
npm run dev
```

### 🎯 완료 확인
- [ ] 백엔드: http://localhost:8080/health → `{"status": "healthy"}`
- [ ] 프론트엔드: http://localhost:5173 → 로그인 페이지
- [ ] 관리자 로그인: 학번 `super`, 비밀번호 `super1234`

## 🚀 15분 Cloud 배포

### ✅ 체크리스트: Cloud 배포 (15분)

#### 1. Google Cloud 설정 (3분)
- [ ] Google Cloud 계정 생성
- [ ] 프로젝트 생성 또는 선택
- [ ] 결제 정보 등록
- [ ] Google Cloud CLI 설치 및 로그인

```bash
# Google Cloud CLI 설치 확인
gcloud version

# 프로젝트 설정
gcloud config set project YOUR_PROJECT_ID
gcloud config set run/region asia-northeast3
```

#### 2. 초기 설정 (5분)
```bash
# 초기 설정 스크립트 실행
./scripts/deploy-setup.sh

# Secret Manager에 비밀 정보 저장
echo -n "your-secret-key-32-chars" | gcloud secrets create vcbl-secret-key --data-file=-
echo -n "your-jwt-secret-key-32" | gcloud secrets create vcbl-jwt-secret-key --data-file=-
echo -n "your-db-password" | gcloud secrets create vcbl-db-password --data-file=-
echo -n "sk-your-openai-api-key" | gcloud secrets create vcbl-openai-api-key --data-file=-
```

#### 3. 첫 배포 (3분)
```bash
# Cloud Build를 통한 배포
gcloud builds submit --config cloudbuild.yaml

# 배포 상태 확인
gcloud run services describe vcbl-chatbot --region=asia-northeast3
```

#### 4. 데이터베이스 마이그레이션 (2분)
```bash
# 마이그레이션 Job 생성
./scripts/create-migration-job.sh

# 마이그레이션 실행
gcloud run jobs execute vcbl-chatbot-migrate --region=asia-northeast3 --wait
```

#### 5. 초기 관리자 생성 (2분)
```bash
# 관리자 정보 저장
echo -n "2024000001" | gcloud secrets create vcbl-super-admin-id --data-file=-
echo -n "관리자" | gcloud secrets create vcbl-super-admin-name --data-file=-
echo -n "SecurePass123!" | gcloud secrets create vcbl-super-admin-password --data-file=-

# 관리자 생성 Job 실행
gcloud run jobs create vcbl-init-admin \
  --image=gcr.io/YOUR_PROJECT_ID/vcbl-chatbot:latest \
  --set-cloudsql-instances=YOUR_PROJECT_ID:asia-northeast3:vcbl-postgres \
  --set-env-vars="CLOUD_SQL_INSTANCE=YOUR_PROJECT_ID:asia-northeast3:vcbl-postgres,DB_USER=vcbl_user,DB_NAME=vcbl_chatbot,FLASK_ENV=production" \
  --set-secrets="DB_PASSWORD=vcbl-db-password:latest,SECRET_KEY=vcbl-secret-key:latest,JWT_SECRET_KEY=vcbl-jwt-secret-key:latest,OPENAI_API_KEY=vcbl-openai-api-key:latest,VCBL_SUPER_ADMIN_ID=vcbl-super-admin-id:latest,VCBL_SUPER_ADMIN_NAME=vcbl-super-admin-name:latest,VCBL_SUPER_ADMIN_PASSWORD=vcbl-super-admin-password:latest" \
  --service-account="vcbl-chatbot-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --command="flask" \
  --args="init-superadmin" \
  --region=asia-northeast3

gcloud run jobs execute vcbl-init-admin --region=asia-northeast3 --wait
```

### 🎯 완료 확인
- [ ] 서비스 URL 확인: `gcloud run services describe vcbl-chatbot --region=asia-northeast3 --format="value(status.url)"`
- [ ] 헬스 체크: `curl https://YOUR_SERVICE_URL/health`
- [ ] 관리자 로그인: 학번 `2024000001`, 비밀번호 `SecurePass123!`

## 📋 필수 명령어 치트시트

### 🔧 로컬 개발 명령어

#### 데이터베이스 관리
```bash
# 데이터베이스 상태 확인
flask check-db

# 마이그레이션 생성
flask db migrate -m "Description"

# 마이그레이션 실행
flask db upgrade

# 데이터베이스 초기화
flask init-db
```

#### 관리자 계정 관리
```bash
# Super admin 생성
flask init-superadmin

# 일반 admin 생성
flask create-admin 2024000002 "새관리자" "password123"

# 데이터베이스 상태 확인
flask check-db
```

#### 개발 서버
```bash
# 백엔드 서버
cd backend
source venv/bin/activate
python run.py

# 프론트엔드 서버
cd frontend
npm run dev

# 전체 서비스 (Docker Compose)
docker-compose up -d
```

### ☁️ Cloud 배포 명령어

#### 배포 관리
```bash
# 빌드 및 배포
gcloud builds submit --config cloudbuild.yaml

# 서비스 상태 확인
gcloud run services describe vcbl-chatbot --region=asia-northeast3

# 서비스 URL 확인
gcloud run services describe vcbl-chatbot --region=asia-northeast3 --format="value(status.url)"
```

#### 로그 관리
```bash
# 최근 로그 확인
gcloud run services logs read vcbl-chatbot --region=asia-northeast3 --limit=50

# 에러 로그만
gcloud run services logs read vcbl-chatbot --region=asia-northeast3 --filter="severity>=ERROR"

# 실시간 로그 스트리밍
gcloud run services logs tail vcbl-chatbot --region=asia-northeast3
```

#### 데이터베이스 관리
```bash
# 마이그레이션 실행
gcloud run jobs execute vcbl-chatbot-migrate --region=asia-northeast3 --wait

# 데이터베이스 상태 확인
gcloud run jobs execute vcbl-check-db --region=asia-northeast3 --wait

# 관리자 생성
gcloud run jobs execute vcbl-init-admin --region=asia-northeast3 --wait
```

### 🔍 모니터링 명령어

#### 헬스 체크
```bash
# 기본 헬스 체크
curl https://YOUR_SERVICE_URL/health

# 준비 상태 체크
curl https://YOUR_SERVICE_URL/readiness

# API 테스트
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" https://YOUR_SERVICE_URL/api/videos
```

#### 리소스 모니터링
```bash
# Cloud Run 메트릭
gcloud run services describe vcbl-chatbot --region=asia-northeast3

# Cloud SQL 상태
gcloud sql instances describe vcbl-postgres

# 비용 확인
gcloud billing budgets list
```

## 🚨 응급 상황 대응

### 서비스 다운 시
```bash
# 1. 서비스 상태 확인
gcloud run services describe vcbl-chatbot --region=asia-northeast3

# 2. 로그 확인
gcloud run services logs read vcbl-chatbot --region=asia-northeast3 --limit=20

# 3. 서비스 재시작
gcloud run services update vcbl-chatbot --region=asia-northeast3
```

### 데이터베이스 문제 시
```bash
# 1. Cloud SQL 상태 확인
gcloud sql instances describe vcbl-postgres

# 2. 인스턴스 재시작
gcloud sql instances restart vcbl-postgres

# 3. 연결 테스트
gcloud sql connect vcbl-postgres --user=vcbl_user --database=vcbl_chatbot
```

### OpenAI API 오류 시
```bash
# 1. API 키 확인
gcloud secrets versions access latest --secret="vcbl-openai-api-key"

# 2. 토큰 제한 조정
gcloud run services update vcbl-chatbot \
  --region=asia-northeast3 \
  --set-env-vars="DAILY_TOKEN_LIMIT=1000"
```

## 📊 성능 최적화

### 리소스 조정
```bash
# CPU/메모리 증가
gcloud run services update vcbl-chatbot \
  --region=asia-northeast3 \
  --memory=4Gi \
  --cpu=2

# 인스턴스 수 조정
gcloud run services update vcbl-chatbot \
  --region=asia-northeast3 \
  --min-instances=2 \
  --max-instances=10
```

### 데이터베이스 최적화
```bash
# Cloud SQL 인스턴스 업그레이드
gcloud sql instances patch vcbl-postgres --tier=db-g1-small

# 연결 풀 설정 확인
# config.py에서 pool_size, max_overflow 조정
```

## 🔧 유용한 스크립트

### 자동화 스크립트
```bash
# 전체 재배포
./scripts/deploy.sh

# 마이그레이션만 실행
./scripts/run-migration.sh

# 초기 설정
./scripts/deploy-setup.sh
```

### 모니터링 스크립트
```bash
# 서비스 상태 체크
curl -s https://YOUR_SERVICE_URL/health | jq .

# 데이터베이스 연결 체크
curl -s https://YOUR_SERVICE_URL/readiness | jq .

# 로그 에러 체크
gcloud run services logs read vcbl-chatbot --region=asia-northeast3 \
  --filter="severity>=ERROR" --limit=5
```

## 📞 지원 및 도움말

### 문제 해결
1. [문제 해결 가이드](4_TROUBLESHOOTING.md) 확인
2. 로그 분석: `gcloud run services logs read vcbl-chatbot --region=asia-northeast3`
3. GitHub Issues에 문제 등록

### 추가 리소스
- [배포 가이드](1_DEPLOYMENT_GUIDE.md): 상세한 배포 방법
- [환경 변수 가이드](2_ENVIRONMENT_VARIABLES.md): 모든 환경 변수 설명
- [유지관리 가이드](3_MAINTENANCE_GUIDE.md): 일상 관리 방법
- [문제 해결 가이드](4_TROUBLESHOOTING.md): 문제 해결 방법
