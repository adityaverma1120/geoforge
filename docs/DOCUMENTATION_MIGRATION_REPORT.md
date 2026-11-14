# GeoForge — Documentation Audit & Consolidation Report

> **Document:** `docs/DOCUMENTATION_MIGRATION_REPORT.md`  
> **Status:** Review Draft (Awaiting User Approval Before Applying Modifications)  
> **Evaluation Date:** November 2026  
> **Scope:** Full comparison of `doc old/` (Original Documentation Pack) against `docs/` (New Master Documentation Pack), verified against the live source code in `backend/`, `frontend/`, `src/`, and root utilities.

---

## Executive Summary

A comprehensive documentation audit and source-code verification was conducted across all files in `doc old/` and `docs/`. 

The new documentation pack in `docs/` establishes a cleaner, modular, topic-based structure (`PRD.md`, `ARCHITECTURE.md`, `COLMAP.md`, etc.). However, **significant high-value technical details, concrete mathematical parameters, algorithmic contrasts, code-level entry point mappings, and realistic test matrices from `doc old/` were omitted or diluted into generic/provisional placeholders** in `docs/`.

Furthermore, several documents in `docs/` contain minor discrepancies or hardcoded legacy developer paths (`C:\Users\Aditya verma\Desktop\Drone3DProject\...`) that conflict with the portable codebase.

This report provides the complete comparative audit, catalogs all missing technical knowledge, verifies each discrepancy against the live source code, and issues formal per-document migration recommendations (**MERGE**, **ALREADY COVERED**, **UPDATE**, **HISTORICAL**, or **DISCARD**).

---

## A. Documentation Comparison (Old vs. New Pack)

The project structure contains:
- **`doc old/`**: 26 files (numerical sequence `00_PROJECT_OVERVIEW.md` through `24_API_AND_FEATURE_MATRIX.md` plus the deep `GEOFORGE_MASTER_CONTEXT.md`).
- **`docs/`**: 29 files (topic-based naming `API.md`, `ARCHITECTURE.md`, `COLMAP.md`, etc.) plus root `README.md` and `AGENTS.md` (totaling 31 files).

