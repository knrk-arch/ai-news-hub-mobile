@echo off
setlocal
cd /d "%~dp0"

echo =========================================
echo  AI News Hub (Mobile)
echo =========================================
echo.

:: 1. Check if .venv exists, if not create it
if not exist .venv (
    echo [INFO] Python virtual environment (.venv) not found. Creating one now...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment. Ensure Python is installed and added to PATH.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created successfully.
)

:: 2. Activate the virtual environment
echo [INFO] Activating virtual environment...
call .venv\Scripts\activate.bat

:: 3. Install/upgrade dependencies
echo [INFO] Checking dependencies from requirements.txt...
call pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

:: 4. Start the application
echo.
echo [INFO] Starting the Streamlit application...
call python -m streamlit run main.py

pause
