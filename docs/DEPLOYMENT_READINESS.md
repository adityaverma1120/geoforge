# GeoForge Deployment & Production Readiness Guide

> **Document:** `DEPLOYMENT_READINESS.md`  
> **Status:** Verified Active Architecture  
> **Target System:** Windows 11 / Linux (Ubuntu 22.04 LTS / 24.04 LTS)  
> **Hardware Target:** NVIDIA CUDA GPU (e.g., RTX 3050 6 GB VRAM, 16 GB System RAM, Intel Core i5-13450HX)  
> **Last Verified:** 2026-11-11

---

## 1. System Architecture Overview

GeoForge operates as a decoupled, two-tier client-server application optimized for compute-heavy photogrammetric workloads:

```
[ Client Browser / WebGL 2.0 ]
         │
         │ HTTP/REST (Port 3000 / Production CDN)
         ▼
[ Frontend: React 19 + Vite + Three.js ]
         │
         │ REST API (Upload, Status Polling, Binary GLB Download)
         ▼
[ Backend: FastAPI + Uvicorn (Port 8000) ]
         │
         ├── [ SQLite Job Store (jobs.db) ]
         ├── [ OpenCV Video Ingestion & Filtering ]
         ├── [ COLMAP 3.9.1 CLI (CUDA SIFT, SfM & Dense MVS) ]
         ├── [ Open3D Poisson Mesher (Trim 7.0%) ]
         └── [ Trimesh / Pillow GLB Exporter ]
```

---

## 2. Hardware & Infrastructure Requirements

### 2.1 Hardware Specifications

| Component | Minimum Specification | Recommended Specification | Verified In-House Profile |
|---|---|---|---|
| **GPU** | NVIDIA GPU with CUDA Compute Capability $\ge 6.0$, 4 GB VRAM | NVIDIA RTX 3060 / 4060 or higher, 8–12 GB VRAM | NVIDIA GeForce RTX 3050 Laptop GPU (6 GB VRAM) |
| **CPU** | 4 Cores, 8 Threads (x86_64) | 8 Cores, 16 Threads (Intel Gen 12+ / AMD Zen 3+) | Intel Core i5-13450HX (10 Cores, 16 Threads) |
| **System RAM** | 16 GB DDR4/DDR5 | 32 GB DDR5 | 16 GB DDR5 |
| **Storage** | 50 GB Free NVMe SSD | 250 GB NVMe SSD (High IOPS) | 512 GB NVMe SSD |
| **OS** | Windows 10/11 64-bit or Ubuntu 22.04 LTS | Windows 11 Pro 64-bit or Ubuntu 24.04 LTS | Windows 11 Home 64-bit (Build 26100) |

### 2.2 Storage & I/O Lifecycle Considerations
Photogrammetry generates substantial intermediate artifacts during dense stereo matching:
- **Raw Video Ingestion:** Stored in `backend/uploads/{job_id}_{filename}` (Typically 20–200 MB).
- **Extracted Frames:** Stored in `backend/temp/{job_id}/frames/` (~100–300 JPEG frames, ~50–150 MB).
- **COLMAP Workspace:** Stored in `backend/temp/{job_id}/colmap/`.
  - Feature database (`database.db`): ~20–80 MB.
  - Undistorted stereo images: ~150–400 MB.
  - Depth and normal maps (`stereo/depth_maps/`, `stereo/normal_maps/`): 500 MB – 2.5 GB.
  - Dense point cloud (`fused.ply`): 10–60 MB.
  - Poisson mesh (`meshed-poisson.ply`): 5–25 MB.
  - Binary GLB model (`model.glb`): 2–15 MB.
- **Disk Space Provisioning:** Plan for **3 to 5 GB of temporary disk space per concurrent active job**. The automated storage manager removes intermediate workspaces upon job completion or failure if configured.

---

## 3. Frontend Deployment Specifications

### 3.1 Production Build Pipeline
The React 19 frontend is bundled into a high-performance static SPA using Vite:

```powershell
cd frontend
npm run build
```

This compiles optimized bundles to `frontend/dist/`:
- `index.html` (Static entrypoint)
- `assets/index-[hash].js` (Code-split Three.js, Lucide, Motion, React)
- `assets/index-[hash].css` (Tailwind CSS v4 stylesheet)

### 3.2 Hosting Options
1. **Static Web Server (Nginx / Caddy / Apache):**
   - Serve `dist/` directly.
   - Configure fallback routing (`try_files $uri /index.html;`) to support React routing.
2. **Edge Platforms (Vercel, Netlify, Cloudflare Pages):**
   - Framework preset: `Vite`.
   - Build command: `npm run build`.
   - Output directory: `dist`.
   - Environment variable: `VITE_API_URL=https://api.yourdomain.com`.

