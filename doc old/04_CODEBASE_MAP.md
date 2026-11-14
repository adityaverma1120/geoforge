# 04 — Codebase map

```text
geoforge-main/
├── README.md                         # Minimal repository README in supplied archive
├── backend/
│   ├── main.py                       # FastAPI routes, job lifecycle, orchestration
│   ├── frame_processing.py           # Video-to-frame extraction
│   ├── frame_filtering.py            # Sharpness/brightness filter
│   ├── redundancy_filter.py           # Similar-frame reduction
│   ├── reconstruction.py              # COLMAP + dense/mesh pipeline
│   ├── convert_to_glb.py              # Textured model conversion to GLB
│   ├── check_3d.py                    # Reconstruction/3D checking utilities
│   └── colmap_test.py                 # COLMAP testing helper
├── frontend/
│   ├── package.json                  # Scripts and JS dependencies
│   ├── vite.config.ts                # Vite, React, Tailwind plugin, chunking
│   ├── .env.example                  # Frontend environment example
│   └── src/
│       ├── App.tsx                   # Main UI state, upload/poll/result flow
│       ├── types.ts                  # Frontend job/error/pipeline types
│       ├── services/api.ts            # HTTP upload/status/model URL helpers
│       ├── components/
│       │   ├── ThreeDViewer.tsx       # Three.js GLB viewer
│       │   ├── ErrorView.tsx          # Error presentation
│       │   ├── DiagnosticsAccordion.tsx
│       │   ├── Header.tsx
│       │   └── Footer.tsx
│       └── pages/
│           ├── HomePage.tsx
│           ├── HowItWorksPage.tsx
│           ├── UploadPage.tsx
│           ├── ProcessingPage.tsx
│           ├── CompletePage.tsx
│           └── ResultPage.tsx
├── src/                              # Standalone/manual frame scripts (not the API worker)
│   ├── extract_frames.py
│   ├── analyze_sharpness.py
│   ├── detect_blur.py
│   └── remove_redundant.py
├── clean_pointcloud.py               # Standalone point-cloud cleanup utility
├── inspect_mesh.py                   # Local mesh inspection script
└── inspect_pointcloud.py              # Local point-cloud inspection script
```

Note: there are similarly named scripts in `src/` and `backend/`. The backend pipeline imports backend modules. The root-level `src/` scripts are separate/manual workflows and should not be confused with the active FastAPI pipeline.
