# Google Cloud Run용 Dockerfile
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 포트 노출 (Google Cloud Run은 PORT 환경변수 사용)
EXPOSE 8080

# 환경변수 설정
ENV FLASK_ENV=production
ENV PORT=8080

# Google Cloud Run용 실행 명령
# PORT 환경변수를 사용하여 동적 포트 바인딩
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 4 --worker-class gevent --worker-connections 1000 --timeout 0 --keep-alive 2 --max-requests 1000 --max-requests-jitter 100 run:app
