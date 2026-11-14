# Local Development Setup Guide — GeoForge

> **Document:** `docs/SETUP.md`  
> **Status:** Canonical Verified Setup Guide (Phase 7 Integration Verified)  
> **Target Version:** GeoForge v1.0.0 (SIH 2026 / NTRO Edition)  
> **Last Verified:** 2026-11-14  
> **Related Documents:** [`docs/CONFIGURATION.md`](CONFIGURATION.md), [`docs/BACKEND.md`](BACKEND.md), [`docs/FRONTEND.md`](FRONTEND.md), [`docs/TROUBLESHOOTING.md`](TROUBLESHOOTING.md), [`docs/INTEGRATION_VERIFICATION_REPORT.md`](INTEGRATION_VERIFICATION_REPORT.md)

---

## 1. System Requirements & Verified Software

Before installing GeoForge, verify that your host workstation meets the following hardware and software requirements:

### 1.1 Hardware Specifications
| Component | Minimum Specification | Recommended Specification |
|---|---|---|
| **CPU** | 4-Core x86_64 Processor | 8-Core Intel Core i7 / AMD Ryzen 7 or better |
| **System RAM** | 16 GB DDR4/DDR5 | 32 GB DDR4/DDR5 (High-density Poisson meshing) |
| **GPU (CUDA)** | NVIDIA GPU with $\ge 4\text{ GB}$ VRAM | NVIDIA RTX 3060/4060+ with $\ge 8\text{ GB}$ VRAM |
| **Storage** | 30 GB free NVMe/SSD space | 100 GB+ NVMe SSD (Dense stereo scratch data) |

### 1.2 Verified Software Runtimes
| Software | Required Version | Verified Version in Development | Verification Command |
|---|---|---|---|
| **Operating System** | Windows 10/11 64-bit or Ubuntu 22.04 LTS | Windows 11 Enterprise (Build 22631) | `[System.Environment]::OSVersion` |
| **Python** | 3.10 – 3.12 (64-bit) | Python 3.12.3 64-bit | `python --version` |
| **Node.js** | $\ge 18.0.0$ | Node.js v20.x / v24.x | `node --version` |
| **npm** | $\ge 9.0.0$ | npm 10.x / 11.x | `npm --version` |
| **COLMAP** | $\ge 3.8$ (CUDA enabled) | COLMAP 4.1.1 (CUDA 12.x) | `& "C:\bin\colmap.exe" -h` |
| **NVIDIA Driver** | CUDA 11.8+ / 12.x compatible | Driver 550.x+ | `nvidia-smi` |

---

## 2. COLMAP Installation & Configuration

GeoForge relies on the compiled COLMAP command-line interface for Structure-from-Motion (SfM) and dense Multi-View Stereo (MVS).

