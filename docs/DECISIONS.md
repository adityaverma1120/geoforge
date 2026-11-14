# Architecture Decision Records (ADR) — GeoForge

> **Document:** `docs/DECISIONS.md`  
> **Status:** Code-Verified Architectural Decision Records  
> **Target Version:** GeoForge v1.0.0 (SIH 2026 / NTRO Edition)  
> **Last Verified:** 2026-11-11  
> **Related Documents:** [`docs/ARCHITECTURE.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/ARCHITECTURE.md), [`docs/RECONSTRUCTION_PIPELINE.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/RECONSTRUCTION_PIPELINE.md), [`docs/ROADMAP.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/ROADMAP.md)

---

## 1. Architecture Decision Summary Matrix

| ADR ID | Decision Title | Decision Status | Impacted Modules | Core Rationale |
|---|---|:---:|---|---|
| **ADR-001** | React 19 + Three.js Browser-Native Viewer | **Accepted / Verified** | `frontend/src/` | Eliminates desktop software installation; universal WebGL compatibility. |
| **ADR-002** | FastAPI Backend with Asynchronous Status Polling | **Accepted / Verified** | `backend/main.py` | Avoids HTTP timeouts on long-running (15 min) photogrammetry jobs. |
| **ADR-003** | In-Process `ThreadPoolExecutor` Concurrency Ceiling | **Accepted / Verified** | `backend/main.py:89` | Enforces `max_workers=2` (HTTP 503 guard) to protect host GPU VRAM and CPU from OOM crashes. |
| **ADR-004** | Binary GLTF (`.glb`) as Primary Delivery Format | **Accepted / Verified** | `convert_to_glb.py` | Single self-contained file with embedded PBR materials; direct streaming to Three.js. |
| **ADR-005** | Two-Stage Pre-Processing Frame Culling | **Accepted / Verified** | `frame_filtering.py`, `redundancy_filter.py` | Discards blurry and stationary frames, reducing COLMAP compute by 60–80%. |
| **ADR-006** | Single-Model SfM (`--Mapper.multiple_models 0`) | **Accepted / Verified** | `backend/reconstruction.py` | Prevents fragmented sub-models; forces single unified 3D coordinate space. |
| **ADR-007** | Screened Poisson Meshing with 7.0% Boundary Trimming | **Accepted / Verified** | `backend/reconstruction.py:75` | Watertight surface reconstruction without inflated "bubble" boundary artifacts. |
| **ADR-008** | In-Memory Job Store (`_jobs`) for v0.5 Prototype | **Accepted with Known Gap** | `backend/main.py:68` | Simplifies prototype architecture; scheduled for SQLite/PostgreSQL in v1.0. |

---

## 2. Detailed Architecture Decision Records

### ADR-001: Browser-Based React 19 + Three.js Frontend
- **Context:** Field operators, defense analysts, and disaster response teams need rapid access to 3D situational intelligence without installing heavy desktop suites (e.g. CloudCompare, Blender, MeshLab).
- **Decision:** Build a responsive web client using React 19, TypeScript, Vite, and Three.js (`^0.185.1`). Models are rendered in-browser using WebGL and inspected via `OrbitControls`.
- **Trade-Offs:**
  - *Advantage:* Zero client-side installation; cross-platform support across laptops, tablets, and smartphones.
  - *Constraint:* Dense meshes ($> 2\text{M}$ triangles) can cause frame rate drops on low-end integrated GPUs. Resolved by setting Poisson octree depth to 11 and trimming unobserved boundary geometry.
- **Verification:** Verified in [`frontend/src/components/ThreeDViewer.tsx`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/frontend/src/components/ThreeDViewer.tsx).

---

### ADR-002: FastAPI ASGI Service with Asynchronous Polling
- **Context:** Structure-from-Motion and dense Multi-View Stereo are computationally expensive, taking 10 to 30 minutes for a typical drone flight video. Standard synchronous HTTP request-response patterns would timeout.
- **Decision:** Implement a non-blocking FastAPI backend. `POST /upload` receives the video, generates a UUID4 `job_id`, enqueues background processing, and returns immediately with HTTP 200 `{status: "queued"}`. The frontend client polls `GET /status/{job_id}` using exponential back-off intervals (`3s, 5s, 10s, 20s, 30s`).
- **Trade-Offs:**
  - *Advantage:* HTTP connection is closed immediately; eliminates proxy timeouts.
  - *Constraint:* Polling generates periodic HTTP traffic. Scheduled for migration to Server-Sent Events (SSE) in v1.0.
- **Verification:** Verified in [`backend/main.py:360-475`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/backend/main.py#L360-L475).

---

### ADR-003: Concurrency Ceiling (`MAX_CONCURRENT_RECONSTRUCTIONS = 2`)
- **Context:** COLMAP dense PatchMatch stereo and Open3D Poisson meshing consume substantial GPU VRAM ($\ge 6\text{ GB}$) and system RAM ($\ge 8\text{ GB}$). Multiple overlapping jobs on a single workstation trigger Out-Of-Memory (OOM) operating system kills.
- **Decision:** Restrict worker execution via `_executor = ThreadPoolExecutor(max_workers=2)`. When 2 jobs are actively processing, subsequent upload attempts receive HTTP 503 Service Unavailable:
  `{"detail": "Server is busy. Maximum concurrent reconstructions reached. Please try again shortly."}`
- **Trade-Offs:**
  - *Advantage:* Protects host operating system stability and prevents mid-reconstruction crashes.
  - *Constraint:* Limits concurrent throughput on a single server node. Addressed in v2.0 by horizontal worker scaling with Celery.
- **Verification:** Verified in [`backend/main.py:89, 440-445`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/backend/main.py#L89).

---

### ADR-004: Binary GLTF (`.glb`) as Primary Delivery Artifact
- **Context:** Traditional photogrammetry produces loose multi-file archives: Wavefront OBJ (`.obj`), material library (`.mtl`), and texture atlas (`.png` or `.jpg`). Multi-file distribution requires zip packaging and complex client-side asset loading.
- **Decision:** Use Python `trimesh` and `pillow` to package geometry, vertex normals, UV mappings, and PBR diffuse materials into a single compressed binary GLTF container (`model.glb`), served at `GET /model/{job_id}`.
- **Trade-Offs:**
  - *Advantage:* Self-contained single-file download; native loader in Three.js (`GLTFLoader`); web-optimized binary structure.
  - *Constraint:* Does not store geodetic GIS CRS tags natively. GIS deliverables (LAS, GeoTIFF) are planned as separate download artifacts in Phase 4.
- **Verification:** Verified in [`backend/convert_to_glb.py:126-218`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/backend/convert_to_glb.py#L126-L218).

---

### ADR-005: Two-Stage Intelligent Pre-Processing Culling
- **Context:** Drone video shot at 30 or 60 FPS contains overwhelming frame redundancy and motion blur. Feeding raw video frames directly into COLMAP causes combinatorial explosion during SIFT feature matching ($O(N^2)$ pairs) and introduces triangulation error from blurry views.
- **Decision:** Implement a deterministic two-stage pre-processing filter:
  1. *Sharpness & Luminance Filter:* Laplacian variance threshold ($\text{Var}(\nabla^2 I) \ge 100.0$) with adaptive lowering floor ($20.0$), combined with luminance bounds ($[30, 240]$).
  2. *Redundancy Reduction Filter:* Mean absolute grayscale difference ($\Delta \ge 5.0$) with a 50% safety floor (`MAX_REMOVAL_RATIO = 0.50`).
- **Trade-Offs:**
  - *Advantage:* Discards 60% to 80% of frames while preserving angular coverage, cutting COLMAP runtime by over half.
  - *Constraint:* Requires tuning for extremely low-light or low-contrast environments.
- **Verification:** Verified in [`backend/frame_filtering.py`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/backend/frame_filtering.py) and [`backend/redundancy_filter.py`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/backend/redundancy_filter.py).

---

### ADR-006: Single-Model SfM (`--Mapper.multiple_models 0`)
- **Context:** COLMAP's default incremental mapper splits disconnected camera tracks into separate sub-models (`sparse/0/`, `sparse/1/`). Multiple sub-models produce disjointed partial geometries that cannot be fused into a single unified mesh.
- **Decision:** Pass `--Mapper.multiple_models 0` to the COLMAP `mapper` command, forcing the reconstruction of a single, coherent coordinate space.
- **Trade-Offs:**
  - *Advantage:* Guarantees a single cohesive 3D model.
  - *Constraint:* If camera tracks break due to insufficient visual overlap, unlinked cameras are dropped rather than forming a second sub-model. Enforces the 30% registration quality gate (`MIN_REGISTRATION_RATIO = 0.30`).
- **Verification:** Verified in [`backend/reconstruction.py:35, 237`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/backend/reconstruction.py#L35).

---

### ADR-007: Screened Poisson Meshing with 7.0% Boundary Trimming
- **Context:** Standard Screened Poisson surface reconstruction constructs an implicit indicator function across the entire bounding octree. In regions where point density drops (e.g. unobserved building sides or scene boundaries), Poisson reconstruction inflates large spherical "bubble" artifacts.
- **Decision:** Compute local vertex support densities in Open3D, calculate the 7.0th percentile threshold, and trim the lowest 7.0% of unconstrained boundary vertices (`POISSON_TRIM = 7.0`).
- **Trade-Offs:**
  - *Advantage:* Eliminates bulbous geometric inflation and yields clean, realistic building boundaries.
  - *Constraint:* Slightly trims true sparse perimeter points if flight capture was incomplete.
- **Verification:** Verified in [`backend/reconstruction.py:76, 480-505`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/backend/reconstruction.py#L76).

---

## 3. Resolution of Previously Open Technical Questions

| Open Question from Previous Audits | Verified Code Truth & Resolution | Canonical Reference |
|---|---|---|
| **Supported Video Formats & Codecs** | Formats: `.mp4, .mov, .avi, .mkv`. Decoded via OpenCV `cv2.VideoCapture()` supporting H.264, H.265/HEVC, and MJPEG. | [`docs/CONFIGURATION.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/CONFIGURATION.md) |
| **Validated Flight Capture Envelope** | $70\text{--}80\%$ overlap, $45^\circ\text{--}60^\circ$ oblique camera tilt, $3\text{--}5\text{ m/s}$ ground speed, orbital trajectory around target structure. | [`docs/PHOTOGRAMMETRY_FUNDAMENTALS.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/PHOTOGRAMMETRY_FUNDAMENTALS.md) |
| **Meshing & Texturing Algorithms** | Open3D Screened Poisson meshing (`depth=11`, trim `7.0%`) followed by COLMAP `mesh_texturer` UV unwrapping and patch projection. | [`docs/MESH_AND_GLB.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/MESH_AND_GLB.md) |
| **Realistic Accuracy Expectations** | High visual fidelity in arbitrary unscaled coordinates. Metric scale requires GCPs or GPS telemetry (Phase 3). Not certified for legal cadastral surveying. | [`docs/SECURITY_AND_ACCURACY_NOTES.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/SECURITY_AND_ACCURACY_NOTES.md) |
| **Storage & Worker Deployment Model** | Tested on single-node Windows 11 workstation with local GPU. Proposed cloud model: FastAPI on Fargate, Celery GPU workers on EC2 Spot (`g4dn.xlarge`), and S3 object storage. | [`docs/DEPLOYMENT.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/DEPLOYMENT.md) |
| **Download Deliverables in Scope** | v0.5 generates GLB and PLY. UI badges for LAS, GeoTIFF, and OBJ are prioritized in Phase 4 of the roadmap. | [`docs/FEATURE_STATUS.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/FEATURE_STATUS.md) |
