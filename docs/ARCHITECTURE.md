# System Architecture — GeoForge

> **Document:** `docs/ARCHITECTURE.md`  
> **Status:** Code-Verified Architecture Specification (Phase 3 Verified)  
> **Target Version:** GeoForge v1.0.0 (SIH 2026 / NTRO Edition)  
> **Source Verification Date:** 2026-11-11  
> **Related Documents:** [`docs/BACKEND.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/BACKEND.md), [`docs/FRONTEND.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/FRONTEND.md), [`docs/RECONSTRUCTION_PIPELINE.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/RECONSTRUCTION_PIPELINE.md), [`docs/API.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/API.md)

---

## 1. High-Level System Architecture

GeoForge is structured as a decoupled client-server architecture consisting of a React 19 single-page web client, a FastAPI Python ASGI service, and an automated photogrammetric computer vision pipeline combining OpenCV, COLMAP, Open3D, Trimesh, and Three.js.

```mermaid
flowchart TD
    subgraph Client["Client Tier (React 19 + TypeScript + Vite)"]
        UI["Web UI (UploadPage / ProcessingPage / ResultPage)"]
        GLTFViewer["Three.js 3D Viewer (GLTFLoader + OrbitControls)"]
        ApiClient["API Client (XMLHttpRequest Upload + Fetch Polling)"]
    end

    subgraph Server["API & Orchestration Tier (FastAPI / Uvicorn)"]
        EndpointUpload["POST /upload"]
        EndpointStatus["GET /status/{job_id}"]
        EndpointModel["GET /model/{job_id}"]
        EndpointHead["HEAD /model/{job_id}"]
        JobStore[("In-Memory Store (_jobs dict)")]
        Executor["ThreadPoolExecutor (max_workers=2)"]
    end

    subgraph Pipeline["Computer Vision & Photogrammetry Engine"]
        FE["OpenCV VideoCapture (extract_frames @ 2.0 FPS)"]
        SF["Laplacian Blur & Luminance Filter (filter_sharp_frames)"]
        RF["AbsDiff Redundancy Filter (remove_redundant_frames)"]
        COLMAP_SfM["COLMAP SfM (SIFT 16k, OPENCV Camera, Sequential Matcher)"]
        COLMAP_MVS["COLMAP Dense MVS (PatchMatch Stereo & Stereo Fusion)"]
        O3D_Clean["Open3D Outlier Removal (nb=20, std=2.0)"]
        O3D_Mesh["Open3D Poisson Meshing (depth=11, 7% Density Trim)"]
        COLMAP_Tex["COLMAP mesh_texturer (Undistorted Camera Projection)"]
        Trimesh_GLB["Trimesh & Pillow PBR Material Packaging (convert_to_glb)"]
    end

    subgraph Storage["Filesystem Workspace"]
        UploadFile["backend/uploads/{job_id}_{filename}"]
        JobDir["backend/temp/{job_id}/"]
        ModelGLB["backend/temp/{job_id}/colmap/textured/model.glb"]
    end

    %% Workflow Connections
    UI -->|1. Multipart Video Stream (XHR)| EndpointUpload
    EndpointUpload -->|Save Upload| UploadFile
    EndpointUpload -->|Register JobStatus.QUEUED| JobStore
    EndpointUpload -->|Submit Background Task| Executor

    Executor --> FE
    FE -->|Raw JPEGs in frames/| SF
    SF -->|Sharp JPEGs in selected_frames/| RF
    RF -->|Final JPEGs in final_frames/| COLMAP_SfM
    COLMAP_SfM -->|Sparse Model sparse/0/| COLMAP_MVS
    COLMAP_MVS -->|fused.ply in colmap/dense/| O3D_Clean
    O3D_Clean -->|fused_cleaned.ply| O3D_Mesh
    O3D_Mesh -->|poisson_mesh.ply in colmap/mesh/| COLMAP_Tex
    COLMAP_Tex -->|model.ply + model.png in colmap/textured/| Trimesh_GLB
    Trimesh_GLB -->|Write model.glb| ModelGLB
    Trimesh_GLB -->|Update JobStatus.COMPLETE with result dict| JobStore

    ApiClient -->|2. Poll Status (3s -> 30s backoff)| EndpointStatus
    EndpointStatus -->|Read status & stats| JobStore

    GLTFViewer -->|3. Fetch GLB Stream| EndpointModel
    EndpointModel -->|Stream Binary GLTF| ModelGLB
```

