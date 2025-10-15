# syntax=docker/dockerfile:1.6
# ============================================
# Multi-arch, multi-stage Dockerfile for Cloud Run and local
# Frontend (React/Vite) + Backend (Flask/Gunicorn) + Nginx
# Works on linux/amd64 and linux/arm64
# ============================================

ARG TARGETPLATFORM=linux/amd64
ARG BUILDPLATFORM=linux/amd64

# ============================================
# Stage 1: Build Frontend
# ============================================
FROM --platform=$BUILDPLATFORM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install dependencies including devDependencies (needed for Vite build)
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build frontend for production
RUN npm run build

# ============================================
# Stage 2: Build Backend Dependencies
# ============================================
FROM --platform=$BUILDPLATFORM python:3.11-slim AS backend-builder

WORKDIR /app

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================
# Stage 3: Final Runtime Image
# ============================================
FROM --platform=$TARGETPLATFORM python:3.11-slim

WORKDIR /app

# Install runtime dependencies (Nginx, PostgreSQL client)
RUN apt-get update && apt-get install -y \
    nginx \
    libpq5 \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy backend application
COPY backend/ ./backend/

# Copy entrypoint script
COPY backend/entrypoint.sh /app/backend/entrypoint.sh
RUN chmod +x /app/backend/entrypoint.sh

# Copy frontend build output to Nginx directory
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

# Copy Nginx configuration
COPY config/nginx-cloud.conf /etc/nginx/sites-available/default

# Create supervisor configuration
RUN echo "[supervisord]\n\
nodaemon=true\n\
user=root\n\
\n\
[program:nginx]\n\
command=/usr/sbin/nginx -g 'daemon off;'\n\
autostart=true\n\
autorestart=true\n\
stdout_logfile=/dev/stdout\n\
stdout_logfile_maxbytes=0\n\
stderr_logfile=/dev/stderr\n\
stderr_logfile_maxbytes=0\n\
\n\
[program:gunicorn]\n\
command=gunicorn --bind 127.0.0.1:5000 --workers 2 --threads 4 --timeout 120 --access-logfile - --error-logfile - run:app\n\
directory=/app/backend\n\
autostart=true\n\
autorestart=true\n\
stdout_logfile=/dev/stdout\n\
stdout_logfile_maxbytes=0\n\
stderr_logfile=/dev/stderr\n\
stderr_logfile_maxbytes=0\n\
environment=PYTHONUNBUFFERED=1\n\
" > /etc/supervisor/conf.d/supervisord.conf

# Cloud Run expects the app to listen on $PORT (default 8080)
ENV PORT=8080
EXPOSE 8080

# Set working directory to backend for database migrations
WORKDIR /app/backend

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Start via entrypoint which runs migrations then supervisor (nginx + gunicorn)
CMD ["/app/backend/entrypoint.sh"]
