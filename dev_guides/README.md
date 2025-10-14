# VCBL Chatbot 배포 및 관리 가이드

이 폴더에는 VCBL Chatbot을 Google Cloud Run에 배포하고 관리하기 위한 상세한 가이드 문서들이 포함되어 있습니다.

## 📚 가이드 문서 목록

### 1. [배포 가이드](1_DEPLOYMENT_GUIDE.md)
- Google Cloud 계정 설정부터 첫 배포까지 단계별 설명
- 스크린샷과 함께 제공
- Secret Manager 설정 방법
- Cloud SQL 인스턴스 생성
- 초기 관리자 계정 생성
- 문제 해결 (Troubleshooting)

### 2. [환경 변수 가이드](2_ENVIRONMENT_VARIABLES.md)
- 모든 환경 변수 상세 설명
- 필수/선택 변수 구분
- 기본값과 권장값
- 보안 관련 주의사항
- Cloud vs Local 환경 차이

### 3. [유지관리 가이드](3_MAINTENANCE_GUIDE.md)
- 일상적인 관리 작업
- 로그 확인 방법
- 데이터베이스 백업/복원
- 사용자 관리
- OpenAI 비용 모니터링
- 업데이트 및 재배포

### 4. [문제 해결 가이드](4_TROUBLESHOOTING.md)
- 자주 발생하는 문제와 해결책
- 로그 해석 방법
- 데이터베이스 연결 문제
- OpenAI API 오류
- Cloud Run 인스턴스 문제

### 5. [빠른 시작 가이드](5_QUICK_START.md)
- 5분 안에 로컬 환경 실행
- 15분 안에 Cloud 배포
- 체크리스트 형식의 단계별 가이드
- 필수 명령어 모음

## 🚀 빠른 시작

### 로컬 개발 환경 (5분)
```bash
# 1. PostgreSQL 시작
docker-compose up -d db

# 2. 환경 설정
cp backend/env.example backend/.env
cp frontend/env.example frontend/.env

# 3. 의존성 설치
./scripts/setup.sh

# 4. 데이터베이스 초기화
cd backend
source venv/bin/activate
flask db upgrade
flask init-superadmin  # 환경 변수 설정 후

# 5. 개발 서버 실행
./dev/start-local.sh
```

### Cloud 배포 (15분)
```bash
# 1. 초기 설정
./scripts/deploy-setup.sh

# 2. 마이그레이션 Job 생성
./scripts/create-migration-job.sh

# 3. 배포
gcloud builds submit --config cloudbuild.yaml

# 4. 마이그레이션 실행
gcloud run jobs execute vcbl-chatbot-migrate --region=asia-northeast3 --wait

# 5. 초기 관리자 생성
gcloud run jobs create vcbl-init-admin \
  --image=gcr.io/PROJECT_ID/vcbl-chatbot:latest \
  --set-env-vars="VCBL_SUPER_ADMIN_ID=2024000001,VCBL_SUPER_ADMIN_NAME=관리자,VCBL_SUPER_ADMIN_PASSWORD=SecurePass123!" \
  --command="flask" \
  --args="init-superadmin"
```

## 📞 지원

문제가 발생하거나 질문이 있으시면:

1. [문제 해결 가이드](4_TROUBLESHOOTING.md)를 먼저 확인하세요
2. GitHub Issues에 문제를 등록하세요
3. 로그를 확인하여 구체적인 오류 메시지를 제공하세요

## 🔧 주요 명령어

### 로컬 개발
```bash
# 데이터베이스 상태 확인
flask check-db

# 관리자 계정 생성
flask create-admin 2024000001 "관리자" "password123"

# 데이터베이스 초기화
flask init-db
```

### Cloud 배포
```bash
# 빌드 및 배포
gcloud builds submit --config cloudbuild.yaml

# 마이그레이션 실행
gcloud run jobs execute vcbl-chatbot-migrate --region=asia-northeast3 --wait

# 로그 확인
gcloud run services logs read vcbl-chatbot --region=asia-northeast3

# 서비스 상태 확인
gcloud run services describe vcbl-chatbot --region=asia-northeast3
```

## 📊 모니터링

### Cloud Console에서 확인할 항목
- **Cloud Run**: 서비스 상태, 요청 수, 에러율
- **Cloud SQL**: 연결 수, CPU 사용률, 메모리 사용률
- **Cloud Logging**: 애플리케이션 로그, 에러 로그
- **Secret Manager**: 비밀 정보 관리

### 주요 메트릭
- **응답 시간**: 평균 200ms 이하 권장
- **에러율**: 1% 이하 권장
- **데이터베이스 연결**: 15개 이하 유지
- **OpenAI 토큰 사용량**: 일일 제한 내 유지
