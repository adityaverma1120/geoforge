# REST API Specification — GeoForge

> **Document:** `docs/API.md`  
> **Status:** Code-Verified API Specification (Phase 3 Verified)  
> **Target Version:** GeoForge v1.0.0 (SIH 2026 / NTRO Edition)  
> **Source Verification Date:** 2026-11-11  
> **Related Documents:** [`docs/BACKEND.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/BACKEND.md), [`docs/JOB_MANAGEMENT.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/JOB_MANAGEMENT.md), [`docs/FRONTEND.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/FRONTEND.md)

---

## 1. Overview & Service Base URL

The GeoForge backend is implemented in FastAPI (`backend/main.py`). The default local development endpoint is:
```text
http://127.0.0.1:8000
```
The React frontend configures its connection via the `VITE_API_URL` environment variable (falling back to `http://127.0.0.1:8000`).

---

## 2. Complete Endpoints Reference

### 2.1 `GET /` — Service Information
Returns backend service identity, online status, and version.
- **Method:** `GET`
- **Response Code:** `200 OK`
- **Response Body (`backend/main.py:140-147`):**
  ```json
  {
    "status": "online",
    "service": "GeoForge Reconstruction API",
    "version": "1.0.0",
    "description": "Single-Pass Drone Video to 3D Model Generation System"
  }
  ```

---

### 2.2 `GET /health` — Liveness & Diagnostics Probe
Fast liveness check indicating that the FastAPI service is running, while providing system diagnostic fields.
- **Method:** `GET`
- **Response Code:** `200 OK`
- **Response Body (`backend/main.py:154-206`):**
  ```json
  {
    "status": "healthy",
    "service": "GeoForge Reconstruction API",
    "version": "1.0.0",
    "reconstruction_ready": true,
    "colmap": {
      "available": true,
      "path": "C:\\Users\\adity\\AppData\\Local\\Programs\\COLMAP\\bin\\colmap.exe",
      "version": "COLMAP 3.9.1 (CUDA)"
    },
    "ffmpeg": {
      "available": true,
      "path": "C:\\Users\\adity\\AppData\\Local\\Programs\\ffmpeg\\bin\\ffmpeg.exe"
    },
    "storage": {
      "disk_free_gb": 105.69,
      "writable": true
    },
    "concurrency": {
      "active_jobs": 0,
      "max_concurrent": 1
    }
  }
  ```

---

### 2.3 `GET /ready` — Subsystem Readiness Probe
Deep readiness endpoint verifying core dependencies, external CLI availability, storage permissions, database connectivity, and worker capacity before dispatching jobs.
- **Method:** `GET`
- **Response Codes:**
  - `200 OK`: All subsystems ready.
  - `503 Service Unavailable`: Subsystem missing, database unreachable, or capacity saturated.
- **Response Body (`backend/main.py:213-286`):**
  ```json
  {
    "status": "ready",
    "service": "GeoForge Reconstruction API",
    "version": "1.0.0",
    "reconstruction_ready": true,
    "database_connected": true,
    "dependencies_loaded": true,
    "colmap": {
      "available": true,
      "path": "C:\\Users\\adity\\AppData\\Local\\Programs\\COLMAP\\bin\\colmap.exe"
    },
    "ffmpeg": {
      "available": true,
      "path": "C:\\Users\\adity\\AppData\\Local\\Programs\\ffmpeg\\bin\\ffmpeg.exe"
    },
    "storage": {
      "disk_free_gb": 105.69,
      "writable": true
    },
    "concurrency": {
      "active_jobs": 0,
      "max_concurrent": 1,
      "capacity_available": true
    }
  }
  ```

---

### 2.4 `POST /upload` — Video Ingestion, Validation & Pipeline Dispatch
Streams uploaded video to `backend/uploads/{job_id}_{filename}`, validates video decodability and frames via OpenCV, registers the job in persistent SQLite (`jobs.db`), and dispatches reconstruction in the thread pool.
- **Method:** `POST`
- **Content-Type:** `multipart/form-data`
- **Form Fields:** `file: UploadFile` (Binary video file)
- **Allowed Formats:** `.mp4`, `.mov`, `.avi`, `.mkv` (`backend/main.py:516`)
- **Max Upload Size:** 4 GiB (`4,294,967,296` bytes, checked against `Content-Length` header)
- **Concurrency Limit:** Rejects upload if a reconstruction is currently active (`MAX_CONCURRENT_RECONSTRUCTIONS = 1`).

#### Responses
- **`200 OK` (Accepted & Enqueued):**
  ```json
  {
    "status": "uploaded",
    "message": "Video uploaded successfully. Reconstruction is running in background.",
    "job_id": "64fd25cd-52e5-4245-aa4d-cbf3940b84f2",
    "filename": "drone_flight.mp4",
    "status_url": "/status/64fd25cd-52e5-4245-aa4d-cbf3940b84f2",
    "status_absolute": "http://127.0.0.1:8000/status/64fd25cd-52e5-4245-aa4d-cbf3940b84f2",
    "model_url": "/model/64fd25cd-52e5-4245-aa4d-cbf3940b84f2",
    "model_absolute": "http://127.0.0.1:8000/model/64fd25cd-52e5-4245-aa4d-cbf3940b84f2",
    "download_url": "/download/64fd25cd-52e5-4245-aa4d-cbf3940b84f2",
    "poll_interval_seconds": 3
  }
  ```
- **`400 Bad Request` (Empty Filename or Empty File):**
  ```json
  {
    "detail": "Uploaded file is empty."
  }
  ```
- **`400 Bad Request` (Unsupported Format):**
  ```json
  {
    "detail": "Unsupported video format: .exe. Supported formats are MP4, MOV, AVI and MKV."
  }
  ```
- **`400 Bad Request` (Corrupted or Undecodable Video):**
  ```json
  {
    "detail": "Uploaded file is not a valid or readable video."
  }
  ```
- **`413 Payload Too Large` (Oversized File):**
  ```json
  {
    "detail": "File is too large. Maximum allowed size is 4 GB."
  }
  ```
- **`503 Service Unavailable` (Worker Saturated):**
  ```json
  {
    "detail": "Reconstruction server is at capacity (1 jobs running). Please try again in a few minutes."
  }
  ```

---

### 2.5 `GET /status/{job_id}` — Job Status & Metrics Polling
Polls current execution status, stage, progress percentage, diagnostic failure reasons, and comprehensive pipeline metrics from the persistent SQLite database.
- **Method:** `GET`
- **Path Parameter:** `job_id` (Valid UUID4 string)
- **Status Enum Values:** `"queued"`, `"processing"`, `"complete"`, `"failed"`

#### Responses
- **`200 OK` (Processing with Stage Progress):**
  ```json
  {
    "job_id": "64fd25cd-52e5-4245-aa4d-cbf3940b84f2",
    "status": "processing",
    "stage": "dense_stereo",
    "progress_percent": 65,
    "message": "Computing MVS depth maps...",
    "filename": "drone_flight.mp4",
    "model_available": false,
    "model_url": "/model/64fd25cd-52e5-4245-aa4d-cbf3940b84f2",
    "download_url": "/download/64fd25cd-52e5-4245-aa4d-cbf3940b84f2",
    "created_at": "2026-11-11T13:40:21.000000+00:00",
    "updated_at": "2026-11-11T13:41:05.000000+00:00",
    "completed_at": null
  }
  ```
- **`200 OK` (Reconstruction Complete with Full Metrics):**
  ```json
  {
    "job_id": "64fd25cd-52e5-4245-aa4d-cbf3940b84f2",
    "status": "complete",
    "stage": "completed",
    "progress_percent": 100,
    "message": "Reconstruction completed successfully!",
    "filename": "drone_flight.mp4",
    "model_available": true,
    "model_url": "/model/64fd25cd-52e5-4245-aa4d-cbf3940b84f2",
    "download_url": "/download/64fd25cd-52e5-4245-aa4d-cbf3940b84f2",
    "created_at": "2026-11-11T13:40:21.000000+00:00",
    "updated_at": "2026-11-11T13:42:15.000000+00:00",
    "completed_at": "2026-11-11T13:42:15.000000+00:00",
    "result": {
      "model_path": "backend/temp/64fd25cd-52e5-4245-aa4d-cbf3940b84f2/colmap/textured/model.glb",
      "model_url": "/model/64fd25cd-52e5-4245-aa4d-cbf3940b84f2",
      "download_url": "/download/64fd25cd-52e5-4245-aa4d-cbf3940b84f2",
      "glb_size_mb": 1.55,
      "frames_extracted": 60,
      "frames_used": 30,
      "num_sparse_points": 2498,
      "num_cameras": 1,
      "num_registered_images": 30,
      "warnings": []
    }
  }
  ```
- **`200 OK` (Reconstruction Failed):**
  ```json
  {
    "job_id": "64fd25cd-52e5-4245-aa4d-cbf3940b84f2",
    "status": "failed",
    "stage": "sparse_reconstruction",
    "progress_percent": 30,
    "message": "Reconstruction failed: Registration ratio 12% below 30% threshold.",
    "error": "Registration ratio 12% below 30% threshold.",
    "filename": "drone_flight.mp4",
    "model_available": false,
    "model_url": "/model/64fd25cd-52e5-4245-aa4d-cbf3940b84f2",
    "download_url": "/download/64fd25cd-52e5-4245-aa4d-cbf3940b84f2"
  }
  ```
- **`400 Bad Request` (Malformed UUID):**
  ```json
  {
    "detail": "Invalid job ID format."
  }
  ```
- **`404 Not Found` (Job Does Not Exist):**
  ```json
  {
    "detail": "Job not found: 8d120db9-e9c1-4200-9c28-8c44e14e5426. The job may have expired or was never created."
  }
  ```

---

### 2.6 `GET /model/{job_id}` — Stream Binary 3D Model (GLB)
Streams the generated binary GLB file located at `backend/temp/{job_id}/colmap/textured/model.glb` for inline WebGL rendering in Three.js.
- **Method:** `GET`
- **Path Parameter:** `job_id` (Valid UUID4 string)
- **Responses:**
  - **`200 OK`:** Streams binary GLB data with headers:
    - `Content-Type: model/gltf-binary`
    - `Cache-Control: public, max-age=86400`
  - **`400 Bad Request`:** Malformed UUID4 format.
  - **`404 Not Found`:** Model not yet ready or job does not exist (`3D model not found or still generating for job: ...`).
  - **`500 Internal Server Error`:** GLB file exists on disk but is 0 bytes (`3D model file is empty.`).

---

### 2.7 `GET /download/{job_id}` — Download 3D Model Attachment
Serves the generated GLB file with an explicit `Content-Disposition: attachment` header forcing browser file download.
- **Method:** `GET`
- **Path Parameter:** `job_id` (Valid UUID4 string)
- **Responses:**
  - **`200 OK`:** Streams binary GLB data with headers:
    - `Content-Type: model/gltf-binary`
    - `Content-Disposition: attachment; filename="geoforge_64fd25cd.glb"`
  - **`400 Bad Request`:** Malformed UUID4 format.
  - **`404 Not Found`:** Model not found or job missing.

---

### 2.8 `HEAD /model/{job_id}` — Model Availability Probe
Checks if the GLB model exists and is ready for download without streaming the payload.
- **Method:** `HEAD`
- **Path Parameter:** `job_id` (Valid UUID4 string)
- **Responses:**
  - **`200 OK`:** Headers present:
    - `Content-Length: <size_in_bytes>`
    - `Content-Type: model/gltf-binary`
  - **`400 Bad Request`:** Malformed UUID format.
  - **`404 Not Found`:** Model not yet ready or job does not exist.

---

### 2.9 `POST /jobs/{job_id}/cancel` — Cancel Reconstruction Job
Allows clients to cancel a queued or running reconstruction job, releasing system resources.
- **Method:** `POST`
- **Path Parameter:** `job_id` (Valid UUID4 string)
- **Responses:**
  - **`200 OK`:**
    ```json
    {
      "status": "cancelled",
      "job_id": "64fd25cd-52e5-4245-aa4d-cbf3940b84f2",
      "message": "Reconstruction job cancelled successfully."
    }
    ```
  - **`400 Bad Request`:** Malformed UUID format.
  - **`404 Not Found`:** Job does not exist.
