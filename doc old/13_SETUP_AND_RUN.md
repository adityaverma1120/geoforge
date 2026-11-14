# 13 — Setup and run locally

This is a source-based starter guide. Exact Python dependencies are not pinned in the supplied archive, so first install the required packages compatible with your Python and COLMAP installation.

## Prerequisites
- Windows environment is the default implied by the COLMAP path; other OS support is not formally established.
- Node.js and npm compatible with the Vite project.
- Python compatible with FastAPI/OpenCV/Open3D and installed dependencies.
- COLMAP executable configured through `COLMAP_EXE`.
- COLMAP vocabulary-tree assets required by the reconstruction configuration.
- Sufficient RAM, disk space, and ideally GPU/CUDA support if your COLMAP build uses it. CUDA is not a universal requirement for all COLMAP builds.

## Backend
From repository root:
```powershell
cd backend
python -m pip install fastapi uvicorn python-multipart opencv-python numpy open3d trimesh pillow
$env:COLMAP_EXE = "C:\bin\colmap.exe"
python -m uvicorn main:app --reload --port 8000
```
This package list is a provisional list based on imports; it is not a tested/pinned requirements file. Some imports/branches may need additional packages or version constraints.

## Frontend
In a separate terminal:
```powershell
cd frontend
npm install
# Optional: create .env.local with VITE_API_URL=http://127.0.0.1:8000
npm run dev
```
Open the Vite URL printed in the terminal (default port 3000).

## Verify
- `http://127.0.0.1:8000/health` should return `{"status":"healthy"}`.
- Frontend should load and reach upload page.
- Use a small known-good video first.
- Inspect backend logs and `/status/{job_id}`.
- Confirm GLB URL and browser viewer load.

## Important
The `npm run clean` script uses Unix `rm -rf`; do not run it blindly in Windows CMD. The archive does not include a backend requirements file; create and validate one before onboarding other developers.
