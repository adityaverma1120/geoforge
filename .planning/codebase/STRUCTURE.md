# Codebase Structure

**Analysis Date:** 2026-11-12

## Directory Layout

```
geoforge-main/
├── backend/                       # Python FastAPI backend & photogrammetry worker
│   ├── uploads/                   # Raw uploaded videos: {job_id}_{filename}
│   ├── temp/                      # Per-job workspaces: temp/{job_id}/...
│   ├── database.py                # Persistent SQLite job manager
│   ├── main.py                    # REST API endpoints & pipeline coordinator
│   ├── frame_processing.py        # Video validation & 2.0 FPS frame extraction
│   ├── frame_filtering.py         # Laplacian blur & luminance filtering
│   ├── redundancy_filter.py       # MAD redundancy reduction
│   ├── reconstruction.py          # COLMAP SfM/MVS & Open3D Poisson meshing
│   ├── convert_to_glb.py          # Trimesh & Pillow binary GLB packager
│   └── requirements.txt           # Python dependency specifications
├── frontend/                      # React 19 + TypeScript + Vite frontend
│   ├── src/
│   │   ├── components/            # Reusable UI widgets (ThreeDViewer, Diagnostics)
│   │   ├── pages/                 # Full-page views (Upload, Processing, Complete, History)
│   │   ├── services/              # API client layer (api.ts)
│   │   ├── types.ts               # Core TypeScript definitions
│   │   ├── App.tsx                # Client-side router & root component
│   │   └── main.tsx               # Application bootstrap
│   ├── package.json               # Node.js dependencies & scripts
│   ├── vite.config.ts             # Vite bundler configuration
│   └── tsconfig.json              # TypeScript compilation rules
├── docs/                          # Authoritative technical documentation
├── doc old/                       # Read-only historical audit archive
├── src/                           # Read-only legacy exploration scripts
├── .planning/                     # GSD project memory, roadmap & codebase maps
├── AGENTS.md                      # Canonical AI agent operating protocols
└── README.md                      # Primary project overview & quickstart guide
```

## Directory Purposes

**`backend/`:**
- Purpose: Complete server-side logic, API endpoints, photogrammetric computer vision workers, and job persistence.
- Contains: Python 3.12 modules, SQLite database file (`jobs.db`), and configuration files (`.env`).
- Key files: `main.py` (FastAPI routes and pipeline worker), `database.py` (SQLite persistence), `reconstruction.py` (COLMAP and Open3D orchestrator).
- Subdirectories:
  - `uploads/`: Stores raw uploaded videos during processing.
  - `temp/`: Working directories for each reconstruction job (`temp/{job_id}/`).

**`frontend/`:**
- Purpose: Modern single-page web client providing video upload interface, real-time stage progress telemetry, 3D WebGL viewport, and job history.
- Contains: TypeScript/React source code, Tailwind CSS styling, Vite configuration, and build scripts.
- Key files: `src/App.tsx` (state machine router), `src/components/ThreeDViewer.tsx` (Three.js viewport), `src/services/api.ts` (API transport).
- Subdirectories:
  - `src/components/`: Reusable UI components.
  - `src/pages/`: Main page views.
  - `src/services/`: HTTP communication layer.
  - `dist/`: Compiled production distribution assets.

**`docs/`:**
- Purpose: The single authoritative technical documentation system for GeoForge (34+ master architectural, pipeline, and specification documents).
- Contains: Detailed Markdown reference documents covering COLMAP, Open3D, GLB packaging, backend architecture, and verification.

**`doc old/`:**
- Purpose: Read-only historical audit archive of earlier project proposals, notes, and legacy documentation. Immutable.

**`src/`:**
- Purpose: Read-only legacy standalone exploration scripts created during initial research. Not used in active production pipeline.

**`.planning/`:**
- Purpose: Get Shit Done (GSD) planning artifacts, project state tracking, roadmap, and codebase intelligence documents.

## Key File Locations

**Entry Points:**
- `backend/main.py` — FastAPI application root and ASGI web server entry point.
- `frontend/src/main.tsx` — React application entry point.
- `start_geoforge.bat` — Single-click root launcher for the complete application stack.

