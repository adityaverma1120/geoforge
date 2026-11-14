# Documentation Changelog — GeoForge

> **Document:** `docs/CHANGELOG.md`  
> **Status:** Canonical Project & Documentation Changelog  
> **Target Version:** GeoForge v1.0.0 (SIH 2026 / NTRO Edition)

---

## 2026-11-14 — Phase 8: Cloud Deployment Planning & Internet Accessibility
- **Added/Changed:**
  - **Cloud Readiness Audit:** Conducted exhaustive audit distinguishing Phase 7 local verified code truth from cloud deployment blockers (Windows pathing, local disk volatility, and CUDA hardware dependency).
  - **Compute Feasibility Analysis:** Confirmed COLMAP PatchMatch dense MVS strictly requires an NVIDIA CUDA GPU; established unit economics showing on-demand GPU execution costs ~$0.043 per reconstruction vs. $380/mo for 24/7 idle GPUs.
  - **Authored 6 Comprehensive Phase 8 Documents:**
    - [`docs/PHASE_8_DEPLOYMENT_STRATEGY.md`](PHASE_8_DEPLOYMENT_STRATEGY.md) (Master architectural strategy & non-commercial discipline).
    - [`docs/CLOUD_ARCHITECTURE.md`](CLOUD_ARCHITECTURE.md) (Decoupled system topology, sequence flows, and component contracts).
    - [`docs/DEPLOYMENT_PROVIDER_COMPARISON.md`](DEPLOYMENT_PROVIDER_COMPARISON.md) (Benchmarking 14 cloud services across 5 operational tiers).
    - [`docs/CLOUD_COST_ESTIMATES.md`](CLOUD_COST_ESTIMATES.md) (Unit economics, 3 usage scenarios, USD/INR models, and hard spending limits).
    - [`docs/DEPLOYMENT_IMPLEMENTATION_ROADMAP.md`](DEPLOYMENT_IMPLEMENTATION_ROADMAP.md) (Staged 9-step execution plan with acceptance criteria and rollbacks).
    - [`docs/PRODUCTION_ENVIRONMENT_CONFIGURATION.md`](PRODUCTION_ENVIRONMENT_CONFIGURATION.md) (Production `.env` contracts, multi-stage Dockerfiles, and reverse proxy configs).
  - **Immutability Guarantee:** Preserved 100% source code immutability during this planning-only phase; zero cloud resources provisioned.

---

## 2026-11-14 — Phase 7: Final End-to-End Acceptance Testing & Certification
- **Added/Changed:**
  - **End-to-End Production Verification:** Executed exhaustive 5-stage acceptance testing suite on live single-port runtime (`http://127.0.0.1:8000`).
  - **New Video Reconstruction:** Successfully processed raw drone orbit video (`sample_drone_orbit.mp4`, 38.87 MB) under new job UUID `00b99ffd-4c6d-45bc-9ae2-13017d411ff3`.
  - **Pipeline Metrics Achieved:** 30/30 frames registered (100.0%), 4,446 sparse points, 148,144 dense points, 108,108 vertices, 214,354 faces, producing verified 4,303,020-byte (4.10 MB) binary GLB (`model.glb`). Total execution: 265.65 seconds (~4.4 minutes).
  - **Viewer, Download & Persistence Audits:** Verified Three.js streaming (`/model/{id}`), attachment download (`/download/{id}`), SQLite job history listing (`/jobs`, 12 records total), and 100% state restoration across cold server daemon restarts.
  - **Immutability Guarantee:** Maintained 100% source code immutability across `backend/` and `frontend/src/` during testing.
  - **Authored:** [`docs/PHASE_7_FINAL_ACCEPTANCE_REPORT.md`](PHASE_7_FINAL_ACCEPTANCE_REPORT.md) certifying GeoForge v1.0.0 as **READY FOR EVALUATION**.

---

