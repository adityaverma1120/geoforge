import asyncio
import logging
import os
import shutil
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from pathlib import Path

from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from convert_to_glb import convert_to_glb
from frame_filtering import filter_sharp_frames
from frame_processing import extract_frames
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
logger = logging.getLogger(__name__)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Drone3D Reconstruction API",
    description="Drone video to 3D reconstruction backend",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

# Frontend currently runs on port 3001.
# Port 3000 is also allowed in case the frontend is moved there.

# Read allowed origins from environment variable.
# In production set: ALLOWED_ORIGINS=https://yourapp.vercel.app,https://yourapp.com
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
# DIRECTORIES
# ============================================================

# ============================================================
# CONFIGURATION
# ============================================================

# Maximum video upload size (4 GB)
MAX_UPLOAD_BYTES = 4 * 1024 * 1024 * 1024

# Minimum frames required for a useful COLMAP reconstruction
MIN_FRAMES_FOR_RECONSTRUCTION = 20

# How long (seconds) to keep job files before auto-deletion (7 days)
JOB_RETENTION_SECONDS = 7 * 24 * 60 * 60

# Maximum number of concurrent reconstructions allowed
MAX_CONCURRENT_RECONSTRUCTIONS = 2

# Thread pool for running blocking reconstruction tasks
_executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_RECONSTRUCTIONS)


# ============================================================
# JOB STATUS STORE
# ============================================================

class JobStatus(str, Enum):
    QUEUED      = "queued"
    PROCESSING  = "processing"
    COMPLETE    = "complete"
    FAILED      = "failed"

# In-memory store: job_id -> {status, result, error}
_jobs: dict = {}


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
TEMP_DIR   = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "output"

