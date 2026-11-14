# Product Requirements Document (PRD) — GeoForge

> **Document:** `docs/PRD.md`  
> **Status:** Canonical Product Requirements Specification (Phase 4 Verified)  
> **Target Version:** GeoForge v1.0.0 (SIH 2026 / NTRO Edition)  
> **Related Documents:** [`docs/PROJECT_OVERVIEW.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/PROJECT_OVERVIEW.md), [`docs/FEATURE_STATUS.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/FEATURE_STATUS.md), [`docs/UI_UX_DESIGN.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/UI_UX_DESIGN.md), [`docs/ROADMAP.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/ROADMAP.md)

---

## 1. Problem Statement & Background

Creating accurate 3D spatial models from aerial drone video is conventionally a fragmented, high-friction process:
1. **Tooling Fragmentation:** Operators must manually extract frames with ffmpeg, inspect blur, operate complex desktop photogrammetry software (e.g., COLMAP CLI, Agisoft Metashape, RealityCapture), tune camera calibration matrices, and manually execute Poisson surface reconstruction and mesh texturing.
2. **Computational Inefficiency:** Raw drone video shot at 30 or 60 FPS contains hundreds of identical, redundant, or motion-blurred frames. Passing raw frames directly into Structure-from-Motion (SfM) creates quadratic matching bottlenecks ($O(N^2)$), exhausts GPU VRAM, and introduces camera trajectory drift.
3. **Delivery Barrier:** The resulting 3D models typically exist as multi-gigabyte point clouds or untextured polygon meshes requiring specialized desktop GIS or CAD workstations to inspect.

### Project Vision
GeoForge solves this end-to-end for **Smart India Hackathon 2026** (Problem Statement: **SIH26158**, Title: *Single-Pass Drone Video to Accurate 3D Model Generation System*, Organisation: *National Technical Research Organisation — NTRO*). 

The vision of GeoForge is to provide an automated, single-pass pipeline: **The operator uploads raw flight video; the system autonomously selects informative keyframes, reconstructs geometry via COLMAP SfM/MVS, cleans and textures the mesh, and delivers a browser-streamable, interactive 3D model (GLB) viewable immediately on standard consumer devices without desktop software.**

---

## 2. Target Users & User Problems

| User Persona | Context & Environment | Core Problems Solved by GeoForge |
|---|---|---|
| **Defense & Intelligence Analysts (NTRO)** | Tactical reconnaissance and rapid situational awareness from surveillance UAV video feeds. | Eliminates manual photogrammetry pipeline orchestration; converts aerial video into actionable 3D situational models in minutes. |
| **Emergency Response & Disaster Teams** | Post-disaster flyover inspection (floods, earthquakes, structural collapses). | Enables rapid 3D volumetric damage inspection without on-site photogrammetry specialists. |
| **Surveying & Mapping Operators** | Commercial drone operators capturing campuses, building facades, and infrastructure assets. | Filters prop-wash blur and hover redundancy automatically; exports standard WebGL and CAD-ready deliverables. |
| **Academic & CV Researchers** | Educational institutions studying computer vision, SfM, and dense reconstruction. | Exposes observable intermediate artifacts (`fused.ply`, `poisson_mesh.ply`, `model.ply`) and transparent pipeline diagnostic telemetry. |

---

## 3. Core Use Cases

- **UC-1: Rapid Campus / Facility 3D Reconnaissance:** An operator conducts an orbital flyover around a facility, uploads the MP4 video, monitors automated stage execution, and interacts with the generated 3D model directly in the browser viewport.
- **UC-2: Structural Damage Inspection:** A drone captures close-proximity video of a bridge or high-rise building. GeoForge discards blurry frames caused by wind drift, runs dense stereo reconstruction, and produces a watertight textured mesh revealing structural defects.
- **UC-3: Pre-Reconstruction Quality Validation:** An operator uploads a video with excessive motion blur or near-zero camera movement. The system detects the deficiency during frame filtering or sparse SfM, halting early with diagnostic guidance to prevent wasted compute.

---

## 4. Input & Output Requirements

