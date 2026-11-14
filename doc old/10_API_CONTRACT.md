# 10 — Backend API contract

Base URL defaults to `http://127.0.0.1:8000`.

## `GET /`
Returns service information such as online status, message, service name, and version.

## `GET /health`
Returns:
```json
{"status":"healthy"}
```

## `POST /upload`
- Content type: `multipart/form-data`
- Field: `file`
- Supported extension allowlist in `main.py`: `.mp4`, `.mov`, `.avi`, `.mkv`
- Configured maximum declared upload size: 4 GiB.
- Rejects missing filename / unsupported extension / oversized declared content length.
- Successful response includes job ID and status URL (inspect exact response fields in current source).

The frontend `uploadDroneVideo()` sends the field `file` using XMLHttpRequest, reports progress if available, parses JSON, and handles HTTP/network errors.

## `GET /status/{job_id}`
Returns job status. States in backend enum: `queued`, `processing`, `complete`, `failed`. Completed status includes `result`; failed status includes error information. Invalid IDs and unknown jobs may produce error responses; inspect exact response shape and status code in current source.

## `GET /model/{job_id}`
Serves GLB with FastAPI `FileResponse` after checking ID/path/existence/size.

## `HEAD /model/{job_id}`
Provides model availability information (the source implements a HEAD handler; confirm actual response headers and response shape in tests).

## Frontend API helpers
- `API_BASE_URL` reads `VITE_API_URL`.
- `getJobStatus(jobId)` uses fetch.
- `getModelGlbUrl(value)` accepts an ID, model path, or complete URL and normalizes to a model URL.

This is a concise contract. Before changing endpoint fields, inspect both backend and frontend caller and update this document plus tests.
