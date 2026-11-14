# AI Coding Agent Operating Protocols & Guidelines — GeoForge

> **Document:** `AGENTS.md`  
> **Target Audience:** Autonomous AI Assistants, Pair Programmers, and Contributing Developers  
> **Project Identity:** GeoForge — Single-Pass Drone Video to 3D Model Generation System (SIH 2026 / NTRO)  
> **Status:** Canonical Agent Operating Protocol  
> **Last Verified:** 2026-11-11

---

## 1. Project Overview & Context

GeoForge is an automated photogrammetric 3D reconstruction system converting continuous drone flight video (.mp4, .mov, .avi, .mkv) into interactive 3D WebGL models.
- **Backend:** Python 3.12, FastAPI, Uvicorn, OpenCV (`cv2`), Open3D, Trimesh, Pillow, and external COLMAP 4.1.1 CLI (CUDA).
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS v4, Lucide React, Motion, and Three.js (`^0.185.1`).
- **Core Workflow:** Video Ingestion $\to$ 2.0 FPS Extraction $\to$ Laplacian Sharpness Filter $\to$ Redundancy Reduction $\to$ COLMAP SfM & Dense MVS $\to$ Open3D Poisson Meshing (Trimmed 7.0%) $\to$ Texture Atlas $\to$ Binary GLB $\to$ Three.js WebGL Viewer.

---

## 2. Core Source-of-Truth Rules

1. **Source Code is King:** The actual source code in `backend/` and `frontend/src/` is the ultimate authority for feature status. Never assume a feature exists because it is mentioned in comments, UI mockups, older chat logs, or external proposals.
2. **Authoritative Documentation in `docs/`:** The `docs/` directory is the single authoritative technical documentation system.
3. **Preserve `doc old/` as Read-Only:** The `doc old/` directory is an immutable historical audit record. **Never delete, rename, or modify files in `doc old/`**.
4. **Distinguish Verified vs. Planned:** Never classify planned features (e.g. LAS point cloud export, GeoTIFF orthomosaics, GPS RTK georeferencing, SQLite/PostgreSQL persistence) as currently working. Refer to [`docs/FEATURE_STATUS.md`](docs/FEATURE_STATUS.md) for the exact 5-tier classification.

---

## 3. Important Repository Directories

```text
geoforge-main/
├── backend/                   # ACTIVE: FastAPI application and photogrammetry worker
│   ├── main.py                # REST endpoints, CORS, in-memory _jobs, ThreadPoolExecutor
│   ├── reconstruction.py      # COLMAP CLI orchestration, Open3D Poisson meshing
│   ├── frame_processing.py    # OpenCV 2.0 FPS video frame extraction
│   ├── frame_filtering.py     # Laplacian variance blur & luminance filtering
│   ├── redundancy_filter.py   # Mean absolute difference redundancy reduction
│   ├── convert_to_glb.py      # Trimesh & Pillow PBR material GLB packager
│   ├── uploads/               # Raw uploaded videos: {job_id}_{filename}
│   └── temp/                  # Per-job workspaces: temp/{job_id}/colmap/textured/model.glb
├── frontend/                  # ACTIVE: React 19 client application
│   ├── src/
│   │   ├── pages/             # LandingPage, UploadPage, ProcessingPage, CompletePage, etc.
│   │   ├── components/        # ThreeDViewer, DiagnosticsAccordion, Navbar, etc.
│   │   └── services/api.ts    # API client (upload, polling, getModelGlbUrl)
│   └── vite.config.ts         # Vite bundler configuration (Port 3000, 0.0.0.0)
├── docs/                      # AUTHORITATIVE: 34 master technical documents
├── doc old/                   # HISTORICAL AUDIT ARCHIVE (READ-ONLY)
└── src/                       # LEGACY EXPLORATION SCRIPTS (READ-ONLY)
```

> [!WARNING]
> **Active vs. Legacy Boundary:**  
> The active backend pipeline runs strictly in `backend/*.py`. The root `src/` directory contains older, standalone exploration scripts (e.g., `src/detect_blur.py`, `src/remove_redundant.py`) that are not wired into the web application. Do not confuse `src/` with active backend modules.

---

## 4. Documentation Lookup Guide Before Tasks

Always read the relevant master documentation in `docs/` before implementing or modifying features:

