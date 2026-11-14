# Testing Patterns

**Analysis Date:** 2026-11-12

## Test Framework

**Backend Test Runner:**
- Standard Python test scripts executed via direct interpreter calls or `unittest`:
  - `backend/test_backend_api.py` — 17-point integration test suite testing all REST API endpoints.
  - `backend/test_reconstruction_smoke.py` — Smoke test verifying pipeline steps with sample assets.
  - `backend/test_phase4_reconstruction.py` — Full pipeline photogrammetry integration test.
- Python syntax validator: `python -m py_compile` for bytecode verification.

**Frontend Verification:**
- TypeScript Compiler: `tsc --noEmit` via `npm run lint`.
- Production Bundler: `vite build` via `npm run build`.
- (Note: Jest / Vitest unit test runner is currently not installed in `frontend/package.json`).

**Run Commands:**
```powershell
# 1. Validate Python backend bytecode
.venv\Scripts\python.exe -m py_compile backend/*.py

# 2. Run backend API integration test suite (17 checks)
.venv\Scripts\python.exe backend/test_backend_api.py

# 3. Verify frontend TypeScript types
cd frontend
npm run lint

# 4. Verify frontend production build bundle
npm run build
```

## Test File Organization

**Location:**
- Backend tests live directly inside `backend/` as dedicated test modules prefixed with `test_`.
- Root evaluation scripts (`clean_pointcloud.py`, `inspect_mesh.py`, `inspect_pointcloud.py`) reside at the repository root.

**Naming:**
- `test_*.py` for backend integration and smoke tests:
  - `backend/test_backend_api.py`
  - `backend/test_reconstruction_smoke.py`
  - `backend/test_full_workflow.py`
  - `backend/test_phase4_reconstruction.py`

**Structure:**
```
backend/
├── test_backend_api.py              # API endpoint suite (17 checks)
├── test_reconstruction_smoke.py    # Photogrammetry smoke test
├── test_full_workflow.py            # End-to-end integration test
└── test_phase4_reconstruction.py    # Pipeline regression test
```

## Test Structure

**Backend API Test Pattern (`test_backend_api.py`):**
```python
import sys
import unittest
import requests

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint():
    # 1. Arrange: Prepare payload, query parameters, or fake file
    files = {"file": ("test.mp4", b"\x00" * 1024, "video/mp4")}

    # 2. Act: Send HTTP request
    response = requests.post(f"{BASE_URL}/upload", files=files)

    # 3. Assert: Verify HTTP status code and response contract
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "job_id" in data, "Response missing job_id"
    assert data["status"] in ("queued", "processing")
```

**Execution Pattern:**
- Sequential execution of test cases with clear step labels (`[1/17]`, `[2/17]`, ...).
- Immediate exit with code 1 upon failure with assertion message and server response detail.
- Summary banner printed on completion with total passed count.

## Mocking

**What to Mock:**
- Synthetic Video Generation: `backend/generate_test_video.py` generates deterministic synthetic MP4 video frames using OpenCV `cv2.VideoWriter` for rapid testing without large external video downloads.
- Small In-Memory Buffers: Synthetic binary headers for container validation testing.

**What NOT to Mock:**
- SQLite Database: Tests interact with the actual SQLite file or a test instance to ensure real transaction isolation and schema compliance.
- Binary GLB Validator: Real Trimesh and GLTF binary header verification (`validate_glb()`) on authentic 3D assets.
- FastApi HTTP Routing: Real HTTP calls against the running Uvicorn server on `127.0.0.1:8000`.

## Fixtures and Factories

**Test Videos:**
- `backend/generate_test_video.py` creates a 5-second rotating cube or textured test sequence.
- Verified Drone Orbit Sample: `backend/uploads/sample_drone_orbit.mp4` (38.8 MB authentic drone flight video used for real SfM reconstruction).

**Pre-Reconstructed Model Fixture:**
- Real 3D Asset: `backend/temp/dda15414-1842-4633-b013-b91e84564d5f/colmap/textured/model.glb` (1.55 MB binary glTF v2 with embedded textures, 40,909 vertices, 81,075 faces).
- Manifest: `backend/temp/dda15414-1842-4633-b013-b91e84564d5f/metadata.json`.

## Coverage

**Requirements:**
- Core API Endpoints: 100% route coverage verified in `test_backend_api.py`:
  - `/health`
  - `/ready`
  - `/upload` (success, empty payload, invalid container type, invalid size)
  - `/status/{job_id}` (valid ID, invalid UUID, non-existent job)
  - `/jobs` (listing, limit capping)
  - `/jobs/{job_id}/cancel` (cancellation handling)
  - `/jobs/{job_id}` (deletion cleanup)
  - `/model/{job_id}` (GET download, HEAD check)
  - `/metadata/{job_id}` (photogrammetric metadata manifest)
- Frontend: Static type correctness (`tsc --noEmit`) and bundle integrity (`vite build`).

## Test Types

**Unit Tests:**
- Video container validation (`validate_video`) in `backend/frame_processing.py`.
- Laplacian variance blur thresholding in `backend/frame_filtering.py`.
- Binary GLB geometry validation (`validate_glb`) in `backend/convert_to_glb.py`.

**Integration Tests:**
- API and database lifecycle in `backend/test_backend_api.py`.
- Server recovery test: verifying that orphaned jobs transition from `processing` to `failed` upon startup.

**End-to-End Photogrammetry Tests:**
- `backend/test_full_workflow.py` executing extraction, filtering, COLMAP SIFT, mapping, dense stereo, Open3D Poisson meshing, and GLB packaging against real video footage.

## Common Patterns

**Subprocess Safety Verification:**
- Testing that all external binary calls (COLMAP) correctly return exit code 0 and capture stdout/stderr without hang on Windows.

**Server Capacity Guard Testing:**
- Ensuring that when a job is actively processing, subsequent upload requests receive `HTTP 503` to prevent GPU memory saturation.

---

*Testing analysis: 2026-11-12*
*Update when test patterns change*