### 3.3 CORS Configuration
If frontend and backend are hosted on separate origins (e.g., `https://geoforge.app` and `https://api.geoforge.app`):
- Ensure `backend/main.py` CORS middleware allows the frontend domain:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["https://geoforge.app", "http://localhost:3000"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```

---

## 4. Backend Deployment Specifications

### 4.1 Process Management & Supervision
The FastAPI application should be run with a production ASGI supervisor.

**Development / Local Production Mode:**
```powershell
& ".\.venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
```

> [!IMPORTANT]
> **Single Worker Concurrency Constraint (`--workers 1`):**  
> Photogrammetric reconstruction is heavily GPU/VRAM bound. Running multiple ASGI worker processes will spawn parallel COLMAP processes that compete for GPU VRAM and crash with CUDA Out-Of-Memory (`CUDA error: out of memory`). The backend enforces `MAX_CONCURRENT_RECONSTRUCTIONS = 1` via a `ThreadPoolExecutor(max_workers=1)`. Keep Uvicorn at `--workers 1`.

**Windows Service Deployment (NSSM):**
To run GeoForge backend as a continuous Windows Service:
```powershell
nssm install GeoForgeBackend "C:\Users\adity\Downloads\geoforge-main\.venv\Scripts\python.exe" "-m uvicorn main:app --app-dir C:\Users\adity\Downloads\geoforge-main\geoforge-main\backend --host 0.0.0.0 --port 8000 --workers 1"
nssm set GeoForgeBackend AppDirectory "C:\Users\adity\Downloads\geoforge-main\geoforge-main\backend"
nssm start GeoForgeBackend
```

**Linux Production Deployment (Systemd):**
```ini
[Unit]
Description=GeoForge Photogrammetry Backend
After=network.target

[Service]
User=geoforge
WorkingDirectory=/opt/geoforge/backend
Environment="PATH=/opt/geoforge/venv/bin:/usr/local/bin"
EnvironmentFile=/opt/geoforge/backend/.env
ExecStart=/opt/geoforge/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

## 5. Configuration & Environment Variables

All settings are configured via `backend/.env` or system environment variables:

| Variable | Type | Default Value | Description |
|---|---|---|---|
| `COLMAP_EXE` | `str` | `C:\Users\adity\AppData\Local\Programs\COLMAP\bin\colmap.exe` | Absolute path to COLMAP binary |
| `COLMAP_VOCAB_TREE` | `str` | Colocated `vocab_tree_flickr100k_words32k.bin` | Path to visual vocabulary tree for fast indexing |
| `FFMPEG_EXE` | `str` | `C:\Users\adity\AppData\Local\Programs\ffmpeg\bin\ffmpeg.exe` | Absolute path to FFmpeg binary |
| `HOST` | `str` | `0.0.0.0` | Network binding interface |
| `PORT` | `int` | `8000` | Backend HTTP listening port |
| `DATABASE_PATH` | `str` | `backend/jobs.db` | SQLite database file path |
| `MAX_UPLOAD_BYTES` | `int` | `4294967296` (4 GiB) | Maximum allowed video file size |
| `MAX_CONCURRENT_JOBS` | `int` | `1` | Maximum simultaneous COLMAP pipelines |

---

## 6. Pre-Flight Health & Verification Checklist

Before accepting live traffic, verify the deployment:

1. **API Health Probe:**
   ```powershell
   Invoke-RestMethod -Uri "http://localhost:8000/health"
   ```
   **Expected Response:**
   ```json
   {
     "status": "healthy",
     "colmap": "COLMAP 3.9.1 (CUDA)",
     "ffmpeg": "available",
     "storage": { "disk_free_gb": 128.45 },
     "queue": { "active_reconstructions": 0, "max_concurrent": 1 },
     "reconstruction_ready": true
   }
   ```

2. **Frontend Accessibility:**
   Verify `http://localhost:3000` renders the GeoForge landing page without JavaScript errors in browser DevTools.

3. **Storage Write Permissions:**
   Ensure `backend/uploads/` and `backend/temp/` are writable by the application user.

4. **CUDA Device Query:**
   Verify NVIDIA drivers are accessible:
   ```powershell
   nvidia-smi
   ```

---

## 7. Operational Runbook & Maintenance

### 7.1 Clearing Temp Workspaces
To clear completed job workspaces older than 24 hours:
```powershell
# PowerShell cleanup script
$tempDir = "C:\Users\adity\Downloads\geoforge-main\geoforge-main\backend\temp"
Get-ChildItem -Path $tempDir -Directory | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-1) } | Remove-Item -Recurse -Force
```

### 7.2 Database Maintenance
SQLite `jobs.db` uses WAL mode with automatic busy timeouts. To compact the database periodically:
```powershell
sqlite3 jobs.db "VACUUM;"
```
