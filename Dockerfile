# Backend-focused Dockerfile (Gunicorn-only for Cloud Run)
FROM python:3.11-slim AS backend-builder

WORKDIR /app

# 시스템 의존성 설치 (컴파일 및 PostgreSQL 클라이언트 헤더)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY backend/ ./backend/

# 최종 이미지는 런타임 의존성만 포함
FROM python:3.11-slim

WORKDIR /app

# 런타임에 필요한 라이브러리만 설치
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지와 실행 파일 복사
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# 애플리케이션 코드 복사
COPY --from=backend-builder /app/backend /app/backend

# Cloud Run 포트
ENV PORT=8080
EXPOSE 8080

# 작업 디렉토리를 backend로 변경
WORKDIR /app/backend

# Flask 앱 직접 실행
CMD ["python", "run.py"]