### 2.1 Windows Installation
1. Download the latest official Windows CUDA build from the [COLMAP Releases](https://github.com/colmap/colmap/releases) (e.g. `COLMAP-3.8-windows-cuda.zip` or `COLMAP-3.9-windows-cuda.zip`).
2. Extract the archive contents into:
   ```text
   C:\bin\
   ```
   Ensuring that `C:\bin\colmap.exe` exists directly at that path.
3. If installed in an alternative location (e.g. `D:\tools\colmap\colmap.exe`), configure the `COLMAP_EXE` environment variable (see Section 4).

> [!WARNING]
> **Space-Safe Path Handling:**  
> Do not invoke COLMAP through Windows `.bat` wrapper scripts or `cmd.exe /c`. If your Windows user folder contains spaces (e.g. `C:\Users\Aditya verma\...`), batch wrappers fail to parse unquoted directory arguments. GeoForge executes `colmap.exe` directly via Python `subprocess.run(list_of_args)`, which handles paths with spaces safely.

### 2.2 Optional Vocabulary Tree Download
For fast loop-detection and visual feature indexing during sequential matching, download the official Flickr100k vocabulary tree:
- **File Name:** `vocab_tree_flickr100k_words32k.bin`
- **Official Download:** [COLMAP Vocabulary Trees](https://demuc.de/colmap/)
- Place the file in any of these candidate discovery locations checked automatically by `backend/reconstruction.py`:
  1. `C:\bin\vocab_tree_flickr100k_words32k.bin` (beside `colmap.exe`)
  2. `backend/assets/vocab_tree_flickr100k_words32k.bin`
  3. `<colmap_dir>/vocab_tree_flickr100k_words32k.bin`

If no vocabulary tree is found, GeoForge automatically falls back to standard sequential matching without loop closure.

---

## 3. Step-by-Step Installation

### Step 3.0: Turnkey Single-Click Launch (Recommended for Windows)
For turnkey evaluation and production deployment on Windows, GeoForge includes an automated batch launcher:

```powershell
# From project root:
.\start_geoforge.bat
```
The launcher automatically verifies the `.venv` Python virtual environment, confirms core dependencies, builds the frontend if `frontend/dist` is missing, checks COLMAP and FFmpeg, launches your web browser to `http://localhost:8000`, and starts the unified Uvicorn server.

---

### Step 3.1: Manual Backend Setup (FastAPI & Computer Vision Engine)
Open a dedicated PowerShell window:

```powershell
# 1. Activate the root virtual environment
.\.venv\Scripts\Activate.ps1
# On Linux / macOS use: source .venv/bin/activate

# 2. Start the unified FastAPI server
python -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000
```

Verify backend package installation:
```powershell
python -c "import fastapi, uvicorn, multipart, cv2, numpy, open3d, trimesh, PIL; print('All backend dependencies verified.')"
```

### Step 3.2: Frontend Setup (React 19, Vite, Three.js)
If developing UI components or building the production bundle:

```powershell
# 1. Navigate to frontend directory
cd frontend

# 2. Install all npm dependencies
npm install

# 3. Compile production bundle (served automatically by FastAPI on port 8000)
npm run build

# 4. (Optional) Run Vite HMR dev server on port 3000
npm run dev
```

> [!CAUTION]
> **Windows `npm run clean` Warning:**  
> The script `"clean": "rm -rf dist node_modules"` in `frontend/package.json` uses Unix shell syntax. Running `npm run clean` directly in Windows PowerShell or CMD will fail with a command not recognized error. On Windows, use PowerShell instead:  
> `Remove-Item -Recurse -Force dist, node_modules`

---

## 4. Environment Variables Configuration

GeoForge uses three verified environment variables. Defaults are pre-configured for standard local development:

| Variable Name | Component | Default Value | Purpose | When to Override |
|---|---|---|---|---|
| `COLMAP_EXE` | Backend | `C:\bin\colmap.exe` | Path to COLMAP CLI binary | Set when COLMAP is installed in a custom directory or on Linux (`/usr/local/bin/colmap`). |
| `ALLOWED_ORIGINS` | Backend | `http://localhost:3000,...` | CORS allowed origins | Set in production when frontend is served from a custom domain or IP. |
| `VITE_API_URL` | Frontend | `http://127.0.0.1:8000` | Backend API URL | Set in `frontend/.env.local` if backend runs on a remote IP or non-default port. |

### Setting Environment Variables (PowerShell):
```powershell
# Backend custom COLMAP location (if applicable)
$env:COLMAP_EXE = "D:\Softwares\COLMAP\colmap.exe"

# Backend custom CORS origin (if applicable)
$env:ALLOWED_ORIGINS = "http://localhost:3000,http://192.168.1.50:3000"
```

### Setting Frontend Configuration (`frontend/.env.local`):
```bash
# Create frontend/.env.local to point to custom backend
VITE_API_URL="http://127.0.0.1:8000"
```

---

## 5. Starting the Application

Always run the backend and frontend in separate terminals.

### Terminal 1: Start Backend Server
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload --port 8000
```
Expected output:
```text
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Terminal 2: Start Frontend Development Server
```powershell
cd frontend
npm run dev
```
Expected output:
```text
  VITE v6.2.3  ready in 320 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: http://192.168.1.X:3000/
  ➜  press h + enter to show help
```

---

## 6. Verifying Servers & Health Checks

Verify both servers are operational before initiating video processing:

### 6.1 Backend Verification Commands
Open a third terminal or PowerShell tab:

```powershell
# 1. Probe the root endpoint
curl http://127.0.0.1:8000/
# Expected: {"name": "GeoForge API", "status": "running"}

# 2. Probe the health check endpoint
curl http://127.0.0.1:8000/health
# Expected: {"status": "healthy"}

# 3. Interactive OpenAPI Documentation (Browser)
# Navigate to: http://127.0.0.1:8000/docs
```

### 6.2 Frontend Verification
1. Open Google Chrome, Microsoft Edge, or Mozilla Firefox.
2. Navigate to `http://localhost:3000`.
3. Confirm the **GeoForge** navigation bar, hero banner, feature cards, and capture guidance load without console errors (press `F12` to open Developer Tools).

---

## 7. End-to-End Smoke Test Procedure

Execute this 5-minute smoke test to validate full pipeline integration:

1. **Prepare Sample Flight Footage:**
   - Use a short 1080p drone video ($15\text{--}30\text{ seconds}$, `.mp4` format, $\sim 30\text{--}50\text{ MB}$).
   - Ensure the video captures an outdoor building or textured object with smooth orbital or linear motion.
2. **Submit Upload:**
   - From `http://localhost:3000/`, click **Get Started** or **Upload**.
   - Drag and drop your test video.
   - Click **Generate 3D Model**.
   - Verify upload progress reaches 100%.
3. **Observe Pipeline Execution:**
   - UI automatically transitions to `/processing`.
   - Backend terminal logs should show the 8 execution stages:
     ```text
     [job_id] STEP 1: Saving video
     [job_id] STEP 2: Extracting frames (target_fps=2.0)
     [job_id] STEP 3: Filtering sharp frames (threshold=100.0)
     [job_id] STEP 4: Removing redundant frames (difference_threshold=5.0)
     [job_id] STEP 5: Running COLMAP reconstruction (OPENCV camera model)
     [job_id] STEP 6: Dense MVS point cloud fusion
     [job_id] STEP 7: Point cloud cleaning & Poisson meshing (depth=11, trim=7.0%)
     [job_id] STEP 8: Texturing & GLB packaging
     ```
4. **Inspect Terminal Result:**
   - UI transitions to `/complete` with summary metrics (reconstructed points, mesh faces, processing time).
   - Click **Open in 3D Viewer**.
   - Confirm the Three.js viewport renders the 3D model with interactive OrbitControls (left-click orbit, right-click pan, scroll zoom).

---

## 8. Workspace Directory & Disk Cleanup

During reconstruction, GeoForge generates intermediate point clouds and depth maps in `backend/temp/{job_id}/`:
- A typical 30-second 1080p video creates $\sim 1\text{--}3\text{ GB}$ of intermediate scratch files.
- Completed jobs are scheduled for automated deletion after 7 days (`JOB_RETENTION_SECONDS = 604800`).
- **Manual Cleanup:** To immediately reclaim disk space, delete subfolders inside `backend/temp/` and `backend/uploads/`:
  ```powershell
  # Powershell command to clear temporary scratch workspaces
  Remove-Item -Recurse -Force backend\temp\*
  Remove-Item -Force backend\uploads\*
  ```
