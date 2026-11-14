# 06 — End-to-end workflow

## User workflow
1. Navigate through home/how-it-works to upload page.
2. Select a supported video.
3. Start upload; frontend sends multipart `file` using XHR and can report upload percentage.
4. Backend validates filename extension and declared content length, saves upload, creates UUID job.
5. Frontend receives job ID and begins polling the status route.
6. Backend worker changes job to processing and runs pipeline.
7. On completion backend exposes result metadata and model URL.
8. Frontend transitions to completion/result UI and requests GLB.
9. Three.js viewer parses and renders GLB; UI reports loading or model errors.

## Backend pipeline (as orchestrated in `backend/main.py`)
1. **Extract frames:** `extract_frames(..., target_fps=2.0)`.
2. **Quality filtering:** `filter_sharp_frames(..., threshold=100.0)`; module also considers brightness and has adaptive behavior documented in its implementation comments.
3. **Redundancy filtering:** `remove_redundant_frames(..., difference_threshold=5.0)`.
4. **Minimum-frame guard:** no empty result allowed; at least 20 frames are required by configuration.
5. **COLMAP reconstruction:** `run_reconstruction(image_dir, workspace_dir)`.
6. **Find texture:** backend looks for PNG/JPG texture candidate in textured directory.
7. **GLB conversion:** `convert_to_glb(ply_file, texture_file, glb_file)`.
8. **Validate output:** checks GLB exists and is non-empty.
9. **Set job complete:** result includes input/frame stats, reconstruction stats, artifact paths and model URL.

## Failure behavior
Worker catches exceptions, records failed status and error text, and logs traceback. API client maps HTTP/network and reconstruction errors into UI errors. Test actual error visibility rather than assuming every message is user-friendly.