| Old Document (`doc old/`) | New Document (`docs/`) | Topic / Subject | Coverage Status | Key Differences & Gaps |
|---|---|---|---|---|
| `00_PROJECT_OVERVIEW.md` | `PROJECT_OVERVIEW.md` | Problem, solution, high-level workflow, outputs | Partial | Old doc explicitly names intermediate artifacts (`fused.ply`, `poisson_mesh.ply`, `model.ply`). New doc is higher level. |
| `01_PRD.md` | `PRD.md` | Product Requirements Document | Partial | Old doc contains a rigorous 15-item functional requirements table (FR-001 to FR-015) and 8 NFRs with exact thresholds. New doc uses generic requirements (FR-01 to FR-09) and omits parameter tables. |
| `02_FEATURES_AND_STATUS.md` | `FEATURE_STATUS.md` | Feature implementation status | Partial | Old doc cites exact source files (`backend/main.py`, `convert_to_glb.py`, `ThreeDViewer.tsx`). New doc states "Previously identified - Inspect package.json". |
| `03_ARCHITECTURE.md` | `ARCHITECTURE.md` | System architecture & data flow | Divergent / Partial | Old doc has a Mermaid pipeline flowchart and describes the real directory topology (`backend/temp/<job_id>`). New doc recommends a fictional `data/jobs/<job_id>` structure. |
| `04_CODEBASE_MAP.md` | *(None)* | Repository layout & script distinction | **Missing** | New doc pack has no codebase file map. Crucially, old doc explains that root `src/` scripts are legacy/manual and distinct from active `backend/` modules. |
| `05_TECH_STACK.md` | `TECH_STACK.md` & `SOFTWARE_INVENTORY.md` | Languages, libraries, frameworks | Partial | Old doc lists exact npm package versions (`React ^19.0.1`, `Three.js ^0.185.1`, `Tailwind ^4.1.14`) and notes unused dependencies (`@google/genai`, `express`). New doc omits exact frontend versions. |
| `06_END_TO_END_WORKFLOW.md` | `RECONSTRUCTION_PIPELINE.md` | 9-step backend execution sequence | Partial | Old doc lists exact function calls (`extract_frames(target_fps=2.0)`, `filter_sharp_frames(threshold=100.0)`, `remove_redundant_frames(difference_threshold=5.0)`). New doc is more conceptual. |
| `07_FRAME_PREPROCESSING.md` | `RECONSTRUCTION_PIPELINE.md` | Extraction, sharpness, redundancy algorithms | Partial | Old doc details the exact algorithms and highlights the parameter contrast between `src/` (Laplacian 300, matchTemplate 0.98) and `backend/` (Laplacian 100 with adaptive floor, absdiff 5.0 with 50% floor). New doc omits this. |
| `08_RECONSTRUCTION_AND_COLMAP.md`| `COLMAP.md` | COLMAP parameters & execution | Partial | Old doc details vocabulary tree discovery paths, single-model enforcement, and binary model selection (`find_best_model`). New doc is a general usage guide. |
| `09_POINTCLOUD_MESH_TEXTURE_GLB.md`| `OPEN3D.md` & `MESH_AND_GLB.md` | Outlier cleaning, Poisson trimming, GLB export | Partial | Old doc explains Trimesh scene concatenation, Pillow PBR material binding, and Poisson density trimming. New docs describe them as generic possibilities. |
| `10_API_CONTRACT.md` | `API.md` | REST API routes and payloads | Partial | Old doc documents frontend helpers (`getModelGlbUrl`) and URL normalization. New doc labels all routes "provisional" despite code being fixed and working. |
| `11_FRONTEND_UI.md` | `FRONTEND.md` & `UI_UX_DESIGN.md` | UI pages, states, viewer, package scripts | Partial | Old doc lists npm scripts and warns that `npm run clean` uses Unix `rm -rf` (failing on Windows). New docs omit this operational warning. |
| `12_BACKEND_JOB_LIFECYCLE.md` | `JOB_MANAGEMENT.md` & `BACKEND.md` | Job transitions, memory store, result schema | Partial | Old doc lists every field returned in `job.result` (registration ratio, point counts, mesh faces, sizes). New doc focuses primarily on future database planning. |
| `13_SETUP_AND_RUN.md` | `SETUP.md` | Local development startup guide | Divergent | Old doc provides a working provisional `pip install` command. New doc uses hardcoded developer paths (`C:\Users\Aditya verma\...`). |
| `14_CONFIGURATION.md` | `CONFIGURATION.md` | Environment variables & pipeline constants | Covered | Both document environment variables and pipeline constants; old doc is slightly more concise. |
| `15_TESTING_ACCEPTANCE.md` | `TESTING.md` | QA strategy & acceptance test matrix | Partial | Old doc features a 10-row scenario-versus-expected outcome matrix. New doc contains general testing principles. |
| `16_ERRORS_TROUBLESHOOTING.md` | `TROUBLESHOOTING.md` | Failure causes & recovery steps | Covered | New doc expands upon old doc with practical tips (e.g. `python -m uvicorn`, ground-plane dominance). |
| `17_SECURITY_PRIVACY_PERFORMANCE.md`| `SECURITY.md` & `SECURITY_AND_ACCURACY_NOTES.md` | Upload limits, CORS, privacy, compute | Covered | New docs cover security, privacy, and performance thoroughly. |
| `18_DEPLOYMENT.md` | `DEPLOYMENT.md` | Reverse proxy, timeouts, compute | Covered | New doc expands deployment architecture across local, cloud, and Linux portability. |
| `19_ROADMAP.md` | `ROADMAP.md` | Phased development milestones | Covered | Old doc uses P0-P3; new doc uses Phase 0-5. Both align on priorities. |
| `20_GLOSSARY.md` | `GLOSSARY.md` | Terminology definitions | Partial | Old doc defines `AGL` (Above Ground Level) used in drone UI tips; new doc omits it. |
| `21_CHANGELOG.md` | `CHANGELOG.md` | Modification history | Partial | Old doc contains actual audit changelogs (2026-11-06 and 2026-11-11). New doc is a blank template. |
| `22_DOCUMENTATION_STATUS.md` | `FEATURE_STATUS.md` | Audit boundaries & established facts | Partial | Old doc contains concrete audit boundary facts. |
| `23_DEVELOPMENT_WORKFLOW.md` | *(None)* | Developer branch rules & PR checklist | **Missing** | New doc pack lacks a developer workflow and pull-request checklist. |
| `24_API_AND_FEATURE_MATRIX.md` | *(None)* | Code symbols & verification mapping | **Missing** | New doc pack has no index mapping functions (`main.py: home()`, `reconstruction.py: run_reconstruction`) to verification actions. |
| `GEOFORGE_MASTER_CONTEXT.md` (40 KB)| `GEOFORGE_MASTER_CONTEXT.md` (4 KB)| Master project context & knowledge base | **Divergent** | Old doc is a comprehensive 20-section master reference with mathematical, algorithmic, and parameter depth. New doc in `docs/` is only an 84-line summary. |

