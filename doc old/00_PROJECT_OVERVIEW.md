# 00 — Project overview

## Product summary
GeoForge takes a video of a scene—intended for drone or phone capture—and creates a textured 3D model suitable for interactive viewing in a browser. The current codebase is a React/TypeScript/Vite frontend and a Python/FastAPI backend. COLMAP performs photogrammetric reconstruction; Open3D and related tooling are used for point-cloud/mesh operations; Trimesh and Pillow are used for GLB packaging.

## User-facing path
1. User opens the application.
2. User selects a supported video and starts reconstruction.
3. Frontend uploads the video to `POST /upload`.
4. Backend returns a job identifier and status URL.
5. Frontend polls `GET /status/{job_id}`.
6. Backend processes frames and reconstructs the scene.
7. On completion, frontend obtains the model URL and loads a GLB using Three.js.
8. User inspects the reconstructed scene in the 3D viewer.

## Main outputs
- COLMAP sparse reconstruction and dense point cloud artifacts
- Cleaned point cloud and Poisson mesh artifacts, subject to pipeline success
- Textured model and texture image
- `model.glb` served through `/model/{job_id}`

## Limits / interpretation
This is photogrammetry, not a guarantee of survey-grade measurement, georeferencing, or complete reconstruction. Output quality depends on coverage, overlap, motion, texture, lighting, camera calibration, and scene characteristics. The source archive does not prove a metric accuracy guarantee or a geospatial coordinate workflow.
