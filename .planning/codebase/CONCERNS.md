# Codebase Concerns

**Analysis Date:** 2026-11-12

## Tech Debt

**Duplicate Route Definition in `backend/main.py`:**
- Issue: `@app.get("/jobs") def list_jobs_endpoint` is defined twice in `backend/main.py` (line 871 and line 962). The second definition silently shadows the first.
- Files: `backend/main.py` (lines 871-875 and lines 962-966)
- Why: Merged from separate PR branches during historical development.
- Impact: Code clutter and maintenance confusion, though functionality is identical.
- Fix approach: Remove the duplicate definition at line 962 and retain line 871 with its docstring.

**Unused Cloud AI Package in `frontend/package.json`:**
- Issue: `@google/genai` (^2.4.0) is present in `frontend/package.json` dependencies but is unused in the active UI code.
- Files: `frontend/package.json` (line 14)
- Why: Leftover from initial prototyping exploration.
- Impact: Unnecessary bundle bloat; potential security confusion regarding air-gapped compliance.
- Fix approach: Remove `@google/genai` and run `npm prune`.

**In-Memory Job Cache Sync:**
- Issue: `_jobs` dictionary in `backend/main.py` duplicates state stored in SQLite `backend/jobs.db`.
- Files: `backend/main.py`
- Why: Implemented as a fast cache for polling endpoints.
- Impact: Potential desynchronization if mutations occur outside `main.py` or during server crashes.
- Fix approach: Use SQLite database as single source of truth; replace `_jobs` cache with direct fast SQLite reads or an LRU cache.

## Known Bugs

**History Route View Mount in `frontend/src/App.tsx`:**
- Symptoms: Clicking "History" in the navbar updates internal route state to `'history'`, but the view does not render if the conditional render block is omitted.
- Trigger: Navigating to History page from navigation menu.
- Files: `frontend/src/App.tsx`
- Workaround: Direct URL routing or state reset.
- Root cause: Missing JSX element `{currentRoute === 'history' && <HistoryPage onSelectJob={handleSelectHistoryJob} onNavigate={navigate} />}` in the main view switch block.
- Fix approach: Insert the `<HistoryPage />` component into the active route switch block before the error route block.

**Potential SQLite Lock Under Rapid Concurrency:**
- Symptoms: `sqlite3.OperationalError: database is locked` on rapid simultaneous reads and writes.
- Trigger: Extremely rapid polling (<100ms) from multiple browser tabs while reconstruction is writing stage logs.
- Files: `backend/database.py`
- Workaround: Connection timeout set to 30.0s.
- Root cause: Default SQLite rollback journal mode locks entire database file during writes.
- Fix approach: Enable Write-Ahead Logging (WAL) in `database.py`: `conn.execute("PRAGMA journal_mode=WAL")`.

## Security Considerations

**Unauthenticated Local API:**
- Risk: Any local process or browser on the network can trigger video uploads, view models, or delete reconstruction jobs.
- Files: `backend/main.py`
- Current mitigation: Designed for single-tenant air-gapped defense workstations with localhost CORS origin protection.
- Recommendations: Add an optional API key header (`X-GeoForge-Key`) or basic HTTP authentication when deploying across a shared local area network.

**4 GB File Upload Memory & Disk Consumption:**
- Risk: Malicious or oversized video uploads can exhaust disk space on the host SSD.
- Files: `backend/main.py:upload_video`
- Current mitigation: Streaming chunk validation rejecting files exceeding `MAX_UPLOAD_BYTES = 4 * 1024 * 1024 * 1024` and disk free space check in `/ready`.
- Recommendations: Pre-validate Content-Length header before accepting chunk streams.

## Performance Bottlenecks

**COLMAP Dense Stereo & Stereo Fusion Execution:**
- Problem: COLMAP MVS stages (`patch_match_stereo` and `stereo_fusion`) represent 70-85% of total reconstruction wall-clock time (typically 3 to 15 minutes depending on frame count).
- Files: `backend/reconstruction.py`
- Measurement: 120 frames take ~8-12 minutes on RTX 3050 Laptop GPU (6 GB VRAM).
- Cause: Intense per-pixel disparity matching and multi-view geometric verification.
- Improvement path: Adjust `PatchMatchStereo.window_radius` from 5 to 4 or limit maximum image dimension (`--max_image_size 1600`) for rapid preview reconstructions.

