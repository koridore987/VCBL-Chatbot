# VCBL 학습 플랫폼 (Video-based Chatbot Learning Platform)

Flask + React + PostgreSQL 기반의 온라인 학습 플랫폼으로, YouTube 동영상 학습과 AI 챗봇(ChatGPT)을 통한 학습 지원, 스캐폴딩 기능을 제공합니다.

## 주요 기능

### 1. 사용자 관리
- 학번 기반 로그인 및 회원가입
- bcrypt 암호화를 통한 안전한 비밀번호 저장
- 권한 계층: `super` > `admin` > `user`
- 관리자 승인 방식의 비밀번호 재설정

### 2. 학습 인터페이스
- **좌측 (2/3)**: YouTube 동영상 임베드
- **우측 (1/3)**: 스캐폴딩 영역
  - 질문 프롬프트 응답 작성형
  - ChatGPT 대화형

### 3. ChatGPT 연동 (gpt-4o-mini)
- **요약 기반 맥락 유지 (Summary Carry-over)**
  - 세션 토큰 3,500 초과 시 자동 요약 생성
  - 요약문 + 최근 5-8턴만 전달
  - PostgreSQL에 요약 저장
- 일일 토큰 한도: 50,000 토큰
- 모든 대화 기록 및 비용 추적

### 4. 관리자 기능
- 사용자 관리 (권한 변경, 활성화/비활성화)
- 비디오 및 스캐폴딩 관리
- **프롬프트 엔지니어링**
  - 시스템 프롬프트 수정 및 버전 관리
  - 비디오별/권한별 프롬프트 지정
  - 코드 에디터 UI 제공
- 로그 관리 및 CSV 다운로드

### 5. 연구 데이터 관리
- 모든 사용자 이벤트 로깅
- CSV 다운로드 지원
- 익명화 없이 영구 보존

## 기술 스택

### Backend
- **Framework**: Flask 3.0
- **ORM**: SQLAlchemy
- **Database**: PostgreSQL
- **Authentication**: Flask-JWT-Extended
- **AI**: OpenAI API (gpt-4o-mini)

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite 5
- **Routing**: React Router 6
- **HTTP Client**: Axios
- **Code Editor**: CodeMirror (프롬프트 편집용)
- **Video**: react-youtube

### Deployment
- **Container**: Docker
- **Cloud**: Google Cloud Run
- **CI/CD**: GitHub Actions
- **Reverse Proxy**: Nginx

## 프로젝트 구조

```
VCBL-Chatbot/
├── backend/                    # Flask API 서버
│   ├── app/
│   │   ├── __init__.py        # Flask 앱 초기화
│   │   ├── models/            # SQLAlchemy 모델
│   │   │   ├── user.py
│   │   │   ├── video.py
│   │   │   ├── chat_session.py
│   │   │   ├── chat_message.py
│   │   │   ├── chat_prompt_template.py
│   │   │   ├── event_log.py
│   │   │   └── scaffolding.py
│   │   ├── routes/            # API 라우트
│   │   │   ├── auth.py
│   │   │   ├── videos.py
│   │   │   ├── chat.py
│   │   │   ├── admin.py
│   │   │   └── logs.py
│   │   └── services/          # 비즈니스 로직
│   │       └── openai_service.py
│   ├── requirements.txt
│   └── run.py
├── frontend/                   # React 웹앱
│   ├── src/
│   │   ├── components/
│   │   ├── contexts/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── config/                     # 설정 파일
│   ├── nginx.conf
│   └── nginx-full.conf
├── scripts/                    # 유틸리티 스크립트
│   ├── start.sh
│   ├── init-db.sh
│   ├── create-admin.sh
│   └── create-default-prompt.sh
├── .github/workflows/          # CI/CD 파이프라인
│   ├── deploy.yml
│   └── ci.yml
├── Dockerfile                  # 통합 Dockerfile
├── Dockerfile.backend          # Backend 전용
├── Dockerfile.frontend         # Frontend 전용
├── docker-compose.yml
└── README.md
```

## 설치 및 실행

### 1. 환경 변수 설정

```bash
# Backend
cp backend/env.example backend/.env
# DATABASE_URL, SECRET_KEY, OPENAI_API_KEY 설정

# Frontend
cp frontend/env.example frontend/.env
# VITE_API_URL 설정
```

### 2. Docker Compose로 실행

```bash
# 모든 서비스 시작 (PostgreSQL + Backend + Frontend)
docker-compose up -d

# 데이터베이스 초기화
docker-compose exec backend flask db upgrade

# Super Admin 생성
docker-compose exec backend bash /app/scripts/create-admin.sh admin001 "관리자" admin123

# 기본 프롬프트 생성
docker-compose exec backend bash /app/scripts/create-default-prompt.sh
```

### 3. 로컬 개발 환경

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 데이터베이스 마이그레이션
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# 서버 실행
python run.py
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 데이터베이스 스키마