---

## 2. Component Technology Verification

| Layer | Component | Source Location | Implementation Details & Evidence |
|---|---|---|---|
| **Frontend Framework** | React 19 SPA | `frontend/package.json`<br/>`frontend/src/App.tsx` | React `^19.0.1`, TypeScript `~5.8.2`, Vite `^6.2.3`. State-machine navigation: `'home'`, `'how-it-works'`, `'upload'`, `'processing'`, `'complete'`, `'result'`, `'error'`. |
| **API Client** | Custom XHR + Fetch | `frontend/src/services/api.ts` | Uses `XMLHttpRequest` for upload progress tracking (`uploadDroneVideo`) and standard `fetch` for status polling and model retrieval. |
| **3D Rendering** | Three.js WebGL Engine | `frontend/src/components/ThreeDViewer.tsx` | Three.js `^0.185.1` with `GLTFLoader`. Auto-centers bounding box (`THREE.Box3`), adds Ambient/Directional lights, OrbitControls, wireframe toggle, and grid helper. |
| **Backend Service** | FastAPI ASGI Server | `backend/main.py:37-65` | FastAPI `1.0.0` running on Uvicorn. CORS middleware allowlist configurable via `ALLOWED_ORIGINS` (defaults: localhost 3000, 3001, 5173). |
| **Job Concurrency** | ThreadPoolExecutor | `backend/main.py:89, 443-457` | `ThreadPoolExecutor(max_workers=2)`. Rejects uploads with HTTP 503 if 2 background reconstructions are currently active. |
| **Frame Extraction** | OpenCV VideoCapture | `backend/frame_processing.py:23-118` | Dynamic interval calculation: $\text{interval} = \max(1, \text{round}(\text{fps} / 2.0))$. Saves JPEGs at quality 95. |
| **Quality Filter** | Laplacian Variance & Brightness | `backend/frame_filtering.py:69-207` | Sharpness via $\text{Var}(\nabla^2 I) \ge 100.0$ with adaptive percentile lowering down to 20.0 if rejection $>40\%$. Luminance bounded in $[30.0, 240.0]$. |
| **Redundancy Filter** | Mean Absolute Difference | `backend/redundancy_filter.py:42-171` | Consecutive frame difference $\Delta(I_t, I_{t-1}) \ge 5.0$ with a strict 50% safety retention floor (`MAX_REMOVAL_RATIO = 0.50`). |
| **Photogrammetry** | COLMAP CLI Executable | `backend/reconstruction.py:17, 149-242` | Windows default: `C:\bin\colmap.exe` (overridden by `COLMAP_EXE`). Subprocess execution passes argument lists directly to avoid batch-file quoting bugs with path spaces. |
| **Point Cloud Denoising** | Open3D PointCloud | `backend/reconstruction.py:541-603` | Statistical outlier removal (`nb_neighbors=20, std_ratio=2.0`). Saves cleaned cloud to `colmap/dense/fused_cleaned.ply`. |
| **Poisson Meshing** | Open3D TriangleMesh | `backend/reconstruction.py:609-700` | Normal estimation + Screened Poisson meshing (`depth=11`) with 7.0% density boundary trimming (`POISSON_TRIM = 7.0`). Has fallback to COLMAP `poisson_mesher`. |
| **Texturing** | COLMAP `mesh_texturer` | `backend/reconstruction.py:1441-1531` | Projects undistorted camera images onto mesh surface, producing `model.ply`, `model.obj`, and diffuse atlas `model.png`. |
| **GLB Packaging** | Trimesh & Pillow | `backend/convert_to_glb.py:29-200` | Loads textured model, concatenates sub-meshes if Scene, binds Pillow diffuse texture as PBRMaterial, and exports `model.glb`. |

---

## 3. Verified Filesystem Workspace Topology

The actual directory layout created and managed by `backend/main.py` and `backend/reconstruction.py` is:

