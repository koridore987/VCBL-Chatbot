# VCBL Chatbot

AI 보조 학습(동영상 + 스캐폴딩 + 챗봇)을 위한 웹 애플리케이션입니다.

## 빠른 시작

```bash
# 1) 환경 변수 준비
cp .env.example .env
# 필수 값(SECRET_KEY, JWT_SECRET_KEY, OPENAI_API_KEY, DATABASE_URL) 입력

# 2) 로컬 실행 (Docker Compose)
docker-compose up -d

# 3) 마이그레이션 및 관리자 계정
docker-compose exec app flask db upgrade
docker-compose exec app flask init-admin

# 접속: http://localhost:8080
```

## 프로젝트 구조 (요약)

```
backend/    # Flask API (JWT, SQLAlchemy, Migrate, OpenAI)
frontend/   # React/Vite SPA
config/     # Nginx (nginx-cloud.conf)
scripts/    # 배포/운영 스크립트 (deploy-unified.sh, local-docker.sh)
Dockerfile  # Cloud Run용 컨테이너 (nginx + gunicorn)
docker-compose.yml
```

## 유용한 스크립트

- 로컬 프로덕션 테스트: `./scripts/local-docker.sh`
- 통합 배포 스크립트: `./scripts/deploy-unified.sh` (quick/full/interactive)

## 헬스 체크

- `GET /health`
- `GET /api/health`

## 라이선스

MIT
