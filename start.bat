@echo off
REM Windows batch script to start backend + frontend locally
REM Requires: Python 3.11+, Node 18+

setlocal enabledelayedexpansion

set HERE=%~dp0
set FRONTEND_DIR=%HERE%frontend
set BACKEND_DIR=%HERE%backend
set DIST_DIR=%FRONTEND_DIR%\dist

echo [1/3] Installing backend deps...
if not exist "%HERE%.venv" (
    python -m venv "%HERE%.venv"
)
call "%HERE%.venv\Scripts\activate.bat"

REM Report Python version and architecture (32/64 bit)
echo Using Python:
"%HERE%.venv\Scripts\python.exe" -c "import sys,struct; print(sys.version.split()[0]+' | '+str(struct.calcsize('P')*8)+'-bit')"

REM Upgrade pip toolchain
python -m pip install -U pip setuptools wheel

REM Prefer binary wheels only to avoid building from source on Windows (numpy/pandas)
set PIP_ONLY_BINARY=:all:
pip install -r "%BACKEND_DIR%\requirements.txt"
if errorlevel 1 (
  echo Failed to install from requirements with wheels-only. Retrying pinned scientific stack...
  pip install numpy==2.2.6 pandas==2.2.3 --only-binary=:all:
)
if errorlevel 1 (
  echo [WARN] Still failed to install scientific stack via wheels.
  echo        Consider installing Microsoft C++ Build Tools or using Docker: docker compose up --build
)

echo [2/3] Building frontend...
cd /d "%FRONTEND_DIR%"
call npm install
call npm run build

REM Runtime environment for backend
set APP_PROGRAM_ENTRYPOINT=mio_runner.py:main
set APP_FRONTEND_DIST_DIR=%DIST_DIR%
set APP_OUTPUT_DIR_BASE=%HERE%data
set APP_ALLOWED_EXTENSIONS=.xlsx
set APP_MAX_FILE_SIZE_MB=50
set APP_JOB_TTL_MINUTES=120
if not exist "%APP_OUTPUT_DIR_BASE%" mkdir "%APP_OUTPUT_DIR_BASE%"

echo [3/3] Starting backend on http://localhost:8080
cd /d "%BACKEND_DIR%"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

pause