**Frontend 3D Model Asset Transfer:**
- Problem: Binary GLB models with high-resolution texture maps range from 1.5 MB to 25 MB.
- Files: `backend/main.py:get_model_glb`, `frontend/src/components/ThreeDViewer.tsx`
- Measurement: 2-5 seconds load time over slower connections.
- Cause: Embedded uncompressed PNG texture maps in GLB.
- Improvement path: Implement JPEG texture compression or WebP textures in Trimesh packaging (`backend/convert_to_glb.py`).

## Fragile Areas

**COLMAP Binary CLI Dependency on Windows:**
- File: `backend/reconstruction.py`
- Why fragile: Relies on external `colmap.bat` or `colmap.exe` in specific system locations with compatible CUDA drivers.
- Common failures: Missing CUDA DLLs (`cudart64_*.dll`), path-with-spaces quoting failures, or driver version mismatches.
- Safe modification: Always execute via `subprocess.run(args)` with argument arrays (never `shell=True`), verify via `backend/colmap_test.py` before pipeline execution.
- Test coverage: Tested in `test_reconstruction_smoke.py`.

**Photogrammetry Single-Pass Video Geometry:**
- File: `backend/frame_processing.py`, `backend/frame_filtering.py`
- Why fragile: Pure linear forward drone flight (without camera tilt, orbit, or lateral parallax) provides insufficient parallax for SfM feature triangulation, leading to COLMAP camera registration failure.
- Common failures: "Could not register any cameras" error from COLMAP mapper.
- Safe modification: Provide clear UI guidance advising users to fly orbit, spiral, or serpentine grid flight patterns.

## Scaling Limits

**Hardware VRAM Ceiling (RTX 3050 Laptop GPU 6 GB):**
- Current capacity: Exactly 1 concurrent reconstruction (`MAX_CONCURRENT_RECONSTRUCTIONS = 1`).
- Limit: Processing 2 concurrent reconstructions triggers CUDA Out-Of-Memory (`CUDA out of memory` in `patch_match_stereo`).
- Symptoms at limit: COLMAP crash with non-zero exit code, pipeline failure.
- Scaling path: Maintain single-worker queue lock on single-GPU workstations; scale horizontally across nodes for multi-user deployments.

**Host Storage Capacity:**
- Current capacity: ~512 GB SSD.
- Limit: Intermediate COLMAP dense workspaces can require 2-5 GB per reconstruction.
- Symptoms at limit: Disk full errors during dense stereo depth map generation.
- Scaling path: Auto-purge ephemeral intermediate frames and depth maps upon successful GLB generation while preserving `model.glb` and `metadata.json`.

## Dependencies at Risk

**Open3D Windows Compatibility:**
- Risk: Open3D (0.18.0) can occasionally encounter C++ runtime library conflicts or DLL load issues across different minor Python versions on Windows.
- Impact: Poisson surface meshing crashes.
- Migration plan: Pinned to verified Python 3.12 64-bit environment in `.venv`.

## Missing Critical Features

**Direct LAS / LAZ Point Cloud Export:**
- Problem: Users currently can only download binary GLB models; raw GIS point clouds (LAS/LAZ) are retained internally in `fused.ply` but lack a dedicated download endpoint.
- Current workaround: Manual PLY extraction from `backend/temp/{job_id}/colmap/dense/fused.ply`.
- Blocks: Integration with geospatial GIS software (QGIS, ArcGIS).
- Implementation complexity: Low (add `laspy` converter and `/download/las/{job_id}` endpoint).

**GPS Exif Georeferencing:**
- Problem: Reconstruction operates in arbitrary metric local coordinates; drone flight GPS logs are not yet embedded into the model spatial transform.
- Current workaround: Relative distance scale measurements.
- Blocks: True geolocated GIS coordinate alignment.
- Implementation complexity: Medium (parse video subtitle/telemetry metadata SRT or flight logs).

## Test Coverage Gaps

**Frontend Automated Unit & Component Tests:**
- What's not tested: React component rendering, Three.js canvas setup, user interactions.
- Risk: UI regressions (e.g. broken viewer controls or routing glitches) slipping through build step.
- Priority: Medium.
- Difficulty to test: Requires setting up Vitest, `@testing-library/react`, and WebGL canvas mocks.

**Stress Testing with Multiple Concurrent Uploads:**
- What's not tested: Behavior when 10+ simultaneous uploads hit `/upload` simultaneously.
- Risk: Thread pool starvation or file descriptor exhaustion.
- Priority: Medium.

---

*Concerns audit: 2026-11-12*
*Update as issues are fixed or new ones discovered*