### 4.1 Input Video Requirements
- **Container Formats:** `.mp4`, `.mov`, `.avi`, `.mkv` (Backend allowlist in `backend/main.py:382`).
- **File Size Bound:** Maximum 4 GiB (`4,294,967,296` bytes enforced via `Content-Length` header check).
- **Video Resolution:** Recommended 1080p ($1920 \times 1080$) to 4K ($3840 \times 2160$).
- **Flight Capture Dynamics:**
  - Forward and lateral visual overlap: Recommended $70\% - 80\%$.
  - Camera pitch: Oblique ($45^\circ - 60^\circ$) for buildings; nadir ($90^\circ$ straight down) for terrain.
  - Motion: Smooth translational velocity ($2 - 5\text{ m/s}$); minimal sudden angular yaw rotation.
  - Lighting: Stable diffuse or daylight illumination; minimal shadow movement.

### 4.2 Output Model Requirements
- **Primary Deliverable:** Binary glTF 2.0 (`.glb`) served via `GET /model/{job_id}`.
- **Material Standards:** Physically Based Rendering (PBR) metallic-roughness material with embedded diffuse texture atlas (`model.png`).
- **Intermediate Artifacts:**
  - `colmap/dense/fused.ply`: Raw fused dense point cloud.
  - `colmap/dense/fused_cleaned.ply`: Outlier-cleaned point cloud (Open3D).
  - `colmap/mesh/poisson_mesh.ply`: Watertight Screened Poisson surface mesh (7% density trimmed).
  - `colmap/textured/model.ply` & `model.obj`: Textured wavefront geometry with UV parameterization.

---

## 5. Functional Requirements (FR-001 – FR-015)

| ID | Requirement Name | Priority | Status | Verified Source Acceptance Criteria |
|---|---|:---:|:---:|---|
| **FR-001** | Multipart Video Upload | Must | **Implemented** | `POST /upload` accepts `file: UploadFile`. Enforces extension allowlist `{".mp4", ".mov", ".avi", ".mkv"}` in `backend/main.py:382`. |
| **FR-002** | Payload Size Boundary | Must | **Implemented** | Inspects `Content-Length` header against 4 GiB (`MAX_UPLOAD_BYTES`); raises HTTP 413 `Payload Too Large` before disk buffering. |
| **FR-003** | Asynchronous Job Allocation | Must | **Implemented** | Generates UUID4 `job_id`, initializes in-memory state in `_jobs`, and returns HTTP 200 with `job_id`, `status_url`, and `model_url`. |
| **FR-004** | Frame Extraction Sampling | Must | **Implemented** | `backend/frame_processing.py` extracts frames at `DEFAULT_TARGET_FPS = 2.0` (interval $\max(1, \text{round}(\text{fps} / 2.0))$). |
| **FR-005** | Blur & Exposure Filtering | Must | **Implemented** | Laplacian variance $\text{Var}(\nabla^2 I) \ge 100.0$ (adaptive fallback down to 20.0 if rejection $>40\%$) and luminance $[30.0, 240.0]$ in `frame_filtering.py`. |
| **FR-006** | Redundancy Minimization | Must | **Implemented** | Mean absolute difference $\Delta \ge 5.0$ in `redundancy_filter.py` with an enforced $50\%$ safety retention floor (`MAX_REMOVAL_RATIO = 0.50`). |
| **FR-007** | Minimum Frame Gate | Must | **Implemented** | Halts pipeline with clear error if surviving keyframes $< 20$ (`MIN_FRAMES_FOR_RECONSTRUCTION`). |
| **FR-008** | Automated COLMAP SfM | Must | **Implemented** | SIFT extraction (16k features, OPENCV camera, GPU), sequential matching (overlap 15, vocab tree loop closure), single-model mapper (`--Mapper.multiple_models 0`). |
| **FR-009** | Sparse Quality Gate | Must | **Implemented** | Binary parser checks `images.bin` / `points3D.bin`. Halts pipeline if $\text{Registration Ratio} < 0.30$ ($30\%$). |
| **FR-010** | Dense Stereo Reconstruction | Must | **Implemented** | Image undistortion (`max_image_size 2400`), PatchMatch stereo (7 iterations, `geom_consistency 1`), stereo fusion (`min_num_pixels 3`). |
| **FR-011** | Point Cloud Denoising | Must | **Implemented** | Open3D statistical outlier removal (`nb_neighbors=20, std_ratio=2.0`) $\to$ `colmap/dense/fused_cleaned.ply`. |
| **FR-012** | Screened Poisson Meshing | Must | **Implemented** | Normal estimation, Poisson reconstruction (`depth=11`), and 7.0% density boundary trimming (`POISSON_TRIM = 7.0`) to remove ballooning bubble hulls. |
| **FR-013** | Mesh Texturing & GLB Export | Must | **Implemented** | COLMAP `mesh_texturer` projects camera imagery onto mesh; `convert_to_glb.py` uses Trimesh + Pillow to assemble PBR `model.glb`. |
| **FR-014** | Status & Diagnostic Polling | Must | **Implemented** | `GET /status/{job_id}` exposes execution state (`queued`, `processing`, `complete`, `failed`), error text, and 27-metric `result` dictionary. |
| **FR-015** | Interactive WebGL Viewer | Must | **Implemented** | `ThreeDViewer.tsx` loads GLB via Three.js `GLTFLoader`, auto-centers bounding box, provides OrbitControls, wireframe toggle, and grid helper. |

