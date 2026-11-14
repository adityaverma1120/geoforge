@echo off
setlocal enabledelayedexpansion

title GeoForge Photogrammetric 3D Reconstruction System

echo ===============================================================================
echo                GeoForge - Single-Pass Drone Video to 3D Model
echo ===============================================================================
echo.

:: Ensure working directory is project root
cd /d "%~dp0"

:: 1. Virtual Environment Validation
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
    echo [OK] Using dedicated virtual environment: .venv
) else if exist "..\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=..\.venv\Scripts\python.exe"
    echo [OK] Using parent virtual environment: ..\.venv
) else (
    set "PYTHON_EXE=python"
    echo [WARN] Virtual environment .venv not found. Falling back to system python.
)

:: 2. Verify Python dependencies
echo [..] Checking backend environment...
"%PYTHON_EXE%" -c "import fastapi, uvicorn, cv2, numpy, open3d, trimesh, PIL; print('   - Core dependencies verified.')"
if %errorlevel% neq 0 (
    echo [ERROR] Required Python packages missing. Please install backend/requirements.txt.
    pause
    exit /b 1
)

:: 3. Check / build frontend assets if missing
if not exist "frontend\dist\index.html" (
    echo [..] Compiled frontend bundle not found. Building with npm...
    if exist "frontend\package.json" (
        cd frontend
        call npm run build
        cd ..
    )
)

if exist "frontend\dist\index.html" (
    echo [OK] Production frontend bundle ready in frontend\dist.
) else (
    echo [WARN] Frontend bundle missing. API will run in headless mode.
)

:: 4. Check COLMAP and FFmpeg availability
"%PYTHON_EXE%" -c "
import os, shutil
colmap = os.environ.get('COLMAP_EXE', r'C:\Users\adity\AppData\Local\Programs\COLMAP\bin\colmap.exe')
ffmpeg = os.environ.get('FFMPEG_EXE', shutil.which('ffmpeg') or r'C:\Users\adity\AppData\Local\Programs\ffmpeg\bin\ffmpeg.exe')
print('   - COLMAP executable:', 'Found' if os.path.exists(colmap) else 'Not Found')
print('   - FFmpeg executable:', 'Found' if os.path.exists(ffmpeg) else 'Not Found')
"

:: 5. Launch Browser
echo.
echo [..] Launching default web browser to http://localhost:8000 ...
start "" "http://localhost:8000"

:: 6. Launch Unified Uvicorn Server (FastAPI + Static SPA)
echo.
echo ===============================================================================
echo   GeoForge server running on http://localhost:8000 (0.0.0.0:8000)
echo   Press Ctrl+C to terminate the application.
echo ===============================================================================
echo.

"%PYTHON_EXE%" -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000

pause