---

## B. Missing Information in New Documentation Pack

The following vital technical information present in `doc old/` is **absent** from `docs/`:

1. **Active Pipeline vs. Standalone Scripts Distinction (`04_CODEBASE_MAP.md`, `07_FRAME_PREPROCESSING.md`):**
   - In `backend/frame_filtering.py`, the Laplacian threshold is `100.0` with an adaptive safety floor (lowers if $>40\%$ rejected) and brightness bounds ($[30, 240]$).
   - In `backend/redundancy_filter.py`, the metric is `cv2.absdiff` with threshold `5.0` and a 50% safety floor.
   - Conversely, root `src/detect_blur.py` uses fixed threshold `300`, and `src/remove_redundant.py` uses `cv2.matchTemplate` normalized correlation threshold `0.98`.
   - *Impact:* Without this, developers confuse the standalone exploration scripts with the actual FastAPI pipeline.
2. **Detailed Functional Requirements & NFR Matrix (`01_PRD.md`):**
   - The detailed requirement IDs (`FR-001` through `FR-015`) and Non-Functional Requirements (`NFR-001` through `NFR-008`) with exact acceptance gates are missing from `docs/PRD.md`.
3. **Exact Code Symbol Verification Matrix (`24_API_AND_FEATURE_MATRIX.md`):**
   - The direct mapping between user-facing actions, backend entry point symbols (`upload_video()`, `get_status()`, `convert_to_glb()`), and test commands is completely missing in `docs/`.
4. **Developer Pull-Request & Verification Checklist (`23_DEVELOPMENT_WORKFLOW.md`):**
   - The 11-step coding protocol and PR acceptance checklist are omitted from `docs/`.
5. **Exact Frontend Dependency Versions & Unused Package Notes (`05_TECH_STACK.md`):**
   - Missing explicit versions from `package.json` (`three ^0.185.1`, `react ^19.0.1`, `vite ^6.2.3`, `typescript ~5.8.2`, `tailwindcss ^4.1.14`) and the observation that `@google/genai` and `express` are installed but unused in the core pipeline.
6. **Windows Clean Script Failure Warning (`11_FRONTEND_UI.md`):**
   - `frontend/package.json` defines `"clean": "rm -rf dist server.js"`, which throws a syntax error in Windows PowerShell / cmd.
7. **Complete Return Schema for `job.result` (`12_BACKEND_JOB_LIFECYCLE.md`):**
   - Missing the complete dictionary structure returned by `reconstruction.py` and served by `/status/{job_id}` (including `registration_ratio`, `dense_cloud_points`, `cleaned_cloud_points`, `outliers_removed`, `mesh_vertices`, `mesh_faces`, `quality_warnings`).