## 2026-11-14 — Phase 7: Final Integration, Structural Repair & Production Consolidation
- **Added/Changed:**
  - **Gate 1 (Cryptographic Backup):** Executed complete transactionally consistent snapshot of all repository assets (`backup_phase7_stage0_20261112_verified/`). Backed up 1,122 files (2,128.99 MB) with 100% SHA-256 cryptographic match, atomic SQLite backups (`jobs_root.db`, `jobs_nested.db`), and verified zip archive of the nested clone (`geoforge_main_nested_snapshot.zip`, 770.27 MB).
  - **Gate 2 (Integration & Repair):**
    - Mounted `<HistoryPage />` inside `frontend/src/App.tsx` on `/history` with `handleSelectHistoryJob` and `navigate`, enabling persistent job inspection and GLB downloads from UI.
    - Eliminated duplicate `@app.get("/jobs")` endpoint in `backend/main.py` (lines 958–966).
    - Mounted compiled frontend assets on `/assets` via FastAPI `StaticFiles` and implemented `spa_fallback` routing in `backend/main.py`, enabling unified single-server operation at `http://localhost:8000`.
    - Normalized `job.id` and `job.job_id` aliasing in `backend/database.py` and `frontend/src/pages/HistoryPage.tsx`.
    - Relocated lingering `redundancy_summary.json` out of `final_frames/` into workspace root, eliminating COLMAP image parser errors.
    - Streamlined `frontend/package.json`: pruned 5 phantom unused dependencies (`@google/genai`, `express`, `@types/express`, `dotenv`, `tsx`), strictly preserved `esbuild`, and modernized `clean` script to standard Node.js `fs.rmSync`.
    - Created turnkey `start_geoforge.bat` launcher for Windows (automated venv activation, dependency checks, frontend compilation, and browser launching).
  - **Gate 3 (Asset Migration):** Migrated all 6 unique video uploads (118.03 MB) and all 4 unique workspaces (444 files, 642.42 MB) into the authoritative root repository with 100% SHA-256 integrity verification. Updated database paths to decouple all 11 records from the nested clone. Zero deletions performed during migration.
  - **Gate 4 (Consolidation & Cleanup):** Permanently deleted redundant nested repository directory `geoforge-main/geoforge-main/` (12,119 files, 1,217.63 MB reclaimed) and obsolete Python 3.15 venv (`.venv_py315/`). Removed `frontend/bun.lock` and relocated legacy exploration scripts into `src/`. Reclaimed 1,217.95 MB of disk space.
  - **Gate 5 (Documentation & Sign-off):** Updated `README.md`, `docs/SETUP.md`, `docs/DEPLOYMENT.md`, `docs/FEATURE_STATUS.md`, and authored comprehensive `docs/PHASE_7_INTEGRATION_REPORT.md`.
- **Reason:** Complete Phase 7 Integration, Structural Repair, and Production Preparation, delivering a unified, production-ready, and verifiable single-pass photogrammetric system.
- **Constraints Maintained:** 100% data preservation guarantee fulfilled. Zero working reconstruction logic altered. Verified end-to-end functionality via physical test execution.

---

## 2026-11-11 — Phase 3: Backend Implementation, Hardening & Persistence
- **Added/Changed:**
  - Implemented persistent SQLite job storage in `backend/database.py` (`jobs.db`) with automatic schema migration, indexes, and full lifecycle tracking across backend restarts.
  - Added `backend/database.py:recover_interrupted_jobs()` called at FastAPI startup to automatically flag interrupted or crashed jobs as failed with clean diagnostic explanations.
  - Implemented deep readiness probe `GET /ready` verifying Python dependencies, COLMAP 3.9.1 CUDA executable, FFmpeg executable, storage write permissions, SQLite database connectivity, and worker capacity.
  - Enhanced liveness probe `GET /health` with system diagnostics (`colmap`, `ffmpeg`, `storage`, `concurrency`).
  - Hardened `POST /upload`: added 0-byte upload rejection (HTTP 400), pre-ingestion OpenCV decodability and visual frame validation (`cv2.VideoCapture`), streaming chunked upload, and response payload with `download_url`.
  - Added dedicated attachment download endpoint `GET /download/{job_id}` serving GLB models with `Content-Disposition: attachment; filename="geoforge_....glb"`.
  - Added job cancellation endpoint `POST /jobs/{job_id}/cancel`.
  - Enforced strict concurrency limit `MAX_CONCURRENT_RECONSTRUCTIONS = 1` tuned for Dell G15 hardware (16 GB RAM + RTX 3050 6 GB VRAM).
  - Implemented safe GLB path resolution `_resolve_glb()` with strict RFC 4122 v4 UUID validation and directory traversal prevention.
  - Created and executed comprehensive 17-point backend unit & integration test suite (`backend/test_backend_api.py`), passing all 17 checks with exit code 0.
  - Executed full 12-stage end-to-end photogrammetry pipeline test (`backend/test_full_workflow.py`), generating verified 40,909-vertex, 81,075-face, 1.55 MB binary GLB.
  - Synchronized backend files (`main.py`, `database.py`, `test_backend_api.py`) between `geoforge-main/backend/` and `backend/`.
  - Updated canonical documentation: `docs/API.md`, `docs/BACKEND.md`, `docs/JOB_MANAGEMENT.md`, `docs/CONFIGURATION.md`, `docs/SECURITY.md`, `docs/TESTING.md`, `docs/CODE_AND_FEATURE_MATRIX.md`.
