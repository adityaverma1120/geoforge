import asyncio
import logging
import os
import shutil
import subprocess
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
_env_path = Path(__file__).resolve().parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    load_dotenv()

import json
from datetime import datetime, timezone
import cv2
from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import database
from convert_to_glb import convert_to_glb, validate_glb
from frame_filtering import filter_sharp_frames
from frame_processing import extract_frames, validate_video
from redundancy_filter import remove_redundant_frames
from reconstruction import run_reconstruction

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("geoforge")


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="GeoForge Drone Reconstruction API",
    description="Single-Pass Drone Video to 3D Model Generation Backend",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

# Frontend currently runs on port 3000 or 3001
_raw_origins = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,http://localhost:5173,http://127.0.0.1:5173"
)
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# CONFIGURATION
# ============================================================

# Maximum video upload size (4 GB)
MAX_UPLOAD_BYTES = 4 * 1024 * 1024 * 1024

# Minimum frames required for a useful COLMAP reconstruction
MIN_FRAMES_FOR_RECONSTRUCTION = 20

# How long (seconds) to keep job files before auto-deletion (7 days)
JOB_RETENTION_SECONDS = 7 * 24 * 60 * 60

# Maximum number of concurrent reconstructions allowed (1 for Dell G15 16 GB / RTX 3050 6 GB)
MAX_CONCURRENT_RECONSTRUCTIONS = 1

# Thread pool for running blocking reconstruction tasks
_executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_RECONSTRUCTIONS)


# ============================================================
# JOB STATUS
# ============================================================

class JobStatus(str, Enum):
    QUEUED      = "queued"
    PROCESSING  = "processing"
    COMPLETE    = "complete"
    FAILED      = "failed"

# In-memory fast cache (backed by SQLite database)
_jobs: dict = {}


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
TEMP_DIR   = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "output"
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"

