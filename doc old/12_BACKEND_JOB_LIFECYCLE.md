# 12 — Backend job lifecycle

## Job creation
`POST /upload` saves the uploaded video and initializes an entry in `_jobs`. The job ID is UUID-based in source. The API response supplies status polling information.

## Execution
A `ThreadPoolExecutor` is configured with `MAX_CONCURRENT_RECONSTRUCTIONS = 2`. The worker is blocking and executes frame processing and reconstruction. Status values are tracked in a Python in-memory dictionary.

## Result
Result metadata includes:
- video frame count, sampled frames, source FPS/resolution/duration
- kept and rejected frames (blur, brightness, redundancy)
- workspace/model directories and image counts
- registration ratio, sparse/dense/cleaned cloud counts, mesh vertices/faces, quality warnings
- dense cloud, Poisson mesh, textured model, texture, GLB path and size
- `/model/{job_id}` URL and pipeline completion status

Exact optional fields depend on the successful reconstruction return values.

## Failure
Worker exceptions are logged and status becomes failed with error text. A process restart clears in-memory jobs. Persistent queue/recovery is not implemented in the source reviewed.

## Retention
Configured retention is seven days (`JOB_RETENTION_SECONDS`). A cleanup coroutine removes job directory, uploaded video, and in-memory record after its delay. Verify that cleanup is scheduled in every lifecycle path before depending on the retention promise.