- **Reason:** Complete Phase 3 Backend Implementation and Repair, transforming the GeoForge backend into a robust, persistent, and verifiable photogrammetric service.

---

## 2026-11-11 — Phase 7: Final Quality Audit & Documentation Closeout
- **Added/Changed:**
  - Authored [`docs/DOCUMENTATION_FINAL_AUDIT.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/DOCUMENTATION_FINAL_AUDIT.md) — complete authoritative 360-degree audit report across all 35 active master documents in `docs/`, 2 root documents (`README.md`, `AGENTS.md`), and 26 historical documents in `doc old/`.
  - Conducted automated link verification across all Markdown files; verified **0 broken links**.
  - Enhanced [`docs/PHOTOGRAMMETRY_FUNDAMENTALS.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/PHOTOGRAMMETRY_FUNDAMENTALS.md) with complete mathematical foundations: pinhole camera projection, OPENCV 8-parameter distortion equations, epipolar geometry, baseline-to-depth ($B/D$) ratios, Ground Sample Distance (GSD) resolution formulas, degenerate capture modes, scale ambiguity, and a field quality checklist for drone pilots.
  - Enhanced [`docs/DECISIONS.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/DECISIONS.md) with 8 formalized Architecture Decision Records (ADRs) and comprehensive resolution of all previously open technical questions.
  - Updated [`docs/MASTER_DOCUMENTATION_INDEX.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/MASTER_DOCUMENTATION_INDEX.md) to catalog all 35 active master documents.
  - Synchronized documentation packs between `geoforge-main/docs/` and workspace root `docs/`.
- **Reason:** Complete final documentation quality audit and verification, achieving Tier-1 production-ready status for Smart India Hackathon 2026 (SIH26158 / NTRO).
- **Constraints Maintained:** `doc old/` left 100% intact. Zero application source code modified.

---

