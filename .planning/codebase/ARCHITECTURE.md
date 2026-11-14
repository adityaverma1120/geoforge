# Architecture

**Analysis Date:** 2026-11-12

## Pattern Overview

**Overall:** Asynchronous Multi-Stage Processing Pipeline with Decoupled React SPA & FastAPI Microservices

**Key Characteristics:**
- **Single-Pass Photogrammetric Workflow:** Transforms raw sequential drone or handheld video into metric 3D models via a deterministic 12-stage pipeline.
- **Hardware-Constrained Asynchronous Execution:** Concurrency ceiling strictly bounded to `MAX_CONCURRENT_RECONSTRUCTIONS = 1` using a background `ThreadPoolExecutor` to protect laptop GPU VRAM (6 GB RTX 3050).
- **Persistent State-Machine Tracking:** Relational SQLite storage tracks job states (`queued`, `processing`, `complete`, `failed`, `cancelled`) across server reboots.
- **Adaptive Polling Client:** React frontend polls the backend `/status/{job_id}` endpoint with exponential back-off intervals (`3s -> 5s -> 10s -> 20s -> 30s`) to prevent event-loop saturation.
- **Unified Full-Stack Distribution:** Capable of serving as two decoupled dev servers (Port 3000 + Port 8000) or as a unified production deployment where FastAPI serves the compiled SPA from `frontend/dist`.

## Layers

**API & Routing Layer (`backend/main.py`):**
- Purpose: Exposes RESTful HTTP endpoints for video upload, job lifecycle queries, 3D asset delivery, history listing, and health checks.
- Contains: FastAPI router, CORS middleware, UUID validation, file size limits, static file serving.
- Depends on: Pipeline Orchestration Layer and Data Persistence Layer.
- Used by: React frontend client and external HTTP callers.

**Pipeline Orchestration Layer (`backend/main.py:_run_pipeline_background`):**
- Purpose: Sequentially executes and monitors the 12 reconstruction stages inside a worker thread, catching exceptions and reporting progress.
- Contains: Stage transition logic, progress percent calculations, diagnostic JSON accumulation, stage callbacks.
- Depends on: Frame processing, computer vision filtering, COLMAP orchestration, Open3D meshing, GLB converter.
- Used by: Upload endpoint worker dispatch.

**Computer Vision & Photogrammetry Processing Layer:**
- Purpose: Performs the heavy mathematical and algorithmic transformations on visual data.
- Modules:
  - `backend/frame_processing.py`: Video stream validation and 2.0 FPS keyframe sampling using OpenCV.
  - `backend/frame_filtering.py`: Laplacian variance blur detection and luminance/contrast filtering.
  - `backend/redundancy_filter.py`: Mean absolute difference image comparison and spatial trajectory coverage selection.
  - `backend/reconstruction.py`: COLMAP CLI orchestration (SfM sparse reconstruction and MVS dense stereo depth fusion) and Open3D Poisson meshing.
  - `backend/convert_to_glb.py`: Trimesh mesh normalization, UV texture binding, PBR material creation, and binary GLB export.

**Data Persistence Layer (`backend/database.py`):**
- Purpose: Manages persistent SQLite connection pooling, job schema migrations, CRUD operations, and interrupted job recovery.
- Contains: `init_db()`, `create_job()`, `update_job_stage()`, `complete_job()`, `fail_job()`, `list_jobs()`, `delete_job()`.
- Depends on: Python standard library `sqlite3` and filesystem storage in `backend/jobs.db`.

**Client UI Presentation Layer (`frontend/src/`):**
- Purpose: Delivers an interactive, accessible, dark-themed UI for video uploading, real-time stage tracking, 3D model exploration, and project history.
- Contains: React components (`ThreeDViewer.tsx`, `DiagnosticsAccordion.tsx`, `Header.tsx`), pages (`UploadPage.tsx`, `ProcessingPage.tsx`, `CompletePage.tsx`, `HistoryPage.tsx`), and API service (`api.ts`).

## Data Flow

**12-Stage Video-to-3D Reconstruction Flow:**