for _d in (UPLOAD_DIR, TEMP_DIR, OUTPUT_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# Mount compiled frontend static assets if available
if (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")


# ============================================================
# STARTUP LIFECYCLE
# ============================================================

@app.on_event("startup")
def startup_event():
    """Initialize persistent SQLite database and recover any interrupted jobs."""
    database.init_db()
    recovered = database.recover_interrupted_jobs()
    logger.info(f"GeoForge backend started. SQLite job store ready (recovered {recovered} interrupted jobs).")


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home(request: Request = None):
    if request is not None:
        accept = request.headers.get("accept", "")
        index_file = FRONTEND_DIST / "index.html"
        if "text/html" in accept and index_file.exists():
            return FileResponse(index_file)
    return {
        "status": "online",
        "service": "GeoForge Reconstruction API",
        "version": "1.0.0",
        "description": "Single-Pass Drone Video to 3D Model Generation System"
    }


# ============================================================
# HEALTH CHECK (Liveness Probe)
# ============================================================

@app.get("/health")
def health():
    """
    Fast liveness check indicating that the FastAPI service is running.
    Maintains backward compatibility with diagnostic status fields.
    """
    colmap_path = Path(os.environ.get("COLMAP_EXE", r"C:\Users\adity\AppData\Local\Programs\COLMAP\bin\colmap.exe"))
    colmap_ok = colmap_path.exists() and colmap_path.is_file()

    env_ffmpeg = os.environ.get("FFMPEG_EXE")
    which_ffmpeg = shutil.which("ffmpeg")
    ffmpeg_candidates = [
        Path(env_ffmpeg) if env_ffmpeg else None,
        Path(which_ffmpeg) if which_ffmpeg else None,
        Path(r"C:\Users\adity\AppData\Local\Programs\ffmpeg\bin\ffmpeg.exe"),
        Path.home() / "AppData" / "Local" / "Programs" / "ffmpeg" / "bin" / "ffmpeg.exe",
    ]
    ffmpeg_path = next((p for p in ffmpeg_candidates if p and p.exists() and p.is_file()), Path(r"C:\Users\adity\AppData\Local\Programs\ffmpeg\bin\ffmpeg.exe"))
    ffmpeg_ok = ffmpeg_path.exists() and ffmpeg_path.is_file()

    free_gb = 0.0
    try:
        disk_usage = shutil.disk_usage(str(BASE_DIR))
        free_gb = round(disk_usage.free / (1024**3), 2)
    except Exception:
        pass

    active_jobs = [j for j in database.list_jobs(20) if j.get("status") == "processing"]
    ready_state = colmap_ok and (len(active_jobs) < MAX_CONCURRENT_RECONSTRUCTIONS)

    return {
        "status": "healthy" if ready_state else "degraded",
        "service": "GeoForge Reconstruction API",
        "version": "1.0.0",
        "reconstruction_ready": ready_state,
        "colmap": {
            "available": colmap_ok,
            "path": str(colmap_path),
            "version": "COLMAP 3.9.1 (CUDA)" if colmap_ok else "Not found"
        },
        "ffmpeg": {
            "available": ffmpeg_ok,
            "path": str(ffmpeg_path)
        },
        "storage": {
            "disk_free_gb": free_gb,
            "writable": True
        },
        "concurrency": {
            "active_jobs": len(active_jobs),
            "max_concurrent": MAX_CONCURRENT_RECONSTRUCTIONS
        }
    }


# ============================================================
# READINESS PROBE
# ============================================================

@app.get("/ready")
def ready():
    """
    Subsystem readiness endpoint verifying:
    - Python dependencies availability
    - COLMAP CUDA executable availability
    - FFmpeg executable availability
    - Upload & Output directory write permissions
    - Database connectivity
    - Worker capacity availability
    """
    deps_ok = True
    try:
        import numpy, cv2, open3d, trimesh, PIL, scipy
    except ImportError:
        deps_ok = False

    colmap_path = Path(os.environ.get("COLMAP_EXE", r"C:\Users\adity\AppData\Local\Programs\COLMAP\bin\colmap.exe"))
    colmap_ok = colmap_path.exists() and colmap_path.is_file()

    env_ffmpeg = os.environ.get("FFMPEG_EXE")
    which_ffmpeg = shutil.which("ffmpeg")
    ffmpeg_candidates = [
        Path(env_ffmpeg) if env_ffmpeg else None,
        Path(which_ffmpeg) if which_ffmpeg else None,
        Path(r"C:\Users\adity\AppData\Local\Programs\ffmpeg\bin\ffmpeg.exe"),
        Path.home() / "AppData" / "Local" / "Programs" / "ffmpeg" / "bin" / "ffmpeg.exe",
    ]
    ffmpeg_path = next((p for p in ffmpeg_candidates if p and p.exists() and p.is_file()), Path(r"C:\Users\adity\AppData\Local\Programs\ffmpeg\bin\ffmpeg.exe"))
    ffmpeg_ok = ffmpeg_path.exists() and ffmpeg_path.is_file()

    storage_ok = UPLOAD_DIR.exists() and TEMP_DIR.exists() and OUTPUT_DIR.exists()
    free_gb = 0.0
    try:
        disk_usage = shutil.disk_usage(str(BASE_DIR))
        free_gb = round(disk_usage.free / (1024**3), 2)
    except Exception:
        pass

    db_ok = database.check_db_connectivity()
    active_jobs = [j for j in database.list_jobs(20) if j.get("status") == "processing"]
    capacity_ok = len(active_jobs) < MAX_CONCURRENT_RECONSTRUCTIONS

    is_ready = deps_ok and colmap_ok and ffmpeg_ok and storage_ok and db_ok and (free_gb >= 1.0) and capacity_ok

    payload = {
        "status": "ready" if is_ready else "not_ready",
        "service": "GeoForge Reconstruction API",
        "version": "1.0.0",
        "reconstruction_ready": is_ready,
        "database_connected": db_ok,
        "dependencies_loaded": deps_ok,
        "colmap": {
            "available": colmap_ok,
            "path": str(colmap_path)
        },
        "ffmpeg": {
            "available": ffmpeg_ok,
            "path": str(ffmpeg_path)
        },
        "storage": {
            "disk_free_gb": free_gb,
            "writable": storage_ok
        },
        "concurrency": {
            "active_jobs": len(active_jobs),
            "max_concurrent": MAX_CONCURRENT_RECONSTRUCTIONS,
            "capacity_available": capacity_ok
        }
    }

    if not is_ready:
        return JSONResponse(status_code=503, content=payload)
    return payload


# ============================================================
# CLEANUP HELPER
# ============================================================

async def _cleanup_job_files(
    job_id: str,
    job_dir: Path,
    video_path: Path,
    delay_seconds: int = JOB_RETENTION_SECONDS
):
    """
    Delete job temp files and uploaded video after delay_seconds retention period.
    """
    await asyncio.sleep(delay_seconds)
    logger.info(f"Cleaning up retention-expired job files: {job_dir}")
    shutil.rmtree(job_dir, ignore_errors=True)
    if video_path.exists():
        video_path.unlink(missing_ok=True)
    _jobs.pop(job_id, None)
    logger.info(f"Retention cleanup complete for: {job_id}")


# ============================================================
# RECONSTRUCTION WORKER
# ============================================================

def _run_reconstruction_job(job_id: str):
    """
    Blocking worker that runs the full photogrammetry pipeline:
    1. Video Validation
    2. Intelligent Frame Extraction (FPS-aware @ 2.0 FPS)
    3. Sharpness, Exposure & Contrast Filtering
    4. Redundancy Reduction (Motion baseline)
    5. COLMAP Feature Extraction (GPU SIFT)
    6. Feature Matching (Sequential / Exhaustive with loop detection)
    7. Sparse Reconstruction & Camera Registration
    8. Sparse Model Quality Check
    9. Image Undistortion
    10. Dense Stereo (PatchMatch MVS)
    11. Stereo Fusion (Point cloud)
    12. Open3D Point Cloud Denoising & Outlier Removal
    13. Poisson Surface Meshing with Density Trimming
    14. Mesh Colorization from Point Cloud
    15. Binary glTF v2 (GLB) Conversion & Header Validation
    16. Metadata Manifest Generation & Persistence
    """
    job = database.get_job(job_id) or _jobs.get(job_id)
    if not job:
        logger.error(f"[{job_id}] Job record not found for background execution.")
        return

    job_dir      = Path(job["job_dir"])
    video_path   = Path(job["video_path"])
    frames_dir   = job_dir / "frames"
    selected_dir = job_dir / "selected_frames"
    final_dir    = job_dir / "final_frames"
    colmap_dir   = job_dir / "colmap"

    start_time = datetime.now(timezone.utc)

    try:
        # ------------------------------------------------
        # STAGE 1 — Validate video stream
        # ------------------------------------------------
        logger.info(f"[{job_id}] STAGE 1: Validating video stream")
        database.update_job_progress(
            job_id,
            status=JobStatus.PROCESSING,
            stage="validating_video",
            progress_percent=5,
            stage_message="Validating video container and visual frames..."
        )
        if job_id in _jobs:
            _jobs[job_id]["status"] = JobStatus.PROCESSING

        video_metadata = validate_video(video_path)

        # ------------------------------------------------
        # STAGE 2 — Extract frames (FPS-aware @ 2.0 FPS)
        # ------------------------------------------------
        logger.info(f"[{job_id}] STAGE 2: Extracting frames")
        database.update_job_progress(
            job_id,
            stage="extracting_frames",
            progress_percent=12,
            stage_message=f"Extracting keyframes from {video_metadata['resolution']} video..."
        )
        extraction_result = extract_frames(
            video_path=str(video_path),
            output_dir=str(frames_dir),
            target_fps=2.0
        )

        # ------------------------------------------------
        # STAGE 3 — Sharpness, exposure & contrast filtering
        # ------------------------------------------------
        logger.info(f"[{job_id}] STAGE 3: Quality filtering")
        database.update_job_progress(
            job_id,
            stage="filtering_frames",
            progress_percent=20,
            stage_message=f"Filtering {extraction_result['frames_saved']} frames for blur, exposure and contrast..."
        )
        sharpness_result = filter_sharp_frames(
            frames_dir=str(frames_dir),
            selected_dir=str(selected_dir),
            threshold=100.0
        )

        # ------------------------------------------------
        # STAGE 4 — Redundancy reduction (baseline coverage)
        # ------------------------------------------------
        logger.info(f"[{job_id}] STAGE 4: Redundancy filtering")
        database.update_job_progress(
            job_id,
            stage="redundancy_filter",
            progress_percent=25,
            stage_message="Removing redundant frames while preserving trajectory baseline..."
        )
        redundancy_result = remove_redundant_frames(
            input_dir=str(selected_dir),
            output_dir=str(final_dir),
            difference_threshold=5.0
        )

        # ------------------------------------------------
        # Minimum frame guard
        # ------------------------------------------------
        final_frame_files = [
            p for p in final_dir.iterdir()
            if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}
        ]

        if not final_frame_files:
            raise RuntimeError("No frames survived filtering.")

        if len(final_frame_files) < MIN_FRAMES_FOR_RECONSTRUCTION:
            raise RuntimeError(
                f"Only {len(final_frame_files)} frames passed filtering. "
                f"At least {MIN_FRAMES_FOR_RECONSTRUCTION} are needed for a useful reconstruction. "
                "Try uploading a longer video or reducing the sharpness threshold."
            )

        logger.info(f"[{job_id}] Final frames for COLMAP: {len(final_frame_files)}")

        # ------------------------------------------------
        # STAGES 5-10 — COLMAP reconstruction with stage callbacks
        # ------------------------------------------------
        logger.info(f"[{job_id}] Launching COLMAP photogrammetry engine")

        def on_colmap_progress(stage: str, percent: int, msg: str):
            database.update_job_progress(
                job_id,
                stage=stage,
                progress_percent=percent,
                stage_message=msg
            )

        reconstruction_result = run_reconstruction(
            image_dir=str(final_dir),
            workspace_dir=str(colmap_dir),
            progress_callback=on_colmap_progress
        )

        # ------------------------------------------------
        # STAGE 11 — Convert to GLB
        # ------------------------------------------------
        logger.info(f"[{job_id}] STAGE 11: Converting to GLB")
        database.update_job_progress(
            job_id,
            stage="exporting_glb",
            progress_percent=98,
            stage_message="Packaging 3D model into GLB format..."
        )

        textured_model = Path(reconstruction_result["textured_model"])
        textured_directory = textured_model.parent

        texture_candidates = (
            list(textured_directory.glob("*.png")) +
            list(textured_directory.glob("*.jpg"))
        )
        texture_file = texture_candidates[0] if texture_candidates else None
        glb_file = textured_directory / "model.glb"

        convert_to_glb(
            ply_file=textured_model,
            texture_file=texture_file,
            glb_file=glb_file
        )

        if not glb_file.exists() or glb_file.stat().st_size == 0:
            raise RuntimeError("GLB file was not created or is empty.")

        # ------------------------------------------------
        # STAGE 12 — Validate GLB geometry & header
        # ------------------------------------------------
        database.update_job_progress(
            job_id,
            stage="validating_model",
            progress_percent=99,
            stage_message="Validating binary GLB geometry and header..."
        )
        glb_validation = validate_glb(glb_file)
        glb_size_mb = glb_validation["file_size_mb"]

        recon_stats = reconstruction_result.get("reconstruction_stats", {})
        quality_warnings = reconstruction_result.get("quality_warnings", [])

        # ------------------------------------------------
        # Generate Comprehensive Metadata Manifest
        # ------------------------------------------------
        completed_time = datetime.now(timezone.utc)
        duration_total = (completed_time - start_time).total_seconds()

        metadata_manifest = {
            "job_id": job_id,
            "filename": job["filename"],
            "created_at": job.get("created_at"),
            "completed_at": completed_time.isoformat(),
            "processing_duration_seconds": round(duration_total, 2),
            "source_video": video_metadata,
            "pipeline_stages": [
                "validating_video",
                "extracting_frames",
                "filtering_frames",
                "redundancy_filter",
                "extracting_features",
                "matching_features",
                "sparse_reconstruction",
                "sparse_quality_check",
                "image_undistortion",
                "dense_stereo",
                "stereo_fusion",
                "processing_pointcloud",
                "generating_mesh",
                "generating_texture",
                "exporting_glb",
                "validating_model",
                "completed"
            ],
            "filtering_stats": {
                "extracted_frames": extraction_result["frames_saved"],
                "sharp_frames_kept": sharpness_result.get("frames_kept", len(final_frame_files)),
                "blurry_frames_removed": sharpness_result.get("blurry_frames_removed", 0),
                "brightness_frames_removed": sharpness_result.get("brightness_frames_removed", 0),
                "contrast_frames_removed": sharpness_result.get("contrast_frames_removed", 0),
                "redundant_frames_removed": redundancy_result.get("redundant_frames_removed", 0),
                "final_frames_for_colmap": len(final_frame_files)
            },
            "photogrammetry_stats": {
                "registered_images": recon_stats.get("registered_images", len(final_frame_files)),
                "registration_ratio": recon_stats.get("registration_ratio", 1.0),
                "num_cameras": recon_stats.get("num_cameras", 1),
                "sparse_points": recon_stats.get("sparse_points", 0),
                "dense_points": recon_stats.get("dense_cloud_points", 0),
                "cleaned_points": recon_stats.get("cleaned_cloud_points", 0),
                "outliers_removed": recon_stats.get("outliers_removed", 0),
                "bounding_box": recon_stats.get("bounding_box", {})
            },
            "mesh_stats": {
                "vertices": recon_stats.get("mesh_vertices", 0),
                "faces": recon_stats.get("mesh_faces", 0),
                "bounding_dimensions": recon_stats.get("bounding_dimensions", [])
            },
            "model_deliverable": {
                "format": "glTF v2.0 (Binary GLB)",
                "file_path": str(glb_file),
                "file_size_mb": glb_size_mb,
                "magic": glb_validation.get("magic"),
                "version": glb_validation.get("version"),
                "download_url": f"/download/{job_id}",
                "model_url": f"/model/{job_id}"
            },
            "quality_warnings": quality_warnings,
            "geospatial_notes": (
                "Reconstructed model is oriented in arbitrary local coordinate space (x, y, z). "
                "Because raw drone video lacked RTK GPS timestamps or Ground Control Points (GCPs), "
                "global metric scale (lambda) and geographic georeferencing (WGS84 UTM) require "
                "external scale constraint or GCP alignment."
            )
        }

        metadata_path = job_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata_manifest, f, indent=2)

        result_payload = {
            "model_path": str(glb_file),
            "model_url": f"/model/{job_id}",
            "download_url": f"/download/{job_id}",
            "metadata_url": f"/metadata/{job_id}",
            "glb_size_mb": glb_size_mb,
            "frames_extracted": extraction_result["frames_saved"],
            "frames_used": len(final_frame_files),
            "num_sparse_points": recon_stats.get("sparse_points", 0),
            "num_cameras": recon_stats.get("num_cameras", 1),
            "num_registered_images": recon_stats.get("registered_images", len(final_frame_files)),
            "warnings": quality_warnings
        }

        database.update_job_progress(
            job_id,
            status=JobStatus.COMPLETE,
            stage="completed",
            progress_percent=100,
            stage_message="Reconstruction completed successfully!",
            result=result_payload,
            model_path=glb_file
        )
        if job_id in _jobs:
            _jobs[job_id]["status"] = JobStatus.COMPLETE
            _jobs[job_id]["result"] = result_payload

        logger.info(f"[{job_id}] Reconstruction fully COMPLETE. GLB: {glb_file} ({glb_size_mb:.2f} MB)")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"[{job_id}] Pipeline failed: {error_msg}")
        traceback.print_exc()
        database.update_job_progress(
            job_id,
            status=JobStatus.FAILED,
            stage="failed",
            stage_message=f"Reconstruction failed: {error_msg}",
            error=error_msg
        )
        if job_id in _jobs:
            _jobs[job_id]["status"] = JobStatus.FAILED
            _jobs[job_id]["error"] = error_msg


