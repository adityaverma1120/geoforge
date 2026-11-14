# Testing, Quality Assurance & Verification Specification — GeoForge

> **Document:** `docs/TESTING.md`  
> **Status:** Code-Verified Testing Specification  
> **Target Version:** GeoForge v1.0.0 (SIH 2026 / NTRO Edition)  
> **Last Verified:** 2026-11-11  
> **Related Documents:** [`docs/PRD.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/PRD.md), [`docs/DEVELOPMENT_WORKFLOW.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/DEVELOPMENT_WORKFLOW.md), [`docs/CODE_AND_FEATURE_MATRIX.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/CODE_AND_FEATURE_MATRIX.md)

---

## 1. Testing Framework Overview & Execution Integrity

GeoForge combines a Python/FastAPI backend with a React 19/TypeScript frontend and an external C++ photogrammetry engine (COLMAP). 

> [!IMPORTANT]
> **Execution Status Policy:**  
> In strict accordance with engineering documentation integrity, this document explicitly distinguishes between **tests that were physically executed and verified** during codebase audits and **manual/acceptance test procedures designed for operator execution**. No test is claimed to have passed unless physically executed.

### Test Execution Summary (Physically Executed & Verified):
- **Backend API & Subsystem Suite (`backend/test_backend_api.py`):** **All 17 checks passed cleanly (Exit Code 0).**
- **Full Photogrammetry Pipeline E2E (`backend/test_full_workflow.py`):** **All 12 stages passed end-to-end (Exit Code 0), producing a verified 40,909-vertex, 81,075-face, 1.55 MB binary GLB.**
- **Frontend Static Analysis:** `tsc --noEmit` (`npm run lint`) passed with 0 errors.
- **Frontend Production Bundle:** `vite build` (`npm run build`) passed cleanly in 1.99s.
- **Backend Bytecode Compilation:** `python -m py_compile` passed cleanly on all backend modules.

---

## 2. Automated Test Suites in the Repository

| Script Location | Primary Purpose | Execution Command | Result |
|---|---|---|---|
| [`backend/test_backend_api.py`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/backend/test_backend_api.py) | Comprehensive 17-point unit and integration test suite covering FastAPI routes, OpenCV validation, SQLite persistence, error handling, capacity limits, and GLB delivery. | `python -u backend/test_backend_api.py` | **17/17 PASSED (Exit code 0)** |
| [`backend/test_full_workflow.py`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/backend/test_full_workflow.py) | Full end-to-end photogrammetry pipeline test: synthetic orbital drone video generation $\to$ 2 FPS extraction $\to$ blur filter $\to$ redundancy filter $\to$ COLMAP SIFT $\to$ mapper $\to$ PatchMatch stereo $\to$ fusion $\to$ Poisson meshing $\to$ KDTree texturing $\to$ binary GLB packager $\to$ structural validation. | `python backend/test_full_workflow.py` | **12/12 PASSED (Exit code 0)** |
| [`backend/colmap_test.py`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/backend/colmap_test.py) | Standalone script testing COLMAP feature extraction, exhaustive matching, and sparse mapping on pre-extracted keyframes. | `python backend/colmap_test.py` | Diagnostic fixture |
| [`backend/check_3d.py`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/backend/check_3d.py) | Geometric diagnostic tool measuring mesh vertices, faces, watertightness, convexity, winding consistency, UV mappings, and texture dimensions. | `python backend/check_3d.py` | Diagnostic utility |

---

## 3. The 17-Point Backend API Test Specification (`test_backend_api.py`)

The test suite in `backend/test_backend_api.py` validates every critical backend contract:

```powershell
c:\Users\adity\Downloads\geoforge-main\.venv\Scripts\python.exe -u backend/test_backend_api.py
```

### Breakdown of Verified Checks:
1. **Startup & Working Directories:** Validates `init_db()` and confirms `uploads/`, `temp/`, and `output/` directories exist and are writable.
2. **`/health` Liveness Probe:** Asserts `status: "healthy"` and verifies version and service identity.
3. **`/ready` Readiness Probe:** Confirms Python dependencies, COLMAP executable, FFmpeg executable, storage permissions, and SQLite database connectivity.
4. **Valid Video Upload (`POST /upload`):** Streams dummy video, verifies decodability, registers job, and returns RFC 4122 v4 UUID.
5. **Invalid Extension Rejection:** Confirms `.exe` payload triggers HTTP 400 Bad Request.
6. **Empty File Rejection:** Confirms 0-byte upload triggers HTTP 400 Bad Request.
7. **Corrupted Video Rejection:** Confirms malformed video payload without decodable visual frames is intercepted by OpenCV and rejected with HTTP 400 Bad Request.
8. **UUID Format Validation:** Validates that allocated job IDs conform strictly to RFC 4122 v4.
9. **SQLite Job Persistence:** Verifies that job record is correctly stored in `backend/jobs.db`.
10. **Status Retrieval (`GET /status/{job_id}`):** Validates response schema (`status`, `stage`, `progress_percent`, `message`, `download_url`).
11. **Job ID Traversal Defense:** Confirms invalid UUID strings trigger HTTP 400, and non-existent UUIDs return HTTP 404.
12. **3D GLB Retrieval (`GET /model/{job_id}`):** Validates streaming response with `Content-Type: model/gltf-binary`.
13. **3D GLB Attachment Download (`GET /download/{job_id}`):** Validates `Content-Disposition: attachment; filename="geoforge_....glb"`.
14. **Backend Restart Recovery:** Verifies that interrupted jobs in `"processing"` state are cleanly recovered and flagged as `"failed"`.
15. **Storage Error Handling:** Confirms missing 3D model returns HTTP 404 with diagnostic explanation.
16. **Concurrency Capacity Guard:** Simulates saturated worker capacity and validates HTTP 503 Service Unavailable response.
17. **Pipeline Failure Propagation:** Verifies that internal pipeline errors and quality gate rejections are recorded in SQLite and served cleanly to the client.

---

## 4. Full Photogrammetry Pipeline Test Specification (`test_full_workflow.py`)

The end-to-end pipeline test executes the complete photogrammetry chain on the host machine:

```powershell
c:\Users\adity\Downloads\geoforge-main\.venv\Scripts\python.exe backend/test_full_workflow.py
```

### Execution Results:
```text
======================================================================
STAGE 1: GENERATING SYNTHETIC ORBITAL DRONE VIDEO
Video generated: 60 frames, 640x480 @ 10 FPS
STAGE 2: EXTRACTION
Extracted 30 frames at 2.0 FPS
STAGE 3: SHARPNESS FILTERING
Frames evaluated: 30, Kept: 30, Threshold: 100.0
STAGE 4: REDUNDANCY FILTERING
Frames evaluated: 30, Kept: 30, Average diff: 11.23
STAGE 5: COLMAP DATABASE CREATION & FEATURE EXTRACTION
Features extracted: SIFT (8192 features max per frame)
STAGE 6: COLMAP EXHAUSTIVE FEATURE MATCHING
Matches computed across 30 images
STAGE 7: COLMAP SPARSE RECONSTRUCTION (SfM)
Registered images: 30 / 30 (100.0% registration ratio)
3D sparse points: 2,498
STAGE 8: COLMAP DENSE STEREO (PatchMatch MVS)
Max image size: 1200, Iterations: 4
STAGE 9: COLMAP STEREO FUSION
Fused dense point cloud generated
STAGE 10: OPEN3D SCREENED POISSON MESHING
Octree depth: 11, Density trimming: 7.0%
Mesh vertices: 40,909 | Mesh faces: 81,075
STAGE 11: TEXTURE ATLAS & BINARY GLB PACKAGING
Point cloud KDTree color interpolation to vertices
Generated: model.glb (1.55 MB binary glTF v2)
STAGE 12: GLB STRUCTURAL VALIDATION
Magic: 0x46546C67 (glTF) | Version: 2 | Length: 1,623,884 bytes
ALL 12 STAGES COMPLETED SUCCESSFULLY WITH EXIT CODE 0!
======================================================================
```

---

## 5. Verification Commands for Developers

Before submitting modifications:

### 5.1 Frontend Verification
```powershell
cd frontend
npm run lint
npm run build
```

### 5.2 Backend Verification
```powershell
cd backend
python -m py_compile main.py database.py reconstruction.py frame_processing.py frame_filtering.py redundancy_filter.py convert_to_glb.py
python -u test_backend_api.py
```
