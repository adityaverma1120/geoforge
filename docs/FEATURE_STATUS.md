# Feature Status & Capability Register — GeoForge

> **Document:** `docs/FEATURE_STATUS.md`  
> **Status:** Code-Verified Feature Inventory (Phase 7 Integration Verified)  
> **Target Version:** GeoForge v1.0.0 (SIH 2026 / NTRO Edition)  
> **Source Verification Date:** 2026-11-14  
> **Related Documents:** [`docs/PRD.md`](PRD.md), [`docs/ROADMAP.md`](ROADMAP.md), [`docs/UI_UX_DESIGN.md`](UI_UX_DESIGN.md), [`docs/INTEGRATION_VERIFICATION_REPORT.md`](INTEGRATION_VERIFICATION_REPORT.md)

---

## 1. Classification Taxonomy

To prevent speculative feature inflation and preserve technical truth, all capabilities in GeoForge are classified into 5 strict tiers:

1. **Currently Implemented:** Fully verified in active Python backend or React frontend source code; working in the end-to-end call path.
2. **Partially Implemented / Discrepant:** Code exists but exhibits discrepancies between frontend UI claims and backend API capabilities.
3. **Features Requiring Technical Validation:** Code exists and is syntactically complete, but requires dedicated physical hardware, consumer GPUs, or benchmark datasets to quantify.
4. **Planned Features:** Architecturally documented on the roadmap for subsequent prototype phases; no backend implementation currently exists.
5. **Research Ideas:** Long-term theoretical concepts (e.g., Gaussian Splatting, NeRFs, RTK Georeferencing) not yet scheduled for implementation.

---

## 2. Currently Implemented Features

