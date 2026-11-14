# 02 — Features and implementation status

Statuses below are based on source inspection only; they are not runtime test results.

| Feature | Evidence in source | Status / caveat |
|---|---|---|
| React application shell and navigation | `frontend/src/App.tsx`, Header/Footer, page components | Present in source |
| Home / intro content | `pages/HomePage.tsx` | Present |
| How-it-works information | `pages/HowItWorksPage.tsx` | Present |
| Upload interface and progress | `pages/UploadPage.tsx`, `services/api.ts` | Present; runtime not tested |
| Job polling and processing screen | `App.tsx`, `pages/ProcessingPage.tsx` | Present; backend stage granularity needs verification |
| Completion / result pages | `CompletePage.tsx`, `ResultPage.tsx` | Present |
| Three.js GLB viewer | `components/ThreeDViewer.tsx` | Present; actual model loading and interaction require runtime test |
| Error view and diagnostic accordion | `ErrorView.tsx`, `DiagnosticsAccordion.tsx` | Present |
| Backend health/root routes | `backend/main.py` | Present |
| Multipart upload endpoint | `backend/main.py` | Present |
| In-memory job status | `backend/main.py` | Present; lost on process restart |
| Frame extraction | `frame_processing.py` | Present |
| Sharpness/brightness frame filtering | `frame_filtering.py` | Present |
| Redundancy reduction | `redundancy_filter.py` | Present |
| COLMAP reconstruction | `reconstruction.py` | Present; needs installed COLMAP and compatible assets |
| Point-cloud cleaning | reconstruction pipeline and helper scripts | Present; algorithm and output quality depend on configuration |
| Poisson meshing | reconstruction code | Present with COLMAP fallback when Open3D path unavailable |
| Texturing | COLMAP mesh texturer path | Present in pipeline source |
| PLY/textured mesh to GLB | `convert_to_glb.py` | Present |
| Orthomosaic/coordinate system outputs | Some frontend type declarations mention fields | Not established as generated backend output; do not claim supported |
| Download/export controls | Inspect UI before asserting; type fields alone are not evidence | Unverified |
| Login, cloud persistence, multi-user accounts | No evidence in this archive | Not present/verified |
