# 15 — Testing and acceptance

## Automated checks available from frontend package
```powershell
cd frontend
npm run lint
npm run build
```
These commands are listed in package.json; this documentation has not executed them against the user’s machine.

## Backend checks to establish
- Python syntax/import checks for backend modules.
- API smoke test: root and `/health`.
- Upload test for valid file and invalid extension.
- Declared oversized upload returns 413.
- Poll queued/processing/complete/failed states.
- Test unknown and malformed job IDs.
- Confirm output GLB exists and is nonzero.
- Confirm GET and HEAD model route behavior.
- Verify cleanup, concurrency, and server restart behavior.

## End-to-end test matrix
| Scenario | Expected |
|---|---|
| Good textured scene, sufficient overlap | Job completes and viewer renders recognizable geometry |
| Unsupported extension | Clear rejection |
| Missing/empty file | Clear rejection |
| Too few useful frames | Job fails with a reason and capture guidance |
| COLMAP executable missing | Clear configuration error |
| COLMAP command fails | Job fails; useful logs preserved |
| No texture / GLB export failure | Job fails, not falsely marked complete |
| Malformed or empty GLB | Viewer reports loading/geometry error |
| Backend unavailable | Frontend displays connection error |
| API restarted during job | User is informed that in-memory job state may be lost |
