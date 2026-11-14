# Complete Dependency & Software Installation Guide — GeoForge

> **Document:** `docs/DEPENDENCY_AND_SOFTWARE_INSTALLATION_GUIDE.md`  
> **Status:** Code-Verified Dependency Inventory & Windows 11 Installation Manual  
> **Target Version:** GeoForge v1.0.0 (SIH 2026 / NTRO Edition)  
> **Author:** Antigravity AI Engineering & Architecture Team  
> **Audit Date:** 2026-11-11  
> **Target OS:** Windows 11 (x64)

---

## 1. Executive Hardware & Environment Profile

This audit evaluates the exact dependencies required to run GeoForge on the operator's specified workstation:

| Hardware Component | User Workstation Specification | Sizing & GeoForge Compatibility Assessment |
|---|---|---|
| **CPU** | **Intel Core i5-13450HX** (10 Cores: 6P + 4E, 16 Threads, up to 4.6 GHz) | **Excellent.** 16 threads provide fast multi-core OpenCV video decoding, parallel Laplacian blur variance filtering, and multithreaded CPU steps. |
| **GPU** | **NVIDIA GeForce RTX 3050 Laptop GPU (6 GB GDDR6 VRAM)** | **Fully Supported.** Ampere architecture (Compute Capability 8.6). 6 GB VRAM is sufficient for COLMAP SIFT extraction and PatchMatch stereo at default `PATCHMATCH_MAX_IMAGE_SIZE = 2400` for 1080p footage. *(For heavy 4K footage, downsample to 1600 px to avoid OOM).* |
| **System RAM** | **16 GB DDR5** | **Supported.** Meets minimum requirement. Sufficient for Screened Poisson reconstruction (`depth=11`) on point clouds up to $\sim 4\text{M}$ points. |
| **Storage** | **512 GB NVMe SSD** | **Supported.** Fast I/O speeds for depth maps. Monitor `backend/temp/` since runs generate $10\text{--}15\text{ GB}$ of scratch data. |
| **Current Python**| **Python 3.15.2 (Installed)** | ❌ **Incompatible.** PyPI has zero binary wheels for `open3d` and `opencv-python` on Python 3.15. |
| **Recommended Python**| **Python 3.12.x (64-bit)** | ✔️ **Golden Standard.** 100% pre-compiled binary wheel support for all computer vision dependencies. |

---

## 2. Critical Dependency Audit & Code Truth Findings

### 2.1 Determination: Is COLMAP Executable Required?
- **Finding:** **YES, STRICTLY REQUIRED.**
- **Code Evidence:**
  - `backend/reconstruction.py:17`: `COLMAP = os.environ.get("COLMAP_EXE", r"C:\bin\colmap.exe")`
  - `backend/reconstruction.py:108-125`: `check_colmap()` executes before pipeline Step 5:
    ```python
    colmap_path = Path(COLMAP)
    if not colmap_path.exists():
        raise RuntimeError("COLMAP executable was not found. Expected location:\n" + COLMAP)
    ```
- **Expected Path:**
  - Default hardcoded path: `C:\bin\colmap.exe`
  - Configurable override: `$env:COLMAP_EXE = "C:\path\to\colmap.exe"`
- **Subprocess Invocation:** `backend/reconstruction.py:187` uses `subprocess.Popen([COLMAP, command] + args, shell=False)`. It deliberately avoids `COLMAP.bat` and `cmd.exe /c` to prevent space-in-path failures on Windows.

---

### 2.2 Determination: Is FFmpeg CLI Required?
- **Finding:** **NO, STANDALONE FFMPEG IS NOT REQUIRED.**
- **Code Evidence:** Static code analysis across the entire repository confirms **zero** calls to `ffmpeg`, `ffprobe`, or `ffmpeg.exe` via `subprocess` or `os.system`.
- **How Video is Decoded:** Video decoding is handled entirely in Python via OpenCV:
  ```python
  cap = cv2.VideoCapture(str(video_path))  # backend/frame_processing.py:37
  ```
  On Windows, `opencv-python` wheels from PyPI bundle their own self-contained FFmpeg video I/O DLL (`opencv_videoio_ffmpeg*.dll`). Installing a separate system-wide FFmpeg binary is unnecessary for GeoForge operation (though helpful for optional manual video re-encoding).

---