# ============================================================
# VIDEO UPLOAD
# ============================================================

@app.post("/upload")
async def upload_video(
    request: Request,
    file: UploadFile = File(...)
):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File is too large. Maximum allowed size is {MAX_UPLOAD_BYTES // (1024**3)} GB."
        )

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected.")

    allowed_extensions = {".mp4", ".mov", ".avi", ".mkv"}
    original_filename = Path(file.filename).name
    extension = Path(original_filename).suffix.lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported video format: {extension}. Supported formats are MP4, MOV, AVI and MKV."
        )

    job_id = str(uuid.uuid4())
    job_dir = TEMP_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    video_path = UPLOAD_DIR / f"{job_id}_{original_filename}"
    logger.info(f"New job: {job_id} | file: {original_filename}")

    # Step 1: Stream video to disk
    try:
        with video_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"[{job_id}] Video save error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Video saving failed: {e}")
    finally:
        await file.close()

    if not video_path.exists() or video_path.stat().st_size == 0:
        if video_path.exists():
            video_path.unlink(missing_ok=True)
        shutil.rmtree(job_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Step 1b: Validate video readability via validate_video
    try:
        video_metadata = validate_video(video_path)
    except Exception as e:
        if video_path.exists():
            video_path.unlink(missing_ok=True)
        shutil.rmtree(job_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=f"Uploaded video validation failed: {e}")

    # Register job in persistent SQLite database & in-memory cache
    database.create_job(job_id, original_filename, video_path, job_dir)
    _jobs[job_id] = {
        "status":     JobStatus.QUEUED,
        "filename":   original_filename,
        "job_dir":    job_dir,
        "video_path": video_path,
        "result":     None,
        "error":      None
    }

    # Queue Guard: check concurrent running jobs
    active_jobs = [j for j in database.list_jobs(20) if j.get("status") == "processing"]
    if len(active_jobs) >= MAX_CONCURRENT_RECONSTRUCTIONS:
        database.update_job_progress(
            job_id,
            status=JobStatus.FAILED,
            stage="failed",
            stage_message="Server at capacity",
            error=f"Server is at capacity ({MAX_CONCURRENT_RECONSTRUCTIONS} jobs running). Please try again shortly."
        )
        shutil.rmtree(job_dir, ignore_errors=True)
        if video_path.exists():
            video_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=503,
            detail=f"Reconstruction server is at capacity ({MAX_CONCURRENT_RECONSTRUCTIONS} jobs running). Please try again in a few minutes."
        )

    # Launch background reconstruction in thread pool
    loop = asyncio.get_running_loop()
    loop.run_in_executor(_executor, _run_reconstruction_job, job_id)

    # Schedule cleanup after retention period
    asyncio.create_task(_cleanup_job_files(job_id, job_dir, video_path))

    base_url = str(request.base_url).rstrip("/")
    status_url  = f"/status/{job_id}"
    model_url   = f"/model/{job_id}"

    logger.info(f"[{job_id}] Job accepted. Reconstruction running in background.")

    return {
        "status":           "uploaded",
        "message":          "Video uploaded successfully. Reconstruction is running in the background.",
        "job_id":           job_id,
        "filename":         original_filename,
        "status_url":       status_url,
        "status_absolute":  f"{base_url}{status_url}",
        "model_url":        model_url,
        "model_absolute":   f"{base_url}{model_url}",
        "download_url":     f"/download/{job_id}",
        "poll_interval_seconds": 5
    }