8. **Provisional Backend Installation Command (`13_SETUP_AND_RUN.md`):**
   - Missing the one-line pip install command:
     ```powershell
     python -m pip install fastapi uvicorn python-multipart opencv-python numpy open3d trimesh pillow
     ```
9. **Acceptance Test Scenario Matrix (`15_TESTING_ACCEPTANCE.md`):**
   - Missing the 10-case tabular test matrix mapping edge-case scenarios (unsupported extension, blurry frames, missing COLMAP, malformed GLB, server restart) to expected outcomes.
10. **Historical Documentation Changelog Records (`21_CHANGELOG.md`):**
    - The actual dated changelog entries from 2026-11-06 and 2026-11-11 were replaced with a blank template in `docs/CHANGELOG.md`.

---

## C. Technical Discrepancies in New Documentation

The following details in `docs/` conflict with the actual codebase:

1. **Workspace Directory Structure Conflict (`docs/ARCHITECTURE.md` Section 4):**
   - `docs/ARCHITECTURE.md` claims jobs are structured under `data/jobs/<job_id>/input/...`.
   - **Source Code Reality:** `backend/main.py` lines 110–113 explicitly define:
     ```python
     UPLOAD_DIR = BASE_DIR / "uploads"
     TEMP_DIR   = BASE_DIR / "temp"
     OUTPUT_DIR = BASE_DIR / "output"
     ```
     Videos are saved to `uploads/{job_id}_{filename}`, and workspaces are created in `temp/{job_id}/` (containing `frames/`, `selected_frames/`, `final_frames/`, `colmap/`).
2. **Hardcoded Machine Paths (`docs/README.md`, `docs/SETUP.md`):**
   - Both documents instruct developers to run:
     `cd "C:\Users\Aditya verma\Desktop\Drone3DProject\backend"`
     `cd "C:\Users\Aditya verma\Desktop\Drone3DProject\frontend"`
   - **Source Code Reality:** The repository path is portable. Scripts must use relative paths or workspace-relative directories.
3. **Provisional vs. Established API Status (`docs/API.md`):**
   - `docs/API.md` labels every endpoint as "provisional based on prior notes" and asks to verify whether `/upload` supports multipart, whether `/model` streams a file, or whether HEAD is supported.
   - **Source Code Reality:** The backend implementation is fully established in `backend/main.py`. Endpoints `/`, `/health`, `/upload`, `/status/{job_id}`, `/model/{job_id}`, and `HEAD /model/{job_id}` are implemented, concrete, and tested.
4. **`GEOFORGE_MASTER_CONTEXT.md` Truncation (`docs/GEOFORGE_MASTER_CONTEXT.md`):**
   - `docs/GEOFORGE_MASTER_CONTEXT.md` was truncated to 84 lines of high-level bullet points, losing the deep mathematical, algorithmic, and parameter specifications established in the master audit.
5. **Codebase-Level Discrepancies (Documented vs. Implemented):**
   - *Extension mismatch:* Backend `main.py:382` accepts `{".mp4", ".mov", ".avi", ".mkv"}`, but frontend `UploadPage.tsx:22` rejects `.mkv`.
   - *Aspirational UI badges:* Frontend `CompletePage.tsx:78-100` displays "Dense Point Cloud (LAS) - READY", "Orthomosaic Map (GeoTIFF) - READY", and "3D Surface Mesh (OBJ/MTL) - READY", none of which are produced by the backend.
   - *Simulated stage progress:* Frontend `ProcessingPage.tsx` shows 10 granular stages, but `App.tsx` simulates this on a client timer because the backend `/status/{job_id}` only returns coarse states (`queued`, `processing`, `complete`, `failed`).

---

## D. Source-Code Verification Evidence

The table below provides direct file and line references from the live repository supporting each correction:

| Component | Source File & Lines | Verifiable Evidence |
|---|---|---|
| **Upload Limits & Formats** | `backend/main.py:77, 382-393` | `MAX_UPLOAD_BYTES = 4 * 1024 * 1024 * 1024` (4 GiB). Formats allowed: `.mp4`, `.mov`, `.avi`, `.mkv`. |
| **Workspace Paths** | `backend/main.py:110-117, 399-403` | `BASE_DIR = Path(__file__).resolve().parent`, `UPLOAD_DIR`, `TEMP_DIR`, `OUTPUT_DIR`. Per-job workspace: `TEMP_DIR / job_id`. |
| **Worker Concurrency** | `backend/main.py:86-89, 443-457` | `MAX_CONCURRENT_RECONSTRUCTIONS = 2`. ThreadPoolExecutor max workers 2. Rejects with HTTP 503 if $\ge 2$ active jobs. |
| **Job Retention** | `backend/main.py:83, 146-164` | `JOB_RETENTION_SECONDS = 7 * 24 * 60 * 60` (7 days). Managed by asyncio background task `_cleanup_job_files`. |
| **Frame Extraction** | `backend/frame_processing.py:16, 27, 72` | `DEFAULT_TARGET_FPS = 2.0`. Frame interval calculated as `max(1, int(round(fps / target_fps)))`. |
| **Blur Filtering** | `backend/frame_filtering.py:19, 25, 29, 50` | Laplacian variance `.var()`. `DEFAULT_SHARPNESS_THRESHOLD = 100.0`, `MAX_BLUR_REJECTION_RATIO = 0.40`, `ABSOLUTE_MIN_SHARPNESS = 20.0`. |
| **Redundancy Filter** | `backend/redundancy_filter.py:21, 26, 39` | `cv2.absdiff(gray1, gray2).mean()`. `DEFAULT_DIFFERENCE_THRESHOLD = 5.0`, `MAX_REMOVAL_RATIO = 0.50` (safety floor). |
| **Minimum Frame Floor** | `backend/main.py:80, 237-242` | `MIN_FRAMES_FOR_RECONSTRUCTION = 20`. Raises RuntimeError if fewer frames survive. |
| **COLMAP Invocation** | `backend/reconstruction.py:17, 149-195` | `COLMAP = os.environ.get("COLMAP_EXE", r"C:\bin\colmap.exe")`. Direct `subprocess.Popen(shell=False)` with list args. |
| **Camera Model & SIFT** | `backend/reconstruction.py:31, 37, 894, 898` | Camera model `OPENCV` (8-parameter). `MAX_NUM_FEATURES = 16384`. Affine shape and domain pooling enabled. |
| **SfM Single Model** | `backend/reconstruction.py:51, 1028` | `--Mapper.multiple_models 0` forces single unified model component. |
| **Sparse Quality Gate** | `backend/reconstruction.py:56, 1096-1107` | `MIN_REGISTRATION_RATIO = 0.30`. Unpacks `images.bin` and `points3D.bin`; throws RuntimeError if $< 30\%$. |
| **PatchMatch & Fusion** | `backend/reconstruction.py:62, 66, 71, 74` | PatchMatch `max_image_size = 2400`, `num_iterations = 7`. Stereo fusion `min_num_pixels = 3`, `max_reproj_error = 2.0`. |
| **Open3D Outlier Clean**| `backend/reconstruction.py:89-91, 582` | `pcd.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)` $\to$ `fused_cleaned.ply`. |
| **Poisson Trimming** | `backend/reconstruction.py:79, 85, 653, 669` | `depth = 11`. Density trimming trims bottom 7.0% (`POISSON_TRIM = 7.0`) to prevent boundary bloating. |
| **Mesh Texturing & GLB** | `backend/convert_to_glb.py:79, 151, 185` | Trimesh loads PLY, Pillow loads texture, binds PBR material with UVs, exports GLB. |
| **Frontend Viewer** | `frontend/src/components/ThreeDViewer.tsx:721` | GLTFLoader loads `modelUrl || '/video_model.glb'`. Custom orbit/pan/zoom, dark grid helper, WebGL cleanup. |
| **Frontend Poller** | `frontend/src/App.tsx:280, 371-381` | Exponential backoff `[3000, 5000, 10000, 20000, 30000]`. Client increments `currentStageIndex` up to stage 8. |
| **Frontend MKV Block** | `frontend/src/pages/UploadPage.tsx:22` | `const allowedExtensions = ['mp4', 'mov', 'avi'];` blocks `.mkv`. |
| **Mock UI Badges** | `frontend/src/pages/CompletePage.tsx:78-100` | Hardcoded badges claiming LAS, GeoTIFF, and OBJ outputs are "READY". |