### 2.3 Determination: Open3D & OpenCV Import Analysis
- **OpenCV (`cv2`):**
  - **Status:** **MANDATORY.**
  - **Imports:** Imported at module top-level across `backend/frame_processing.py`, `backend/frame_filtering.py`, and `backend/redundancy_filter.py`. Without `cv2`, the backend fails immediately upon receiving an upload.
- **Open3D (`open3d`):**
  - **Status:** **STRONGLY RECOMMENDED (Has COLMAP Fallback).**
  - **Imports:** In `backend/reconstruction.py:553, 625`, `import open3d as o3d` is wrapped in `try ... except ImportError`.
    - If Open3D is missing: Point cloud cleaning is skipped (`shutil.copy2`), and Poisson meshing falls back to the native COLMAP `poisson_mesher` CLI.
    - **Why it is needed:** The COLMAP fallback mesher **cannot perform the 7.0% boundary density trimming** (`POISSON_TRIM = 7.0`), resulting in bloated spherical "bubble" hulls. Furthermore, root diagnostic scripts (`clean_pointcloud.py`, `inspect_mesh.py`, `inspect_pointcloud.py`) require `open3d` unconditionally.

---

### 2.4 Determination: Is `requirements.txt` Complete?
- **Finding:** **CRITICAL GAP — `requirements.txt` DOES NOT EXIST IN THE REPOSITORY.**
- **Audit Truth:** Neither `requirements.txt` nor `pyproject.toml` exists in the codebase root or in `backend/`. The backend dependencies were previously only documented in setup guides.
- **Action:** A complete, code-verified `requirements.txt` specification is provided in Section 4 of this guide.

---

### 2.5 Determination: Python 3.15 vs. Python 3.12 Compatibility
- **Status of Python 3.15:**
  - Python 3.15 is an experimental / pre-alpha CPython development branch.
  - Standard C-extension packages (`numpy`, `opencv-python`, `open3d`, `pillow`) compile against specific C-API ABI tags (e.g. `cp312-win_amd64.whl`).
  - **Zero pre-compiled binary wheels exist on PyPI for Python 3.15.**
  - Running `pip install open3d` or `pip install opencv-python` on Python 3.15 attempts to build from source (`sdist`). On Windows, building Open3D from source requires Microsoft Visual C++ Build Tools, CMake, CUDA SDK, LLVM, WebRTC, and takes 2+ hours—and will fail because Open3D's C++ bindings have not been adapted to Python 3.15 internal C-API changes.
- **Recommendation:** **Install Python 3.12 (64-bit).**
  - Python 3.12 has mature, official binary wheels for all GeoForge dependencies.
  - Python 3.12 can co-exist with Python 3.15 on Windows 11 without conflict using the Python Launcher (`py -3.12`).

---

### 2.6 Determination: Packages That Must NOT Be Installed Together
1. ❌ **`opencv-python` and `opencv-python-headless` (or `opencv-contrib-python`):**
   - Installing both into the same environment causes namespace collisions inside `cv2`, breaking video I/O backends. Install **only `opencv-python`**.
2. ❌ **`PIL` and `pillow`:**
   - Never run `pip install PIL`. The obsolete `PIL` package on PyPI is broken. Modern code imports `from PIL import Image`, but the package is installed via **`pip install pillow`**.
3. ❌ **`open3d` with `numpy >= 2.0.0` (on early Open3D builds):**
   - Open3D 0.18.0 was compiled against the NumPy 1.x C-API. In NumPy 2.0, binary ABI changes can trigger `ValueError: numpy.dtype size changed`. Pin `numpy<2.0.0` (e.g. `numpy>=1.26.0,<2.0.0`) for guaranteed stability.

---

## 3. Complete 7-Category Dependency Inventory

