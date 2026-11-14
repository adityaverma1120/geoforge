# 16 — Error handling and troubleshooting

## Common failure classes
- Upload network error / backend unavailable
- Unsupported file extension
- Upload too large
- No usable frames after preprocessing
- Fewer than 20 frames remain
- COLMAP path missing or executable cannot start
- COLMAP reconstruction command exits unsuccessfully
- No texture file found
- GLB conversion fails or creates empty file
- Browser cannot load GLB or finds no visible geometry

## Troubleshooting order
1. Confirm backend `/health`.
2. Confirm `VITE_API_URL` matches backend host/port.
3. Inspect backend console logs and job status response.
4. Confirm file extension is supported and input video opens in OpenCV.
5. Confirm COLMAP executable path and required vocabulary assets.
6. Confirm enough frames pass filtering; improve overlap, sharpness, lighting, and camera motion.
7. Check workspace disk space and memory.
8. Verify textured model and texture exist before conversion.
9. Test GLB independently in a GLB viewer, then investigate Three.js camera/scale/materials.

## Avoid misleading fixes
Do not lower thresholds or disable quality checks without understanding their effect. Do not delete a job workspace until logs/artifacts needed for diagnosis have been preserved.