| Capability | Category | Source Location | Code Implementation Evidence |
|---|---|---|---|
| **Video Ingestion & Size Bound** | Backend API | `backend/main.py:356-425` | `POST /upload` validates `Content-Length <= 4GB`, checks extension `{".mp4", ".mov", ".avi", ".mkv"}`, saves to `backend/uploads/`. |
| **Worker Concurrency Limit** | Architecture | `backend/main.py:86, 443-457` | `ThreadPoolExecutor(max_workers=2)` rejects concurrent uploads above 2 with HTTP 503 `Busy`. |
| **FPS-Aware Frame Extraction** | Computer Vision | `backend/frame_processing.py:23-118` | Dynamic sampling $\max(1, \text{round}(\text{fps} / 2.0))$ extracts frames at 2.0 FPS; writes JPEGs (quality 95) to `frames/`. |
| **Adaptive Laplacian Blur Filter**| Computer Vision | `backend/frame_filtering.py:69-207` | Computes $\text{Var}(\nabla^2 I) \ge 100.0$; adaptively lowers threshold to 40th percentile (min 20.0) if rejection ratio $>40\%$. |
| **Luminance Filtering** | Computer Vision | `backend/frame_filtering.py:53-67` | Grayscale mean brightness bounded within $[30.0, 240.0]$; discards night and blown-out glare frames. |
| **Redundancy Reduction Filter** | Computer Vision | `backend/redundancy_filter.py:42-171` | Consecutive frame difference $\Delta \ge 5.0$ (`cv2.absdiff`) bounded by a strict 50% safety retention floor (`MAX_REMOVAL_RATIO = 0.50`). |
| **Minimum Frame Count Gate** | Quality Assurance| `backend/main.py:227-243` | Halts reconstruction with clear error if surviving keyframes $< 20$ (`MIN_FRAMES_FOR_RECONSTRUCTION`). |
| **COLMAP SIFT Feature Extraction**| Photogrammetry | `backend/reconstruction.py:858-916` | SIFT extraction (16,384 features, OPENCV camera model, affine shape, domain pooling, GPU enabled). |
| **COLMAP Sequential Matching** | Photogrammetry | `backend/reconstruction.py:918-980` | Sequential matching (overlap 15) with automatic vocabulary tree loop detection across 5 candidate paths. |
| **Single-Model SfM Mapping** | Photogrammetry | `backend/reconstruction.py:982-1048` | Forces unified coordinate model via `--Mapper.multiple_models 0`; 50 global BA iterations. |
| **Sparse Registration Gate** | Quality Assurance| `backend/reconstruction.py:1060-1122`| Binary parser (`struct.unpack`) checks `images.bin` / `points3D.bin`. Halts if $\text{Registration Ratio} < 0.30$. |
| **Dense Multi-View Stereo (MVS)**| Photogrammetry | `backend/reconstruction.py:1124-1340`| Image undistortion (`max_image_size 2400`); PatchMatch stereo (7 iterations, `geom_consistency 1`); stereo fusion $\to$ `fused.ply`. |
| **Point Cloud Outlier Cleaning** | 3D Geometry | `backend/reconstruction.py:541-603` | Open3D statistical outlier removal (`nb_neighbors=20, std_ratio=2.0`) $\to$ `fused_cleaned.ply`. |
| **Screened Poisson Meshing** | 3D Geometry | `backend/reconstruction.py:609-700` | Normal estimation, Poisson reconstruction (`depth=11`), 7.0% density boundary trimming (`POISSON_TRIM = 7.0`). |
| **COLMAP Mesh Texturing** | 3D Geometry | `backend/reconstruction.py:1441-1531`| `mesh_texturer` projects camera radiance onto mesh $\to$ `model.ply`, `model.obj`, and diffuse atlas `model.png`. |
| **Binary GLB Packaging** | 3D Geometry | `backend/convert_to_glb.py:29-200` | Trimesh geometry loading & scene concatenation; Pillow diffuse PBR material binding; GLTF 2.0 binary export. |
| **Binary 3D Model Serving** | Backend API | `backend/main.py:553-580` | `GET /model/{job_id}` streams `colmap/textured/model.glb` via `FileResponse(media_type="model/gltf-binary")`. |
| **Model Availability Probe** | Backend API | `backend/main.py:586-610` | `HEAD /model/{job_id}` returns headers and byte size without transmitting binary payload. |
| **Status Polling API** | Backend API | `backend/main.py:496-540` | `GET /status/{job_id}` returns status (`queued`, `processing`, `complete`, `failed`) and 27-metric `result` dictionary. |
| **7-Day Retention Cleanup** | Storage Lifecycle| `backend/main.py:146-164` | `_cleanup_job_files` deletes `temp/{job_id}/`, unlinks video, and purges `_jobs` after `JOB_RETENTION_SECONDS = 604800`. |
| **XHR Upload Progress Tracking**| Frontend Client | `frontend/src/services/api.ts:40-275`| Native `XMLHttpRequest` tracks `xhr.upload.onprogress` for live percentage upload progress bar. |
| **Interactive Three.js 3D Viewer**| Frontend Client | `frontend/src/components/ThreeDViewer.tsx`| Three.js `GLTFLoader`, dynamic centering, OrbitControls, Wireframe toggle, Ground Grid, and camera reset. |
| **Capture Guidance UI** | Frontend Client | `frontend/src/pages/HowItWorksPage.tsx` | 5-stage timeline explaining flight overlap, blur removal, camera solving, meshing, and viewing. |
| **Diagnostic Failure Accordion**| Frontend Client | `frontend/src/components/DiagnosticsAccordion.tsx`| Displays error codes, server timestamp, failure stages, and suggested capture remediation. |
| **Persistent SQLite Job Store** | Persistence Layer | `backend/database.py`, `backend/jobs.db` | Atomic thread-safe SQLite database logging jobs, timestamps, stages, and metrics. Automatically recovers interrupted jobs on startup. |
| **Job History Page** | Frontend Client | `frontend/src/pages/HistoryPage.tsx`, `frontend/src/App.tsx` | Full interactive audit history page (`/history`) listing past reconstructions, download links, and direct Three.js viewer inspection. |
| **Unified Single-Server Mount** | Deployment Architecture | `backend/main.py` | FastAPI `StaticFiles` mounts `/assets` and `spa_fallback` serves `index.html` for client-side routes (`http://localhost:8000`). |
| **Turnkey Single-Click Launcher** | Operational Tooling | `start_geoforge.bat` | Automated batch script for Windows with venv detection, dependency validation, frontend compilation, and browser launching. |