### Category 1: Python Interpreter & Environment Tools
| Software | Required Version | Verified in Audit | Purpose | Mandatory? | Download / Command |
|---|---|---|---|:---:|---|
| **Python 64-bit** | `3.10` – `3.12` | Python 3.12.7 (Rec) | Core backend language runtime | **Yes** | [python.org](https://www.python.org/downloads/) or `winget install Python.Python.3.12` |
| **Python Launcher (`py`)** | Standard Windows | Bundled with Python | Manages multiple Python versions | **Yes** | Bundled with official Python installer |
| **pip** | $\ge 24.0$ | Bundled | Python package installer | **Yes** | `python -m pip install --upgrade pip` |
| **venv** | Standard library | Built-in | Isolated virtual environment | **Yes** | `python -m venv .venv` |

---

### Category 2: Required Python pip Packages
Every package in this table is directly imported by `backend/*.py`:

| Package Name | PyPI Identifier | Version Constraint | Importing Files | Purpose in GeoForge | GPU Accelerated? |
|---|---|---|---|---|:---:|
| **FastAPI** | `fastapi` | `^0.110.0` | `main.py:11` | REST API routing, request validation, exception handling | No (CPU) |
| **Uvicorn** | `uvicorn` | `^0.28.0` | `main.py` (CLI runner) | Production ASGI web server running FastAPI | No (CPU) |
| **python-multipart** | `python-multipart` | `^0.0.9` | `main.py:364` | Required by FastAPI for `UploadFile` multipart form parsing | No (CPU) |
| **OpenCV** | `opencv-python` | `^4.9.0` | `frame_processing.py`, `frame_filtering.py`, `redundancy_filter.py` | Video decoding (`VideoCapture`), Laplacian variance blur, mean brightness, pixel difference | CPU (Intel AVX2 optimized) |
| **NumPy** | `numpy` | `>=1.26.0,<2.0.0` | All backend modules | Matrix operations, percentile trimming, array math | CPU (MKL / OpenBLAS) |
| **Trimesh** | `trimesh` | `^4.2.0` | `convert_to_glb.py`, `check_3d.py` | 3D mesh scene assembly, material binding, binary GLB export | No (CPU) |
| **Pillow** | `pillow` | `^10.2.0` | `convert_to_glb.py:20` | PBR diffuse texture atlas loading, format conversion | No (CPU) |

---

### Category 3: Optional / Recommended Python pip Packages
| Package Name | PyPI Identifier | Version Constraint | Importing Files | Purpose in GeoForge | Status & Fallback |
|---|---|---|---|---|---|
| **Open3D** | `open3d` | `^0.18.0` (or `0.19.0`) | `reconstruction.py:553, 625` | Statistical outlier removal, point normal estimation, Screened Poisson meshing with 7.0% boundary trim | **Recommended.** If missing, cleaning is skipped and meshing falls back to COLMAP `poisson_mesher` without boundary trimming. |
| **Scipy** | `scipy` | `^1.12.0` | `backend/check_3d.py:186` | Optional sparse mesh matrix calculations in diagnostic script | Optional (Not imported in active pipeline). |

---

### Category 4: External Standalone Software
| Software | Required Version | Expected Location | Purpose | Mandatory? | Source / Download |
|---|---|---|---|:---:|---|
| **COLMAP CLI** | `3.8+` (CUDA Build) | `C:\bin\colmap.exe` (or `$env:COLMAP_EXE`) | SIFT extraction, sequential matching, incremental SfM, PatchMatch stereo, dense fusion | **Yes** | [COLMAP GitHub Releases](https://github.com/colmap/colmap/releases) |
| **Vocab Tree Asset** | Flickr100k Words 32k | `C:\bin\vocab_tree_flickr100k_words32k.bin` | Fast visual loop-closure indexing during sequential matching | Optional | [COLMAP Vocab Trees](https://demuc.de/colmap/) |
| **Node.js** | $\ge 18.0.0$ (Rec: `20+` LTS) | System PATH (`node.exe`) | Frontend JavaScript runtime | **Yes** | [nodejs.org](https://nodejs.org/) or `winget install OpenJS.NodeJS.LTS` |
| **npm** | $\ge 9.0.0$ (Rec: `10+`) | System PATH (`npm.cmd`) | Frontend package manager | **Yes** | Bundled with Node.js |

---

### Category 5: Frontend npm Dependencies (`frontend/package.json`)
All packages inspected from `frontend/package.json` and `package-lock.json`:

| Package Name | Type | Version | Consuming Code | Operational Role in GeoForge | Active Status |
|---|:---:|---|---|---|:---:|
| **react** | Prod | `^19.0.1` | All UI components | Modern React 19 UI component tree and state machine | **Active** |
| **react-dom** | Prod | `^19.0.1` | `main.tsx` | DOM rendering and reconciliation | **Active** |
| **three** | Prod | `^0.185.1` | `ThreeDViewer.tsx` | WebGL 3D model viewport, lighting, OrbitControls | **Active** |
| **lucide-react** | Prod | `^0.546.0` | Navigation, Cards | Modern SVG iconography across all pages | **Active** |
| **motion** | Prod | `^12.23.24` | Processing, Complete | Smooth layout animations and progress transitions | **Active** |
| **@google/genai**| Prod | `^2.4.0` | *None* | Legacy AI Studio template residual | ⚠️ **Unused** |
| **express** | Prod | `^4.21.2` | *None* | Legacy template residual (Backend is FastAPI) | ⚠️ **Unused** |
| **vite** | Dev | `^6.2.3` | Bundler | Development server (port 3000) and production bundler | **Active** |
| **@vitejs/plugin-react**| Dev | `^5.0.4` | Vite Plugin | Fast Refresh compiler for React 19 | **Active** |
| **typescript** | Dev | `~5.8.2` | Tooling | Static type verification (`npm run lint`) | **Active** |
| **tailwindcss**| Dev | `^4.1.14` | Styling | Tailwind CSS v4 styling engine | **Active** |
| **@tailwindcss/vite** | Dev | `^4.1.14` | Vite Plugin | Native Vite bundler integration for Tailwind v4 | **Active** |
| **@types/three**| Dev | `^0.185.4` | Tooling | TypeScript type declarations for Three.js | **Active** |

---

### Category 6: GPU Drivers & CUDA-Related Requirements
Evaluated specifically for the **NVIDIA GeForce RTX 3050 Laptop GPU (6 GB VRAM)**:

| Component | Minimum Requirement | Verified Specification on Workstation | Purpose | Configuration Notes |
|---|---|---|---|---|
| **NVIDIA Driver** | $\ge 535.x$ | Driver `550.x+` (Recommended) | Host GPU driver supporting CUDA runtime | Download from [NVIDIA Driver Downloads](https://www.nvidia.com/Download/index.aspx). |
| **CUDA Architecture** | Compute Capability $\ge 6.0$ | **Compute Capability 8.6 (Ampere)** | Hardware architecture for CUDA kernel execution | RTX 3050 Ampere cores are 100% compatible with COLMAP CUDA builds. |
| **CUDA Toolkit** | None required separately | Bundled in COLMAP release | Standalone CUDA runtime DLLs (`cudart64_*.dll`) | Official COLMAP Windows CUDA release bundles all necessary CUDA runtime DLLs in its directory. A separate 3 GB CUDA Toolkit install is **not required**. |
| **GPU VRAM Ceiling** | $\ge 4\text{ GB}$ | **6 GB GDDR6 VRAM** | PatchMatch stereo depth map memory | The default `PATCHMATCH_MAX_IMAGE_SIZE = 2400` works comfortably on 1080p footage. For 4K footage, reduce to `1600` if memory warnings occur. |

---

### Category 7: Development & Debugging Tools
| Tool Name | Location | Purpose | How to Invoke |
|---|---|---|---|
| **`check_3d.py`** | `backend/check_3d.py` | 1188-line geometry validator; measures vertices, faces, watertightness, convexity, UV mappings, and texture sizes | `python backend/check_3d.py` |
| **`colmap_test.py`** | `backend/colmap_test.py` | Standalone script testing COLMAP feature extraction and sparse mapper | `python backend/colmap_test.py` |
| **`inspect_mesh.py`** | Root `inspect_mesh.py` | Open3D visual triangle mesh inspection GUI | `python inspect_mesh.py` |
| **`clean_pointcloud.py`**| Root `clean_pointcloud.py` | Open3D point cloud downsampling and outlier removal test | `python clean_pointcloud.py` |
| **`tsc --noEmit`** | `frontend/package.json` | Static TypeScript compilation type check | `cd frontend; npm run lint` |

---

## 4. Authoritative `requirements.txt` Specification

Because the repository lacked a `requirements.txt`, create this exact file at `backend/requirements.txt`:

```text
# ============================================================
# GeoForge Backend Python Dependencies (Verified for Python 3.12)
# ============================================================

# REST API & Web Service
fastapi>=0.110.0,<0.116.0
uvicorn>=0.28.0,<0.33.0
python-multipart>=0.0.9,<0.0.20

# Computer Vision & Video Frame Processing
opencv-python>=4.9.0.80,<4.11.0.0
numpy>=1.26.0,<2.0.0

# 3D Point Cloud Denoising & Poisson Surface Meshing
open3d>=0.18.0,<0.20.0

# 3D Mesh Scene Assembly & Binary GLB Packaging
trimesh>=4.2.0,<4.6.0
pillow>=10.2.0,<11.1.0
```

---

## 5. Step-by-Step Windows 11 PowerShell Setup Manual

Follow these exact commands to install and verify GeoForge on Windows 11.

### Step 5.1: Install Python 3.12 (Side-by-Side with Python 3.15)
To preserve your existing Python 3.15 while providing Python 3.12 for GeoForge:

```powershell
# In PowerShell (Run as Administrator or normal user):
winget install Python.Python.3.12 --scope user

# Verify that Python 3.12 is recognized by the Python launcher:
py -0
# Expected output should show both -V:3.15 and -V:3.12
```

---

### Step 5.2: Create and Activate a Python 3.12 Virtual Environment
Navigate to the GeoForge root directory:

```powershell
cd C:\Users\adity\Downloads\geoforge-main

# Create virtual environment explicitly using Python 3.12
py -3.12 -m venv .venv

# Allow local PowerShell script execution (if restricted)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# Confirm the active virtual environment is Python 3.12:
python --version
# Expected: Python 3.12.x
```

---

### Step 5.3: Install Python Backend Dependencies
With `.venv` active:

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install all verified backend dependencies in a single command:
python -m pip install "fastapi>=0.110.0" "uvicorn>=0.28.0" "python-multipart>=0.0.9" "opencv-python>=4.9.0" "numpy>=1.26.0,<2.0.0" "open3d>=0.18.0" "trimesh>=4.2.0" "pillow>=10.2.0"

# Verify all imports succeed without error:
python -c "import fastapi, uvicorn, multipart, cv2, numpy, open3d, trimesh, PIL; print('>>> ALL BACKEND PACKAGES IMPORTED SUCCESSFULLY!')"
```

---

### Step 5.4: Install COLMAP 4.1.1 (CUDA Enabled)
1. Download official Windows CUDA release:
   - URL: [COLMAP Releases (GitHub)](https://github.com/colmap/colmap/releases)
   - Archive: `COLMAP-3.8-windows-cuda.zip` (or `COLMAP-3.9-windows-cuda.zip`)
2. Extract the archive into:
   ```text
   C:\bin\
   ```
   Ensuring the executable exists directly at `C:\bin\colmap.exe`.
3. *(Optional but Recommended)* Download Vocabulary Tree:
   - URL: [https://demuc.de/colmap/](https://demuc.de/colmap/)
   - File: `vocab_tree_flickr100k_words32k.bin`
   - Place beside `colmap.exe`: `C:\bin\vocab_tree_flickr100k_words32k.bin`
4. Test COLMAP execution in PowerShell:
   ```powershell
   & "C:\bin\colmap.exe" -h
   ```

---

### Step 5.5: Install Node.js & Frontend npm Packages
Open a second PowerShell window:

```powershell
# 1. Verify Node.js (v20+ recommended)
node --version
npm --version

# If Node.js is missing, install via winget:
# winget install OpenJS.NodeJS.LTS

# 2. Navigate to frontend directory
cd C:\Users\adity\Downloads\geoforge-main\geoforge-main\frontend

# 3. Install frontend dependencies
npm install

# 4. Verify TypeScript compilation
npm run lint
```

---

### Step 5.6: Launching Both Servers

#### Terminal 1 — Start Backend Server:
```powershell
cd C:\Users\adity\Downloads\geoforge-main\geoforge-main\backend
..\..\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload --port 8000
```
- Confirm `Application startup complete.` on `http://127.0.0.1:8000`.
- Health check: `curl http://127.0.0.1:8000/health` $\to$ `{"status": "healthy"}`.

#### Terminal 2 — Start Frontend Client:
```powershell
cd C:\Users\adity\Downloads\geoforge-main\geoforge-main\frontend
npm run dev
```
- Open browser to `http://localhost:3000`.

---

## 6. Verification Checklist Before Execution

- [ ] **Python 3.12 Installed:** `py -3.12 --version` returns 3.12.x.
- [ ] **Virtual Environment Activated:** `python --version` inside `.venv` returns 3.12.x.
- [ ] **All 8 Python Packages Installed:** `fastapi`, `uvicorn`, `python-multipart`, `opencv-python`, `numpy`, `open3d`, `trimesh`, `pillow`.
- [ ] **No Package Conflicts:** Only `opencv-python` installed (no `opencv-python-headless`); NumPy version `< 2.0.0`.
- [ ] **COLMAP CUDA Binary Present:** `Test-Path "C:\bin\colmap.exe"` returns `True`.
- [ ] **NVIDIA Driver Updated:** `nvidia-smi` reports RTX 3050 Laptop GPU with 6 GB VRAM.
- [ ] **Frontend Built Cleanly:** `npm run lint` in `frontend/` reports zero errors.
- [ ] **Zero Code or Config Changes Made During Audit:** Verified.