## 2026-11-11 — Phase 6: Root Documentation & AI Agent Instructions
- **Added/Changed:**
  - Overhauled root [`README.md`](file:///c:/Users/adity/Downloads/geoforge-main/README.md) into a comprehensive project showcase covering 18 required sections: identity, SIH problem statement, objectives, 8-stage pipeline overview, multi-tier Mermaid architecture diagram, code-verified technology stack, verified features table with source citations, UI screenshots/mockups, installation/startup guides, environment variables, output storage layout, known limitations, master documentation guide, roadmap, and contribution rules.
  - Rewrote root [`AGENTS.md`](file:///c:/Users/adity/Downloads/geoforge-main/AGENTS.md) establishing an authoritative operating protocol for autonomous AI coding agents: source-of-truth hierarchy, active vs. legacy directory boundaries, task-to-documentation lookup table, Python/TypeScript coding conventions, dependency management rules, testing protocols, security/air-gap defense standards, and an 8-rule mandatory behavior checklist.
  - Synchronized root files between `geoforge-main/` and workspace root.
- **Reason:** Fulfill Phase 6 requirements, providing clear developer onboarding and safe agent operating protocols.
- **Constraints Maintained:** `doc old/` left 100% intact. Zero application source code modified.

---

## 2026-11-11 — Phase 5: Engineering Operations Documentation
- **Added/Changed:**
  - Upgraded [`docs/SETUP.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/SETUP.md) detailing exact supported runtimes (Python 3.12, Node 20/24, COLMAP 4.1.1 CUDA), step-by-step venv and npm installation, space-safe COLMAP CLI path guidelines, verified environment variables, dual-terminal launch commands, health verification endpoints, and 5-minute smoke test procedure.
  - Rewrote [`docs/CONFIGURATION.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/CONFIGURATION.md) documenting all verified environment variables (`COLMAP_EXE`, `ALLOWED_ORIGINS`, `VITE_API_URL`), configuration files, processing constants, directory paths, and client polling intervals, while explicitly noting unused template placeholders (`GEMINI_API_KEY`, `APP_URL`).
  - Overhauled [`docs/DEPLOYMENT.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/DEPLOYMENT.md) with complete architectural decoupling, hardware sizing (GPU VRAM $\ge 6\text{ GB}$, Host RAM $\ge 16\text{ GB}$, NVMe $\ge 30\text{ GB}$ per job), Nginx reverse proxy configurations with 4 GiB streaming limits, Cloudflare 100 MB proxy caveats, and explicit separation between verified single-node local deployment and proposed Docker/Cloud-native architectures.
  - Upgraded [`docs/SECURITY.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/SECURITY.md) providing an in-depth audit separating verified active protections (extension allowlist, UUID4 sandboxing, `uuid.UUID()` path traversal defense, header 4 GiB limit) from potential vulnerabilities (chunked streaming upload DoS, missing magic-byte check, volatile in-memory cleanup, unauthenticated endpoints).
  - Rewrote [`docs/SECURITY_AND_ACCURACY_NOTES.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/SECURITY_AND_ACCURACY_NOTES.md) contrasting visual photorealism with metric accuracy, scale ambiguity ($\lambda$), lens distortion bowl effects, arbitrary local coordinate bounds, civilian PII safeguards, and NTRO air-gapped zero-telemetry compliance.
  - Overhauled [`docs/TESTING.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/TESTING.md) detailing existing test scripts (`colmap_test.py`, `check_3d.py`, root scripts), manual testing workflows, cURL API integration tests, module-level pipeline tests, model geometric validation via Trimesh, and the complete 10-scenario failure matrix, with strict demarcation of executed vs specified tests.
  - Rewrote [`docs/TROUBLESHOOTING.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/TROUBLESHOOTING.md) with a visual diagnostic decision tree and practical step-by-step solutions for 12 real-world errors (Uvicorn PATH, Windows `npm run clean`, port conflicts, network/CORS errors, HTTP 413/503 limits, missing COLMAP, sparse gate $<30\%$ failure, CUDA OOM, Poisson RAM spikes, Three.js empty canvas, server restart).
  - Expanded [`docs/SOFTWARE_INVENTORY.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/SOFTWARE_INVENTORY.md) cataloging runtimes, Python packages, Node.js production/dev dependencies, external CLI binaries, and vocabulary tree candidate paths.
- **Reason:** Fulfill Phase 5 Engineering Operations requirements, establishing an exhaustive, code-verified operational and diagnostic manual.
- **Constraints Maintained:** `doc old/` left 100% intact. Zero application source code modified.

---

## 2026-11-11 — Phase 4: Product & UI/UX Documentation Overhaul
- **Added/Changed:**
  - Upgraded [`docs/PRD.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/PRD.md) with complete problem statement (SIH26158 / NTRO), project vision, target users, user problems, core use cases, 15 Functional Requirements (`FR-001`–`FR-015`), 8 Non-Functional Requirements (`NFR-001`–`NFR-008`), input/output specifications, system constraints, acceptance criteria, known limitations, and future possibilities.
  - Overhauled [`docs/UI_UX_DESIGN.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/UI_UX_DESIGN.md) documenting the comprehensive 8-stage user journey with detailed screen specifications (Purpose, Layout, Main Components, User Actions, Loading States, Empty States, Error States, Responsive Behavior, Accessibility Standards) based on actual React 19 source code (`LandingPage.tsx`, `HowItWorksPage.tsx`, `UploadPage.tsx`, `ProcessingPage.tsx`, `CompletePage.tsx`, `ViewerPage.tsx`, `ThreeDViewer.tsx`).
  - Restructured [`docs/FEATURE_STATUS.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/FEATURE_STATUS.md) into a strict 5-tier classification taxonomy: Currently Implemented, Partially Implemented / Discrepant, Features Requiring Technical Validation, Planned Features, and Research Ideas.
  - Rewrote [`docs/ROADMAP.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/ROADMAP.md) detailing realistic engineering priorities across 10 critical dimensions: reconstruction accuracy, processing speed, memory/GPU bounds, large video uploads, job persistence, model storage, deployment costs (with Mermaid xychart), user experience, security, and scalability.
  - Synchronized and aligned [`docs/PROJECT_OVERVIEW.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/PROJECT_OVERVIEW.md) reflecting exact code directories (`backend/uploads/` and `backend/temp/{job_id}/colmap/textured/model.glb`), exponential back-off polling (`[3000, 5000, 10000, 20000, 30000]` ms), and realistic photogrammetry boundaries.
- **Reason:** Fulfill Phase 4 Product and UI/UX documentation requirements, establishing absolute transparency between product vision and code truth.
- **Constraints Maintained:** `doc old/` left 100% intact. Zero application source code modified.

---

## 2026-11-11 — Phase 3: Technical Architecture Verification
- **Added/Changed:**
  - Performed deep source-code verification of 9 core technical documents:
    - [`docs/ARCHITECTURE.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/ARCHITECTURE.md) — Multi-tier verified call graph and workspace topology.
    - [`docs/BACKEND.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/BACKEND.md) — FastAPI routes, `ThreadPoolExecutor(max_workers=2)`, in-memory `_jobs`, and 7-day retention delay.
    - [`docs/FRONTEND.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/FRONTEND.md) — React 19 state-machine routing, XHR upload progress, exponential back-off polling, and Three.js viewer.
    - [`docs/API.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/API.md) — Upgraded to code-verified REST API contract with exact JSON schemas for all 6 endpoints.
    - [`docs/RECONSTRUCTION_PIPELINE.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/RECONSTRUCTION_PIPELINE.md) — Complete 13-stage photogrammetry pipeline breakdown across 7 required fields (Source files, Input, Output, Method, Dependencies, Limitations, Error conditions).
    - [`docs/COLMAP.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/COLMAP.md) — Verified CLI parameters (`--Mapper.multiple_models 0`), binary parser (`struct.unpack`), and 30% quality gate.
    - [`docs/OPEN3D.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/OPEN3D.md) — Statistical outlier removal (`nb=20, std=2.0`), Screened Poisson (`depth=11`), and 7.0% boundary trimming.
    - [`docs/MESH_AND_GLB.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/MESH_AND_GLB.md) — Verified UV texturing, Trimesh scene concatenation, Pillow PBR material attachment, and binary GLB export.
    - [`docs/JOB_MANAGEMENT.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/JOB_MANAGEMENT.md) — 4-state lifecycle, HTTP 503 capacity guard, 27-metric `job.result` schema.
- **Reason:** Code-level technical architecture audit eliminating obsolete or speculative descriptions.
- **Constraints Maintained:** `doc old/` left 100% intact. Zero application source code modified.

---

## 2026-11-11 — Phase 2: Master Documentation Consolidation & Verification
- **Added/Changed:**
  - Completed Phase 2 documentation consolidation executing [`docs/DOCUMENTATION_MIGRATION_PLAN.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/DOCUMENTATION_MIGRATION_PLAN.md).
  - Consolidated all 26 historical documents from `doc old/` into authoritative `docs/` master pack.
  - Authored new tooling documents:
    - [`docs/CODEBASE_MAP.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/CODEBASE_MAP.md) — Directory map and active vs. legacy script demarcation.
    - [`docs/DEVELOPMENT_WORKFLOW.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/DEVELOPMENT_WORKFLOW.md) — 11-step coding protocol and PR verification checklist.
    - [`docs/CODE_AND_FEATURE_MATRIX.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/CODE_AND_FEATURE_MATRIX.md) — Feature-to-code symbol verification matrix.
  - Upgraded [`docs/CONFIGURATION.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/CONFIGURATION.md), [`docs/TECH_STACK.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/TECH_STACK.md), [`docs/SOFTWARE_INVENTORY.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/SOFTWARE_INVENTORY.md), [`docs/GLOSSARY.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/GLOSSARY.md).
  - Sanitized all personal developer machine paths (`C:\Users\Aditya verma\...`) across `docs/` and root `README.md`.
  - Added 10-scenario end-to-end acceptance test matrix to [`docs/TESTING.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/TESTING.md).
- **Reason:** Establish `docs/` as the single, authoritative, technically rigorous, and code-verified documentation system for Smart India Hackathon 2026.
- **Constraints Maintained:** `doc old/` left 100% intact and untouched. Zero source code altered.

---

## 2026-11-11 — Phase 1: Master Technical Knowledge Base & Audit
- **Added/Changed:**
  - Authored comprehensive [`docs/GEOFORGE_MASTER_CONTEXT.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/GEOFORGE_MASTER_CONTEXT.md) (40 KB) master technical knowledge base for SIH 2026 / NTRO problem statement SIH26158.
  - Authored [`docs/DOCUMENTATION_MIGRATION_REPORT.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/DOCUMENTATION_MIGRATION_REPORT.md) auditing 26 historical documents against 31 new documents and live source code.
  - Authored [`docs/DOCUMENTATION_MIGRATION_PLAN.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/DOCUMENTATION_MIGRATION_PLAN.md) mapping out the 3-step phased migration.
- **Reason:** Comprehensive technical audit and discrepancy identification between documentation and source code.

---

## 2026-11-06 — Initial Archive Ingestion & Baseline Documentation
- **Added/Changed:**
  - Ingested initial `geoforge-main.zip` codebase.
  - Authored initial 26-document exploratory pack (`doc old/`) capturing early architectural notes, UI workflows, API endpoints, and COLMAP configurations.
  - Documented baseline Windows local development environment (Python 3.12, Node 24, Vite 3000, FastAPI 8000).
