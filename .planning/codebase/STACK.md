# Technology Stack

**Analysis Date:** 2026-11-12

## Languages

**Primary:**
- Python 3.12 (64-bit) — Backend photogrammetry pipeline, REST API, frame extraction, computer vision filtering, mesh processing, and packaging (`backend/*.py`)
- TypeScript 5.8 / ES2022 — Frontend application logic, UI components, state machines, API integration, and Three.js 3D viewport (`frontend/src/**/*.ts`, `frontend/src/**/*.tsx`)

**Secondary:**
- PowerShell / Windows Batch (`.bat`) — Automation, service startup, dev environment scripts (`start_geoforge.bat`)
- CSS (Tailwind CSS v4) — Styling and utility design system (`frontend/src/index.css`)
- SQL (SQLite 3 dialect) — Persistent relational job tracking schema (`backend/database.py`)

## Runtime

**Environment:**
- Python 3.12.8 64-bit runtime (virtual environment in `.venv/Scripts/python.exe`)
- Node.js v22.14.0 / npm 10.9.2 runtime (`C:\Users\adity\AppData\Local\Programs\nodejs`)
- External Binary Runtime: COLMAP 4.1.1 CLI (CUDA enabled, installed at `C:\Users\adity\Downloads\COLMAP-3.11.1-windows-cuda\bin\colmap.bat` / `colmap.exe`)
- Client Browser Runtime: WebGL 2.0-capable modern desktop browser (Chrome, Edge, Firefox)

**Package Manager:**
- Python: `pip` (Python 3.12 wheels, standard library venv)
- Frontend: `npm` (Lockfile: `frontend/package-lock.json` present)

## Frameworks

**Core:**
- FastAPI (>=0.110.0, <1.0.0) — High-performance asynchronous REST API server (`backend/main.py`)
- Uvicorn (>=0.28.0, <1.0.0) — ASGI production web server running on port 8000
- React 19 (^19.0.1) — Modern functional component UI library with declarative hooks
- Three.js (^0.185.1) — WebGL 3D rendering library with OrbitControls and GLTFLoader (`frontend/src/components/ThreeDViewer.tsx`)

**Testing:**
- Python `unittest` / direct test runners (`backend/test_backend_api.py`, `backend/test_reconstruction_smoke.py`)
- TypeScript compiler verification (`tsc --noEmit` via `npm run lint`)
- Production bundler validation (`vite build` via `npm run build`)

**Build/Dev:**
- Vite 6 (^6.2.3) — Frontend module bundler and dev server (Port 3000 / Port 8000 unified serving)
- Tailwind CSS 4 (^4.1.14) via `@tailwindcss/vite` plugin — Modern CSS-first build pipeline
- TypeScript 5.8 (~5.8.2) — Static type checker and transpile pipeline

## Key Dependencies

**Critical:**
- `opencv-python` (>=4.9.0, <5.0.0) — Video decoding, 2.0 FPS keyframe sampling, Laplacian blur detection, and luminance filtering (`backend/frame_processing.py`, `backend/frame_filtering.py`)
- `open3d` (>=0.18.0) — Dense point cloud filtering, Poisson surface reconstruction meshing, and density trimming (`backend/reconstruction.py`)
- `trimesh` (>=4.2.0) — 3D mesh import, UV texture binding, PBR material creation, and binary GLB export (`backend/convert_to_glb.py`)
- `pillow` (>=10.2.0) — Image processing for texture map manipulation and GLB embedding (`backend/convert_to_glb.py`)
- `three` (^0.185.1) — Real-time WebGL rendering, orbit controls, bounding box calculation, lighting, and wireframe toggle (`frontend/src/components/ThreeDViewer.tsx`)
- `lucide-react` (^0.546.0) — Iconography for stages, statuses, controls, and UI navigation (`frontend/src/`)
- `motion` (^12.23.24) — Framer Motion animations for page transitions and stage progress bars

**Infrastructure:**
- `python-multipart` (>=0.0.9) — Streaming multi-part form data parser for video uploads up to 4 GB
- `numpy` (>=1.26.0, <2.0.0) — High-performance numeric array calculations for frames and point clouds
- `scipy` (>=1.12.0) — Spatial algorithms and scientific computing helpers
- `dotenv` / `python-dotenv` — Environment variable loader from `backend/.env`

## Configuration

**Environment:**
- Backend configuration: `backend/.env` (mirrored from `backend/.env.example`)
  - `COLMAP_EXE`: Absolute or PATH location of COLMAP CLI binary
  - `MAX_CONCURRENT_RECONSTRUCTIONS`: Concurrency ceiling (set to 1 for 6 GB RTX 3050 VRAM)
  - `ALLOWED_ORIGINS`: Comma-separated CORS allowed domains (e.g. `http://localhost:3000,http://127.0.0.1:8000`)
- Frontend configuration: `frontend/vite.config.ts`, environment via `VITE_API_URL` (defaults to `http://127.0.0.1:8000`)

**Build:**
- `backend/requirements.txt` — Python dependency manifest
- `frontend/package.json` — Node dependency manifest and npm lifecycle scripts
- `frontend/vite.config.ts` — Vite bundling and Tailwind plugin setup
- `frontend/tsconfig.json` — TypeScript compiler configuration

## Platform Requirements

**Development:**
- OS: Windows 11 64-bit (Tested on Dell G15 5530: Intel Core i5-13450HX, 16 GB RAM, NVIDIA RTX 3050 Laptop GPU 6 GB VRAM)
- Python 3.12 64-bit + Node.js 22.x
- CUDA Toolkit & NVIDIA Drivers compatible with COLMAP CUDA builds

**Production:**
- Host: Local workstation / Windows Server (designed for air-gapped NTRO defense deployments)
- Concurrency limit: 1 active reconstruction at a time (hardware protected against GPU OOM)
- Unified HTTP endpoint: FastAPI serving both API and bundled React frontend (`frontend/dist`) on port 8000

---

*Stack analysis: 2026-11-12*
*Update after major dependency changes*

