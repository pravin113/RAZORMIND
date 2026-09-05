@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   RazorMind AI -- Production Demo Startup Launcher
echo ============================================================
echo.

set "PROJECT_ROOT=D:\RazorMind"
set "MODEL_PATH=D:\RazorMind\models\Qwen3-8B-Q4_K_M.gguf"
set "BACKEND_DIR=D:\RazorMind\backend"
set "BACKEND_PYTHON=D:\RazorMind\backend\.venv\Scripts\python.exe"
set "FRONTEND_DIR=D:\RazorMind\frontend"

:: -----------------------------------------------------------
:: 1. Validate Pre-requisites
:: -----------------------------------------------------------
echo [CHECK] Validating pre-requisites...

if not exist "%PROJECT_ROOT%" (
    echo [ERROR] Project root not found: %PROJECT_ROOT%
    pause
    exit /b 1
)

if not exist "%MODEL_PATH%" (
    echo [ERROR] Qwen3 model not found: %MODEL_PATH%
    pause
    exit /b 1
)

if not exist "%BACKEND_PYTHON%" (
    echo [ERROR] Backend venv python not found: %BACKEND_PYTHON%
    echo Please run: cd backend ^&^& python -m venv .venv ^&^& .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

if not exist "%FRONTEND_DIR%\package.json" (
    echo [ERROR] Frontend package.json not found: %FRONTEND_DIR%
    pause
    exit /b 1
)

:: Locate llama-server.exe on PATH
set "LLAMA_EXE="
for /f "delims=" %%I in ('where llama-server.exe 2^>nul') do (
    if not defined LLAMA_EXE set "LLAMA_EXE=%%I"
)

if not defined LLAMA_EXE (
    echo [ERROR] llama-server.exe not found on PATH.
    echo Install via: winget install ggml.llamacpp
    pause
    exit /b 1
)

echo [OK] All pre-requisites verified.
echo.

:: -----------------------------------------------------------
:: 2. Launch Qwen3-8B llama-server (Port 8080)
:: -----------------------------------------------------------
netstat -ano 2>nul | findstr /R /C:":8080 .*LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [SKIP] Qwen3 llama-server already running on port 8080.
) else (
    echo [1/3] Starting Qwen3-8B LLM Server on port 8080...
    start "RazorMind - Qwen3 LLM" "%LLAMA_EXE%" -m "%MODEL_PATH%" --port 8080 -c 4096 --host 127.0.0.1
    ping 127.0.0.1 -n 4 >nul
)

:: -----------------------------------------------------------
:: 3. Launch FastAPI Backend (Port 8000)
:: -----------------------------------------------------------
netstat -ano 2>nul | findstr /R /C:":8000 .*LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [SKIP] FastAPI backend already running on port 8000.
) else (
    echo [2/3] Starting FastAPI Backend on port 8000...
    start "RazorMind - FastAPI" /D "%BACKEND_DIR%" "%BACKEND_PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
    ping 127.0.0.1 -n 4 >nul
)

:: -----------------------------------------------------------
:: 4. Launch Frontend Dev Server (Port 5173)
:: -----------------------------------------------------------
netstat -ano 2>nul | findstr /R /C:":5173 .*LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [SKIP] Frontend dev server already running on port 5173.
) else (
    echo [3/3] Starting Frontend on port 5173...
    start "RazorMind - Frontend" /D "%FRONTEND_DIR%" cmd /k npm run dev
    ping 127.0.0.1 -n 3 >nul
)

:: -----------------------------------------------------------
:: 5. Display status
:: -----------------------------------------------------------
echo.
echo ============================================================
echo RazorMind AI started
echo.
echo Qwen3:
echo http://127.0.0.1:8080
echo.
echo Backend:
echo http://127.0.0.1:8000
echo.
echo API Docs:
echo http://127.0.0.1:8000/docs
echo.
echo Frontend:
echo http://localhost:5173
echo ============================================================
echo.
echo To stop all services, run: stop.bat
echo.
