# Full-stack Dockerfile (PostgreSQL + Google Cloud Run 최적화)
FROM python:3.11-slim AS backend-builder

WORKDIR /backend

# 시스템 의존성 설치 (PostgreSQL 클라이언트 라이브러리 포함)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 백엔드 의존성 설치
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 백엔드 코드 복사
COPY backend/ .

# 프론트엔드 빌드 단계
FROM node:18-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

# 최종 프로덕션 단계
FROM python:3.11-slim

WORKDIR /app

# 런타임 의존성 설치 (PostgreSQL 클라이언트 라이브러리 포함)
RUN apt-get update && apt-get install -y \
    nginx \
    libpq5 \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 백엔드 복사
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /backend /app/backend

# 프론트엔드 빌드 복사
COPY --from=frontend-builder /frontend/dist /app/frontend/dist

# nginx 설정 복사
COPY config/nginx-full.conf /etc/nginx/sites-available/default

# 포트 설정
ENV PORT=8080
EXPOSE 8080

# 시작 스크립트 복사
COPY scripts/start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]

