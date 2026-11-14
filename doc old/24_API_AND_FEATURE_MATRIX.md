# 24 — API and feature verification matrix

| Surface | Source entry point | Verification to run |
|---|---|---|
| API root | `backend/main.py: home()` | GET `/` and inspect JSON |
| Health | `backend/main.py: health()` | GET `/health` |
| Upload | `backend/main.py: upload_video()` | Valid/invalid/missing/oversized file tests |
| Job status | `backend/main.py: get_status()` | Poll all status states and unknown ID |
| Model GET | `backend/main.py: get_model()` | Fetch GLB, validate MIME/bytes |
| Model HEAD | `backend/main.py: check_model()` | Inspect status and headers |
| Frame extraction | `backend/frame_processing.py` | Known video metadata/frame count |
| Quality filter | `backend/frame_filtering.py` | Synthetic sharp/blurry and brightness cases |
| Redundancy filter | `backend/redundancy_filter.py` | Similar vs changed frames |
| COLMAP | `backend/reconstruction.py` | End-to-end run with COLMAP installed |
| GLB export | `backend/convert_to_glb.py` | Open generated GLB in independent viewer |
| Upload UI | `frontend/src/pages/UploadPage.tsx` | Browser manual test |
| Polling state | `frontend/src/App.tsx` | Network throttling, job failures |
| Three.js viewer | `frontend/src/components/ThreeDViewer.tsx` | valid/invalid/large GLB, resize, GPU |
| Error UI | `frontend/src/components/ErrorView.tsx` | Map backend error cases to messages |

Line numbers are intentionally omitted because they change; use symbols and current source.
