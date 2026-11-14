# Technology Stack — GeoForge

> **Document:** `docs/TECH_STACK.md`  
> **Status:** Canonical Verified Technology Stack  
> **Target Version:** GeoForge v1.0.0 (SIH 2026 / NTRO Edition)  
> **Related Documents:** [`docs/SOFTWARE_INVENTORY.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/SOFTWARE_INVENTORY.md), [`docs/SETUP.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/SETUP.md), [`docs/ARCHITECTURE.md`](file:///c:/Users/adity/Downloads/geoforge-main/geoforge-main/docs/ARCHITECTURE.md)

---

## 1. System Technology Summary

| Layer / Role | Technology | Exact Version (Verified) | Verified Package / Source | Notes & Purpose |
|---|---|:---:|---|---|
| **Frontend Framework** | React | `^19.0.1` | `react`, `react-dom` in `package.json` | Modern component UI with hooks and state routing. |
| **Language (Frontend)**| TypeScript | `~5.8.2` | `typescript` in `package.json` | Strict static typing and interface definitions. |
| **Frontend Build Tool**| Vite | `^6.2.3` | `vite`, `@vitejs/plugin-react ^5.0.4` | Fast HMR dev server (port 3000) and production bundler. |
| **CSS Styling** | Tailwind CSS | `^4.1.14` | `tailwindcss`, `@tailwindcss/vite` | Modern utility-first CSS framework. |
| **3D WebGL Rendering** | Three.js | `^0.185.1` | `three`, `@types/three ^0.185.4` | Renders `.glb` with `GLTFLoader` and `OrbitControls`. |
| **UI Iconography** | Lucide React | `^0.546.0` | `lucide-react` in `package.json` | Vector icon set for UI navigation and status cards. |
| **UI Motion / Anim** | Motion | `^12.23.24`| `motion` in `package.json` | Smooth UI transitions and loading spinner effects. |
| **Backend Framework** | FastAPI | `0.110+` | `fastapi` | High-performance Python ASGI REST API framework. |
| **ASGI Web Server** | Uvicorn | `0.28+` | `uvicorn` | Asynchronous server serving FastAPI on port 8000. |
| **Video Decoding** | OpenCV | `4.9+` | `opencv-python` | Video frame extraction and image filtering (`cv2`). |
| **Numerical Processing**| NumPy | `1.26+` / `2.0+` | `numpy` | Array operations, Laplacian variance, percentile math. |
| **Photogrammetry** | COLMAP | `3.8+` / `4.1.1` | External Binary CLI (`C:\bin\colmap.exe`) | SIFT SfM, PatchMatch MVS, mesh texturing. |
| **Point Cloud / Mesh** | Open3D | `0.18.0+` / `0.19.0` | `open3d` | Statistical outlier removal, Screened Poisson meshing. |
| **3D File Conversion** | Trimesh & Pillow | `4.2+` / `10.2+` | `trimesh`, `pillow` | Assembles OBJ/PLY, binds PBR materials, exports `.glb`. |

---

## 2. Unused / Extraneous Frontend Dependencies

The following packages are currently declared in `frontend/package.json` but have no active references in the GeoForge client code:
- **`@google/genai` (`^2.4.0`):** Added during early AI prototype experimentation; not currently referenced or imported in `frontend/src/`.
- **`express` (`^4.21.2`) & `@types/express` (`^4.17.21`):** Node.js server dependencies; unused because the application relies on Vite for local dev and FastAPI for API delivery.
- *Recommendation:* Retain as non-critical or prune in a future maintenance refactoring to minimize `node_modules` footprint.

---

## 3. Backend Dependency Specification

Because the initial repository archive did not include a frozen `requirements.txt`, the canonical pip installation string for GeoForge backend is:

```bash
python -m pip install fastapi uvicorn python-multipart opencv-python numpy open3d trimesh pillow
```

### Key Python Module Responsibilities
- `fastapi` & `python-multipart`: Streaming multipart video upload reception and OpenAPI schema generation.
- `uvicorn`: ASGI server running the asynchronous event loop.
- `opencv-python`: High-performance video container decoding and frame capture.
- `numpy`: Variance of the Laplacian and percentile calculations.
- `open3d`: KD-tree spatial searches, normal estimation, and Poisson octree solver.
- `trimesh`: 3D geometry manipulation, mesh healing, and binary GLTF 2.0 serialization.
- `pillow`: Texture image decoding, resizing, and PBR diffuse map embedding.

---

## 4. Hardware & Acceleration Architecture

- **CUDA GPU Acceleration:** COLMAP SIFT extraction, sequential matching, and PatchMatch stereo benefit dramatically from NVIDIA CUDA. A GPU with $\ge 6\text{ GB}$ VRAM is strongly recommended.
- **CPU Fallback:** When CUDA is absent, COLMAP automatically runs SIFT and matching on CPU threads (configurable via `OMP_NUM_THREADS`), though processing duration will increase substantially.
