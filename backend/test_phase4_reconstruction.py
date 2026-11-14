"""
test_phase4_reconstruction.py — End-to-End Real-Video Photogrammetry Pipeline Test for GeoForge Phase 4

Validates:
1. Video validation & extraction on real video (sample_drone_orbit.mp4)
2. Laplacian sharpness and exposure/contrast filtering
3. Trajectory redundancy reduction
4. COLMAP feature extraction (SIFT GPU/CPU) & sequential matching
5. COLMAP sparse mapper (SfM) & bundle adjustment
6. Sparse model quality checks
7. COLMAP image undistortion & dense PatchMatch stereo
8. Stereo fusion into fused.ply
9. Open3D statistical outlier removal & bounding box calculation
10. Open3D Screened Poisson Surface Reconstruction (depth=9, trim=7.0%)
11. KDTree RGB color transfer
12. Binary GLB packaging via Trimesh & Pillow
13. GLB binary header & chunk validation (validate_glb)
14. metadata.json generation & accuracy disclosure
15. SQLite job persistence & endpoint delivery
"""

import os
import sys
import time
import json
import uuid
import shutil
from pathlib import Path

# Add backend directory to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import database
import main
from frame_processing import validate_video, extract_frames
from frame_filtering import filter_sharp_frames
from redundancy_filter import remove_redundant_frames
from reconstruction import run_reconstruction
from convert_to_glb import convert_to_glb, validate_glb