```text
backend/
├── uploads/
│   └── {job_id}_{original_filename}             # Ingested raw video file
├── output/                                      # Static output root
└── temp/
    └── {job_id}/                                # Per-job isolated transient workspace
        ├── frames/                              # Raw extracted frames from video (frame_XXXXXX.jpg)
        ├── selected_frames/                     # Sharpness & brightness-filtered frames
        ├── final_frames/                        # Redundancy-filtered keyframes (input to COLMAP)
        └── colmap/                              # COLMAP workspace directory
            ├── database.db                      # SQLite feature and matching database
            ├── sparse/
            │   └── 0/                           # SfM model (cameras.bin, images.bin, points3D.bin)
            ├── dense/
            │   ├── images/                      # Undistorted pinhole camera frames
            │   ├── sparse/                      # Undistorted sparse cameras
            │   ├── stereo/                      # PatchMatch depth and normal maps (.bin)
            │   ├── fused.ply                    # Raw fused dense point cloud from stereo fusion
            │   └── fused_cleaned.ply            # Outlier-cleaned dense point cloud (Open3D)
            ├── mesh/
            │   └── poisson_mesh.ply             # Trimmed Screened Poisson surface mesh
            └── textured/                        # Final textured model directory
                ├── model.ply                    # Vertex-colored mesh
                ├── model.obj                    # UV-mapped Wavefront OBJ
                ├── model.mtl                    # Material definition file
                ├── model.png                    # Diffuse texture atlas image
                └── model.glb                    # Final self-contained binary GLB served to viewer
```

> [!IMPORTANT]
> **Source Evidence on Model Location:**  
> In `backend/main.py:547-550`, the helper `_resolve_glb(job_id)` resolves the model path directly to:  
> `TEMP_DIR / job_id / "colmap" / "textured" / "model.glb"`  
> The final binary GLB is stored inside the `colmap/textured/` directory, adjacent to the texture atlas.

---

## 4. End-to-End Processing Call Graph

```text
POST /upload
  │
  ├── 1. Enforce content-length <= 4 GB
  ├── 2. Validate extension in {".mp4", ".mov", ".avi", ".mkv"}
  ├── 3. Save to backend/uploads/{job_id}_{filename}
  ├── 4. Check running_jobs < 2 (else HTTP 503)
  ├── 5. Schedule async cleanup after 7 days
  └── 6. Dispatch ThreadPoolExecutor worker (_run_reconstruction_job)
            │
            ├── extract_frames(video, frames/, target_fps=2.0)
            ├── filter_sharp_frames(frames/, selected_frames/, threshold=100.0)
            ├── remove_redundant_frames(selected_frames/, final_frames/, diff=5.0)
            ├── Guard: Check len(final_frames) >= 20
            │
            ├── run_reconstruction(final_frames/, colmap/)
            │     ├── colmap feature_extractor (SIFT 16384, OPENCV)
            │     ├── colmap sequential_matcher (overlap 15, vocab tree loop closure)
            │     ├── colmap mapper (multiple_models=0)
            │     ├── check_sparse_reconstruction_quality (registration >= 30%)
            │     ├── colmap image_undistorter (max_image_size 2400)
            │     ├── colmap patch_match_stereo (iterations 7, geom_consistency 1)
            │     ├── colmap stereo_fusion -> colmap/dense/fused.ply
            │     ├── clean_point_cloud (Open3D nb=20, std=2.0) -> fused_cleaned.ply
            │     ├── poisson_mesh_with_trimming (Open3D depth=11, trim 7.0%) -> poisson_mesh.ply
            │     └── colmap mesh_texturer -> colmap/textured/model.ply & model.png
            │
            ├── convert_to_glb(textured_model, texture_png, colmap/textured/model.glb)
            │     ├── Trimesh load & concatenate
            │     ├── Pillow PBR material attachment
            │     └── Validate model.glb exists and size > 0
            │
            └── Update _jobs[job_id]["status"] = JobStatus.COMPLETE with 20 metrics
```

---

## 5. Security Architecture & Trust Boundaries

1. **Untrusted Video Uploads:**
   - Client filenames are sanitized via `Path(filename).name` and prepended with a server-generated UUID4 to prevent directory traversal (`../`) attacks.
   - Initial size rejection is performed using the `Content-Length` header before buffering payload bytes.
2. **Subprocess Isolation:**
   - External CLI commands (`colmap.exe`) are executed with `shell=False` and parameter lists, preventing command injection and Windows batch-file quoting bugs when paths contain spaces.
3. **In-Memory Volatility:**
   - Job tracking is held in `_jobs: dict`. If the API process restarts, all in-memory records are lost. Disk files remain in `backend/temp/` until the 7-day cleanup runs.
