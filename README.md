# VCBL 학습 플랫폼

YouTube 기반 학습에 AI 챗봇을 결합한 웹 플랫폼입니다. 동영상 시청과 스캐폴딩(유도 질문), 대화형 챗봇을 통해 학습을 지원하며, 관리자 기능과 연구용 로그 수집을 제공합니다.

## 주요 기능

- **사용자 관리**: 학번 기반 가입/로그인, 권한 계층(`super` > `admin` > `user`)
- **학습 인터페이스**: 동영상 + 스캐폴딩 + 챗봇
- **AI 챗봇**: OpenAI 모델 연동, 요약 기반 컨텍스트 유지로 비용/성능 최적화
- **관리자 도구**: 사용자/비디오/스캐폴딩/프롬프트 관리
- **연구 로그**: 이벤트/채팅 로그 조회 및 CSV 내보내기

## 아키텍처 개요

- **Backend (Flask)**: REST API, JWT 인증, SQLAlchemy ORM, 레이트 리밋, OpenAI 연동, Pydantic/Marshmallow 검증, 표준화된 응답/에러 처리
- **Frontend (React)**: Vite 기반 SPA, React Router, Axios 인터셉터로 JWT 자동 주입, Tailwind UI

헬스 체크: `GET /health`, `GET /api/health`

## 기술 스택(주요 패키지)

- Backend: Flask, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-CORS, Flask-Limiter, Flask-Migrate, openai, tiktoken, pydantic, marshmallow, redis, psycopg2-binary, gunicorn
- Frontend: React, Vite, react-router-dom, axios, tailwindcss, framer-motion, lucide-react, @uiw/react-codemirror, dompurify, react-youtube

## 프로젝트 구조

```
vcbl-chatbot/
├── backend/
│   ├── app/
│   │   ├── models/                 # SQLAlchemy 모델
│   │   ├── routes/                 # API 라우트(auth, videos, chat, admin, logs, surveys)
│   │   ├── services/               # 비즈니스 로직(OpenAI, chat, video, user, survey 등)
│   │   ├── validators/             # Pydantic/Marshmallow 검증 스키마
│   │   └── utils/                  # 로깅/에러/데코레이터/응답 헬퍼
│   ├── migrations/                 # Alembic 마이그레이션
│   └── run.py                      # 앱 진입점
├── frontend/
│   ├── src/
│   │   ├── components/             # 재사용 컴포넌트
│   │   ├── pages/                  # 페이지 컴포넌트
│   │   ├── hooks/                  # 도메인 훅(useChat/useVideo/useScaffolding)
│   │   ├── contexts/               # AuthContext
│   │   └── services/               # Axios API 클라이언트
├── config/                          # Nginx 설정
├── scripts/                         # 배포/운영 스크립트
├── Dockerfile
├── docker-compose.yml
└── cloudbuild.yaml
```

## 데이터 개념(요약)

- `users`: 사용자/권한/토큰 사용량
- `videos`: 동영상 메타데이터, 썸네일, 순서, 스캐폴딩 모드
- `chat_sessions`: 세션 요약/토큰/비용 누적
- `chat_messages`: 대화 메시지(프롬프트/컴플리션/총 토큰)
- `chat_prompt_templates`: 비디오/역할/기본 프롬프트
- `scaffoldings` + `scaffolding_responses`: 학습 질문과 사용자 응답
- `event_logs`: 사용자 이벤트(시청/응답/완료 등)

## API 개요

### 인증(`/api/auth`)

- `POST /register` 회원가입(사전 등록된 학번 기반)
- `POST /login` 로그인(JWT 발급)
- `GET /me` 현재 사용자 정보
- `POST /change-password` 비밀번호 변경
- `POST /password-reset-request` 비밀번호 재설정 요청(알림 로그)

### 비디오(`/api/videos`)

- `GET /` 비디오 목록(활성)
- `GET /:videoId` 비디오 상세(스캐폴딩 포함, 조회 이벤트 기록)
- `POST /:videoId/scaffoldings/:scaffoldingId/respond` 스캐폴딩 응답 저장
- `POST /:videoId/scaffoldings/respond-all` 여러 응답 일괄 저장
- `POST /:videoId/event` 임의 이벤트 기록