for _d in (UPLOAD_DIR, TEMP_DIR, OUTPUT_DIR):
    _d.mkdir(parents=True, exist_ok=True)


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Drone3D Backend is running",
        "service": "Drone3D Reconstruction API",
        "version": "1.0.0"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {"status": "healthy"}


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
    Delete job temp files and the uploaded video after `delay_seconds`.
    Also removes the in-memory job entry so _jobs doesn't grow forever.
    Runs as a background asyncio task so it never blocks the API.
    """
    await asyncio.sleep(delay_seconds)
    logger.info(f"Cleaning up job files: {job_dir}")
    shutil.rmtree(job_dir, ignore_errors=True)
    if video_path.exists():
        video_path.unlink(missing_ok=True)
    _jobs.pop(job_id, None)          # ← remove from memory store
    logger.info(f"Cleanup complete for: {job_dir.name}")


# ============================================================
# RECONSTRUCTION WORKER
# ============================================================

def _run_reconstruction_job(job_id: str):
    """
    Blocking worker that runs the full pipeline.
    Executed in a ThreadPoolExecutor so FastAPI stays responsive.
    Updates _jobs[job_id] when done.
    """
    job = _jobs[job_id]

    job_dir     = job["job_dir"]
    video_path  = job["video_path"]
    frames_dir  = job_dir / "frames"
    selected_dir = job_dir / "selected_frames"
    final_dir   = job_dir / "final_frames"
    colmap_dir  = job_dir / "colmap"

    try:
        _jobs[job_id]["status"] = JobStatus.PROCESSING

        # ------------------------------------------------
        # STEP 2 — Extract frames (FPS-aware)
        # ------------------------------------------------
        # Uses target_fps=2.0 by default: extracts ~2 frames
        # per second regardless of source FPS (30/60/etc.)
        logger.info(f"[{job_id}] STEP 2: Extracting frames")
        extraction_result = extract_frames(
            video_path=str(video_path),
            output_dir=str(frames_dir),
            target_fps=2.0
        )

        # ------------------------------------------------
        # STEP 3 — Sharpness filter (adaptive)
        # ------------------------------------------------
        # Threshold 100 (down from 300) — old value was too
        # aggressive for typical drone footage and discarded
        # usable frames. Adaptive lowering kicks in if too
        # many frames would be rejected.
        logger.info(f"[{job_id}] STEP 3: Sharpness filter")
        sharpness_result = filter_sharp_frames(
            frames_dir=str(frames_dir),
            selected_dir=str(selected_dir),
            threshold=100.0
        )

        # ------------------------------------------------
        # STEP 4 — Redundancy filter (with safety floor)
        # ------------------------------------------------
        # Threshold 5.0 (down from 8.0) — keeps more frames
        # for better camera-baseline coverage.
        logger.info(f"[{job_id}] STEP 4: Redundancy filter")
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
        # Frame selection summary
        # ------------------------------------------------
        logger.info(f"[{job_id}] Frame pipeline summary:")
        logger.info(f"  Frames extracted       : {extraction_result['frames_saved']}")
        logger.info(f"  Rejected for blur      : {sharpness_result.get('blurry_frames_removed', 0)}")
        logger.info(f"  Rejected for brightness: {sharpness_result.get('brightness_frames_removed', 0)}")
        logger.info(f"  Rejected for redundancy: {redundancy_result['redundant_frames_removed']}")
        logger.info(f"  Frames sent to COLMAP  : {len(final_frame_files)}")

        # ------------------------------------------------
        # STEP 5 — COLMAP reconstruction
        # ------------------------------------------------
        logger.info(f"[{job_id}] STEP 5: COLMAP reconstruction")
        reconstruction_result = run_reconstruction(
            image_dir=str(final_dir),
            workspace_dir=str(colmap_dir)
        )

        # ------------------------------------------------
        # STEP 6 — Convert to GLB
        # ------------------------------------------------
        logger.info(f"[{job_id}] STEP 6: Converting to GLB")
        textured_model = Path(reconstruction_result["textured_model"])
        textured_directory = textured_model.parent

        # Discover texture file dynamically
        texture_candidates = (
            list(textured_directory.glob("*.png")) +
            list(textured_directory.glob("*.jpg"))
        )
        if not texture_candidates:
            raise RuntimeError(
                f"No texture file found in textured directory:\n{textured_directory}"
            )
        texture_file = texture_candidates[0]

        glb_file = textured_directory / "model.glb"

        convert_to_glb(
            ply_file=textured_model,
            texture_file=texture_file,
            glb_file=glb_file
        )

        if not glb_file.exists() or glb_file.stat().st_size == 0:
            raise RuntimeError("GLB file was not created or is empty.")

        glb_size_mb = glb_file.stat().st_size / (1024 * 1024)

        logger.info(f"[{job_id}] Reconstruction complete. GLB: {glb_file} ({glb_size_mb:.2f} MB)")

        # Extract reconstruction stats from the improved pipeline
        recon_stats = reconstruction_result.get("reconstruction_stats", {})
        quality_warnings = reconstruction_result.get("quality_warnings", [])

        _jobs[job_id]["status"] = JobStatus.COMPLETE
        _jobs[job_id]["result"] = {
            # Video processing
            "total_video_frames":       extraction_result["total_frames"],
            "frames_extracted":         extraction_result["frames_saved"],
            "video_fps":                extraction_result.get("fps", 0),
            "video_resolution":         f"{extraction_result.get('width', '?')}x{extraction_result.get('height', '?')}",
            "video_duration_seconds":   extraction_result.get("duration_seconds", 0),
            "sharp_frames_kept":        sharpness_result["frames_kept"],
            "blurry_frames_removed":    sharpness_result["blurry_frames_removed"],
            "brightness_frames_removed": sharpness_result.get("brightness_frames_removed", 0),
            "final_frames":             redundancy_result["frames_kept"],
            "redundant_frames_removed": redundancy_result["redundant_frames_removed"],
            # Reconstruction
            "final_frames_directory":   str(final_dir),
            "colmap_workspace":         reconstruction_result["workspace"],
            "sparse_directory":         reconstruction_result["sparse_directory"],
            "model_directory":          reconstruction_result["model_directory"],
            "model_name":               reconstruction_result["model_name"],
            "images_used_for_reconstruction": reconstruction_result["images_used"],
            # Reconstruction quality statistics
            "registered_images":        recon_stats.get("registered_images", 0),
            "registration_ratio":       recon_stats.get("registration_ratio", 0),
            "sparse_points":            recon_stats.get("sparse_points", 0),
            "dense_cloud_points":       recon_stats.get("dense_cloud_points", 0),
            "cleaned_cloud_points":     recon_stats.get("cleaned_cloud_points", 0),
            "outliers_removed":         recon_stats.get("outliers_removed", 0),
            "mesh_vertices":            recon_stats.get("mesh_vertices", 0),
            "mesh_faces":               recon_stats.get("mesh_faces", 0),
            "quality_warnings":         quality_warnings,
            # 3D output
            "dense_point_cloud":        reconstruction_result["dense_point_cloud"],
            "poisson_mesh":             reconstruction_result["poisson_mesh"],
            "textured_model":           str(textured_model),
            "texture":                  str(texture_file),
            "glb_model":                str(glb_file),
            "glb_size_mb":              round(glb_size_mb, 2),
            # URL
            "model_url":                f"/model/{job_id}",
            # Status
            "pipeline_status":          "complete"
        }

    except Exception as e:
        logger.error(f"[{job_id}] Reconstruction FAILED: {e}")
        traceback.print_exc()
        _jobs[job_id]["status"] = JobStatus.FAILED
        _jobs[job_id]["error"]  = str(e)


# ============================================================
# VIDEO UPLOAD
# ============================================================

@app.post("/upload")
async def upload_video(
    request: Request,
    file: UploadFile = File(...)
):
    # ========================================================
    # CHECK FILE SIZE (Content-Length header)
    # ========================================================

    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(
                f"File is too large. "
                f"Maximum allowed size is {MAX_UPLOAD_BYTES // (1024**3)} GB."
            )
        )

    # ========================================================
    # CHECK FILE NAME
    # ========================================================

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected.")

    allowed_extensions = {".mp4", ".mov", ".avi", ".mkv"}
    original_filename = Path(file.filename).name
    extension = Path(original_filename).suffix.lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported video format: {extension}. "
                "Supported formats are MP4, MOV, AVI and MKV."
            )
        )

    # ========================================================
    # CREATE JOB
    # ========================================================

    job_id = str(uuid.uuid4())
    job_dir = TEMP_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    video_path = UPLOAD_DIR / f"{job_id}_{original_filename}"

    logger.info(f"New job: {job_id} | file: {original_filename}")

    # ========================================================
    # STEP 1 — Save video
    # ========================================================

    logger.info(f"[{job_id}] STEP 1: Saving video to {video_path}")

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
        raise HTTPException(status_code=500, detail="Uploaded video was not saved or is empty.")

    # ========================================================
    # REGISTER JOB
    # ========================================================

    _jobs[job_id] = {
        "status":     JobStatus.QUEUED,
        "filename":   original_filename,
        "job_dir":    job_dir,
        "video_path": video_path,
        "result":     None,
        "error":      None
    }

    # ========================================================
    # QUEUE GUARD — reject if both worker threads are busy
    # ========================================================

    running_jobs = sum(
        1 for j in _jobs.values()
        if j.get("status") == JobStatus.PROCESSING
    )
    if running_jobs >= MAX_CONCURRENT_RECONSTRUCTIONS:
        shutil.rmtree(job_dir, ignore_errors=True)
        if video_path.exists():
            video_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=503,
            detail=(
                f"Reconstruction server is at capacity ({MAX_CONCURRENT_RECONSTRUCTIONS} jobs running). "
                "Please try again in a few minutes."
            )
        )

    # ========================================================
    # LAUNCH BACKGROUND RECONSTRUCTION
    # ========================================================

    loop = asyncio.get_running_loop()
    loop.run_in_executor(_executor, _run_reconstruction_job, job_id)

    # Schedule cleanup after retention period
    asyncio.create_task(_cleanup_job_files(job_id, job_dir, video_path))

    # ========================================================
    # BUILD RESPONSE URLS
    # ========================================================

    base_url = str(request.base_url).rstrip("/")
    status_url  = f"/status/{job_id}"
    model_url   = f"/model/{job_id}"

    logger.info(f"[{job_id}] Job accepted. Reconstruction running in background.")

    return {
        "status":           "accepted",
        "message":          "Video uploaded. Reconstruction is running in the background.",
        "job_id":           job_id,
        "filename":         original_filename,
        "status_url":       status_url,
        "status_absolute":  f"{base_url}{status_url}",
        "model_url":        model_url,
        "model_absolute":   f"{base_url}{model_url}",
        "poll_interval_seconds": 30
    }


# ============================================================
# JOB STATUS
# ============================================================

@app.get("/status/{job_id}")
def get_status(job_id: str):
    """
    Poll the status of a reconstruction job.

    Returns one of:
        queued      — job is waiting to start
        processing  — reconstruction is running
        complete    — model is ready; result contains all details
        failed      — something went wrong; error contains the message
    """

    try:
        uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID.")

    if job_id not in _jobs:
        # Return "failed" (not 404) so the frontend stops polling immediately.
        # 404s are silently retried by older browser sessions; "failed" is a
        # recognised terminal state that stops the polling loop.
        return {
            "status": "failed",
            "job_id": job_id,
            "error": (
                "Job not found. The server may have been restarted and "
                "lost its in-memory job state. Please upload your video again."
            ),
        }

    job = _jobs[job_id]
    status = job["status"]

    response = {
        "job_id": job_id,
        "status": status,
        "filename": job.get("filename")
    }

    if status == JobStatus.COMPLETE:
        response["result"] = job["result"]
    elif status == JobStatus.FAILED:
        response["error"] = job["error"]

    return response


# ============================================================
# SERVE GLB MODEL
# ============================================================

def _resolve_glb(job_id: str) -> Path:
    """Find the GLB file for a given job ID."""
    return TEMP_DIR / job_id / "colmap" / "textured" / "model.glb"


@app.get("/model/{job_id}")
def get_model(job_id: str):

    try:
        uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID.")

    glb_file = _resolve_glb(job_id)

    if not glb_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"3D model not found for job: {job_id}"
        )

    if not glb_file.is_file():
        raise HTTPException(status_code=404, detail="3D model path is not a file.")

    if glb_file.stat().st_size == 0:
        raise HTTPException(status_code=500, detail="3D model file is empty.")

    return FileResponse(
        path=glb_file,
        media_type="model/gltf-binary",
        filename="model.glb",
        headers={"Cache-Control": "no-cache"}
    )


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

    if not glb_file.exists():
        raise HTTPException(status_code=404, detail="3D model not found.")

    if not glb_file.is_file():
        raise HTTPException(status_code=404, detail="3D model is not a file.")

    if glb_file.stat().st_size == 0:
        raise HTTPException(status_code=500, detail="3D model file is empty.")

    return {
        "status": "available",
        "job_id": job_id,
        "filename": "model.glb",
        "size_bytes": glb_file.stat().st_size
    }

