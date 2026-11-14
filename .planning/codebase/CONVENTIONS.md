# Coding Conventions

**Analysis Date:** 2026-11-12

## Naming Patterns

**Files:**
- Backend: `snake_case.py` for all Python modules (`frame_processing.py`, `convert_to_glb.py`, `database.py`)
- Frontend Components: `PascalCase.tsx` (`ThreeDViewer.tsx`, `DiagnosticsAccordion.tsx`)
- Frontend Pages: `PascalCasePage.tsx` (`UploadPage.tsx`, `CompletePage.tsx`, `HistoryPage.tsx`)
- Frontend Utilities: `camelCase.ts` (`api.ts`, `types.ts`)
- Configuration & Manifests: `UPPERCASE.md` (`AGENTS.md`, `README.md`, `ARCHITECTURE.md`)

**Functions:**
- Backend: `snake_case` for all functions and methods (`extract_frames`, `run_reconstruction`, `validate_video`)
- Frontend: `camelCase` for functions and React hooks (`uploadDroneVideo`, `getModelGlbUrl`, `useCallback`)
- Frontend Event Handlers: `handleAction` or `onAction` (`handleSelectHistoryJob`, `onCancel`, `handleUpload`)

**Variables:**
- Backend: `snake_case` for local variables and parameters (`job_id`, `frame_count`, `video_path`)
- Backend Constants: `UPPER_SNAKE_CASE` (`MAX_UPLOAD_BYTES`, `MIN_FRAMES_FOR_RECONSTRUCTION`, `TEMP_DIR`)
- Frontend: `camelCase` for variables (`uploadProgress`, `activeJobId`, `stageIndex`)
- Frontend Constants: `UPPER_SNAKE_CASE` (`TOTAL_STAGES`, `API_BASE_URL`)

**Types:**
- Backend Enums: `PascalCase` with `UPPER_SNAKE_CASE` values (`JobStatus.QUEUED`, `JobStatus.PROCESSING`)
- Frontend Interfaces: `PascalCase`, without Hungarian `I` prefix (`ReconstructionJob`, `UploadResponse`, `JobHistoryItem`)
- Frontend Types: `PascalCase` (`AppRoute`, `JobStage`)

## Code Style

**Formatting:**
- Python: PEP 8 compliant with 4-space indentation; strict avoidance of trailing whitespace.
- TypeScript/React: 2-space indentation, single quotes for strings, semicolons required.
- Styling: Tailwind CSS v4 utility classes following dark slate aesthetic (`bg-slate-900`, `text-slate-100`, `border-slate-800`, `text-blue-400`).

**Linting & Verification:**
- Python: Bytecode compilation checks:
  ```powershell
  python -m py_compile backend/*.py
  ```
- Frontend: TypeScript static type checking without emit:
  ```powershell
  npm run lint    # runs tsc --noEmit
  npm run build   # runs vite build
  ```

## Import Organization

**Python Backend:**
1. Standard library modules (`asyncio`, `logging`, `os`, `pathlib`, `subprocess`, `uuid`)
2. Third-party packages (`cv2`, `numpy`, `fastapi`, `open3d`, `trimesh`, `PIL`)
3. Local application modules (`import database`, `from frame_processing import extract_frames`)

**Frontend TypeScript:**
1. React and third-party packages (`react`, `three`, `lucide-react`, `motion`)
2. Local types and interfaces (`import { JobStatus, UploadResponse } from '../types'`)
3. Local services and utilities (`import { getJobStatus } from '../services/api'`)
4. Local UI components (`import Header from './components/Header'`)

**Path Resolution:**
- Backend: Always use `pathlib.Path` for filesystem path manipulation. Avoid raw string concatenation.
- Subprocess Calls: Pass command arguments as discrete lists (`[COLMAP_EXE, "mapper", ...]`). Never use `shell=True` or string interpolation.

## Error Handling

**Backend Strategy:**
- Fail-fast validation at route boundaries:
  - All `job_id` path parameters must validate against `uuid.UUID(job_id)`.
  - Video uploads must validate file size (<= 4 GB) and file extension against `{".mp4", ".mov", ".avi", ".mkv"}`.
- Unhandled background pipeline exceptions are captured in `try-except` blocks, recorded with `traceback.format_exc()`, persisted to SQLite via `database.fail_job(job_id, error_message)`, and mapped to client status.
- Concurrency violations return `HTTP 503 Service Unavailable`.
- Resource not found returns `HTTP 404 Not Found`.

**Frontend Strategy:**
- Network transport errors in `api.ts` catch network disconnects and return user-friendly fallback error messages.
- Polling in `ProcessingPage.tsx` handles transient network drops without immediately declaring job failure.
- Error states render through `ErrorView.tsx` with diagnostic details and retry buttons.

## Logging

**Framework:**
- Python standard library `logging.getLogger("geoforge")`.
- Format: `"%(asctime)s %(levelname)s [%(name)s] %(message)s"` with UTC timestamp.

**Patterns:**
- Always prepend job ID to pipeline log messages: `logger.info(f"[{job_id}] STAGE {stage_num}: {message}")`.
- Log critical lifecycle events: job registration, stage entry/exit, file conversions, and errors.
- Never output sensitive user tokens or raw binary content to console logs.

## Comments

**When to Comment:**
- Document complex photogrammetry formulas and geometric filtering rules (e.g. Laplacian blur threshold rationale, Poisson depth octree levels, trimming percentages).
- Explain hardware workarounds (e.g. why `MAX_CONCURRENT_RECONSTRUCTIONS` is locked to 1).
- Avoid obvious comments (`# increment counter`).

**Docstrings:**
- Mandatory docstrings on all public backend functions detailing parameters, return types, and exceptions raised.
- TSDoc comments on exported API client functions in `frontend/src/services/api.ts`.

## Function Design

**Size:**
- Single responsibility principle: separate video decoding, blur filtering, redundancy checking, SfM/MVS execution, and meshing into discrete, testable functions.

**Parameters:**
- Type-annotated arguments and return values for all Python functions (`job_id: str`, `video_path: Path -> Dict[str, Any]`).
- Explicit TypeScript props interfaces for all React components.

**Return Values:**
- Structured dictionaries for backend processing results (`{"status": "success", "frames_saved": N}`).
- Consistent schema responses across all REST API endpoints.

---

*Convention analysis: 2026-11-12*
*Update when patterns change*