# ============================================================
# JOB STATUS
# ============================================================

@app.get("/status/{job_id}")
def get_status(job_id: str):
    """
    Poll the status of a reconstruction job from persistent SQLite store.
    """
    try:
        uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format.")

    job = database.get_job(job_id)

    if not job:
        job_mem = _jobs.get(job_id)
        if not job_mem:
            raise HTTPException(
                status_code=404,
                detail=f"Job not found: {job_id}. The job may have expired or was never created."
            )
        job = {
            "job_id": job_id,
            "status": job_mem.get("status", "failed"),
            "stage": "processing",
            "progress_percent": 50,
            "stage_message": "",
            "filename": job_mem.get("filename"),
            "result": job_mem.get("result"),
            "error_message": job_mem.get("error"),
            "created_at": None,
            "updated_at": None,
            "completed_at": None
        }

    glb_file = _resolve_glb(job_id)
    model_available = glb_file is not None and glb_file.exists() and glb_file.stat().st_size > 0

    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "stage": job.get("stage", "processing"),
        "progress_percent": job.get("progress_percent", 0),
        "message": job.get("stage_message", ""),
        "filename": job.get("filename"),
        "model_available": model_available,
        "model_url": f"/model/{job_id}" if model_available else None,
        "download_url": f"/download/{job_id}" if model_available else None,
        "result": job.get("result"),
        "error": job.get("error_message"),
        "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at"),
        "completed_at": job.get("completed_at")
    }