---

## E. Migration Recommendations (File-by-File Actions)

Every document in `doc old/` has been assigned one of five definitive actions:

| Document in `doc old/` | Recommended Action | Target Destination in `docs/` | Action Summary & Justification |
|---|---|---|---|
| `00_PROJECT_OVERVIEW.md` | **MERGE** | `docs/PROJECT_OVERVIEW.md` | Merge the exact deliverable file artifact names (`fused.ply`, `poisson_mesh.ply`, `model.glb`) into the overview. |
| `01_PRD.md` | **MERGE** | `docs/PRD.md` | Merge the complete 15-item functional requirements table (FR-001 to FR-015) and NFR table with exact thresholds. |
| `02_FEATURES_AND_STATUS.md` | **MERGE** | `docs/FEATURE_STATUS.md` | Update feature register with the verified source file citations. |
| `03_ARCHITECTURE.md` | **MERGE** | `docs/ARCHITECTURE.md` | Add the Mermaid pipeline flowchart and replace the fictional `data/jobs` path with the verified `backend/temp` structure. |
| `04_CODEBASE_MAP.md` | **MERGE** | `docs/ARCHITECTURE.md` (or new `docs/CODEBASE_MAP.md`) | Reintroduce the visual codebase tree and the vital distinction between root `src/` and active `backend/` scripts. |
| `05_TECH_STACK.md` | **MERGE** | `docs/TECH_STACK.md` | Add exact package version numbers from `package.json` and note unused packages (`@google/genai`, `express`). |
| `06_END_TO_END_WORKFLOW.md` | **MERGE** | `docs/RECONSTRUCTION_PIPELINE.md` | Integrate the exact function signatures and call sequence into the pipeline document. |
| `07_FRAME_PREPROCESSING.md` | **MERGE** | `docs/RECONSTRUCTION_PIPELINE.md` | Add detailed blur/exposure/redundancy mathematical logic and the contrast with legacy `src/` scripts. |
| `08_RECONSTRUCTION_AND_COLMAP.md`| **MERGE** | `docs/COLMAP.md` | Add vocabulary tree candidate paths, single-model enforcement flag, and binary model selection logic. |
| `09_POINTCLOUD_MESH_TEXTURE_GLB.md`| **MERGE** | `docs/OPEN3D.md` & `docs/MESH_AND_GLB.md` | Add Open3D outlier parameters, Poisson density trim logic, and Trimesh/Pillow PBR material conversion details. |
| `10_API_CONTRACT.md` | **UPDATE** | `docs/API.md` | Upgrade `docs/API.md` from provisional to established, add frontend helper documentation (`getModelGlbUrl`), and specify exact schemas. |
| `11_FRONTEND_UI.md` | **MERGE** | `docs/FRONTEND.md` | Add the frontend npm script inventory and the operational warning regarding Windows compatibility with `npm run clean`. |
| `12_BACKEND_JOB_LIFECYCLE.md` | **MERGE** | `docs/JOB_MANAGEMENT.md` & `docs/BACKEND.md` | Document the complete dictionary structure of `job.result` as returned by the pipeline. |
| `13_SETUP_AND_RUN.md` | **UPDATE** | `docs/SETUP.md` | Replace hardcoded developer machine paths with portable commands and provide the one-line pip install command. |
| `14_CONFIGURATION.md` | **ALREADY COVERED** | `docs/CONFIGURATION.md` | Contents are already represented in `docs/CONFIGURATION.md`. |
| `15_TESTING_ACCEPTANCE.md` | **MERGE** | `docs/TESTING.md` | Merge the 10-case scenario-versus-expected outcome acceptance test matrix. |
| `16_ERRORS_TROUBLESHOOTING.md` | **ALREADY COVERED** | `docs/TROUBLESHOOTING.md` | Fully covered and expanded in `docs/TROUBLESHOOTING.md`. |
| `17_SECURITY_PRIVACY_PERFORMANCE.md`| **ALREADY COVERED** | `docs/SECURITY.md` | Fully covered in `docs/SECURITY.md` and `docs/SECURITY_AND_ACCURACY_NOTES.md`. |
| `18_DEPLOYMENT.md` | **ALREADY COVERED** | `docs/DEPLOYMENT.md` | Fully covered and expanded in `docs/DEPLOYMENT.md`. |
| `19_ROADMAP.md` | **ALREADY COVERED** | `docs/ROADMAP.md` | Fully covered and structured in `docs/ROADMAP.md`. |
| `20_GLOSSARY.md` | **MERGE** | `docs/GLOSSARY.md` | Add definition for `AGL` (Above Ground Level). |
| `21_CHANGELOG.md` | **MERGE** | `docs/CHANGELOG.md` | Merge dated changelog entries from 2026-11-06 and 2026-11-11 into `docs/CHANGELOG.md`. |
| `22_DOCUMENTATION_STATUS.md` | **HISTORICAL** | *(Retain in `doc old/`)* | Preserve as the baseline audit record of the original archive inspection. |
| `23_DEVELOPMENT_WORKFLOW.md` | **MERGE** | New `docs/DEVELOPMENT_WORKFLOW.md` | Add the 11-step coding protocol and PR acceptance checklist to `docs/`. |
| `24_API_AND_FEATURE_MATRIX.md` | **MERGE** | New `docs/CODE_AND_FEATURE_MATRIX.md` | Add the surface-to-source symbol verification matrix mapping functions to verification commands. |
| `GEOFORGE_MASTER_CONTEXT.md` (40 KB)| **UPDATE** | `docs/GEOFORGE_MASTER_CONTEXT.md` | Overwrite the brief 84-line stub in `docs/` with the comprehensive 20-section master knowledge base. |