| Task Domain | Mandatory Documents to Read First |
|---|---|
| **Photogrammetry, COLMAP & CV** | [`docs/RECONSTRUCTION_PIPELINE.md`](docs/RECONSTRUCTION_PIPELINE.md), [`docs/COLMAP.md`](docs/COLMAP.md), [`docs/OPEN3D.md`](docs/OPEN3D.md), [`docs/PHOTOGRAMMETRY_FUNDAMENTALS.md`](docs/PHOTOGRAMMETRY_FUNDAMENTALS.md) |
| **Meshing, Texturing & GLB** | [`docs/MESH_AND_GLB.md`](docs/MESH_AND_GLB.md), [`docs/OPEN3D.md`](docs/OPEN3D.md) |
| **Backend, API & Jobs** | [`docs/BACKEND.md`](docs/BACKEND.md), [`docs/API.md`](docs/API.md), [`docs/JOB_MANAGEMENT.md`](docs/JOB_MANAGEMENT.md), [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md) |
| **Frontend & 3D Viewer** | [`docs/FRONTEND.md`](docs/FRONTEND.md), [`docs/UI_UX_DESIGN.md`](docs/UI_UX_DESIGN.md), [`docs/API.md`](docs/API.md) |
| **Setup, Deployment & Testing** | [`docs/SETUP.md`](docs/SETUP.md), [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md), [`docs/TESTING.md`](docs/TESTING.md), [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) |
| **Requirements & Status** | [`docs/PRD.md`](docs/PRD.md), [`docs/FEATURE_STATUS.md`](docs/FEATURE_STATUS.md), [`docs/ROADMAP.md`](docs/ROADMAP.md) |
| **System Map & Cross-References** | [`docs/CODEBASE_MAP.md`](docs/CODEBASE_MAP.md), [`docs/CODE_AND_FEATURE_MATRIX.md`](docs/CODE_AND_FEATURE_MATRIX.md), [`docs/MASTER_DOCUMENTATION_INDEX.md`](docs/MASTER_DOCUMENTATION_INDEX.md) |

---

## 5. Coding Conventions & Implementation Standards

### 5.1 Python Backend Conventions
- **PEP 8 Compliance:** Follow standard Python formatting with 4-space indentation.
- **Type Annotations:** Use explicit type hints for all function arguments and returns (`str`, `Path`, `dict`, `tuple`).
- **Pathlib Over OS Path:** Always use `pathlib.Path` for filesystem path operations. Never use raw string concatenations for paths.
- **Subprocess Safety:**
  - Pass command arguments as discrete lists (e.g. `[COLMAP, "mapper", "--database_path", str(db)]`).
  - Never use `shell=True`, `cmd.exe /c`, or string formatting when calling external binaries. This prevents path-with-spaces failures on Windows.
- **Logging Over Print:** Use `logger = logging.getLogger("geoforge")` with structured log prefixes (`[job_id] STEP X: ...`).
- **Clean Exception Handling:** Catch specific exceptions, log stack traces with `traceback.print_exc()`, and map errors to appropriate HTTP status codes (400 Bad Request, 413 Payload Too Large, 500 Internal Error, 503 Busy).

### 5.2 TypeScript / React Frontend Conventions
- **Functional Components:** Use modern React 19 functional components with TypeScript interfaces for props.
- **State Machine Routing:** State transitions between pages are managed in `App.tsx` (`currentPage` state: `landing`, `how-it-works`, `upload`, `processing`, `complete`, `viewer`).
- **Adaptive Polling:** When checking `/status/{job_id}`, maintain the exponential back-off interval schedule (`[3000, 5000, 10000, 20000, 30000]` ms) to avoid saturating backend event loops.
- **Safe GLB URL Resolution:** Use `getModelGlbUrl()` from `services/api.ts` to construct model URLs and avoid duplicate `/model//model/` prefixes.
- **Tailwind Utility Styling:** Adhere to the established dark slate palette (`bg-slate-900`, `text-slate-100`, `border-slate-800`, `text-blue-400`).

---

## 6. Dependency Management Rules