---

## 3. Partially Implemented Features / Known Discrepancies

The following capabilities exist in code but exhibit discrepancies between client UI representations and backend realities:

| Feature | Frontend State | Backend Reality | Reconciliation Recommendation |
|---|---|---|---|
| **Format Extension Allowlist** | `UploadPage.tsx:22` accepts only `.mp4`, `.mov`, `.avi`. | `main.py:382` accepts `{".mp4", ".mov", ".avi", ".mkv"}`. | Update `UploadPage.tsx` to include `mkv` in `allowedExtensions`. |
| **Mock Download Badges** | `CompletePage.tsx:78-100` displays green "READY" badges for LAS, GeoTIFF, and OBJ downloads. | Backend produces only `model.glb` and `model.ply`; clicking LAS/GeoTIFF does not deliver real files. | Change non-GLB badges to "ROADMAP" or disable click triggers. |
| **Simulated Stage Progress** | `ProcessingPage.tsx` advances 10 simulated stages on an artificial timer. | `/status/{job_id}` returns coarse state strings (`processing`) without stage indices. | Maintain simulated timer until WebSocket/SSE event streaming is added to backend. |

---

## 4. Features Requiring Technical Validation

These capabilities are implemented in code but require dedicated physical hardware and field testing to establish empirical bounds:

- **GPU VRAM Ceiling & 4K Video Scaling:** `PATCHMATCH_MAX_IMAGE_SIZE = 2400` operates reliably on GPUs with $\ge 6\text{ GB}$ VRAM. Validation is required to determine maximum video duration before VRAM exhaustion on 4 GB or 8 GB GPUs.
- **CPU Fallback Execution Duration:** COLMAP supports CPU-only SIFT extraction and matching, but dense MVS on CPU takes hours. A benchmark matrix comparing processing times on pure CPU vs. NVIDIA GPU is needed.
- **Adaptive Blur Threshold Floor:** `ABSOLUTE_MIN_SHARPNESS = 20.0` prevents over-filtering. Validation is needed across diverse weather conditions (overcast, midday sun, dawn) to verify threshold stability.

---

## 5. Planned Features (Roadmap)

Features architecturally designed but not yet implemented in backend or frontend code:

- **WebSocket / Server-Sent Events (SSE) Telemetry (Phase 2):** Streaming live COLMAP terminal lines and stage progress directly to `ProcessingPage.tsx` over a real-time socket.
- **Ground Control Point (GCP) RTK Georeferencing (Phase 3):** Parsing drone EXIF GPS tags or user-uploaded GCP coordinates to scale and georeference models in UTM/WGS84.
- **Orthomosaic GeoTIFF Export (Phase 3):** True orthophoto generation via projective camera ray orthorectification.
- **Multi-Tenant User Accounts & Role-Based Access Control (Phase 4):** Authentication, API keys, and workspace isolation for multi-user organizational teams.

---

## 6. Research Ideas (Theoretical / Long-Term)

Long-term computer vision paradigms under exploratory review:

- **3D Gaussian Splatting (3DGS):** Evaluating real-time radiance field rendering (e.g., via WebGL Gaussian viewers) as a complementary representation alongside polygonal meshes.
- **Neural Radiance Fields (NeRF):** Instant-NGP style volumetric representation for complex thin foliage structures where classical MVS struggles.
- **Automated Defect & Crack Segmentation:** Integrating a fine-tuned YOLO or Mask R-CNN model to highlight structural cracks directly on the 3D mesh surface.