---

## F. Proposed Consolidation Plan (For User Review)

Once approved, consolidation will proceed in three structured steps:

1. **Step 1 (Master Context & Core Specifications):**
   - Update `docs/GEOFORGE_MASTER_CONTEXT.md` with the full 20-section master knowledge base.
   - Update `docs/PRD.md` with the full FR and NFR tables from `doc old/01_PRD.md`.
   - Update `docs/ARCHITECTURE.md` with the Mermaid flowchart, codebase layout, and correct `backend/temp` workspace paths.
2. **Step 2 (Technical Deep Dives & API):**
   - Update `docs/RECONSTRUCTION_PIPELINE.md`, `docs/COLMAP.md`, `docs/OPEN3D.md`, and `docs/MESH_AND_GLB.md` with exact algorithms, flags, and parameter floors.
   - Update `docs/API.md`, `docs/JOB_MANAGEMENT.md`, and `docs/FRONTEND.md` with verified schemas and client helpers.
   - Update `docs/SETUP.md` and `README.md` to remove hardcoded user paths and add the provisional pip install command.
3. **Step 3 (QA, Workflow & Indices):**
   - Update `docs/TESTING.md` with the 10-scenario acceptance matrix.
   - Add `docs/DEVELOPMENT_WORKFLOW.md` and `docs/CODE_AND_FEATURE_MATRIX.md`.
   - Update `docs/MASTER_DOCUMENTATION_INDEX.md` and `docs/CHANGELOG.md` to index all consolidated documents.
   - Preserve `doc old/` completely untouched as the historical archive.

---

*Report prepared and submitted for user review in accordance with Phase 5 instructions. No source code or existing documentation has been altered.*