# ============================================================
# SERVE GLB MODEL
# ============================================================

def _resolve_glb(job_id: str) -> Optional[Path]:
    """Find the GLB file for a given job ID across temp and output directories safely."""
    try:
        uuid.UUID(job_id)
    except ValueError:
        return None
    candidates = [
        TEMP_DIR / job_id / "colmap" / "textured" / "model.glb",
        OUTPUT_DIR / job_id / "model.glb",
        TEMP_DIR / job_id / "model.glb"
    ]
    for c in candidates:
        if c.exists() and c.is_file() and c.stat().st_size > 0:
            return c.resolve()
    return None


@app.get("/model/{job_id}")
def get_model(job_id: str):
    """Serve the 3D GLB model directly for Three.js WebGL viewing."""
    try:
        uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format.")

    glb_file = _resolve_glb(job_id)

    if not glb_file or not glb_file.exists() or glb_file.stat().st_size == 0:
        raise HTTPException(status_code=404, detail=f"3D model not found or still generating for job: {job_id}")

    return FileResponse(
        path=glb_file,
        media_type="model/gltf-binary",
        filename="model.glb",
        headers={"Cache-Control": "public, max-age=3600"}
    )


# ============================================================
# DOWNLOAD GLB ATTACHMENT
# ============================================================

