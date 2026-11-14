# Development Workflow & Contribution Guidelines — GeoForge

> **Document:** `docs/DEVELOPMENT_WORKFLOW.md`  
> **Status:** Canonical Verified Development Protocol  
> **Target Version:** GeoForge v1.0.0 (SIH 2026 / NTRO Edition)  
> **Related Documents:** [`AGENTS.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/AGENTS.md), [`docs/TESTING.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/TESTING.md), [`docs/CODEBASE_MAP.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/CODEBASE_MAP.md)

---

## 1. Core Development Protocol (11-Step Process)

All contributors—both software engineers and AI coding assistants—must adhere to this 11-step protocol when developing or maintaining GeoForge:

1. **Feature Branching:** Never commit directly to `main`. Create a descriptive feature branch (`feature/sift-tuning`, `fix/upload-mkv-allowlist`, `docs/consolidation`).
2. **Review Context & Constraints:** Read [`AGENTS.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/AGENTS.md) and [`docs/GEOFORGE_MASTER_CONTEXT.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/GEOFORGE_MASTER_CONTEXT.md) before writing code. Respect existing architectures.
3. **Inspect Active Source Paths:** Verify whether your target component resides in active production directories (`backend/` or `frontend/`) or legacy exploration directories (`src/`). Never modify active pipeline behavior by editing `src/`.
4. **Scope Narrowly:** Formulate a clear, bounded issue statement with measurable acceptance criteria before making modifications.
5. **Minimal Surgical Changes:** Write minimal, idiomatic changes. Preserve existing docstrings, comments, and unrelated module behaviors.
6. **Frontend Verification:**
   - Execute TypeScript check: `npm run lint` (`tsc --noEmit`).
   - Execute production build: `npm run build` (`vite build`).
   - Confirm zero type errors or broken component interfaces.
7. **Backend Syntax & Import Checks:**
   - Verify Python syntax: `python -m py_compile backend/<modified_file>.py`.
   - Verify module imports: `python -c "import main, reconstruction, frame_processing, frame_filtering, redundancy_filter, convert_to_glb"`.
8. **End-to-End Pipeline Smoke Test:**
   - Run a test reconstruction using a verified sample video (1080p, 15–30s).
   - Verify that all quality gates pass and `backend/temp/{job_id}/output/model.glb` is generated.
9. **Documentation Synchronization:** If modifying endpoints, thresholds, or components, immediately update [`docs/API.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/API.md), [`docs/CONFIGURATION.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/CONFIGURATION.md), and [`docs/CHANGELOG.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/CHANGELOG.md).
10. **Sanitize Diff:** Inspect `git diff` for:
    - Personal machine paths (e.g., `C:\Users\...`).
    - API keys, credentials, or sensitive tokens.
    - Accidental deletions of test assets or historical archives (`doc old/`).
11. **Commit & Pull Request:** Author a clear, conventional commit message (`feat:`, `fix:`, `docs:`, `perf:`) and submit a Pull Request following the checklist below.

---

## 2. Pull Request (PR) Acceptance Checklist

Before submitting or merging any code change, verify all checklist items:

- [ ] **Scope Defined:** PR clearly explains the problem solved and links the relevant issue or PRD requirement (`FR-XXX` / `NFR-XXX`).
- [ ] **Minimal Blast Radius:** Changes are strictly confined to the intended functionality; no formatting churn across unrelated files.
- [ ] **Frontend Quality Gate:** `npm run lint` and `npm run build` execute with zero errors.
- [ ] **Backend Quality Gate:** Python service starts cleanly with `python -m uvicorn main:app --reload --port 8000`.
- [ ] **No Personal Paths:** Confirmed zero instances of hardcoded machine paths (`C:\Users\Aditya verma\...` or similar developer-specific roots).
- [ ] **No Hardcoded Secrets:** Confirmed no API tokens, private IPs, or security credentials.
- [ ] **Documentation Updated:** Corresponding master documents in `docs/` updated to reflect the new code truth.
- [ ] **No Silent Fallbacks:** Errors are explicitly logged and surfaced to users with actionable messages; no silent suppression of COLMAP failure return codes.

---

## 3. Rules for AI Coding Agents

1. **Never Invent Architecture:** Do not replace the existing FastAPI/React/COLMAP stack with unrequested new frameworks (e.g., Next.js, Django, Celery) unless explicitly instructed by the user.
2. **Preserve `doc old/`:** The `doc old/` directory is an immutable historical audit record. Never modify, overwrite, or delete files in `doc old/`.
3. **Verify Against Code:** Never declare a feature "implemented" solely because it is mentioned in a roadmap or interface definition. Verify actual implementation in `backend/` or `frontend/`.

