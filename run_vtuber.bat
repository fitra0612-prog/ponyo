@echo off
title AI VTuber Bot - Live Stream Assistant
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment tidak ditemukan.
    pause
    exit /b 1
)

echo ===================================================
echo   Menjalankan AI VTuber Live Stream Bot...
echo ===================================================
echo.
set "YOUTUBE_VIDEO_ID="
set /p "YOUTUBE_VIDEO_ID=Masukkan YouTube Video ID (Enter = mode offline): "
if defined YOUTUBE_VIDEO_ID (
    echo [CHAT] Mode YouTube aktif untuk Video ID yang diberikan.
) else (
    echo [CHAT] Tidak ada Video ID. Mode offline/terminal aktif tanpa request YouTube.
)
echo.
".venv\Scripts\python.exe" main.py %*

if errorlevel 1 (
    echo.
    echo Program berhenti dengan error.
    pause
)