@app.get("/download/{job_id}")
def download_model(job_id: str):
    """Download the generated 3D GLB model as an attachment file."""
    try:
        uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format.")

    glb_file = _resolve_glb(job_id)

    if not glb_file or not glb_file.exists() or glb_file.stat().st_size == 0:
        raise HTTPException(status_code=404, detail=f"3D model not found or still generating for job: {job_id}")

    filename = f"geoforge_{job_id[:8]}.glb"
    return FileResponse(
        path=glb_file,
        media_type="application/octet-stream",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ============================================================
# LIST JOBS HISTORY
# ============================================================

@app.get("/jobs")
def list_jobs_endpoint(limit: int = 50):
    """Retrieve history of reconstruction jobs from the persistent database."""
    return database.list_jobs(limit=min(limit, 100))


# ============================================================
# CANCEL OR DELETE JOB
# ============================================================

@app.post("/jobs/{job_id}/cancel")
def cancel_job_endpoint(job_id: str):
    """Cancel an active or queued reconstruction job safely."""
    try:
        uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format.")

    job = database.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    if job["status"] in ("completed", "complete"):
        raise HTTPException(status_code=400, detail="Cannot cancel an already completed job.")

    cancelled = database.cancel_job(job_id)
    if job_id in _jobs:
        _jobs[job_id]["status"] = "cancelled"

    return {
        "status": "cancelled",
        "job_id": job_id,
        "message": "Job successfully cancelled."
    }


# ============================================================
# MODEL HEAD CHECK
# ============================================================

@app.head("/model/{job_id}")
def check_model(job_id: str):
    try:
        uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID.")

    glb_file = _resolve_glb(job_id)

    if not glb_file.exists() or not glb_file.is_file() or glb_file.stat().st_size == 0:
        raise HTTPException(status_code=404, detail="3D model not found.")

    return {
        "status": "available",
        "job_id": job_id,
        "filename": "model.glb",
        "size_bytes": glb_file.stat().st_size
    }


# ============================================================
# RECONSTRUCTION METADATA MANIFEST
# ============================================================

@app.get("/metadata/{job_id}")
def get_metadata(job_id: str):
    """Retrieve full photogrammetric metadata manifest for a completed reconstruction."""
    try:
        valid_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format.")

    job_dir = TEMP_DIR / str(valid_uuid)
    metadata_file = job_dir / "metadata.json"

    if not metadata_file.exists():
        job = database.get_job(str(valid_uuid))
        if not job:
            raise HTTPException(status_code=404, detail="Job not found.")
        if job["status"] != JobStatus.COMPLETE:
            raise HTTPException(status_code=404, detail=f"Job is not complete (current status: {job['status']}).")
        raise HTTPException(status_code=404, detail="Metadata manifest file not found on disk.")

    with open(metadata_file, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# CANCEL OR DELETE JOB
# ============================================================

@app.delete("/jobs/{job_id}")
def delete_job(job_id: str):
    """Cancel an active job or delete a completed job's files and database record."""
    try:
        uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID.")

    job = database.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    job_dir = TEMP_DIR / job_id
    if job_dir.exists():
        shutil.rmtree(job_dir, ignore_errors=True)

    if job.get("video_path"):
        vpath = Path(job["video_path"])
        if vpath.exists():
            vpath.unlink(missing_ok=True)

    database.delete_job(job_id)
    _jobs.pop(job_id, None)
    return {"status": "deleted", "job_id": job_id, "message": "Job successfully removed."}


# ============================================================
# SPA CLIENT ROUTING FALLBACK
# ============================================================

@app.get("/{full_path:path}")
def spa_fallback(full_path: str):
    """Serve static frontend build and fall back to index.html for client-side routing."""
    api_prefixes = ("health", "ready", "status", "model", "download", "jobs", "docs", "openapi.json", "redoc")
    if full_path.split("/")[0] in api_prefixes:
        raise HTTPException(status_code=404, detail="Endpoint not found.")

    candidate = FRONTEND_DIST / full_path
    if candidate.is_file():
        return FileResponse(candidate)

    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="Not found.")
