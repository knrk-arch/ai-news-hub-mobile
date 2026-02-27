@echo off
setlocal
cd /d "%~dp0"

echo ===================================================
echo AI News Hub - The Daily 3 Curation Engine
echo ===================================================
echo.
echo Running powerful NLP background generation...
echo This process will evaluate hundreds of articles,
echo translate them safely, and generate your curated feed.
echo.

if not exist ".venv" (
    echo [ERROR] Virtual environment not found. Please run StartMobileApp.bat first to initialize.
    pause
    exit /b
)

call .venv\Scripts\activate.bat

python generate_curation.py

echo.
echo ===================================================
echo Curation Complete! You can now run StartMobileApp.bat
echo for a zero-load, instant startup experience.
echo ===================================================
pause