**Configuration:**
- `backend/.env` — Backend environment variables (COLMAP path, port, concurrency ceiling).
- `frontend/vite.config.ts` — Vite compiler, proxy, and Tailwind plugin configuration.
- `frontend/tsconfig.json` — Frontend TypeScript compiler options.
- `backend/requirements.txt` — Python backend dependency specifications.
- `frontend/package.json` — Frontend dependencies and build lifecycle scripts.

**Core Logic:**
- `backend/reconstruction.py` — COLMAP SfM/MVS subprocess pipeline and Open3D Poisson surface meshing.
- `backend/convert_to_glb.py` — Trimesh mesh normalization and binary GLB packaging.
- `backend/frame_processing.py` — OpenCV 2.0 FPS keyframe sampling.
- `backend/frame_filtering.py` — Laplacian variance blur detection.
- `backend/redundancy_filter.py` — Redundant frame reduction.
- `backend/database.py` — SQLite persistent state management.
- `frontend/src/components/ThreeDViewer.tsx` — Three.js WebGL 3D viewer.
- `frontend/src/services/api.ts` — Frontend REST API client.

**Testing:**
- `backend/test_backend_api.py` — 17-point integration test for backend endpoints.
- `backend/test_reconstruction_smoke.py` — Smoke verification for reconstruction pipeline.

**Documentation:**
- `README.md` — Project overview and user manual.
- `AGENTS.md` — Canonical AI coding protocol and guardrails.
- `docs/ARCHITECTURE.md` — Authoritative backend and frontend architectural specifications.
- `docs/RECONSTRUCTION_PIPELINE.md` — Authoritative photogrammetric pipeline details.

## Naming Conventions

**Files:**
- Backend: `snake_case.py` for Python modules (e.g. `frame_processing.py`, `database.py`).
- Frontend Components & Pages: `PascalCase.tsx` (e.g. `ThreeDViewer.tsx`, `UploadPage.tsx`).
- Frontend Utilities & Services: `camelCase.ts` (e.g. `api.ts`, `types.ts`).
- Documentation: `UPPER_SNAKE_CASE.md` (e.g. `ARCHITECTURE.md`, `RECONSTRUCTION_PIPELINE.md`).

**Directories:**
- Top-level & Source Directories: `snake_case` or single lowercase word (`backend/`, `frontend/`, `docs/`, `src/`).
- Component Categories: `kebab-case` or lowercase plural (`components/`, `pages/`, `services/`).

**Special Patterns:**
- Per-job directories: `backend/temp/{UUIDv4}/` (e.g. `backend/temp/dda15414-1842-4633-b013-b91e84564d5f/`).
- Uploaded video files: `backend/uploads/{UUIDv4}_{sanitized_filename}`.

## Where to Add New Code

**New Photogrammetry / CV Stage:**
- Primary algorithm: Implement in `backend/` as a dedicated module (e.g. `backend/point_cloud_denoiser.py`).
- Pipeline integration: Wire into `backend/main.py:_run_pipeline_background()` between existing stages and assign a new stage identifier and percentage.
- UI mapping: Update `TOTAL_STAGES` and `mapBackendStageToIndex()` in `frontend/src/App.tsx`.

**New Frontend View or Page:**
- Implementation: Add `frontend/src/pages/NewPage.tsx`.
- Types: Update `AppRoute` union type in `frontend/src/App.tsx`.
- Navigation: Add routing block and navigation callback in `frontend/src/App.tsx`.

**New REST API Endpoint:**
- Definition: Add FastAPI route in `backend/main.py` with explicit UUID and payload validation.
- Database access: Add corresponding query helper in `backend/database.py`.
- Frontend service: Add API caller function in `frontend/src/services/api.ts`.
- Tests: Add verification assertion in `backend/test_backend_api.py`.

## Special Directories

**`backend/temp/`:**
- Purpose: Ephemeral scratch space containing heavy intermediate artifacts (extracted frames, COLMAP databases, point clouds, depth maps).
- Committed: No (listed in `.gitignore`).

**`backend/uploads/`:**
- Purpose: Raw uploaded drone video files.
- Committed: No (listed in `.gitignore`).

**`frontend/dist/`:**
- Purpose: Production-ready bundled JavaScript, CSS, and HTML assets generated by `npm run build`.
- Committed: No (build artifact).

**`.venv/`:**
- Purpose: Local Python 3.12 virtual environment containing installed wheels.
- Committed: No (listed in `.gitignore`).

---

*Structure analysis: 2026-11-12*
*Update when directory structure changes*

