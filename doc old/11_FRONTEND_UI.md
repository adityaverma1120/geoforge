# 11 — Frontend and UI

## Application structure
`App.tsx` composes Header/Footer, pages, and the main workflow state. Page components include Home, How It Works, Upload, Processing, Complete, and Result.

## Main interactions
- Upload selection and start action
- Upload percentage display
- Job status polling with retry/backoff behavior in app logic
- Processing screen / stage visualization
- Completion state with model URL
- 3D model load progress and error display
- Error categories and diagnostic details
- Help/capture tips

## Viewer
Three.js is used in `ThreeDViewer.tsx`. The viewer handles GLB loading, progress, and some model validity checks. The presence of code does not establish a polished or bug-free viewer. Test:
- orbit/zoom/pan controls
- initial camera framing and centering
- responsive sizing
- loading progress
- empty/invalid GLB handling
- component unmount and renderer cleanup
- browser GPU / WebGL compatibility

## Frontend scripts
From `frontend/package.json`:
- `npm run dev`: Vite on port 3000, host `0.0.0.0`
- `npm run build`: Vite production build
- `npm run preview`: Vite preview
- `npm run lint`: TypeScript check (`tsc --noEmit`)
- `npm run clean`: shell command using `rm -rf`; not Windows CMD-native and should be reviewed before use on Windows.

## Environment
`VITE_API_URL` configures the backend base URL. `.env.example` is the example source; copy to `.env.local` or a suitable Vite environment file and ensure the value is appropriate for the environment.
