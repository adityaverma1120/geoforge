# GeoForge — Environment Setup & Toolchain Manual

> **Document:** `docs/ENVIRONMENT_SETUP.md`  
> **Status:** Code-Verified Workstation Environment Specification (Phase 2 Complete)  
> **Target Audience:** Developers, DevOps Engineers, and System Evaluators  
> **Host OS:** Windows 11 Home (64-bit, Build 26100)  
> **Target Hardware:** Intel Core i5-13450HX, NVIDIA RTX 3050 Laptop GPU (6 GB VRAM), 16 GB RAM

---

## 1. Prerequisites & Version Requirements

| Software / Tool | Required Version | Installed / Verified Version | Purpose in GeoForge |
|---|---|---|---|
| **Python** | 3.12.x (64-bit) | `3.12.8` | Core backend runtime and scientific package host. |
| **Virtual Environment** | Python venv | `.venv` (Python 3.12.8) | Isolated project dependency container. |
| **Node.js** | v20.19.0+ or v22.12.0+ | `v22.14.0 LTS` | Frontend build engine and Vite bundler host. |
| **npm** | 10.x+ | `10.9.2` | Node package manager. |
| **COLMAP** | 3.9.x+ (CUDA) | `3.9.1 (CUDA enabled)` | Structure-from-Motion (SfM) and Dense Stereo (MVS). |
| **Vocabulary Tree** | 32K visual words | `vocab_tree_flickr100K_words32K.bin` | Fast sequential matching with loop closure. |
| **FFmpeg** | 7.x+ or 9.x+ | `9.0.2 Essentials` | Video metadata inspection and stream probe. |
| **Git** | 2.4x+ | `2.47.1` | Source code control and submodule support. |

---

## 2. Directory Layout & Storage

The system uses standard user-space paths that require **no administrator privileges** for ongoing development or pipeline execution:

- **GeoForge Workspace:** `c:\Users\adity\Downloads\geoforge-main\`
- **Application Root:** `c:\Users\adity\Downloads\geoforge-main\geoforge-main\`
- **Python 3.12:** `C:\Users\adity\AppData\Local\Programs\Python\Python312\`
- **COLMAP (CUDA):** `C:\Users\adity\AppData\Local\Programs\COLMAP\bin\colmap.exe`
- **Node.js:** `C:\Users\adity\AppData\Local\Programs\nodejs\node.exe`
- **FFmpeg:** `C:\Users\adity\AppData\Local\Programs\ffmpeg\bin\ffmpeg.exe`
- **Git:** `C:\Users\adity\AppData\Local\Programs\Git\cmd\git.exe`

---

## 3. Environment Variables Configuration

The following user environment variables must be present:

```powershell
# Set persistent User environment variables
[Environment]::SetEnvironmentVariable("COLMAP_EXE", "C:\Users\adity\AppData\Local\Programs\COLMAP\bin\colmap.exe", "User")
[Environment]::SetEnvironmentVariable("COLMAP_VOCAB_TREE", "C:\Users\adity\AppData\Local\Programs\COLMAP\vocab_tree_flickr100k_words32k.bin", "User")

# Add tools to User PATH
$newPaths = @(
    "C:\Users\adity\AppData\Local\Programs\Python\Python312",
    "C:\Users\adity\AppData\Local\Programs\Python\Python312\Scripts",
    "C:\Users\adity\AppData\Local\Programs\COLMAP\bin",
    "C:\Users\adity\AppData\Local\Programs\nodejs",
    "C:\Users\adity\AppData\Local\Programs\ffmpeg\bin",
    "C:\Users\adity\AppData\Local\Programs\Git\cmd"
)
```

The application loads environment variables at runtime from `backend/.env`:
```ini
COLMAP_EXE=C:\Users\adity\AppData\Local\Programs\COLMAP\bin\colmap.exe
COLMAP_VOCAB_TREE=C:\Users\adity\AppData\Local\Programs\COLMAP\vocab_tree_flickr100k_words32k.bin
HOST=0.0.0.0
PORT=8000
```

---

## 4. Step-by-Step Installation & Verification Commands

### Step 1: Virtual Environment Setup
```powershell
cd c:\Users\adity\Downloads\geoforge-main
& "C:\Users\adity\AppData\Local\Programs\Python\Python312\python.exe" -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 2: Install Python Dependencies
```powershell
python -m pip install --upgrade pip
python -m pip install -r geoforge-main\backend\requirements.txt
```

Verified `requirements.txt`:
```text
fastapi>=0.110.0,<1.0.0
uvicorn[standard]>=0.28.0,<1.0.0
python-multipart>=0.0.9
opencv-python>=4.9.0,<5.0.0
numpy>=1.26.0,<2.0.0
open3d>=0.18.0
trimesh>=4.2.0
pillow>=10.2.0
scipy>=1.12.0
httpx>=0.28.0
```

### Step 3: Install Frontend Dependencies
```powershell
cd geoforge-main\frontend
npm install --no-audit
npm run lint    # tsc --noEmit
npm run build   # vite build
```

---

## 5. System Verification Probe

To verify the entire development stack in a single automated command:
```powershell
& "c:\Users\adity\Downloads\geoforge-main\.venv\Scripts\python.exe" -c "
import sys, os
import fastapi, uvicorn, multipart, cv2, numpy, open3d, trimesh, PIL, scipy, httpx
import subprocess

print('Python Version:', sys.version)
print('OpenCV Version:', cv2.__version__)
print('NumPy Version: ', numpy.__version__)
print('Open3D Version:', open3d.__version__)
print('Trimesh Version:', trimesh.__version__)

colmap = os.environ.get('COLMAP_EXE', r'C:\Users\adity\AppData\Local\Programs\COLMAP\bin\colmap.exe')
res = subprocess.run([colmap, 'help'], capture_output=True, text=True)
print('COLMAP Help Returncode:', res.returncode)
assert res.returncode == 0, 'COLMAP verification failed'

ffmpeg = r'C:\Users\adity\AppData\Local\Programs\ffmpeg\bin\ffmpeg.exe'
res_ff = subprocess.run([ffmpeg, '-version'], capture_output=True, text=True)
print('FFmpeg Version Returncode:', res_ff.returncode)
assert res_ff.returncode == 0, 'FFmpeg verification failed'

print('ALL ENVIRONMENT VERIFICATIONS PASSED SUCCESSFULLY!')
"
```

