# GeoForge Production Environment Configuration & Container Specification

> **Document:** `PRODUCTION_ENVIRONMENT_CONFIGURATION.md`  
> **Status:** Configuration Contract & Deployment Specification (Phase 8 Planning)  
> **Target Version:** GeoForge v1.1.0 Cloud Architecture  
> **Author:** Antigravity Engineering Team  
> **Last Verified:** 2026-11-14  
> **Related Documents:** [`docs/PHASE_8_DEPLOYMENT_STRATEGY.md`](PHASE_8_DEPLOYMENT_STRATEGY.md), [`docs/CLOUD_ARCHITECTURE.md`](CLOUD_ARCHITECTURE.md), [`docs/DEPLOYMENT_IMPLEMENTATION_ROADMAP.md`](DEPLOYMENT_IMPLEMENTATION_ROADMAP.md)

---

## 1. Environment Variables Specification

Production deployments separate frontend and backend configurations using environment variables. **No secrets or production credentials are ever committed to the repository.**

### 1.1 Backend Production Environment Variables (`backend/.env.production`)

```bash
# ============================================================
# GEOFORGE BACKEND PRODUCTION CONFIGURATION
# ============================================================

# --- Server & Networking ---
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production
LOG_LEVEL=INFO

# --- CORS & Origins (Comma-separated) ---
# Set to the exact deployed frontend URL on Cloudflare Pages
ALLOWED_ORIGINS=https://geoforge.pages.dev,https://geoforge.app

# --- Database Connection ---
# If using Railway Persistent Volume SQLite:
DATABASE_URL=sqlite:////data/jobs.db
# If using Supabase / Hosted PostgreSQL:
# DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres

# --- Cloudflare R2 / S3 Object Storage ---
S3_ENDPOINT_URL=https://<CLOUDFLARE_ACCOUNT_ID>.r2.cloudflarestorage.com
S3_ACCESS_KEY_ID=<R2_ACCESS_KEY_ID>
S3_SECRET_ACCESS_KEY=<R2_SECRET_ACCESS_KEY>
S3_BUCKET_NAME=geoforge-production
S3_PUBLIC_DOMAIN=https://assets.geoforge.app

# --- Reconstruction Compute Worker ---
# Mode: "local" (in-process for staging) or "runpod_serverless" (decoupled cloud)
WORKER_MODE=runpod_serverless
RUNPOD_API_KEY=<RUNPOD_API_KEY>
RUNPOD_ENDPOINT_ID=<RUNPOD_ENDPOINT_ID>
COLMAP_EXE=/usr/local/bin/colmap

# --- Concurrency & Quotas ---
MAX_CONCURRENT_RECONSTRUCTIONS=2
MAX_UPLOAD_BYTES=524288000           # 500 MB public web limit
DAILY_RECONSTRUCTION_LIMIT=25        # Abuse prevention ceiling
JOB_RETENTION_DAYS=14                # Auto-cleanup raw uploads after 14 days
```

### 1.2 Frontend Production Environment Variables (`frontend/.env.production`)

```bash
# ============================================================
# GEOFORGE FRONTEND PRODUCTION CONFIGURATION
# ============================================================

# Target Backend API URL (Bakes into Vite build at deploy time)
VITE_API_URL=https://api.geoforge.app

# Application Metadata
VITE_APP_TITLE=GeoForge — Drone Video to 3D Model
VITE_APP_VERSION=1.1.0
```

---

## 2. Dockerfile Specifications

### 2.1 Backend API Container: `backend/Dockerfile.api`
*Purpose:* Ultra-lightweight, CPU-only container running FastAPI, request validation, database interactions, and task dispatch.

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm AS base

# Install system dependencies for OpenCV and networking
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source
COPY . .

# Ensure storage mount points exist
RUN mkdir -p /data /app/uploads /app/temp

# Non-root user for security
RUN useradd -m -u 1000 geoforge && chown -R geoforge:geoforge /app /data
USER geoforge

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### 2.2 GPU Reconstruction Worker Container: `backend/Dockerfile.worker`
*Purpose:* CUDA-enabled heavy worker running COLMAP 3.9.1, Open3D, and the 12-stage photogrammetric pipeline.

```dockerfile
# syntax=docker/dockerfile:1
FROM nvidia/cuda:12.2.2-runtime-ubuntu22.04 AS base

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install runtime dependencies for COLMAP, OpenCV, and Open3D
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.12 \
    python3-pip \
    ffmpeg \
    libgl1-mesa-glx \
    libgomp1 \
    libsuitesparse-dev \
    libglew2.2 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-compiled headless COLMAP 3.9.1 CUDA binaries
# In CI/CD, these are built in a builder stage or pulled from verified artifact cache
COPY --from=colmap-builder /usr/local/bin/colmap /usr/local/bin/colmap
COPY --from=colmap-builder /usr/local/share/colmap /usr/local/share/colmap

WORKDIR /worker

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run worker consumer process
CMD ["python3", "worker_daemon.py"]
```

---

## 3. Local/Cloud Staging Compose Specification (`docker-compose.prod.yml`)

```yaml
version: "3.8"

services:
  geoforge-api:
    build:
      context: ./backend
      dockerfile: Dockerfile.api
    container_name: geoforge-api
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - ALLOWED_ORIGINS=http://localhost:3000,https://geoforge.pages.dev
      - DATABASE_URL=sqlite:////data/jobs.db
    volumes:
      - geoforge-db-data:/data
    restart: unless-stopped

  geoforge-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: geoforge-frontend
    ports:
      - "3000:80"
    depends_on:
      - geoforge-api
    restart: unless-stopped

volumes:
  geoforge-db-data:
    driver: local
```

---

## 4. Reverse Proxy & CDN Rules (Nginx / Cloudflare)

### 4.1 Nginx Production Ingestion Headers
When routing public traffic through Nginx:

```nginx
# Handle large video streaming without buffering timeouts
client_max_body_size 500M;
client_body_buffer_size 128k;
client_body_timeout 300s;

proxy_read_timeout 300s;
proxy_connect_timeout 60s;
proxy_send_timeout 300s;

# Preserve client IP and protocol
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
```

### 4.2 Cloudflare CDN Rules for 3D GLB Streaming
- **Route:** `api.geoforge.app/model/*`
- **Cache-Control:** `public, max-age=86400, stale-while-revalidate=3600`
- **Content-Type:** `model/gltf-binary`
- **Range Requests:** `Accept-Ranges: bytes` enabled for partial downloads by Three.js GLTFLoader.

