# 14 — Configuration and environment

| Variable / setting | Source | Meaning |
|---|---|---|
| `VITE_API_URL` | frontend `services/api.ts` / Vite env | Backend base URL; default `http://127.0.0.1:8000` |
| `ALLOWED_ORIGINS` | backend `main.py` | Comma-separated allowed CORS origins |
| `COLMAP_EXE` | backend `reconstruction.py` | COLMAP executable path; default `C:\bin\colmap.exe` |
| `MAX_UPLOAD_BYTES` | backend `main.py` | 4 GiB configured limit |
| `MIN_FRAMES_FOR_RECONSTRUCTION` | backend `main.py` | 20-frame floor |
| `JOB_RETENTION_SECONDS` | backend `main.py` | 7-day retention delay |
| `MAX_CONCURRENT_RECONSTRUCTIONS` | backend `main.py` | 2 executor workers |
| extraction target FPS | `main.py` worker call | 2.0 |
| sharpness threshold | `main.py` worker call | 100.0 |
| redundancy difference threshold | `main.py` worker call | 5.0 |

Do not commit `.env` secrets. Vite variables prefixed with `VITE_` are exposed to the client bundle; never put private credentials in them.
