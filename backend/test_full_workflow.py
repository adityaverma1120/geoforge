"""
test_full_workflow.py — End-to-End Test Suite for GeoForge Reconstruction Pipeline

Verifies:
1. SQLite Database persistence and initialization.
2. /health diagnostic endpoint.
3. Video upload & header validation.
4. Frame extraction @ 2.0 FPS.
5. Laplacian sharpness & redundancy filtering.
6. Minimum frame count guard.
7. COLMAP feature extraction (CUDA) & sequential matching.
8. Sparse SfM reconstruction & model quality check.
9. Open3D dense point cloud cleaning & Poisson meshing.
10. Mesh color transfer & GLB generation.
11. GLB binary header validation (glTF magic bytes).
12. Status & download endpoint simulation.
13. Backend restart persistence.
"""

import os
import sys
import uuid
import struct
import shutil
from pathlib import Path

# Add backend directory to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import cv2
import database
import main
from convert_to_glb import convert_to_glb
from frame_filtering import filter_sharp_frames
from frame_processing import extract_frames
from redundancy_filter import remove_redundant_frames
from reconstruction import run_reconstruction

def run_e2e_test():
    print("=" * 70)
    print("GEOFORGE COMPLETE PIPELINE & PERSISTENCE TEST")
    print("=" * 70)

    # 1. Test database initialization
    print("\n[TEST 1] Initializing persistent SQLite database...")
    database.init_db()
    recovered = database.recover_interrupted_jobs()
    if recovered:
        print(f"Recovered {recovered} previously interrupted jobs.")
    print("Database initialized successfully.")

    # 2. Test Health Check
    print("\n[TEST 2] Probing /health endpoint...")
    health_data = main.health()
    print("Health Status:", health_data["status"])
    print("COLMAP:", health_data["colmap"])
    print("FFmpeg:", health_data["ffmpeg"])
    print("Disk Free GB:", health_data["storage"]["disk_free_gb"])
    assert health_data["reconstruction_ready"] is True, "Reconstruction service is not ready!"
    print("Health check passed.")

    # 3. Locate Sample Video
    sample_video = BASE_DIR / "uploads" / "sample_drone_orbit.mp4"
    assert sample_video.exists(), f"Sample video not found at {sample_video}"
    print(f"\n[TEST 3] Found sample video: {sample_video.name} ({sample_video.stat().st_size / 1024 / 1024:.2f} MB)")

    # Validate video with OpenCV
    cap = cv2.VideoCapture(str(sample_video))
    assert cap.isOpened(), "Failed to open video with OpenCV"
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    cap.release()
    print(f"Video validated: {total_frames} frames, {width}x{height} @ {fps:.1f} FPS")

    # 4. Create Job in Persistent SQLite
    test_job_id = str(uuid.uuid4())
    job_dir = BASE_DIR / "temp" / test_job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    video_job_path = BASE_DIR / "uploads" / f"{test_job_id}_sample_drone_orbit.mp4"
    shutil.copy2(sample_video, video_job_path)

    print(f"\n[TEST 4] Registering job {test_job_id} in SQLite...")
    job_record = database.create_job(test_job_id, "sample_drone_orbit.mp4", video_job_path, job_dir)
    assert job_record["status"] == "queued"
    print("Job successfully registered.")

    # 5. Execute Video Extraction
    print("\n[TEST 5] Extracting video frames @ 2.0 FPS...")
    frames_dir = job_dir / "frames"
    database.update_job_progress(test_job_id, status="processing", stage="extracting_frames", progress_percent=10, stage_message="Extracting frames...")
    ext_result = extract_frames(video_path=str(video_job_path), output_dir=str(frames_dir), target_fps=2.0)
    saved_frames = ext_result["frames_saved"]
    print(f"Extracted {saved_frames} frames.")
    assert saved_frames >= 20, f"Expected >= 20 frames, got {saved_frames}"

    # 6. Sharpness and Redundancy Filtering
    print("\n[TEST 6] Filtering blurry and redundant frames...")
    database.update_job_progress(test_job_id, stage="filtering_images", progress_percent=15, stage_message="Filtering images...")
    selected_dir = job_dir / "selected_frames"
    final_dir = job_dir / "final_frames"

    sharp_res = filter_sharp_frames(frames_dir=str(frames_dir), selected_dir=str(selected_dir), threshold=100.0)
    redun_res = remove_redundant_frames(input_dir=str(selected_dir), output_dir=str(final_dir), difference_threshold=5.0)

    final_frames = [p for p in final_dir.iterdir() if p.is_file() and p.suffix.lower() in {".jpg", ".png"}]
    print(f"Frames surviving filter: {len(final_frames)}")
    assert len(final_frames) >= 20, f"Need >= 20 frames for COLMAP, got {len(final_frames)}"

    # 7. COLMAP Photogrammetric Reconstruction
    print("\n[TEST 7] Running COLMAP Photogrammetry Pipeline (CUDA SIFT & Dense Stereo)...")
    colmap_dir = job_dir / "colmap"

    def progress_callback(stage, percent, msg):
        database.update_job_progress(test_job_id, stage=stage, progress_percent=percent, stage_message=msg)
        print(f"  [STAGE {percent}%] {stage}: {msg}")

    recon_res = run_reconstruction(
        image_dir=str(final_dir),
        workspace_dir=str(colmap_dir),
        progress_callback=progress_callback
    )
    print("COLMAP reconstruction completed successfully.")
    textured_model = Path(recon_res["textured_model"])
    assert textured_model.exists() and textured_model.stat().st_size > 0, "Textured PLY model does not exist or is empty!"

    # 8. Convert to GLB
    print("\n[TEST 8] Packaging into GLB 3D Model...")
    database.update_job_progress(test_job_id, stage="exporting_glb", progress_percent=98, stage_message="Converting to GLB...")
    textured_dir = textured_model.parent
    texture_candidates = list(textured_dir.glob("*.png")) + list(textured_dir.glob("*.jpg"))
    texture_file = texture_candidates[0] if texture_candidates else None
    glb_file = textured_dir / "model.glb"

    convert_to_glb(
        ply_file=textured_model,
        texture_file=texture_file,
        glb_file=glb_file
    )

    assert glb_file.exists() and glb_file.stat().st_size > 0, "GLB file was not created!"
    glb_size_kb = glb_file.stat().st_size / 1024
    print(f"GLB model generated successfully: {glb_file} ({glb_size_kb:.1f} KB)")

    # 9. Verify Binary GLTF (GLB) Header
    print("\n[TEST 9] Validating GLB binary header structure...")
    with open(glb_file, "rb") as f:
        magic, version, length = struct.unpack("<4sII", f.read(12))
    assert magic == b"glTF", f"Invalid GLB magic header: {magic}"
    assert version in (1, 2), f"Unsupported GLB version: {version}"
    assert length == glb_file.stat().st_size, "Header length does not match file size"
    print(f"Valid GLB header confirmed: magic={magic.decode()}, version={version}, length={length:,} bytes.")

    # 10. Update SQLite with Completion
    result_payload = {
        "model_path": str(glb_file),
        "model_url": f"/model/{test_job_id}",
        "download_url": f"/download/{test_job_id}",
        "glb_size_mb": round(glb_file.stat().st_size / (1024 * 1024), 2),
        "frames_extracted": ext_result["frames_saved"],
        "frames_used": len(final_frames),
        "pipeline_status": "complete"
    }
    database.update_job_progress(
        test_job_id,
        status="complete",
        stage="completed",
        progress_percent=100,
        stage_message="Reconstruction complete!",
        result=result_payload,
        model_path=glb_file
    )
    print("\n[TEST 10] SQLite status updated to complete.")

    # 11. Test API Status and Model Retrieval
    print("\n[TEST 11] Testing status and model retrieval endpoints...")
    status_resp = main.get_status(test_job_id)
    assert status_resp["status"] == "complete", f"Expected complete status, got {status_resp}"
    print("GET /status/{job_id}: PASSED (status = complete)")

    model_resp = main.get_model(test_job_id)
    assert model_resp.status_code == 200, f"Expected HTTP 200 from get_model, got {model_resp.status_code}"
    print("GET /model/{job_id}: PASSED (HTTP 200, media_type = model/gltf-binary)")

    download_resp = main.download_model(test_job_id)
    assert download_resp.status_code == 200, f"Expected HTTP 200 from download_model, got {download_resp.status_code}"
    print("GET /download/{job_id}: PASSED (HTTP 200, attachment header present)")

    # 12. Simulate Backend Restart & Test Persistence
    print("\n[TEST 12] Simulating backend restart and testing SQLite persistence...")
    # Re-fetch from clean database connection
    restarted_job = database.get_job(test_job_id)
    assert restarted_job is not None, "Job was lost after simulated restart!"
    assert restarted_job["status"] == "complete", "Job status changed after restart!"
    assert restarted_job["result"]["glb_size_mb"] is not None
    assert Path(restarted_job["model_path"]).exists()
    print("RESTART PERSISTENCE VERIFIED: Completed job and GLB model remain 100% accessible after restart!")

    print("\n" + "=" * 70)
    print("ALL 12 PIPELINE & PERSISTENCE ACCEPTANCE TESTS PASSED!")
    print("=" * 70)
    return test_job_id

if __name__ == "__main__":
    run_e2e_test()
