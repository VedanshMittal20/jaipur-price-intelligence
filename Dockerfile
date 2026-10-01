# Multi-stage production Dockerfile for Jaipur Price Intelligence Platform
# Follows ADR-1 (static-artifact serving) and ADR-3 (lean dependencies; no geopandas/shap)

# Stage 1: Build static React frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /web
COPY web/package.json ./
RUN npm install
COPY web/ ./
RUN npm run build

# Stage 2: Python lean serving runtime
FROM python:3.11-slim AS runner

# System dependencies for LightGBM
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install lean serving dependencies
COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy application code
COPY src/ /app/src/
COPY api/ /app/api/

# Copy model artifacts & precomputed data
COPY artifacts/ /app/artifacts/
COPY data/external/ /app/data/external/
COPY data/processed/listings_clean.parquet /app/data/processed/
COPY data/processed/features.parquet /app/data/processed/

# Copy compiled React static assets from Stage 1
COPY --from=frontend-builder /web/dist /app/web/dist

ENV PYTHONPATH="/app/src:/app"
ENV PORT=8000
EXPOSE 8000

# Lean single-worker uvicorn serving (preserves 512 MB memory budget)
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

