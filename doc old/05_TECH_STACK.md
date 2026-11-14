# 05 — Technology stack

## Frontend (from package.json)
- React `^19.0.1`, React DOM `^19.0.1`
- TypeScript `~5.8.2`
- Vite `^6.2.3`, React Vite plugin `^5.0.4`
- Three.js `^0.185.1`
- Tailwind CSS `^4.1.14` with `@tailwindcss/vite`
- lucide-react, motion
- Google GenAI package and Express are dependencies, but their actual use in the core GeoForge reconstruction workflow is not established by this documentation. Verify references before removing or relying on them.

## Backend (from imports/source)
- Python
- FastAPI, Uvicorn expected to serve it
- OpenCV (`cv2`)
- NumPy
- COLMAP executable (configurable through `COLMAP_EXE`; source default is `C:\bin\colmap.exe`)
- Open3D (optional in some meshing paths)
- Trimesh
- Pillow

## Important dependency gap
The provided ZIP does not include a backend dependency manifest such as `requirements.txt` or `pyproject.toml`. Exact backend package versions are therefore not established. Add a tested, pinned dependency file as a separate maintenance task.

## Runtime configuration
- `VITE_API_URL`: frontend API base URL; defaults to `http://127.0.0.1:8000`.
- `ALLOWED_ORIGINS`: comma-separated backend CORS origins.
- `COLMAP_EXE`: path to COLMAP executable.
