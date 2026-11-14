# 19 — Upgrade roadmap

This is a suggested order, not a claim that these features are already built.

## P0 — Make current workflow dependable
- Establish backend dependency manifest and supported Python/COLMAP versions.
- Test complete sample video path and write reproducible setup.
- Resolve mismatch between frontend pipeline stage labels and backend status detail.
- Verify job cleanup is scheduled and handles failed uploads/jobs.
- Add integration tests for upload, status, model GET/HEAD, and errors.
- Confirm viewer camera framing, resize, renderer cleanup, and reload state.

## P1 — Usability and observability
- Show honest per-stage progress from backend, not only client-side simulation.
- Add processing logs/diagnostics downloadable without sensitive local paths.
- Add user cancellation and explicit retry where safe.
- Improve quality warnings and capture recommendations.
- Add model download/export action if desired.

## P2 — Reliability / scaling
- Persistent job database and queue.
- Resumable upload and streaming size enforcement.
- Worker process isolation and resource caps.
- Retention settings and user deletion controls.
- Authentication/authorization for deployed use.

## P3 — Advanced product features (only after validation)
- Georeferencing / coordinate-system support with documented accuracy.
- Model simplification and levels of detail.
- Alternative export formats.
- Multi-project organization and sharing.
- Cloud storage / team workflows.
