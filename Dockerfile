# Multi-stage build: frontend -> backend runtime

# 1) Frontend build
FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* frontend/pnpm-lock.yaml* ./
RUN npm install --no-audit --no-fund || true
COPY frontend/ ./
RUN npm run build

# 2) Backend build
FROM python:3.11-slim AS backend
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ ./backend/

# Copy frontend dist into backend static mount path
COPY --from=frontend /app/frontend/dist ./frontend_dist

# 3) Runtime image
FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8080 \
    APP_OUTPUT_DIR_BASE=/data \
    APP_FRONTEND_DIST_DIR=/app/frontend_dist
WORKDIR /app
COPY --from=backend /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=backend /usr/local/bin /usr/local/bin
COPY --from=backend /app/backend /app/backend
COPY --from=backend /app/frontend_dist /app/frontend_dist
VOLUME ["/data"]
EXPOSE 8080
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