1. **Never Invent Dependencies:** Do not add unverified npm or pip packages without explicit justification.
2. **Pinned Versions:** Maintain compatibility with existing package versions (`React ^19.0.1`, `Three.js ^0.185.1`, `FastAPI ^0.110.0`, `Open3D ^0.18.0`).
3. **No Unused AI SDKs:** Do not import or re-enable `@google/genai` or external cloud AI packages unless the user explicitly requests LLM features.
4. **Windows Cross-Platform Discipline:** Avoid Unix-only shell constructs in `package.json` scripts (e.g. avoid `rm -rf`, use cross-env or Node rimraf).

---

## 7. Testing & Quality Requirements

Before declaring any coding task complete:
1. **Frontend Type Check:** Execute `npm run lint` (`tsc --noEmit`) in `frontend/` to confirm zero TypeScript compilation errors.
2. **Frontend Build Check:** Execute `npm run build` in `frontend/` to ensure production bundle compiles cleanly.
3. **Backend Bytecode Validation:** Run `python -m py_compile` on all modified Python files in `backend/`.
4. **Dependency Probe:** Ensure all backend dependencies import without runtime errors:
   ```powershell
   python -c "import fastapi, uvicorn, multipart, cv2, numpy, open3d, trimesh, PIL; print('Imports valid.')"
   ```
5. **Truth in Reporting:** Never claim a test passed unless you physically executed it and verified exit code 0.

---

## 8. Security & Boundary Defense Protocols

1. **Path Traversal Defense:**
   - Any endpoint receiving a `job_id` must validate it using `uuid.UUID(job_id)`.
   - Any uploaded file must sanitize the name using `Path(file.filename).name`.
2. **File Size Enforcement:** Enforce `MAX_UPLOAD_BYTES = 4 * 1024 * 1024 * 1024` (4 GiB).
3. **Container Whitelisting:** Enforce file extensions strictly against `{".mp4", ".mov", ".avi", ".mkv"}`.
4. **Air-Gap & Privacy Compliance:** GeoForge is designed for NTRO defense evaluations. Ensure zero outbound telemetry, no third-party CDN asset fetching, and no cloud data leakage.

---

## 9. File Modification & Workspace Guardrails

1. **No Personal Developer Paths:** Never introduce developer-specific machine paths (e.g. `C:\Users\Aditya verma\...` or `Drone3DProject`). Use relative paths and environment variables (`COLMAP_EXE`, `VITE_API_URL`).
2. **Preserve Comments & Docstrings:** Retain existing explanatory comments, photogrammetry formulas, and docstrings unless explicitly refactoring that specific logic.
3. **Targeted Diffs Only:** Do not perform mass reformatting or complete rewrites of working files when a targeted 5-line change achieves the goal.
4. **Preserve User Data:** Never delete contents of `backend/uploads/` or `backend/temp/` without explicit user instruction.

---

## 10. Documentation Maintenance Protocols

Whenever you modify application source code, API schemas, or configuration defaults:
1. Update the canonical document in `docs/` (e.g., [`docs/API.md`](docs/API.md) for endpoints, [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md) for parameters).
2. Update [`docs/CODE_AND_FEATURE_MATRIX.md`](docs/CODE_AND_FEATURE_MATRIX.md) if functions or symbols change.
3. Log the change in [`docs/CHANGELOG.md`](docs/CHANGELOG.md) with date, affected files, and rationale.
4. Synchronize modifications between `geoforge-main/docs/` and root `docs/`.

---

## 11. Mandatory Agent Behavior Checklist

When responding to user coding prompts, every AI Agent MUST adhere to these 8 rules:

- [ ] **1. Read Before Editing:** Inspect relevant documentation in `docs/` before altering code.
- [ ] **2. Inspect Live Implementation:** Inspect the real file content and line numbers before proposing edits.
- [ ] **3. Never Assume Features Exist:** Check code truth; do not assume planned features are implemented.
- [ ] **4. Avoid Unnecessary Rewrites:** Make the minimal coherent change needed to accomplish the task.
- [ ] **5. Preserve Working Functionality:** Protect existing API routes, concurrency limits, and 3D rendering pipelines.
- [ ] **6. Explain Important Changes:** Clearly articulate what was modified, why, and which files were touched.
- [ ] **7. Run Relevant Tests:** Verify static types (`npm run lint`) and syntax (`py_compile`) where feasible.
- [ ] **8. Update Documentation:** Keep `docs/` in sync with the codebase at all times.
