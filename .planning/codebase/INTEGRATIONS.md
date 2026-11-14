# External Integrations

**Analysis Date:** 2026-11-12

## APIs & External Services

**Photogrammetry Engine (Subprocess Binary):**
- **COLMAP 4.1.1 CLI (CUDA enabled):** External photogrammetry engine running locally via discrete subprocess commands.
  - Subcommands used: `feature_extractor`, `exhaustive_matcher`, `mapper`, `image_undistorter`, `patch_match_stereo`, `stereo_fusion`.
  - Path resolution: Environment variable `COLMAP_EXE` (e.g. `C:\Users\adity\Downloads\COLMAP-3.11.1-windows-cuda\bin\colmap.bat` or PATH).
  - Calling convention: Python `subprocess.run(args, capture_output=True, text=True, check=True)` without shell invocation to ensure space-safe path execution.

**Air-Gap & Defense Compliance:**
- **Zero Outbound Cloud APIs:** GeoForge is strictly designed for air-gapped, on-premise defense evaluations (NTRO / SIH 2026).
- **No Third-Party CDNs:** All frontend dependencies (Three.js, Lucide icons, fonts, CSS) are bundled locally into `frontend/dist`.
- **No External Cloud AI SDKs:** No outbound telemetry or remote LLM API calls are activated in production.

## Data Storage

**Databases:**
- **SQLite 3 (`backend/jobs.db`):**
  - Primary persistent data store for reconstruction job lifecycle states, stage progression, timestamps, and error messages.
  - Driver: Python standard library `sqlite3` with `check_same_thread=False` and thread-safe row factories (`backend/database.py`).
  - Schema: `jobs` table with primary key `job_id (TEXT)`, columns `filename`, `status`, `stage`, `progress_percent`, `stage_message`, `video_path`, `job_dir`, `model_path`, `result_json`, `error_message`, `created_at`, `updated_at`, `completed_at`.
  - Indexing: `idx_jobs_status` and `idx_jobs_created_at`.
  - Migration: Automatic schema recovery and column migration on startup (`backend/database.py:init_db()`).

**File Storage:**
- **Local File System Workspace:**
  - `backend/uploads/` — Raw uploaded drone/phone video files named `{job_id}_{sanitized_filename}`.
  - `backend/temp/{job_id}/` — Per-job isolated processing workspace:
    - `frames/` — Raw frames extracted at 2.0 FPS from video.
    - `selected_frames/` — Frames remaining after Laplacian blur and luminance filtering.
    - `redundancy_summary.json` — Frame selection metrics and baseline variance metadata.
    - `colmap/database.db` — COLMAP SQLite feature extraction and matching database.
    - `colmap/sparse/` — SfM camera poses and sparse 3D point cloud (`points3D.bin`, `cameras.bin`, `images.bin`).
    - `colmap/dense/` — Dense MVS depth maps and fused point cloud (`fused.ply`).
    - `colmap/textured/` — Open3D Poisson surface mesh and final binary GLB model (`model.glb`).
    - `metadata.json` — Comprehensive photogrammetric manifest (camera intrinsics, point counts, bounding box, timing).

**Caching:**
- **In-Memory Job Cache:** Fast dictionary cache `_jobs` in `backend/main.py` synchronized with SQLite database writes.

## Authentication & Identity

**Auth Provider:**
- Currently unauthenticated / single-tenant local operation suited for secure local evaluation workstations.
- Security boundaries: UUIDv4 format validation on all `job_id` path parameters, filename sanitization via `Path(filename).name`, and strict upload container whitelisting (`.mp4`, `.mov`, `.avi`, `.mkv`).

## Monitoring & Observability

**Health & Readiness Probes:**
- **`GET /health`:** Fast liveness probe returning API version, status, and timestamp (`backend/main.py`).
- **`GET /ready`:** Deep readiness probe verifying:
  - SQLite database connectivity and write access
  - Free disk space on the active drive (requires >= 5.0 GB available)
  - COLMAP executable existence and execution permissions
  - NVIDIA CUDA GPU detection via `cv2.cuda.getCudaEnabledDeviceCount()` or NVML probe

**Logging:**
- Standard Python `logging` with structured formatting (`%(asctime)s %(levelname)s [%(name)s] %(message)s`).
- Structured prefixes (`[job_id] STAGE X: ...`) tracking end-to-end execution across video extraction, filtering, COLMAP, Open3D, and Trimesh.
- Console output and terminal logs recorded during execution.

**Diagnostics:**
- Persistent job diagnostics stored in `result_json` in `jobs.db` and rendered client-side via `DiagnosticsAccordion.tsx`.

## CI/CD & Deployment

**Hosting:**
- Local Windows 11 host (Dell G15 5530 workstation).
- Dual-mode deployment:
  - Development: FastAPI on `http://127.0.0.1:8000` + Vite dev server on `http://localhost:3000`.
  - Production: Unified single-server FastAPI serving static bundled React assets from `frontend/dist` on `http://127.0.0.1:8000`.

**Launcher Scripts:**
- `start_geoforge.bat` — Single-click launcher executing environment verification, building frontend if needed, and launching Uvicorn ASGI server.

## Environment Configuration

**Development:**
- Backend `.env` (`backend/.env`):
  - `COLMAP_EXE=C:\Users\adity\Downloads\COLMAP-3.11.1-windows-cuda\bin\colmap.bat`
  - `MAX_CONCURRENT_RECONSTRUCTIONS=1`
  - `ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:8000`
- Frontend environment (`frontend/.env` / `import.meta.env`):
  - `VITE_API_URL=http://127.0.0.1:8000`

**Production:**
- Air-gapped on-premise execution with all environment variables read from `backend/.env`.

## Webhooks & Callbacks

**Incoming:**
- None (air-gapped design).

**Outgoing:**
- None (no third-party webhook dependencies).

---

*Integration audit: 2026-11-12*
*Update when adding/removing external services*

