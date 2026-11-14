# 01 — Product Requirements Document (PRD)

## 1. Product purpose
Provide a workflow to transform user-provided video into an interactive 3D model, with an understandable upload, processing, completion, error, and viewing experience.

## 2. Problem
Creating 3D models from aerial or handheld video requires extracting useful images, selecting a coherent image set, running photogrammetry, producing a mesh/texture, and making the result viewable. GeoForge brings those stages behind a web UI and a local Python reconstruction service.

## 3. Users
- Drone operators / mapping hobbyists who have video and want a 3D representation.
- Students and researchers learning photogrammetry.
- Engineering/design users exploring visual 3D capture.
These are intended user groups, not evidence of commercial validation.

## 4. Core user stories
- As a user, I can select a video and upload it to begin a job.
- As a user, I can see upload progress.
- As a user, I can see whether my job is queued, processing, complete, or failed.
- As a user, I can open the produced 3D model in a viewer.
- As a user, I can receive a useful error when input or processing fails.
- As a developer, I can run frontend and backend separately and configure their connection.

## 5. Functional requirements
| ID | Requirement | Priority | Acceptance criteria |
|---|---|---|---|
| FR-001 | Accept a video upload through the frontend | Must | UI sends multipart field `file` to `/upload`; backend accepts allowed extension subject to size and other checks. |
| FR-002 | Enforce upload size limit | Must | Backend rejects a declared content length above configured 4 GiB limit with HTTP 413. Streaming/body-level enforcement should be verified separately. |
| FR-003 | Create a reconstruction job | Must | Successful upload returns a job ID and status URL; job is stored in backend process memory. |
| FR-004 | Extract frames at target sampling rate | Must | Worker calls frame extraction at target 2 FPS; extraction reports frame/video metadata. |
| FR-005 | Filter poor frames | Must | Sharpness and brightness filtering functions run; counts are returned/logged. |
| FR-006 | Reduce redundant frames | Must | Similarity/difference filter selects frames before COLMAP. |
| FR-007 | Run COLMAP reconstruction | Must | Worker invokes reconstruction function and returns artifacts/stats on success. |
| FR-008 | Produce textured mesh and GLB | Must | A nonempty `model.glb` is created and served for job ID. |
| FR-009 | Expose job status | Must | `/status/{job_id}` returns current status and result/error when available. |
| FR-010 | Serve model | Must | `/model/{job_id}` returns a valid nonempty GLB; HEAD availability endpoint behavior is documented. |
| FR-011 | Display GLB interactively | Must | Three.js viewer loads the model and exposes visual interaction; browser behavior needs runtime test. |
| FR-012 | Explain process / help user capture footage | Should | Frontend has “How it works” content and capture tips. |
| FR-013 | Diagnostics and error UX | Should | UI has error and diagnostic components; confirm each failure mode in integration tests. |
| FR-014 | Durable jobs across server restart | Could / not currently verified | Would require persistent job store; current source uses in-memory `_jobs`. |
| FR-015 | Live progress for individual reconstruction stages | Could / not verified | Current status contract exposes job state; stage-by-stage progress API is not established in inspected source. |

## 6. Non-functional requirements
| ID | Requirement | Priority | Notes / acceptance |
|---|---|---|---|
| NFR-001 | Backend remains responsive during reconstruction | Must | Worker is submitted to a ThreadPoolExecutor; verify under concurrent load. |
| NFR-002 | Limit concurrent reconstruction workers | Must | Config currently sets max workers to 2; verify job scheduling behavior. |
| NFR-003 | Clear failures and logs | Should | Errors update job state and are logged; ensure UI surfaces actionable messages. |
| NFR-004 | Configurable frontend API endpoint | Must | `VITE_API_URL` overrides default `http://127.0.0.1:8000`. |
| NFR-005 | CORS configured for local frontend | Must | Allowed origins configurable by `ALLOWED_ORIGINS`; defaults include common localhost ports. |
| NFR-006 | Retain job artifacts only for a bounded time | Should | Source sets 7-day cleanup delay; verify cleanup task scheduling and lifecycle. |
| NFR-007 | Safe handling of untrusted uploads | Must | Validate filename/extension/size; review content sniffing, upload streaming, and subprocess security before production. |
| NFR-008 | Reproducible setup | Should | Pin/record backend dependencies and COLMAP version; repository archive does not show a backend requirements file. |

## 7. Scope
### In scope based on source
Video upload; frame extraction; sharpness/brightness and redundancy filtering; COLMAP reconstruction; point-cloud cleanup and mesh/texturing path; GLB conversion; status polling; browser model viewing; diagnostics/error UI.

### Not established / out of scope unless explicitly implemented
Survey-grade accuracy; guaranteed georeferencing; orthomosaic export as a working feature; LAS/OBJ download UI; cloud multi-user deployment; persistent queue; authentication/authorization; billing; mobile app; live video reconstruction.

## 8. Acceptance / release gates
- Frontend type check/build passes.
- Backend imports and starts with documented dependencies.
- `/health` returns healthy.
- Valid supported video upload creates a job and status can be polled.
- A known-good video completes the pipeline and produces nonempty GLB.
- Model URL loads in viewer without console/runtime errors.
- Invalid extension, too-large upload, missing COLMAP, insufficient usable frames, and failed reconstruction show meaningful errors.
- Job cleanup behavior and concurrent requests are tested.

## 9. Open questions
- Which operating systems are officially supported? Source uses a Windows-style COLMAP default, but platform support is not formally stated.
- Are models intended to be georeferenced or scale-accurate?
- Should users download GLB or other outputs directly?
- Should job metadata persist after API restart?
- What limits should apply to video duration, resolution, and file size in practice?
- Is upload content-type validation intended in addition to extension validation?
