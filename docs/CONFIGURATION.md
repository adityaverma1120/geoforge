# Configuration Reference — GeoForge

> **Document:** `docs/CONFIGURATION.md`  
> **Status:** Code-Verified Configuration Specification  
> **Target Version:** GeoForge v1.0.0 (SIH 2026 / NTRO Edition)  
> **Last Verified:** 2026-11-11  
> **Related Documents:** [`docs/BACKEND.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/BACKEND.md), [`docs/FRONTEND.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/FRONTEND.md), [`docs/RECONSTRUCTION_PIPELINE.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/RECONSTRUCTION_PIPELINE.md)

---

## 1. Environment Variables Reference

Every environment variable below has been confirmed by direct static code inspection in `backend/` and `frontend/src/`. No other environment variables are read by the application.

| Variable Name | Component | Consuming File & Line | Default Value | Purpose & Operating Behavior |
|---|---|---|---|---|
| `COLMAP_EXE` | Backend | `backend/main.py:160`, `reconstruction.py:17` | `C:\Users\adity\AppData\Local\Programs\COLMAP\bin\colmap.exe` | Absolute filesystem path to the compiled COLMAP CLI executable. Overridden on Linux or custom Windows installations. |
| `FFMPEG_EXE` | Backend | `backend/main.py:163-171` | `C:\Users\adity\AppData\Local\Programs\ffmpeg\bin\ffmpeg.exe` | Absolute filesystem path to the compiled FFmpeg executable. Falls back to PATH detection and standard installation locations. |
| `ALLOWED_ORIGINS` | Backend | `backend/main.py:62-66` | `http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,http://localhost:5173,http://127.0.0.1:5173` | Comma-separated list of allowed client origins configured in FastAPI `CORSMiddleware`. |
| `VITE_API_URL` | Frontend | `frontend/src/services/api.ts:10-13` | `http://127.0.0.1:8000` | Base URL used by the frontend client to dispatch upload, polling, and model retrieval requests. |

### Note on Legacy Template Placeholders
The file `frontend/.env.example` contains `GEMINI_API_KEY` and `APP_URL`. Codebase grepping confirms **neither variable is imported, read, or utilized** anywhere in `frontend/src/` or `backend/`. They are harmless remnants of an earlier AI Studio starter template and should not be treated as active application configurations.

---

## 2. Configuration Files

### 2.1 `frontend/vite.config.ts`
Controls Vite development server port, host binding, and React plugin bundling:
```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: '0.0.0.0'  // Allows local network devices (tablets, mobile) to test the UI
  }
})
```

### 2.2 `frontend/.env.example` / `frontend/.env.local`
Frontend local environment overrides read at build/dev time:
```bash
# Base URL for GeoForge FastAPI backend
VITE_API_URL="http://127.0.0.1:8000"
```

### 2.3 `frontend/package.json`
Defines toolchain scripts and exact dependencies:
- `"dev": "vite"` — Starts development server on port 3000.
- `"build": "vite build"` — Compiles production assets into `frontend/dist/`.
- `"lint": "tsc --noEmit"` — Static TypeScript type verification.

---

## 3. Backend Processing Parameters & Constants

All processing constants are defined at module scope in the backend codebase:

### 3.1 Service Limits & Workspace Layout (`backend/main.py`)
| Parameter | Value | Location | Description |
|---|---|---|---|
| `MAX_UPLOAD_BYTES` | `4294967296` ($4\text{ GiB}$) | `main.py:82` | Hard ceiling for uploaded video size checked against `Content-Length`. |
| `MIN_FRAMES_FOR_RECONSTRUCTION` | `20` | `main.py:85` | Minimum surviving frame count required before initiating COLMAP SfM. |
| `JOB_RETENTION_SECONDS` | `604800` ($7\text{ days}$) | `main.py:88` | Time before background `_cleanup_job_files()` deletes temporary scratch files. |
| `MAX_CONCURRENT_RECONSTRUCTIONS` | `1` | `main.py:91` | Maximum concurrent worker threads in `_executor = ThreadPoolExecutor(max_workers=1)`. Tuned for RTX 3050 (6 GB VRAM) and 16 GB host RAM. |
| `ALLOWED_EXTENSIONS` | `{".mp4", ".mov", ".avi", ".mkv"}` | `main.py:516` | File container format extension allowlist. |

#### Filesystem Paths (`backend/main.py:115-121`, `backend/database.py:17`):
- `BASE_DIR`: Absolute directory of `main.py` (`backend/`).
- `UPLOAD_DIR`: `BASE_DIR / "uploads"` — Persists raw uploaded videos named `{job_id}_{filename}`.
- `TEMP_DIR`: `BASE_DIR / "temp"` — Root workspace for ephemeral reconstruction data.
- `OUTPUT_DIR`: `BASE_DIR / "output"` — Retained for compatibility.
- `DB_PATH`: `BASE_DIR / "jobs.db"` — Persistent SQLite database.

#### Per-Job Scratch Subfolders (`backend/main.py:328-331`):
Inside `TEMP_DIR / {job_id}/`:
- `frames/`: Raw video frames sampled at target FPS.
- `selected_frames/`: Frames passing Laplacian blur and luminance checks.
- `final_frames/`: Keyframe subset passing redundancy reduction.
- `colmap/`: Full COLMAP workspace containing `sparse/`, `dense/`, and `textured/`.
- Final Model Path: `TEMP_DIR / {job_id} / "colmap" / "textured" / "model.glb"` (served by `_resolve_glb()`).

---

### 3.2 Frame Extraction Parameters (`backend/frame_processing.py:16-20`)
| Constant | Default Value | Description |
|---|---|---|
| `DEFAULT_TARGET_FPS` | `2.0` | Target extraction rate. Frame step calculated as $\max(1, \text{round}(\text{fps} / 2.0))$. |
| `JPEG_QUALITY` | `95` | OpenCV compression quality for extracted frame JPEGs. |

---

### 3.3 Quality & Sharpness Filtering Parameters (`backend/frame_filtering.py:19-34`)
| Constant | Default Value | Description |
|---|---|---|
| `DEFAULT_SHARPNESS_THRESHOLD` | `100.0` | Baseline Laplacian variance blur threshold $\text{Var}(\nabla^2 I)$. |
| `MAX_BLUR_REJECTION_RATIO` | `0.40` | If $> 40\%$ of frames are rejected as blurry, triggers adaptive threshold lowering. |
| `ABSOLUTE_MIN_SHARPNESS` | `20.0` | Absolute floor for adaptive threshold lowering to avoid accepting severely blurred frames. |
| `MIN_BRIGHTNESS` | `30.0` | Minimum mean grayscale pixel value ($[0, 255]$). Rejects underexposed/night footage. |
| `MAX_BRIGHTNESS` | `240.0` | Maximum mean grayscale pixel value ($[0, 255]$). Rejects blown-out/overexposed footage. |

---

### 3.4 Redundancy Filtering Parameters (`backend/redundancy_filter.py:18-24`)
| Constant | Default Value | Description |
|---|---|---|
| `DEFAULT_DIFFERENCE_THRESHOLD` | `5.0` | Mean absolute difference (MAD) threshold between consecutive normalized grayscale frames. |
| `MIN_RETENTION_RATIO` | `0.50` | Safety retention floor: at least 50% of candidate frames are retained even in near-static hover videos. |

---

### 3.5 Photogrammetry Parameters (`backend/reconstruction.py:27-46`)
| Constant | Default Value | Description |
|---|---|---|
| `FORCE_SINGLE_MODEL` | `False` | When `False`, allows COLMAP to extract multiple sub-models and selects the largest coherent component, avoiding premature failure. |
| `MIN_REGISTRATION_RATIO` | `0.30` | Quality gate: at least 30% of candidate images must successfully register in the sparse model. |
| `POISSON_DEPTH` | `11` | Octree depth for Open3D Screened Poisson Surface Reconstruction. |
| `POISSON_DENSITY_TRIM_PERCENTILE` | `7.0` | Bottom 7.0% low-density mesh boundary faces trimmed to eliminate Poisson bubble artifacts. |
| `PATCHMATCH_MAX_IMAGE_SIZE` | `1200` | Maximum image dimension for dense PatchMatch stereo, preventing GPU VRAM exhaustion. |
| `PATCHMATCH_NUM_ITERATIONS` | `4` | Number of PatchMatch iterations per image, balancing quality and reconstruction latency. |
| `MAX_NUM_FEATURES` | `8192` | SIFT feature limit per image, optimizing GPU memory consumption on laptop GPUs. |
