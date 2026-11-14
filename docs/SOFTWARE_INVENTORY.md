# Software & External Dependency Inventory — GeoForge

> **Document:** `docs/SOFTWARE_INVENTORY.md`  
> **Status:** Canonical Verified Software Inventory  
> **Target Version:** GeoForge v1.0.0 (SIH 2026 / NTRO Edition)  
> **Last Verified:** 2026-11-11  
> **Related Documents:** [`docs/TECH_STACK.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/TECH_STACK.md), [`docs/SETUP.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/SETUP.md), [`docs/CONFIGURATION.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/CONFIGURATION.md)

---

## 1. System Runtimes & External CLI Tools

| Component | Category | Exact / Minimum Version | Verified Version in Dev | Required By | Verification Command | Mandatory? |
|---|---|:---:|:---:|---|---|:---:|
| **Python** | Runtime | `3.10` – `3.12` | `3.12.3` (64-bit) | Backend & CV Pipeline | `python --version` | **Yes** |
| **Node.js** | Runtime | `18.0.0+` (Rec: `20+` / `24.x`) | `v20.x` / `v24.x` | Frontend Build & Dev | `node --version` | **Yes** |
| **npm** | Package Manager | `9.0.0+` (Rec: `10+` / `11.x`) | `10.x` / `11.x` | Frontend Dependencies | `npm --version` | **Yes** |
| **COLMAP** | External Binary CLI | `3.8+` (CUDA Build) | `4.1.1` (CUDA 12.x) | SfM & Dense MVS | `& "C:\bin\colmap.exe" -h` | **Yes** |
| **NVIDIA Driver** | GPU Driver | CUDA 11.8+ / 12.x | Driver `550.x+` | GPU Stereo Matching | `nvidia-smi` | Recommended (CPU fallback slow) |
| **Vocab Tree Asset** | Binary Data File | Flickr100k Words 32k | Optional download | Loop-Closure Matching | File existence check | Optional |

---

## 2. Python Backend Dependencies (`backend/`)

| Package Name | Minimum Version | Verified Version | Primary Module Consumer | Purpose & Architectural Role | Mandatory? |
|---|:---:|:---:|---|---|:---:|
| **fastapi** | `^0.110.0` | `0.110.0+` | `main.py` | Asynchronous REST API routing, HTTP request validation, status endpoints. | **Yes** |
| **uvicorn** | `^0.28.0` | `0.28.0+` | `main.py` | High-performance ASGI server for FastAPI. | **Yes** |
| **python-multipart** | `^0.0.9` | `0.0.9+` | `main.py` | Streaming multipart/form-data video upload parsing. | **Yes** |
| **opencv-python** | `^4.9.0` | `4.9.0+` | `frame_processing.py`, `frame_filtering.py`, `redundancy_filter.py` | Video decoding (`VideoCapture`), Laplacian variance blur filtering, mean luminance, frame difference calculations. | **Yes** |
| **numpy** | `^1.26.0` / `^2.0` | `1.26.4` / `2.0+` | All backend modules | Matrix math, image arrays, percentile threshold calculations, vector math. | **Yes** |
| **open3d** | `^0.18.0` | `0.18.0` / `0.19.0` | `reconstruction.py` | Statistical outlier removal, point cloud normal estimation, Screened Poisson surface reconstruction. | Recommended (Has COLMAP fallback) |
| **trimesh** | `^4.2.0` | `4.2.0+` | `convert_to_glb.py`, `check_3d.py` | Polygonal mesh concatenation, scene assembly, texture attachment, GLB export. | **Yes** |
| **pillow (`PIL`)** | `^10.2.0` | `10.2.0+` | `convert_to_glb.py` | PBR material diffuse texture loading, resizing, format conversion. | **Yes** |

---

## 3. Node.js Frontend Dependencies (`frontend/package.json`)

### 3.1 Production Runtime Dependencies
| Package Name | Declared Version | Consuming Components | Operational Role in GeoForge | Active Status |
|---|:---:|---|---|:---:|
| **react** | `^19.0.1` | All pages & components | Modern React 19 UI component framework. | **Active** |
| **react-dom** | `^19.0.1` | `main.tsx` | DOM rendering and reconciliation. | **Active** |
| **three** | `^0.185.1` | `ThreeDViewer.tsx` | WebGL 3D rendering engine, OrbitControls, GLTFLoader, scene lighting. | **Active** |
| **lucide-react** | `^0.546.0` | Navigation, Cards, Actions | Modern SVG iconography across all pages. | **Active** |
| **motion** | `^12.23.24` | Processing & Complete pages | Smooth layout animations and state transition effects. | **Active** |
| **@google/genai** | `^2.4.0` | *None* | Legacy AI Studio starter template residue. Not imported or consumed. | ⚠️ **Unused** |
| **express** | `^4.21.2` | *None* | Legacy Node server starter residue. Not used; backend is FastAPI. | ⚠️ **Unused** |

### 3.2 Development & Tooling Dependencies
| Package Name | Declared Version | Primary Purpose |
|---|:---:|---|
| **vite** | `^6.2.3` | High-speed frontend development server, Hot Module Replacement (HMR), production bundler. |
| **@vitejs/plugin-react**| `^5.0.4` | Vite React compiler and Fast Refresh plugin. |
| **typescript** | `~5.8.2` | Static type analysis and checking (`npm run lint`). |
| **tailwindcss** | `^4.1.14` | Utility-first CSS styling engine (v4 Vite integration). |
| **@tailwindcss/vite** | `^4.1.14` | Native Vite bundler plugin for Tailwind v4. |
| **autoprefixer** | `^10.4.21` | CSS vendor prefix post-processor. |
| **@types/three** | `^0.185.4` | TypeScript type declarations for Three.js. |
| **@types/react** | `^19.2.18` | TypeScript type declarations for React 19. |
| **@types/react-dom** | `^19.2.5` | TypeScript type declarations for React DOM. |
| **@types/node** | `^22.14.0` | TypeScript definitions for Node runtimes. |
| **esbuild** | `^0.25.0` | Ultra-fast JS/TS transform and minification engine inside Vite. |
| **dotenv** | `^17.2.3` | Environment file parser. |
| **tsx** | `^4.21.0` | TypeScript execute runner for development scripts. |

---

## 4. Vocabulary Tree Candidate Search Order (`backend/reconstruction.py`)

When feature matching begins, GeoForge attempts to locate the vocabulary tree asset in this specific sequence:
1. `<colmap_dir>/vocab_tree_flickr100k_words32k.bin`
2. `<colmap_dir>/vocab_tree_faiss.bin`
3. `<colmap_dir>/vocab_tree.bin`
4. `C:\bin\vocab_tree_flickr100k_words32k.bin`
5. `backend/assets/vocab_tree_flickr100k_words32k.bin`

If none of these paths exist, COLMAP executes standard sequential feature matching without vocabulary-tree loop closure.
