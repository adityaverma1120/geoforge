# Security Architecture & Risk Assessment — GeoForge

> **Document:** `docs/SECURITY.md`  
> **Status:** Code-Verified Security Specification & Vulnerability Assessment  
> **Target Version:** GeoForge v1.0.0 (SIH 2026 / NTRO Edition)  
> **Last Verified:** 2026-11-11  
> **Related Documents:** [`docs/ARCHITECTURE.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/ARCHITECTURE.md), [`docs/SECURITY_AND_ACCURACY_NOTES.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/SECURITY_AND_ACCURACY_NOTES.md), [`docs/API.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/API.md)

---

## 1. Security Architecture Summary

GeoForge is designed for processing untrusted, multi-gigabyte video files and generating complex 3D meshes. Because photogrammetry involves external native CLI binaries (COLMAP) and C++ computer vision runtimes (OpenCV, Open3D), strict input sanitization, pre-ingestion validation, and boundary defense are essential.

This document clearly demarcates **verified protections currently active in the codebase** from **potential vulnerabilities and operational risks**.

---

## 2. In-Depth Security Audit by Domain

### 2.1 File Upload Validation
| Aspect | Current Implementation Status | Security Evaluation |
|---|---|---|
| **Extension Whitelisting** | **Verified Active** (`backend/main.py:516-524`) | Backend checks `extension in {".mp4", ".mov", ".avi", ".mkv"}`. Requests with unauthorized extensions (`.exe`, `.sh`, `.php`, `.zip`) are immediately rejected with HTTP 400. |
| **Empty File Rejection** | **Verified Active** (`backend/main.py:544-548`) | Files with 0 bytes are immediately intercepted and deleted with HTTP 400 `"Uploaded file is empty."` |
| **Pre-Ingestion Decodability Gate** | **Verified Active** (`backend/main.py:550-574`) | Before job creation or worker dispatch, OpenCV opens the video stream via `cv2.VideoCapture()`. If `cap.isOpened()` is False, or if decoded `frame_count <= 0`, `width <= 0`, or `height <= 0`, the file and workspace directory are immediately unlinked, and the request is rejected with HTTP 400 `"Uploaded file is not a valid or readable video."` |
| **Magic-Byte Inspection** | ℹ️ **Container Gate Active** | OpenCV's C++ demuxer natively validates container headers (MP4 `moov`/`ftyp`, AVI `RIFF`, MKV EBML) during the pre-ingestion validation check. |

---

### 2.2 File Size Limits & Denial of Service (DoS)
| Aspect | Current Implementation Status | Security Evaluation |
|---|---|---|
| **Header-Based Limit** | **Verified Active** (`backend/main.py:506-511`) | Enforces `MAX_UPLOAD_BYTES = 4 * 1024 * 1024 * 1024` ($4\text{ GiB}$) by checking `request.headers.get("content-length")`. Returns HTTP 413 `Payload Too Large`. |
| **Streaming Chunked Guard** | **Verified Active** (`backend/main.py:535`) | Streams video chunks directly to disk using `shutil.copyfileobj`, avoiding memory buffering of 4 GB payloads into server RAM. |
| **Concurrency Saturation Guard** | **Verified Active** (`backend/main.py:587-603`) | Inspects active jobs in SQLite before queuing. If an active job is already processing, rejects with HTTP 503 `"Reconstruction server is at capacity"`. |

---

### 2.3 Path Traversal & Workspace Isolation
| Aspect | Current Implementation Status | Security Evaluation |
|---|---|---|
| **Upload Path Sanitization** | **Verified Active** (`backend/main.py:517`) | Extracts `Path(file.filename).name`, discarding all relative path traversal tokens (e.g. `../../etc/passwd` becomes `passwd`). |
| **Filename Prefixing** | **Verified Active** (`backend/main.py:530`) | Prepends a UUID4 token: `video_path = UPLOAD_DIR / f"{job_id}_{original_filename}"`. Prevents file collision or overwriting of existing uploads. |
| **Workspace Sandboxing** | **Verified Active** (`backend/main.py:527-529`) | Each job operates in an isolated directory: `backend/temp/{job_id}/`. Subdirectories (`frames/`, `colmap/`) are strictly confined within this root. |
| **Safe GLB Path Resolution** | **Verified Active** (`backend/main.py:657-674`) | `_resolve_glb(job_id)` validates the UUID4 format, resolves the physical target via `candidate.resolve()`, and verifies that the resolved path is strictly relative to `TEMP_DIR` or `OUTPUT_DIR`. Rejects any traversal attempt with HTTP 400. |

---

### 2.4 Temporary File Cleanup & Disk Exhaustion
| Aspect | Current Implementation Status | Security Evaluation |
|---|---|---|
| **Automated Job Cleanup** | **Verified Active** (`backend/main.py:293-308`) | `_cleanup_job_files()` runs as an asynchronous background task, sleeping for `JOB_RETENTION_SECONDS = 604800` ($7\text{ days}$) before deleting `job_dir` and the original upload. |
| **Persistent Job Recovery** | **Verified Active** (`backend/database.py:198-219`) | All job records and failure states are persisted in SQLite (`backend/jobs.db`). On startup, `recover_interrupted_jobs()` flags crashed jobs as failed, allowing clean status inspection and preventing orphaned running states. |

---

### 2.5 API Access, Authentication & Authorization
| Aspect | Current Implementation Status | Security Evaluation |
|---|---|---|
| **Endpoint Authentication** | ⚠️ **Prototype Design** | All endpoints (`/upload`, `/status/{job_id}`, `/model/{job_id}`, `/download/{job_id}`) are unauthenticated in the local hackathon prototype. For enterprise/defense deployment, reverse-proxy mTLS or OAuth2/JWT should be fronted. |
| **Job Access Control** | ℹ️ **UUIDv4 Entropy** | Job URLs are protected by 128-bit RFC 4122 v4 UUIDs (122 bits of cryptographically strong pseudo-random entropy), preventing sequential enumeration attacks. |

---

### 2.6 Cross-Origin Resource Sharing (CORS)
| Aspect | Current Implementation Status | Security Evaluation |
|---|---|---|
| **Origin Whitelisting** | **Verified Active** (`backend/main.py:62-75`) | Configured via `CORSMiddleware`. Restricts origins to development hosts (`localhost:3000`, `127.0.0.1:3000`, `localhost:3001`, `127.0.0.1:3001`, `localhost:5173`, `127.0.0.1:5173`). |
| **Production Override** | **Verified Active** | Configurable via `ALLOWED_ORIGINS` environment variable without code changes. |
