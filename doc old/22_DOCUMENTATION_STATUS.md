# 22 — Documentation status and audit limits

## Source archive inspected
`geoforge-main.zip`, containing 51 archive entries, including backend Python modules and React/TypeScript frontend source.

## Directly inspected source areas
- Backend API/job orchestration in `backend/main.py`
- Frame extraction, filtering, and redundancy modules
- COLMAP/reconstruction module structure
- Textured model to GLB conversion module
- Frontend package scripts/dependencies
- Frontend app, API service/types, page/component structure (source file inventory)

## Facts established from source
- Created and validated `GEOFORGE_MASTER_CONTEXT.md` as the unified master knowledge base for GeoForge (SIH 2026 / NTRO SIH26158).
- FastAPI routes include `/`, `/health`, `/upload`, `/status/{job_id}`, `/model/{job_id}`, and HEAD model route.
- Job statuses include queued, processing, complete, failed.
- API worker calls extraction at 2 FPS, sharp filtering threshold 100, redundancy threshold 5, minimum 20 frames.
- Configured upload max is 4 GiB; worker pool is set to two; retention setting is seven days.
- Frontend default API URL is `http://127.0.0.1:8000`; Vite dev script uses port 3000.
- Main frontend includes upload, processing, completion/result, error/diagnostic, and Three.js viewer components.
- Verified discrepancy: Backend accepts `.mp4`, `.mov`, `.avi`, `.mkv`, while frontend `UploadPage.tsx` only accepts `.mp4`, `.mov`, `.avi`.
- Verified discrepancy: `CompletePage.tsx` displays LAS, GeoTIFF, and OBJ outputs as "READY", but backend only generates PLYs and a GLB.
- Verified discrepancy: Frontend stage progress during polling is client-side simulated up to stage 8, rather than granular backend stage streaming.
- Verified discrepancy: Hardcoded user paths exist in `convert_to_glb.py`, `check_3d.py`, and standalone inspection scripts.

## Not verified
- End-to-end runtime on user's laptop.
- Actual quality/accuracy of generated models for representative footage.
- Whether every optional dependency/branch works in current Python environment.
- Production deployment and security readiness.
- Whether frontend stage indicators match real backend stage telemetry.
- Cleanup scheduling for every path.
- Exact behavior of all API responses without live API tests.
- Existence of georeferencing, orthomosaic, downloadable secondary outputs, or durable jobs as working features.
- Backend dependency versions (no requirements/pyproject manifest included in supplied ZIP).

## Instruction
Update this file whenever runtime tests or code changes establish new facts. Avoid treating a source comment or type declaration as proof of an operational feature.
