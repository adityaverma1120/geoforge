# Code and Feature Verification Matrix — GeoForge

> **Document:** `docs/CODE_AND_FEATURE_MATRIX.md`  
> **Status:** Canonical Verified Feature-to-Code Mapping  
> **Target Version:** GeoForge v1.0.0 (SIH 2026 / NTRO Edition)  
> **Related Documents:** [`docs/FEATURE_STATUS.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/FEATURE_STATUS.md), [`docs/CODEBASE_MAP.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/CODEBASE_MAP.md), [`docs/TESTING.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/TESTING.md)

---

## 1. Feature to Source Symbol Mapping

The following matrix maps every user-facing feature in GeoForge directly to its backend and frontend implementation symbols, test verification procedures, and expected results:

| Feature / Capability | Backend Symbol(s) | Frontend Symbol(s) | Verification Command / Procedure | Expected Outcome |
|---|---|---|---|---|
| **Service Root & Health** | `backend/main.py`<br/>`home()`, `health()` | `frontend/src/services/api.ts` | `curl -i http://127.0.0.1:8000/health`<br/>`curl -i http://127.0.0.1:8000/` | HTTP 200 with `status: "healthy"`, version, and subsystem diagnostic data. |
| **Subsystem Readiness Probe** | `backend/main.py`<br/>`ready()` | N/A (DevOps / Health check) | `curl -i http://127.0.0.1:8000/ready` | HTTP 200 with `status: "ready"`, checking COLMAP, FFmpeg, SQLite, disk space, and worker capacity. |
| **Video File Selection & Upload** | `backend/main.py`<br/>`upload_video()` | `pages/UploadPage.tsx`<br/>`handleDrop()`, `handleFileSelect()` | Upload 1080p MP4 via UI or `curl -F file=@test.mp4 http://127.0.0.1:8000/upload` | HTTP 200 with `job_id`, `status: uploaded`, file saved to `backend/uploads/`. |
| **Pre-Ingestion Decodability Gate** | `backend/main.py`<br/>`cv2.VideoCapture` validation | `pages/UploadPage.tsx`<br/>Error modal | Upload 0-byte or corrupted non-video file | HTTP 400 Bad Request before occupying worker thread. |
| **Payload Size Enforcement** | `backend/main.py`<br/>`MAX_UPLOAD_BYTES` (4 GiB) | `pages/UploadPage.tsx`<br/>Client size warning | Send request with declared `Content-Length > 4 GiB` | HTTP 413 `Payload Too Large` before streaming payload to disk. |
| **Format Extension Allowlist** | `backend/main.py`<br/>`allowed_extensions` | `pages/UploadPage.tsx`<br/>Extension check | Submit file with `.wmv` or `.exe` extension | HTTP 400 `Bad Request` with list of allowed extensions. |
| **Job Concurrency Guard** | `backend/main.py`<br/>`MAX_CONCURRENT_RECONSTRUCTIONS = 1` | `services/api.ts`<br/>Error handling | Submit simultaneous upload while job is processing | Request rejected with HTTP 503 `Service Unavailable`. |
| **SQLite Job Persistence** | `backend/database.py`<br/>`init_db()`, `create_job()`, `get_job()` | `services/api.ts` | Query `jobs.db` via sqlite3 CLI | Full job history, timestamps, progress, and stage persisted across server restarts. |
| **Crash & Interruption Recovery** | `backend/database.py`<br/>`recover_interrupted_jobs()` | `pages/ProcessingPage.tsx` | Kill backend during reconstruction and restart | Interrupted jobs flagged as `failed` with diagnostic explanation. |
| **Job Cancellation** | `backend/main.py`<br/>`cancel_job_endpoint()`, `database.cancel_job()` | Frontend cancel button | `curl -X POST http://127.0.0.1:8000/jobs/{job_id}/cancel` | HTTP 200 with `status: "cancelled"`, halting pipeline execution. |
| **Frame Extraction (2 FPS)** | `backend/frame_processing.py`<br/>`extract_frames()` | N/A (Backend worker) | Run unit test with 30-sec 30 FPS video | Exactly $60 \pm 1$ raw JPEG frames extracted into `temp/{id}/frames/`. |
| **Laplacian Blur Filtering** | `backend/frame_filtering.py`<br/>`filter_sharp_frames()`, `calculate_sharpness()` | N/A (Backend worker) | Process mix of intentionally blurred and crisp frames | Blurry frames discarded; adaptive threshold lowers to 20.0 if $>40\%$ rejected. |
| **Redundancy Reduction** | `backend/redundancy_filter.py`<br/>`remove_redundant_frames()` | N/A (Backend worker) | Process static hover footage ($>80\%$ identical frames) | Near-duplicates pruned ($\Delta < 5.0$) while enforcing 50% safety retention floor. |
| **Usable Frame Gate** | `backend/main.py`<br/>`MIN_FRAMES_FOR_RECONSTRUCTION` | `components/DiagnosticsAccordion.tsx` | Process short video yielding $<20$ frames | Job halts cleanly with diagnostic error: `"Only X frames passed filtering. At least 20 are needed"`. |
| **COLMAP SfM Mapping** | `backend/reconstruction.py`<br/>`run_reconstruction()` | N/A (Backend worker) | Execute feature extraction and sequential matching | Largest coherent sparse model selected from multi-model mapper output. |
| **Sparse Quality Gate** | `backend/reconstruction.py`<br/>`check_sparse_reconstruction_quality()` | `components/DiagnosticsAccordion.tsx` | Simulate disconnected camera trajectories | Halts with error if registered images ratio $< 30\%$ (`MIN_REGISTRATION_RATIO`). |
| **Dense MVS Point Cloud** | `backend/reconstruction.py`<br/>PatchMatch & Stereo Fusion | N/A (Backend worker) | Trace MVS output in `colmap/dense/` | Generates non-empty `colmap/dense/fused.ply`. |
| **Open3D Point Denoising** | `backend/reconstruction.py`<br/>`remove_statistical_outlier()` | N/A (Backend worker) | Inspect point counts before and after denoising | Outlier points pruned (`nb=20, std=2.0`), writes `colmap/dense/fused_cleaned.ply`. |
| **Screened Poisson Meshing** | `backend/reconstruction.py`<br/>`poisson_mesh_with_trimming()` | N/A (Backend worker) | Inspect mesh vertices and boundary faces | Poisson octree depth 11 solved; bottom 7.0% low-density vertices pruned (`poisson_mesh.ply`). |
| **Projective Texturing** | `backend/reconstruction.py`<br/>KDTree color transfer & UV mapper | N/A (Backend worker) | Check `colmap/textured/` directory | Generates `model.ply` and diffuse texture atlas `model.png`. |
| **Binary GLB Packaging** | `backend/convert_to_glb.py`<br/>`convert_to_glb()` | N/A (Backend worker) | Run validator on `temp/{id}/colmap/textured/model.glb` | Non-empty binary GLB with embedded PBR material and diffuse texture. |
| **Job Status Polling** | `backend/main.py`<br/>`get_status()` | `services/api.ts`<br/>`getJobStatus()` | Poll `GET /status/{job_id}` at adaptive intervals | Returns accurate status, stage, progress %, timestamps, and `result` dictionary. |
| **Binary Model Serving** | `backend/main.py`<br/>`get_model()`, `check_model()` | `services/api.ts`<br/>`getModelGlbUrl()`, `checkModelAvailability()` | `curl -I http://127.0.0.1:8000/model/{job_id}`<br/>`curl -o out.glb http://...` | Streams GLB with `Content-Type: model/gltf-binary` and valid `Content-Length`. |
| **GLB Attachment Download** | `backend/main.py`<br/>`download_model()` | `services/api.ts`<br/>`getModelGlbUrl()` | `curl -i http://127.0.0.1:8000/download/{job_id}` | Serves file with `Content-Disposition: attachment; filename="geoforge_....glb"`. |
| **Interactive 3D Viewer** | N/A (Client WebGL) | `components/ThreeDViewer.tsx`<br/>Three.js `GLTFLoader` | Load completed model in browser viewport | Model centers dynamically; mouse orbit, zoom, pan, and lighting controls operate smoothly. |
| **Error Diagnostics UI** | `backend/main.py`<br/>`job.error` serialization | `components/DiagnosticsAccordion.tsx`, `ErrorView.tsx` | Trigger deliberate reconstruction failure | Expandable diagnostics accordion displays raw failure cause and suggested remediation. |
