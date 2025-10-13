# Full-stack Dockerfile (Backend + Frontend)
FROM python:3.11-slim AS backend-builder

WORKDIR /backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy and install backend dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Frontend build stage
FROM node:18-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

# Final production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Copy backend
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /backend /app/backend

# Copy frontend build
COPY --from=frontend-builder /frontend/dist /app/frontend/dist

# Copy nginx config
COPY config/nginx-full.conf /etc/nginx/sites-available/default

# Expose port
ENV PORT=8080
EXPOSE 8080

# Start script
COPY scripts/start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]