### users
- 사용자 정보, 권한, 토큰 사용량 추적

### videos
- 비디오 정보, YouTube ID, 스캐폴딩 모드

### chat_sessions
- 채팅 세션, 요약문, 토큰 사용량

### chat_messages
- 개별 메시지, role(user/assistant/system), 토큰 정보

### chat_prompt_templates
- 시스템 프롬프트, 버전 관리, 비디오/권한별 지정

### scaffoldings
- 학습 질문 프롬프트

### scaffolding_responses
- 사용자의 질문 응답

### event_logs
- 모든 사용자 이벤트 (동영상 재생, 일시정지, 채팅 등)

## API 엔드포인트

### 인증 (`/api/auth`)
- `POST /register` - 회원가입
- `POST /login` - 로그인
- `GET /me` - 현재 사용자 정보
- `POST /change-password` - 비밀번호 변경

### 비디오 (`/api/videos`)
- `GET /` - 비디오 목록
- `GET /:id` - 비디오 상세 (스캐폴딩 포함)
- `POST /:id/scaffoldings/:scaffoldingId/respond` - 스캐폴딩 응답 저장
- `POST /:id/event` - 이벤트 로깅

### 채팅 (`/api/chat`)
- `POST /sessions` - 채팅 세션 생성
- `GET /sessions/:id` - 세션 조회
- `POST /sessions/:id/messages` - 메시지 전송

### 관리자 (`/api/admin`) [관리자 권한 필요]
- **사용자**: `GET /users`, `PUT /users/:id/role`, `PUT /users/:id/activate`
- **비디오**: `POST /videos`, `PUT /videos/:id`, `DELETE /videos/:id`
- **스캐폴딩**: `POST /videos/:id/scaffoldings`, `PUT /scaffoldings/:id`
- **프롬프트**: `GET /prompts`, `POST /prompts`, `PUT /prompts/:id`, `DELETE /prompts/:id`

### 로그 (`/api/logs`) [관리자 권한 필요]
- `GET /events` - 이벤트 로그 조회
- `GET /events/export` - CSV 다운로드
- `GET /chat-sessions/export` - 채팅 로그 CSV
- `GET /stats` - 통계 정보

## Cloud Run 배포

### 1. GitHub Secrets 설정

Repository Settings > Secrets and variables > Actions에서 다음 설정:

- `GCP_PROJECT_ID`: GCP 프로젝트 ID
- `GCP_SA_KEY`: GCP Service Account JSON 키
- `CLOUD_RUN_REGION`: 리전 (예: asia-northeast3)
- `DATABASE_URL`: PostgreSQL 연결 URL
- `SECRET_KEY`: Flask 시크릿 키
- `OPENAI_API_KEY`: OpenAI API 키

### 2. 자동 배포

```bash
# main 브랜치에 푸시하면 자동 배포
git push origin main

# develop 브랜치는 스테이징 환경 배포
git push origin develop
```

## 요약 기반 맥락 유지 (Summary Carry-over)

### 동작 원리

1. 세션의 누적 토큰이 3,500 초과 시 자동 요약 생성
2. 기존 대화 중 오래된 메시지를 요약
3. 요약문을 system 메시지로 삽입
4. 최근 5-8턴만 전체 내용 전달
5. 요약문은 PostgreSQL `chat_sessions.summary`에 저장

### 예시

```
시스템: [기본 프롬프트]
시스템: 이전 대화 요약: [요약문]
유저: [최근 5턴]
AI: [최근 5턴]
유저: [새 질문]
```

## 프롬프트 엔지니어링

관리자는 `/admin/prompts`에서 시스템 프롬프트를 관리할 수 있습니다.

### 프롬프트 우선순위

1. 비디오 전용 프롬프트
2. 권한별 프롬프트
3. 기본 프롬프트

### 버전 관리

- 프롬프트 수정 시 자동으로 버전 증가
- 이전 버전으로 롤백 가능 (데이터베이스에 기록 유지)

## 로깅 및 연구 데이터

모든 사용자 활동이 기록됩니다:

- 동영상 재생/일시정지/탐색
- 채팅 메시지 (입력/출력)
- 스캐폴딩 응답
- 로그인/로그아웃

관리자는 CSV로 다운로드하여 연구 데이터로 활용할 수 있습니다.

## 보안

- 비밀번호: bcrypt 해싱
- API 인증: JWT (Bearer Token)
- CORS: Flask-CORS로 설정
- SQL Injection: SQLAlchemy ORM 사용

## 성능 최적화

- 프론트엔드: Vite 빌드 최적화, 코드 스플리팅
- 백엔드: Gunicorn 멀티워커
- 데이터베이스: 인덱스 설정 (user_id, video_id, created_at 등)
- Cloud Run: 최소 1개 인스턴스 유지, 자동 스케일링

## 라이센스

MIT License

## 문의

프로젝트 관련 문의사항은 이슈를 등록해주세요.

