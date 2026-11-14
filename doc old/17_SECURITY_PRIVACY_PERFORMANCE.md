# 17 — Security, privacy, and performance

## Security observations
- Upload validation checks filename, extension, and declared content length in source. Confirm actual streamed bytes are bounded too; content-length can be absent or misleading.
- Uploaded videos are parsed by OpenCV and passed through external tooling. Keep dependencies updated and isolate processing for untrusted inputs where practical.
- CORS defaults are permissive for several localhost origins; configure explicit origins for deployed environments.
- No authentication or authorization mechanism is established by the inspected source. Do not expose a public deployment with unrestricted large uploads/reconstruction without access and abuse controls.
- Ensure filenames are normalized and job IDs are validated before filesystem access.
- Never expose absolute local file paths or raw traceback to end users in production.

## Privacy
Uploaded video may capture people, homes, infrastructure, or sensitive sites. Document retention, access, consent, and deletion behavior before public use. Current source configures a seven-day cleanup interval, but verify lifecycle scheduling.

## Performance
- 4 GiB configured upload maximum is high for a single web request.
- Two simultaneous reconstruction workers can use substantial CPU, RAM, GPU, and disk.
- Dense reconstruction and mesh texturing are resource-intensive.
- Large GLB assets may cause browser memory/GPU pressure.
- Consider queueing, cancellation, progress telemetry, resource caps, model simplification, and resumable uploads as future work—but do not claim they currently exist.
