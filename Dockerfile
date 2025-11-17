# Multi-stage build for production deployment with uv
# Stage 1: Build frontend
FROM node:18-slim AS frontend-builder

WORKDIR /app

# Install CA certificates and Elm compiler
RUN apt-get update && \
    apt-get install -y ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    npm install -g elm@latest-0.19.1

# Copy frontend dependency files first to leverage layer caching
COPY elm.json package*.json vite.config.js index.html ./

# Pre-fetch Elm packages
RUN elm make --help || true

# Copy frontend source
COPY src/ ./src/

# Install dependencies and build frontend
RUN npm ci && npm run build

# Stage 2: Python backend with uv
FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application into the container
WORKDIR /app

# Copy Python project files
COPY pyproject.toml ./
COPY backend/ ./backend/

# Copy database.py to root for imports
COPY backend/database.py ./database.py

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/dist ./static

# Install dependencies with uv (creates .venv)
RUN uv sync --no-cache

# Create data directory
RUN mkdir -p /data
ENV DATA=/data

# Set port for Fly.io
ENV PORT=8080
EXPOSE 8080

# Set PYTHONPATH so database.py can be imported
ENV PYTHONPATH=/app

# Run the application using uv's virtual environment
CMD ["/app/.venv/bin/uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
