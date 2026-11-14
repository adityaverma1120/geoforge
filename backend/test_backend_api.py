"""
test_backend_api.py — Comprehensive Unit & Integration Test Suite for GeoForge Backend

Tests all 17 required backend capabilities:
1. Backend startup & directory initialization
2. /health liveness endpoint
3. /ready readiness endpoint
4. Valid video upload
5. Invalid file extension rejection (HTTP 400)
6. Empty file rejection (HTTP 400)
7. Corrupted video rejection (HTTP 400)
8. Job ID generation & UUID validity
9. SQLite job persistence
10. Status retrieval & field completeness
11. Invalid job ID validation (HTTP 400 & 404)
12. 3D GLB model retrieval (/model/{job_id})
13. GLB attachment download (/download/{job_id})
14. Backend restart & interrupted job recovery
15. Storage & missing file error handling (HTTP 404)
16. Concurrency capacity guard (HTTP 503)
17. Pipeline failure recording & error propagation
"""

import io
import json
import os
import shutil
import struct
import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import cv2
import numpy as np
from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse

import database
import main

def create_dummy_mp4(path: Path, num_frames: int = 15, width: int = 320, height: int = 240) -> Path:
    """Helper: create a small, valid decodable MP4 video."""
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(path), fourcc, 10.0, (width, height))
    for i in range(num_frames):
        frame = np.full((height, width, 3), (i * 15 % 255, 120, 80), dtype=np.uint8)
        cv2.putText(frame, f"TEST {i}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        out.write(frame)
    out.release()
    return path

def create_dummy_glb(path: Path) -> Path:
    """Helper: create a minimal, structurally valid binary glTF v2 file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # glTF JSON chunk
    gltf_dict = {
        "asset": {"version": "2.0", "generator": "GeoForge Test"},
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}]
    }
    json_bytes = json.dumps(gltf_dict).encode("utf-8")
    while len(json_bytes) % 4 != 0:
        json_bytes += b" "

    json_chunk_len = len(json_bytes)
    total_len = 12 + 8 + json_chunk_len

    with open(path, "wb") as f:
        # Header: magic (4s), version (I), length (I)
        f.write(struct.pack("<4sII", b"glTF", 2, total_len))
        # JSON Chunk: length (I), type (4s), data
        f.write(struct.pack("<I4s", json_chunk_len, b"JSON"))
        f.write(json_bytes)
    return path

def run_tests():
    print("=" * 70)
    print("GEOFORGE BACKEND UNIT & INTEGRATION TEST SUITE (17 CHECKS)")
    print("=" * 70)

    # 1. Backend startup & directory initialization
    print("\n[TEST 1] Backend startup & directory initialization...")
    database.init_db()
    for d in (main.UPLOAD_DIR, main.TEMP_DIR, main.OUTPUT_DIR):
        assert d.exists(), f"Required directory does not exist: {d}"
    print("PASS: Database and working directories verified.")

    # 2. /health liveness endpoint
    print("\n[TEST 2] Probing /health liveness endpoint...")
    h = main.health()
    assert h["status"] in ("healthy", "degraded")
    assert h["version"] == "1.0.0"
    print(f"PASS: /health returned status={h['status']}")

    # 3. /ready readiness endpoint
    print("\n[TEST 3] Probing /ready readiness endpoint...")
    r = main.ready()
    # In case of degraded/not_ready it returns JSONResponse
    if hasattr(r, "status_code"):
        assert r.status_code in (200, 503)
        r_data = json.loads(r.body.decode())
    else:
        r_data = r
    assert "reconstruction_ready" in r_data
    assert "database_connected" in r_data
    print(f"PASS: /ready returned ready={r_data['reconstruction_ready']}, db_connected={r_data['database_connected']}")

    # 4. Valid video upload
    print("\n[TEST 4] Testing valid video upload...")
    test_video_path = main.TEMP_DIR / "unit_test_sample.mp4"
    create_dummy_mp4(test_video_path)

    dummy_request = MagicMock()
    dummy_request.headers = {}
    dummy_request.base_url = "http://localhost:8000/"

    with open(test_video_path, "rb") as f:
        upload_file = UploadFile(filename="unit_test_sample.mp4", file=f)
        import asyncio
        with patch.object(main, "_run_reconstruction_job", return_value=None):
            upload_resp = asyncio.run(main.upload_video(dummy_request, upload_file))

    assert upload_resp["status"] in ("uploaded", "accepted")
    test_job_id = upload_resp["job_id"]
    assert uuid.UUID(test_job_id)
    print(f"PASS: Valid video uploaded successfully. Job ID: {test_job_id}")

    # 5. Invalid extension
    print("\n[TEST 5] Testing invalid file extension rejection...")
    try:
        invalid_file = UploadFile(filename="malicious.exe", file=io.BytesIO(b"fake binary"))
        asyncio.run(main.upload_video(dummy_request, invalid_file))
        assert False, "Failed to reject invalid extension"
    except HTTPException as e:
        assert e.status_code == 400
        print(f"PASS: Rejected invalid extension with HTTP 400: {e.detail}")

    # 6. Empty upload
    print("\n[TEST 6] Testing empty file rejection...")
    try:
        empty_file = UploadFile(filename="empty.mp4", file=io.BytesIO(b""))
        asyncio.run(main.upload_video(dummy_request, empty_file))
        assert False, "Failed to reject empty file"
    except HTTPException as e:
        assert e.status_code == 400
        print(f"PASS: Rejected empty file with HTTP 400: {e.detail}")

    # 7. Corrupted video
    print("\n[TEST 7] Testing corrupted video rejection...")
    try:
        corrupted_file = UploadFile(filename="corrupted.mp4", file=io.BytesIO(b"not a valid mp4 header content"))
        asyncio.run(main.upload_video(dummy_request, corrupted_file))
        assert False, "Failed to reject corrupted video"
    except HTTPException as e:
        assert e.status_code == 400
        print(f"PASS: Rejected corrupted video with HTTP 400: {e.detail}")

    # 8. Job ID generation & UUID validity
    print("\n[TEST 8] Validating Job ID format...")
    parsed_uuid = uuid.UUID(test_job_id)
    assert parsed_uuid.version == 4
    print(f"PASS: Job ID {test_job_id} is a valid RFC 4122 v4 UUID.")

    # 9. SQLite job persistence
    print("\n[TEST 9] Verifying SQLite job persistence...")
    persisted_job = database.get_job(test_job_id)
    assert persisted_job is not None
    assert persisted_job["filename"] == "unit_test_sample.mp4"
    assert persisted_job["job_id"] == test_job_id
    print("PASS: Job correctly persisted in SQLite database.")

    # 10. Status retrieval & field completeness
    print("\n[TEST 10] Testing status retrieval endpoint...")
    status_data = main.get_status(test_job_id)
    assert status_data["job_id"] == test_job_id
    assert "status" in status_data
    assert "stage" in status_data
    assert "progress_percent" in status_data
    print(f"PASS: Status retrieval verified. Status={status_data['status']}, Stage={status_data['stage']}")

    # 11. Invalid job ID validation
    print("\n[TEST 11] Testing invalid job ID validation...")
    try:
        main.get_status("invalid-not-uuid")
        assert False, "Failed to reject invalid UUID format"
    except HTTPException as e:
        assert e.status_code == 400
        print(f"PASS: Invalid UUID rejected with HTTP 400: {e.detail}")

    # Test non-existent valid UUID
    non_existent = str(uuid.uuid4())
    try:
        main.get_status(non_existent)
        assert False, "Failed to return 404 for non-existent job"
    except HTTPException as e:
        assert e.status_code == 404
        print(f"PASS: Non-existent job returned HTTP 404: {e.detail}")

    # 12. 3D GLB model retrieval
    print("\n[TEST 12] Testing GLB model retrieval (/model/{job_id})...")
    dummy_glb_path = main.TEMP_DIR / test_job_id / "colmap" / "textured" / "model.glb"
    create_dummy_glb(dummy_glb_path)
    model_response = main.get_model(test_job_id)
    assert isinstance(model_response, FileResponse)
    assert model_response.media_type == "model/gltf-binary"
    print("PASS: /model/{job_id} returned valid FileResponse with media_type='model/gltf-binary'.")

    # 13. GLB attachment download
    print("\n[TEST 13] Testing GLB attachment download (/download/{job_id})...")
    download_response = main.download_model(test_job_id)
    assert isinstance(download_response, FileResponse)
    assert "Content-Disposition" in download_response.headers
    assert "attachment" in download_response.headers["Content-Disposition"]
    print(f"PASS: /download/{test_job_id} returned attachment header: {download_response.headers['Content-Disposition']}")

    # 14. Backend restart & interrupted job recovery
    print("\n[TEST 14] Testing restart & interrupted job recovery...")
    interrupted_id = str(uuid.uuid4())
    database.create_job(interrupted_id, "interrupted.mp4", Path("fake/path"), Path("fake/dir"))
    database.update_job_progress(interrupted_id, status="processing", stage="dense_stereo", progress_percent=70)
    recovered_count = database.recover_interrupted_jobs()
    assert recovered_count >= 1
    recovered_job = database.get_job(interrupted_id)
    assert recovered_job["status"] == "failed"
    assert "interrupted" in recovered_job["error_message"].lower()
    print(f"PASS: Interrupted job {interrupted_id} cleanly recovered to failed status.")

    # 15. Storage & missing file error handling
    print("\n[TEST 15] Testing storage & missing file handling...")
    missing_id = str(uuid.uuid4())
    try:
        main.get_model(missing_id)
        assert False, "Failed to return 404 for missing model"
    except HTTPException as e:
        assert e.status_code == 404
        print(f"PASS: Missing 3D model correctly returned HTTP 404: {e.detail}")

    # 16. Concurrency capacity guard
    print("\n[TEST 16] Testing concurrency capacity guard (HTTP 503)...")
    busy_job_id = str(uuid.uuid4())
    database.create_job(busy_job_id, "busy.mp4", Path("fake/path"), Path("fake/dir"))
    database.update_job_progress(busy_job_id, status="processing")
    try:
        with open(test_video_path, "rb") as f:
            busy_upload = UploadFile(filename="busy_test.mp4", file=f)
            asyncio.run(main.upload_video(dummy_request, busy_upload))
        assert False, "Failed to trigger concurrency capacity 503 guard"
    except HTTPException as e:
        assert e.status_code == 503
        print(f"PASS: Concurrency limit enforced with HTTP 503: {e.detail}")
    finally:
        database.delete_job(busy_job_id)

    # 17. Pipeline failure recording & error propagation
    print("\n[TEST 17] Testing pipeline failure recording & error propagation...")
    fail_job_id = str(uuid.uuid4())
    database.create_job(fail_job_id, "fail_test.mp4", Path("fake/path"), Path("fake/dir"))
    database.update_job_progress(
        fail_job_id,
        status="failed",
        stage="sparse_reconstruction",
        stage_message="Sparse SfM failed: insufficient feature matches",
        error="Registration ratio 12% below 30% threshold."
    )
    fail_status = main.get_status(fail_job_id)
    assert fail_status["status"] == "failed"
    assert fail_status["stage"] == "sparse_reconstruction"
    assert "insufficient" in fail_status["message"]
    assert "threshold" in fail_status["error"]
    print("PASS: Pipeline failure details correctly recorded in SQLite and served via API.")

    # Clean up test artifacts
    if test_video_path.exists():
        test_video_path.unlink(missing_ok=True)
    database.delete_job(test_job_id)
    database.delete_job(interrupted_id)
    database.delete_job(fail_job_id)
    shutil.rmtree(main.TEMP_DIR / test_job_id, ignore_errors=True)

    print("\n" + "=" * 70)
    print("ALL 17 BACKEND UNIT & INTEGRATION TESTS PASSED CLEANLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
