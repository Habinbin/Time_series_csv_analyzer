# ─────────────────────────────────────────────────────────────
# Stage 1: SvelteKit 프론트엔드 빌드
# ─────────────────────────────────────────────────────────────
FROM node:22-alpine AS frontend-builder

WORKDIR /build/frontend

# 의존성 캐싱을 위해 package 파일 먼저 복사
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install --frozen-lockfile

# 소스 복사 후 빌드
COPY frontend/ ./
RUN pnpm build

# ─────────────────────────────────────────────────────────────
# Stage 2: Python 최종 이미지
# ─────────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY backend/pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir "fastapi>=0.135.3" "uvicorn>=0.44.0" "lttb>=0.3.1" "pandas>=3.0.1" "python-multipart"

# 백엔드 소스 복사
COPY backend/ ./backend/

# Stage 1에서 빌드된 프론트엔드 결과물 복사
COPY --from=frontend-builder /build/frontend/build ./frontend/build

# SQLite DB 복사 (백엔드 디렉토리 기준 경로와 맞춤)
# backend/simulation_results.sqlite → /app/backend/simulation_results.sqlite
# (service.py가 참조하는 경로 그대로 유지)

# Railway는 PORT 환경변수를 자동으로 설정함
ENV PORT=8000

EXPOSE 8000

# 백엔드 디렉토리에서 실행 (features/ 모듈 경로 유지)
CMD ["sh", "-c", "cd /app/backend && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
