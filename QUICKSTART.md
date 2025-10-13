# VCBL Chatbot - 빠른 시작 가이드

이 가이드는 VCBL Chatbot을 가능한 한 빠르게 실행하기 위한 단계별 안내입니다.

## 목차

- [로컬 개발 환경](#로컬-개발-환경)
- [Google Cloud Run 배포](#google-cloud-run-배포)

---

## 로컬 개발 환경

### 사전 준비

- Docker와 Docker Compose 설치
- OpenAI API 키

### 3단계로 시작하기

#### 1. 환경 변수 설정

```bash
# backend/.env 파일 생성
cp backend/env.example backend/.env
```

`backend/.env` 파일을 열고 다음 값을 설정하세요:

```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
SECRET_KEY=your-secret-key-min-32-chars
```

#### 2. Docker Compose로 시작

```bash
# 모든 서비스 시작 (PostgreSQL + Redis + 애플리케이션)
docker-compose up -d

# 로그 확인 (선택사항)
docker-compose logs -f app
```

#### 3. 접속

브라우저에서 http://localhost:8080 접속

**초기 관리자 계정** (자동 생성됨):
- 학번: `super`
- 비밀번호: `super1234`

> ⚠️ **보안 경고**: 첫 로그인 후 반드시 비밀번호를 변경하세요!

### 관리자 계정 커스터마이징 (선택사항)

`.env` 파일에서 초기 관리자 계정 정보를 변경할 수 있습니다:

```bash
# 초기 관리자 계정 설정
ADMIN_STUDENT_ID=super
ADMIN_NAME=Super Administrator
ADMIN_PASSWORD=super1234
```

변경 후 컨테이너를 재시작하세요:

```bash
docker-compose down
docker-compose up -d
```

### 중지 및 재시작

```bash
# 중지
docker-compose down

# 재시작
docker-compose up -d

# 데이터 포함 완전 삭제
docker-compose down -v
```

---

## Google Cloud Run 배포

### 사전 준비

- Google Cloud 계정 및 프로젝트
- `gcloud` CLI 설치 및 인증
- OpenAI API 키

### 3단계로 배포하기

#### 1. 초기 설정 (최초 1회)

```bash
./scripts/deploy-setup.sh
```

이 스크립트가 다음을 자동으로 수행합니다:
- Google Cloud API 활성화
- Cloud SQL PostgreSQL 인스턴스 생성
- 서비스 계정 생성 및 권한 설정
- Secret Manager에 비밀 저장

실행 중 다음 정보를 입력하게 됩니다:
- Google Cloud 프로젝트 ID
- 데이터베이스 비밀번호
- SECRET_KEY (최소 32자)
- JWT_SECRET_KEY (최소 32자)
- OpenAI API 키

#### 2. 데이터베이스 마이그레이션

```bash
./scripts/run-migration.sh
```

Cloud Run Job을 생성하여 데이터베이스 스키마를 설정합니다.

#### 3. 애플리케이션 배포

```bash
./scripts/deploy.sh
```

또는 Cloud Build를 직접 실행:

```bash
gcloud builds submit --config cloudbuild.yaml
```

배포 완료 후 서비스 URL이 표시됩니다.

### 배포 확인

```bash
# 서비스 URL 확인
gcloud run services describe vcbl-chatbot \
  --region=asia-northeast3 \
  --format="value(status.url)"

# 헬스 체크
curl https://YOUR-SERVICE-URL/health
```

### 관리자 계정 생성

배포 후 관리자 계정을 생성해야 합니다:

```bash
# Cloud SQL Proxy를 사용한 로컬 연결
wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
chmod +x cloud_sql_proxy

# Proxy 시작 (백그라운드)
./cloud_sql_proxy -instances=PROJECT_ID:asia-northeast3:vcbl-postgres=tcp:5432 &

# 관리자 생성
cd backend
export DATABASE_URL='postgresql://vcbl_user:YOUR_PASSWORD@127.0.0.1:5432/vcbl_chatbot'
export SECRET_KEY='temp-key'
export OPENAI_API_KEY='temp-key'

python -c "
from app import create_app, db, bcrypt
from app.models.user import User

app = create_app('production')
with app.app_context():
    admin = User(
        student_id='admin001',
        name='관리자',
        hashed_password=bcrypt.generate_password_hash('admin_password').decode('utf-8'),
        is_admin=True
    )
    db.session.add(admin)
    db.session.commit()
    print('관리자 계정 생성 완료!')
"
```

---

## 다음 단계

### 로컬 개발

- [개발 가이드](docs/DEVELOPMENT.md) - 개발 환경 상세 설정
- [API 문서](docs/API.md) - API 엔드포인트 상세

### 프로덕션 배포

- [Google Cloud Deployment 가이드](docs/GOOGLE_CLOUD_DEPLOYMENT.md) - 상세 배포 가이드
  - CI/CD 파이프라인 설정
  - 모니터링 및 로깅
  - 보안 설정
  - 비용 최적화

### 커스터마이징

1. **비디오 추가**: 관리자 대시보드에서 YouTube 비디오 추가
2. **프롬프트 설정**: AI 챗봇의 시스템 프롬프트 커스터마이징
3. **스캐폴딩 생성**: 학습 질문 프롬프트 작성
4. **사용자 관리**: 권한 설정 및 사용자 활성화

---

## 문제 해결

### 로컬 환경

**포트 충돌**
```bash
# 다른 포트로 변경
PORT=9000 docker-compose up -d
```

**데이터베이스 초기화**
```bash
docker-compose down -v
docker-compose up -d
```

### Cloud Run

**로그 확인**
```bash
gcloud run services logs read vcbl-chatbot --region=asia-northeast3 --limit=50
```

**서비스 재시작**
```bash
gcloud run services update vcbl-chatbot --region=asia-northeast3
```

**Secret 업데이트**
```bash
echo -n "new-value" | gcloud secrets versions add SECRET_NAME --data-file=-
```

---

## 지원

더 많은 도움이 필요하신가요?

- 📖 [전체 README](README.md)
- 🚀 [배포 가이드](docs/GOOGLE_CLOUD_DEPLOYMENT.md)
- 💻 [개발 가이드](docs/DEVELOPMENT.md)
- 📝 [API 문서](docs/API.md)
- 🐛 [GitHub Issues](https://github.com/your-repo/issues)

---

**즐거운 학습 되세요! 🎓**