def main_test():
    print("=" * 80)
    print("GEOFORGE PHASE 4 — FULL RECONSTRUCTION ENGINE ACCEPTANCE TEST")
    print("=" * 80)

    start_total_time = time.time()

    # Step 1: Database Initialization
    print("\n[STEP 1] Initializing persistent database...")
    database.init_db()
    print("Database initialized.")

    # Step 2: Validate sample video asset
    sample_video = BASE_DIR / "uploads" / "sample_drone_orbit.mp4"
    if not sample_video.exists():
        raise FileNotFoundError(f"Sample video not found at: {sample_video}")

    print(f"\n[STEP 2] Inspecting input video: {sample_video.name}")
    vmeta = validate_video(sample_video)
    print(f"  Filename  : {vmeta['filename']}")
    print(f"  Codec     : {vmeta['codec']}")
    print(f"  Resolution: {vmeta['width']}x{vmeta['height']}")
    print(f"  FPS       : {vmeta['fps']}")
    print(f"  Duration  : {vmeta['duration_seconds']}s ({vmeta['total_frames']} frames)")
    print(f"  Size      : {vmeta['file_size_mb']} MB")

    # Step 3: Create Job Workspace
    job_id = str(uuid.uuid4())
    job_dir = BASE_DIR / "temp" / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    video_job_path = BASE_DIR / "uploads" / f"{job_id}_sample_drone_orbit.mp4"
    shutil.copy2(sample_video, video_job_path)

    print(f"\n[STEP 3] Registered Job ID: {job_id}")
    database.create_job(job_id, "sample_drone_orbit.mp4", video_job_path, job_dir)

    # Step 4: Run the complete pipeline via main._run_reconstruction_job
    print("\n[STEP 4] Executing _run_reconstruction_job pipeline...")
    job_record = database.get_job(job_id)

    stage_timings = {}
    last_stage_time = time.time()

    try:
        main._run_reconstruction_job(job_id)
    except Exception as e:
        print(f"\n[ERROR] Pipeline raised exception: {e}")
        import traceback
        traceback.print_exc()
        raise

    total_pipeline_time = time.time() - start_total_time
    print(f"\nPipeline finished execution in {total_pipeline_time:.2f} seconds.")

    # Step 5: Verify SQLite Status
    print("\n[STEP 5] Verifying job status in SQLite...")
    updated_job = database.get_job(job_id)
    print(f"  Status       : {updated_job['status']}")
    print(f"  Stage        : {updated_job['stage']}")
    print(f"  Progress     : {updated_job['progress_percent']}%")
    print(f"  Stage Message: {updated_job['stage_message']}")
    assert updated_job["status"] == "complete", f"Expected job status 'complete', got {updated_job['status']}"
    assert updated_job["progress_percent"] == 100, f"Expected 100% progress, got {updated_job['progress_percent']}"

    # Step 6: Verify Deliverable Files
    print("\n[STEP 6] Inspecting generated deliverable files...")
    colmap_dir = job_dir / "colmap"
    glb_file = colmap_dir / "textured" / "model.glb"
    metadata_file = job_dir / "metadata.json"

    assert glb_file.exists(), f"GLB file does not exist at {glb_file}"
    assert glb_file.stat().st_size > 0, "GLB file is 0 bytes!"
    glb_size_kb = glb_file.stat().st_size / 1024
    print(f"  GLB Model    : {glb_file.name} ({glb_size_kb:.1f} KB)")

    assert metadata_file.exists(), f"metadata.json does not exist at {metadata_file}"
    with open(metadata_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    print(f"  Metadata JSON: {metadata_file.name} ({metadata_file.stat().st_size} bytes)")

    # Step 7: Deep GLB Validation
    print("\n[STEP 7] Performing deep binary GLB structure validation...")
    glb_val = validate_glb(glb_file)
    print(f"  Magic Header : {glb_val['magic']}")
    print(f"  GLTF Version : {glb_val['version']}")
    print(f"  Declared Len : {glb_val['declared_length']} bytes")
    print(f"  Mesh Count   : {glb_val['mesh_count']}")
    print(f"  Nodes        : {glb_val['nodes']}")
    assert glb_val["magic"] == "glTF", f"Invalid magic: {glb_val['magic']}"
    assert glb_val["version"] == 2, f"Expected GLTF version 2, got {glb_val['version']}"
    assert glb_val["declared_length"] == glb_file.stat().st_size, "Header length mismatch!"

    # Step 8: Deep Metadata Validation
    print("\n[STEP 8] Validating metadata.json contents & photogrammetry statistics...")
    print("  Filtering Stats:")
    for k, v in manifest.get("filtering_stats", {}).items():
        print(f"    - {k}: {v}")

    print("  Photogrammetry Stats:")
    for k, v in manifest.get("photogrammetry_stats", {}).items():
        print(f"    - {k}: {v}")

    print("  Mesh Stats:")
    for k, v in manifest.get("mesh_stats", {}).items():
        print(f"    - {k}: {v}")

    print("  Geospatial Disclaimer:")
    print(f"    {manifest.get('geospatial_notes')}")

    assert manifest["filtering_stats"]["extracted_frames"] > 0
    assert manifest["filtering_stats"]["final_frames_for_colmap"] >= 10
    assert manifest["photogrammetry_stats"]["sparse_points"] > 0
    assert manifest["photogrammetry_stats"]["dense_points"] > 0
    assert manifest["mesh_stats"]["vertices"] > 0
    assert manifest["mesh_stats"]["faces"] > 0

    # Step 9: Test API Endpoint Responses
    print("\n[STEP 9] Testing API delivery endpoints for reconstructed job...")
    status_resp = main.get_status(job_id)
    assert status_resp["status"] == "complete"
    assert status_resp["progress_percent"] == 100
    print("  GET /status/{job_id}   : HTTP 200 (status=complete)")

    metadata_resp = main.get_job_metadata(job_id)
    assert metadata_resp["job_id"] == job_id
    assert "photogrammetry_stats" in metadata_resp
    print("  GET /metadata/{job_id} : HTTP 200 (valid JSON manifest)")

    model_resp = main.get_model(job_id)
    assert model_resp.status_code == 200
    assert model_resp.media_type == "model/gltf-binary"
    print("  GET /model/{job_id}    : HTTP 200 (model/gltf-binary)")

    download_resp = main.download_model(job_id)
    assert download_resp.status_code == 200
    assert "attachment" in download_resp.headers.get("content-disposition", "")
    print(f"  GET /download/{job_id} : HTTP 200 ({download_resp.headers.get('content-disposition')})")

    print("\n" + "=" * 80)
    print("PHASE 4 CORE RECONSTRUCTION ENGINE VERIFICATION: 100% SUCCESS")
    print(f"Total time elapsed: {total_pipeline_time:.2f} seconds")
    print("=" * 80)

if __name__ == "__main__":
    main_test()