### 채팅(`/api/chat`)

- `POST /sessions` 세션 생성/조회(비디오 기준 단일 활성 세션)
- `GET /sessions/:sessionId` 세션 조회(메시지 포함)
- `POST /sessions/:sessionId/messages` 메시지 전송(AI 응답 생성/저장, 토큰/비용/요약 갱신)

### 관리자(`/api/admin`)

- 사용자: `GET /users`, `PUT /users/:id/role`, `PUT /users/:id/activate`, `POST /users/:id/reset-password`, `POST /users/pre-register`, `POST /users/bulk-register`
- 비디오: `GET /videos`, `POST /videos`, `PUT /videos/:id`, `DELETE /videos/:id`
- 스캐폴딩: `POST /videos/:id/scaffoldings`, `PUT /scaffoldings/:id`, `DELETE /scaffoldings/:id`
- 프롬프트: `GET /prompts`, `POST /prompts`, `PUT /prompts/:id`, `DELETE /prompts/:id`

### 로그(`/api/logs`)

- `GET /events` 이벤트 로그(페이지네이션/필터)
- `GET /events/export` 이벤트 로그 CSV
- `GET /chat-messages` 채팅 메시지 로그(+세션 메타)
- `GET /timeline` 세션 + 비디오 이벤트 통합 타임라인
- `GET /chat-sessions-grouped` 세션 단위 그룹 조회
- `GET /chat-sessions/export` 채팅 세션 CSV
- `GET /stats` 전체 통계(사용자/토큰/채팅/이벤트)

### 설문(`/api/surveys`)

- 관리자: `POST /`, `PUT /:surveyId`, `DELETE /:surveyId`, `GET /`(activeOnly), `POST /:surveyId/questions`, `PUT /:surveyId/questions/:questionId`, `DELETE /:surveyId/questions/:questionId`, `POST /:surveyId/questions/reorder`, `GET /:surveyId/responses`, `GET /:surveyId/statistics`
- 사용자: `GET /registration` 가입 후 설문 목록(+완료 여부), `GET /:surveyId`, `POST /:surveyId/responses`, `GET /:surveyId/responses/my`

## OpenAI 연동 및 요약 전략

- 모델: 기본 `gpt-4o-mini`
- 토큰 관리: `tiktoken`으로 컨텍스트 토큰 산정, 요청/응답 토큰을 합산하여 사용자/세션에 누적
- 요약 트리거: 세션 누적 토큰이 임계치(`SUMMARY_TRIGGER_TOKENS`) 초과 시 오래된 대화 요약 → system 메시지로 삽입 → 최근 대화만 전체 전달
- 비용 산정: 프롬프트/컴플리션 토큰을 기반으로 비용 계산 및 세션에 누적

## 보안/운영 정책

- 인증: JWT(Bearer) 기반, 보호 라우트에 `@jwt_required()` 적용
- 권한: `admin_required`/`super_admin_required` 데코레이터로 관리자 경로 보호
- 입력 검증: Pydantic/Marshmallow 스키마 기반의 본문 검증, 민감 필드 마스킹 로깅
- CORS: 허용 오리진 제한, 인증 헤더 허용
- 레이트 리밋: 민감 엔드포인트에 분당 호출 제한(환경별 on/off)
- 표준 응답: `success_response`/`error_response` 일관 포맷, 전역 에러 핸들러

## 환경 변수(핵심)

Backend

```
SECRET_KEY=...
JWT_SECRET_KEY=...
OPENAI_API_KEY=...
MODEL_NAME=gpt-4o-mini
DATABASE_URL=postgresql+psycopg2://user:password@host:5432/db
# 또는 CLOUD_SQL_INSTANCE 사용 시 DB_USER/DB_PASSWORD/DB_NAME와 조합
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
RATELIMIT_STORAGE_URL=memory://
DAILY_TOKEN_LIMIT=50000
SUMMARY_TRIGGER_TOKENS=3500
```

Frontend

```
VITE_API_URL=http://localhost:8080/api
```

## 라이선스

MIT License
