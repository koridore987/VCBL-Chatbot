# VCBL Chatbot

AI 보조 학습(동영상 + 스캐폴딩 + 챗봇)을 위한 웹 애플리케이션입니다.

## 배포(Cloud Run)

```bash
# 1) GCP 프로젝트 설정 (필요 시 변경)
export GCP_PROJECT_ID="your-project-id"
gcloud config set project "$GCP_PROJECT_ID"

# 2) 통합 배포 스크립트 실행 (빠른 배포 또는 전체 설정)
./scripts/deploy_setup.sh --quick
# 또는
./scripts/deploy_setup.sh --full-setup

# 3) 배포 상태/URL 확인 (스크립트 출력 참고)
gcloud run services describe vcbl-chatbot \
  --region=asia-northeast3 \
  --format="value(status.url)"
```

### 환경 변수(요약)
- 필수 시크릿: `SECRET_KEY`, `JWT_SECRET_KEY`, `OPENAI_API_KEY`, `DATABASE_URL`
- 권장 환경변수: `MODEL_NAME`, `DAILY_TOKEN_LIMIT`, `SUMMARY_TRIGGER_TOKENS`, `MAX_TOKENS_PER_REQUEST`, `MAX_TOKENS_OUTPUT`, `OPENAI_TIMEOUT`, `OPENAI_MAX_RETRIES`, `LOG_LEVEL`
- 예시는 `docs/env.example` 참고

## 프로젝트 구조 (요약)

```
backend/    # Flask API (JWT, SQLAlchemy, Migrate, OpenAI)
frontend/   # React/Vite SPA
config/     # Nginx (nginx-cloud.conf)
scripts/    # 배포/운영 스크립트 (deploy_setup.sh)
Dockerfile  # Cloud Run용 컨테이너 (nginx + gunicorn)
docker-compose.yml
```

## 헬스 체크

- `GET /health`
- `GET /api/health`

## 라이선스

MIT