---

## 6. Non-Functional Requirements (NFR-001 – NFR-008)

| ID | Requirement Name | Category | Target Metric | Verified Source Enforcement |
|---|---|---|---|---|
| **NFR-001** | Responsive Event Loop | Performance | API latency $< 50\text{ ms}$ | Heavy photogrammetry tasks execute off the asyncio event loop via `ThreadPoolExecutor(max_workers=2)`. |
| **NFR-002** | Concurrency Protection | Reliability | Max 2 active reconstructions | Handled in `POST /upload`: returns HTTP 503 `Busy` if 2 workers are active to prevent system lockup. |
| **NFR-003** | Path Space-Safety | Reliability | Zero batch quoting crashes | `backend/reconstruction.py:run_colmap` executes binary directly (`shell=False`) with argument lists, bypassing Windows batch-file quoting bugs when paths contain spaces. |
| **NFR-004** | Artifact Lifecycle Limits | Storage | 7-day automated purge | Background task `_cleanup_job_files` deletes `temp/{job_id}/` and source video after `JOB_RETENTION_SECONDS = 604800` (7 days). |
| **NFR-005** | Portable API Binding | Maintainability | Configurable endpoints | Frontend dynamically configures `API_BASE_URL` from `VITE_API_URL` with clean URL normalization (`getModelGlbUrl`). |
| **NFR-006** | CORS Access Control | Security | Origin allowlist | Configured via `ALLOWED_ORIGINS` covering `localhost:3000`, `3001`, `5173`. |
| **NFR-007** | Subprocess Safety | Security | Path isolation | UUID-generated workspaces (`backend/temp/{job_id}/`); no arbitrary command string evaluation. |
| **NFR-008** | Client Graphics Performance| Usability | $\ge 30\text{ FPS}$ WebGL rendering | Three.js perspective camera with depth clipping, directional shadow mapping, and automated resource disposal on unmount. |

---

## 7. System Constraints & Operating Boundaries

1. **Hardware Requirements:**
   - Minimum: 16 GB RAM, 6-core x86_64 CPU, 20 GB free SSD disk space.
   - Recommended: NVIDIA GPU with CUDA support ($\ge 6\text{ GB}$ VRAM, e.g., RTX 3060 / 4060). CPU-only fallback is operational but increases dense MVS processing time significantly.
2. **In-Memory Job Store Volatility:**
   - `_jobs` resides in process memory. If the Uvicorn server restarts, all job records are lost. Recovering jobs requires client re-upload until persistent database storage is implemented.
3. **Local Unscaled Coordinate Space:**
   - Models are reconstructed in local photogrammetric camera coordinates. Absolute metric scale and geospatial orientation (WGS84 / UTM) are not established without Ground Control Points (GCPs).

---

## 8. Release Acceptance Criteria

A production release of GeoForge must pass the following 6 quality gates:
1. **Frontend Type & Bundle Check:** `npm run lint` (`tsc --noEmit`) and `npm run build` execute with zero compilation or typing errors.
2. **Backend Startup Verification:** FastAPI server initializes cleanly on port 8000; `GET /health` returns `{"status": "healthy"}`.
3. **Nominal End-to-End Run:** A standard drone test video (1080p, 30–45s) completes all 13 pipeline stages and produces a non-empty `model.glb`.
4. **Viewer Rendering Verification:** Three.js viewport successfully parses and renders the generated GLB with functioning OrbitControls and no WebGL context exceptions.
5. **Quality Failure Handling:** Degenerate video input (e.g., stationary camera or pure motion blur) halts cleanly at quality gates with diagnostic feedback rather than crashing the worker.
6. **Resource Cleanup Verification:** Server does not leak temporary directories or unreferenced in-memory dictionaries beyond configured retention periods.
