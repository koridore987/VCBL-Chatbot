# VCBL Chatbot 빠른 시작 가이드

## 🚀 5분 안에 시작하기

### 로컬 개발 (직접 실행)

```bash
# 1. 저장소 클론
git clone <repository-url>
cd vcbl-chatbot

# 2. 로컬 개발 환경 설정
./setup-local-dev.sh

# 3. 환경 변수 설정
# .env 파일을 열고 OPENAI_API_KEY를 설정하세요

# 4. 데이터베이스 시작 (Docker 사용)
docker-compose up -d db redis

# 5. 개발 서버 시작
# 터미널 1: 백엔드
./start-backend.sh

# 터미널 2: 프론트엔드  
./start-frontend.sh

# 또는 통합 실행 (tmux 사용)
./start-dev.sh

# 6. 접속
# 🌐 http://localhost:5173 (프론트엔드)
# 🔧 http://localhost:5000 (백엔드 API)
```

### 중지
```bash
# 개발 서버 중지: Ctrl+C
# 데이터베이스 중지
docker-compose down
```

---

## 🐳 로컬 전체 테스트 (Docker)

```bash
# 전체 애플리케이션을 Docker로 테스트
docker-compose up -d

# 접속: http://localhost:8080
```

## ☁️ Google Cloud 배포

### 1단계: 초기 설정 (최초 1회만)

```bash
# GCP 프로젝트 설정
export GCP_PROJECT_ID="your-project-id"

# 초기화 스크립트 실행
./scripts/setup-gcloud.sh
```

이 스크립트가 다음을 자동으로 처리합니다:
- ✅ Google Cloud API 활성화
- ✅ Cloud SQL (PostgreSQL) 생성
- ✅ Secret Manager 시크릿 등록
- ✅ 권한 설정

### 2단계: 배포

```bash
# cloudbuild.yaml 수정
# _CLOUD_SQL_INSTANCE 값을 setup 스크립트 출력값으로 변경

# 배포!
./scripts/deploy-unified.sh
```

### 3단계: 데이터베이스 초기화

```bash
# 마이그레이션 실행
gcloud run jobs create vcbl-chatbot-migrate \
  --image=gcr.io/$GCP_PROJECT_ID/vcbl-chatbot:latest \
  --region=asia-northeast3 \
  --set-cloudsql-instances=$CLOUD_SQL_INSTANCE \
  --set-secrets=DATABASE_URL=DATABASE_URL:latest \
  --command=flask,db,upgrade

gcloud run jobs execute vcbl-chatbot-migrate --region=asia-northeast3

# 관리자 계정 생성
gcloud run jobs create vcbl-chatbot-init-admin \
  --image=gcr.io/$GCP_PROJECT_ID/vcbl-chatbot:latest \
  --region=asia-northeast3 \
  --set-cloudsql-instances=$CLOUD_SQL_INSTANCE \
  --set-secrets=DATABASE_URL=DATABASE_URL:latest \
  --command=flask,init-admin

gcloud run jobs execute vcbl-chatbot-init-admin --region=asia-northeast3
```

### 배포 URL 확인

```bash
gcloud run services describe vcbl-chatbot \
  --region=asia-northeast3 \
  --format="value(status.url)"
```

---

## 📝 다음 단계

- 📖 상세 가이드: [README.md](README.md)
- 🔧 환경 변수 설정: `env.example` (로컬 개발용)
- 📊 API 문서: README.md의 "API 개요" 섹션

## ❓ 문제 해결

### 로컬 개발
- **포트 충돌**: 백엔드는 5000, 프론트엔드는 5173 포트 사용
- **DB 연결 실패**: `docker-compose ps`로 데이터베이스 상태 확인
- **권한 오류**: `chmod +x *.sh`
- **Python 가상환경**: `cd backend && source venv/bin/activate`

### Cloud Run
- **빌드 실패**: API 활성화 확인 (`setup-gcloud.sh` 재실행)
- **DB 연결 실패**: Secret Manager의 `DATABASE_URL` 확인
- **로그 확인**: `gcloud run services logs tail vcbl-chatbot --region=asia-northeast3`

## 🎯 주요 명령어

### Docker
```bash
docker-compose logs -f              # 로그 보기
docker-compose restart app          # 재시작
docker-compose exec app bash        # 쉘 접속
```

### GCloud
```bash
gcloud run services logs tail vcbl-chatbot --region=asia-northeast3  # 로그
gcloud run services describe vcbl-chatbot --region=asia-northeast3    # 상태
```

---

**🎉 완료! 문제가 있으면 README.md의 "트러블슈팅" 섹션을 참고하세요.**