```
[Raw Drone Video]
       │
       ▼ (POST /upload)
[Stage 1: validating_video] ── OpenCV header & stream integrity check
       │
       ▼
[Stage 2: extracting_frames] ─ 2.0 FPS temporal extraction to temp/{job_id}/frames/
       │
       ▼
[Stage 3: filtering_frames] ── Laplacian blur & exposure filter to temp/{job_id}/selected_frames/
       │
       ▼
[Stage 4: redundancy_filter] ─ Redundant frame suppression; baseline preservation
       │
       ▼
[Stage 5: feature_extraction] ─ COLMAP SIFT feature extractor (CUDA GPU)
       │
       ▼
[Stage 6: feature_matching] ── COLMAP exhaustive feature matcher (CUDA GPU)
       │
       ▼
[Stage 7: sparse_reconstruction] COLMAP mapper (SfM camera poses & points3D)
       │
       ▼
[Stage 8: dense_undistort] ─── COLMAP image undistorter (pinhole model conversion)
       │
       ▼
[Stage 9: dense_stereo] ────── COLMAP patch_match_stereo (depth map generation)
       │
       ▼
[Stage 10: dense_fusion] ───── COLMAP stereo_fusion (dense fused.ply point cloud)
       │
       ▼
[Stage 11: exporting_glb] ──── Open3D Poisson meshing (depth 9, 7% trim) + Trimesh GLB
       │
       ▼
[Stage 12: validating_model] ─ Header verification, vertex bounds, metadata.json generation
       │
       ▼
[Reconstruction Complete] ──── 3D GLB rendered in Three.js WebGL viewport
```

**State Management:**
- Server State: Persistently stored in `jobs.db` SQLite database with status transitions (`queued` $\to$ `processing` $\to$ `complete` / `failed`).
- Frontend State: Managed via React 19 functional state hooks in `App.tsx` (`currentRoute`, `activeJobId`, `jobStatus`).

## Key Abstractions

**Reconstruction Job (`database.py`, `types.ts`):**
- Encapsulates job ID, original filename, current processing stage, percentage progress (0-100%), stage message, timing metrics, and diagnostics.

**Stage Callback Interface (`main.py`, `reconstruction.py`):**
- Higher-order callback function `on_progress(stage: str, percent: int, msg: str)` passed into long-running COLMAP operations to update database state in real-time.

**GLB Converter & Validator (`convert_to_glb.py`):**
- Encapsulates Trimesh mesh ingestion, vertex normal calculation, texture embedding, PBR material creation, and binary file integrity verification.

**Three.js Model Viewport (`ThreeDViewer.tsx`):**
- Encapsulates WebGL canvas initialization, GLTFLoader parsing, automatic camera centering, bounding box framing, orbit controls, wireframe toggling, and screenshot capture.

## Entry Points

**Backend Server:**
- Location: `backend/main.py`
- Invocation: `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
- Triggers: HTTP requests from frontend or external clients.

**Frontend Client:**
- Location: `frontend/src/main.tsx` (bundling entry: `frontend/index.html`)
- Invocation: `vite` or production bundle served via Uvicorn.

**Launcher:**
- Location: `start_geoforge.bat`
- Invocation: Double-click or terminal execution to boot both frontend and backend.

## Error Handling

**Strategy:** Fail-safe containment with structured HTTP status codes and persistent error logging.

**Patterns:**
- **UUID Validation:** All endpoints receiving `job_id` reject invalid formats with `HTTP 400 Bad Request`.
- **Concurrency Gate:** If another reconstruction is already running, new uploads are rejected with `HTTP 503 Service Unavailable` (`Reconstruction server is at capacity`).
- **Pipeline Try-Except Wrap:** Unhandled exceptions during reconstruction trigger `database.fail_job(job_id, str(e))` and record stack traces in the backend logs, releasing the concurrency lock.
- **Server Restart Recovery:** Startup lifecycle (`@app.on_event("startup")`) calls `database.recover_interrupted_jobs()` to transition orphaned `processing` records to `failed`.

## Cross-Cutting Concerns

**Logging:**
- Standard Python logger `geoforge` with UTC timestamps and structured `[job_id]` prefixes.

**Security & Path Traversal Guard:**
- Pathlib resolution, UUID validation, strict filename basename sanitization, and 4 GB upload limits.

**Hardware Concurrency Guard:**
- Concurrency ceiling `MAX_CONCURRENT_RECONSTRUCTIONS = 1` enforced at upload intake to protect GPU memory.

---

*Architecture analysis: 2026-11-12*
*Update when major patterns change*

