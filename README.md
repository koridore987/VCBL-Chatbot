# VCBL 학습 플랫폼

Flask + React + PostgreSQL 기반의 온라인 학습 플랫폼으로, YouTube 동영상 학습과 AI 챗봇(ChatGPT)을 통한 학습 지원, 스캐폴딩 기능을 제공합니다.

## 주요 기능

- **사용자 관리**: 학번 기반 인증, 권한 계층 관리 (`super` > `admin` > `user`)
- **학습 인터페이스**: YouTube 동영상 + 스캐폴딩 (질문/채팅) 병렬 제공
- **ChatGPT 연동**: gpt-4o-mini 모델, 요약 기반 맥락 유지
- **관리자 기능**: 사용자/비디오/스캐폴딩/프롬프트 관리
- **연구 데이터 관리**: 모든 사용자 이벤트 로깅 및 CSV 내보내기

## 기술 스택

### Backend
- Flask 3.0, SQLAlchemy, PostgreSQL
- Flask-JWT-Extended, OpenAI API

### Frontend
- React 18, Vite 5, React Router 6
- Axios, CodeMirror, react-youtube

### Deployment
- Docker, PostgreSQL 15, Google Cloud Run
- Cloud Build, Secret Manager, Redis

## 빠른 시작

### Docker Compose 실행

```bash
# 1. 환경 변수 설정
cp backend/env.example backend/.env
# backend/.env 파일에서 OPENAI_API_KEY 등 필수 값 설정

# 2. 서비스 시작
docker-compose up -d

# 3. 접속
# http://localhost:8080
```

**초기 관리자 계정**: `super` / `super1234`

### 🚀 자동 배포 (GitHub Actions)

GitHub main 브랜치에 push하면 자동으로 Google Cloud Run에 배포됩니다.

#### 1. 초기 설정
```bash
./scripts/setup-deployment.sh YOUR_PROJECT_ID
```

#### 2. GitHub Secrets 설정
GitHub 저장소 > Settings > Secrets and variables > Actions:
- `GCP_PROJECT_ID`: Google Cloud 프로젝트 ID
- `GCP_SA_KEY`: 서비스 계정 키 (Base64 인코딩)

#### 3. Secret Manager 설정
```bash
echo -n 'YOUR_DB_PASSWORD' | gcloud secrets create vcbl-db-password --data-file=-
echo -n 'YOUR_OPENAI_API_KEY' | gcloud secrets create vcbl-openai-key --data-file=-
echo -n 'YOUR_SECRET_KEY' | gcloud secrets create vcbl-secret-key --data-file=-
echo -n 'YOUR_JWT_SECRET_KEY' | gcloud secrets create vcbl-jwt-secret --data-file=-
```

#### 4. Cloud SQL 설정
```bash
gcloud sql instances create vcbl-chatbot-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=asia-northeast3 \
    --root-password=YOUR_ROOT_PASSWORD

gcloud sql databases create vcbl_chatbot --instance=vcbl-chatbot-db
gcloud sql users create vcbl_user --instance=vcbl-chatbot-db --password=YOUR_DB_PASSWORD
```

#### 5. 배포 테스트
```bash
git add .
git commit -m "Setup automatic deployment"
git push origin main
```

#### 6. 로그 확인
```bash
# Cloud Run 로그
gcloud run services logs read vcbl-chatbot --region=asia-northeast3

# 배포 테스트
./scripts/test-deployment.sh YOUR_PROJECT_ID
```

### 수동 배포 (Cloud Build)

```bash
# 1. Cloud SQL, Secret Manager, Cloud Run 설정
gcloud services enable sqladmin.googleapis.com secretmanager.googleapis.com run.googleapis.com

# 2. 데이터베이스 마이그레이션
./scripts/run-migration.sh

# 3. 애플리케이션 배포
gcloud builds submit --config cloudbuild.yaml
```

## 프로젝트 구조

```
vcbl-chatbot/
├── backend/                    # Flask API 서버
│   ├── app/
│   │   ├── models/            # SQLAlchemy 모델
│   │   ├── routes/            # API 라우트
│   │   ├── services/          # 비즈니스 로직
│   │   ├── validators/        # 입력 검증
│   │   └── utils/             # 유틸리티
│   ├── migrations/            # Alembic 마이그레이션
│   └── run.py                 # 진입점
├── frontend/                   # React 웹앱
│   └── src/
│       ├── components/        # 재사용 컴포넌트
│       ├── pages/             # 페이지 컴포넌트
│       └── services/          # API 클라이언트
├── scripts/                    # 배포/관리 스크립트
├── config/                     # Nginx 설정
├── Dockerfile                  # 프로덕션 Docker 이미지
├── docker-compose.yml          # 로컬 Docker 환경
└── cloudbuild.yaml             # GCP Cloud Build
```

## 데이터베이스 스키마

- **users**: 사용자 정보, 권한, 토큰 사용량
- **videos**: 비디오 정보, YouTube ID, 스캐폴딩 모드
- **chat_sessions**: 채팅 세션, 요약문, 토큰 사용량
- **chat_messages**: 개별 메시지 (role, 토큰 정보)
- **chat_prompt_templates**: 시스템 프롬프트, 버전 관리
- **scaffoldings**: 학습 질문 프롬프트
- **scaffolding_responses**: 사용자 응답
- **event_logs**: 모든 사용자 이벤트

## API 엔드포인트

### 인증 (`/api/auth`)
- `POST /register` - 회원가입
- `POST /login` - 로그인
- `GET /me` - 현재 사용자 정보
- `POST /change-password` - 비밀번호 변경

### 비디오 (`/api/videos`)
- `GET /` - 비디오 목록
- `GET /:id` - 비디오 상세 (스캐폴딩 포함)
- `POST /:id/scaffoldings/:scaffoldingId/respond` - 응답 저장
- `POST /:id/event` - 이벤트 로깅

### 채팅 (`/api/chat`)
- `POST /sessions` - 세션 생성
- `GET /sessions/:id` - 세션 조회
- `POST /sessions/:id/messages` - 메시지 전송

### 관리자 (`/api/admin`)
- **사용자**: `GET /users`, `PUT /users/:id/role`, `PUT /users/:id/activate`
- **비디오**: `POST /videos`, `PUT /videos/:id`, `DELETE /videos/:id`
- **스캐폴딩**: `POST /videos/:id/scaffoldings`, `PUT /scaffoldings/:id`
- **프롬프트**: `GET /prompts`, `POST /prompts`, `PUT /prompts/:id`, `DELETE /prompts/:id`

### 로그 (`/api/logs`)
- `GET /events` - 이벤트 로그 조회
- `GET /events/export` - CSV 다운로드
- `GET /chat-sessions/export` - 채팅 로그 CSV
- `GET /stats` - 통계 정보

## 요약 기반 맥락 유지

세션의 누적 토큰이 3,500 초과 시:
1. 기존 대화 중 오래된 메시지를 요약
2. 요약문을 system 메시지로 삽입
3. 최근 5-8턴만 전체 내용 전달
4. 요약문은 PostgreSQL `chat_sessions.summary`에 저장

## 환경 변수

### Backend
```bash
# 데이터베이스
DATABASE_URL=postgresql://user:password@host:5432/dbname

# 보안
SECRET_KEY=your-secret-key-min-32-chars
JWT_SECRET_KEY=your-jwt-secret-key

# OpenAI
OPENAI_API_KEY=sk-your-api-key
MODEL_NAME=gpt-4o-mini

# 옵션
DAILY_TOKEN_LIMIT=50000
```

### Frontend
```bash
VITE_API_URL=http://localhost:8080/api
```

## 보안

- 비밀번호: bcrypt 해싱
- API 인증: JWT (Bearer Token)
- CORS: Flask-CORS 설정
- SQL Injection: SQLAlchemy ORM 사용

## 라이센스

MIT License
