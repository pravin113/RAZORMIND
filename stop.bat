@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   RazorMind AI -- Safe Service Shutdown
echo ============================================================
echo.

set "STOPPED=0"

:: -----------------------------------------------------------
:: Stop processes on RazorMind ports: 8080, 8000, 5173
:: -----------------------------------------------------------
for %%P in (8080 8000 5173) do (
    for /f "tokens=5" %%A in ('netstat -ano 2^>nul ^| findstr /R /C:":%%P .*LISTENING"') do (
        set "PID=%%A"
        if defined PID if not "!PID!"=="0" (
            echo [STOP] Killing PID !PID! on port %%P...
            taskkill /F /PID !PID! >nul 2>&1
            if !errorlevel! equ 0 (
                echo   OK - Process !PID! stopped.
                set /a STOPPED+=1
            ) else (
                echo   WARN - Could not stop PID !PID! on port %%P.
            )
        )
    )
)

:: -----------------------------------------------------------
:: Also kill any orphaned llama-server process by image name
:: -----------------------------------------------------------
tasklist /FI "IMAGENAME eq llama-server.exe" 2>nul | findstr /I "llama-server" >nul 2>&1
if %errorlevel% equ 0 (
    echo [STOP] Killing orphaned llama-server.exe...
    taskkill /F /IM llama-server.exe >nul 2>&1
    if !errorlevel! equ 0 (
        echo   OK - llama-server.exe terminated.
        set /a STOPPED+=1
    )
)

echo.
echo ============================================================
if !STOPPED! gtr 0 (
    echo RazorMind AI services stopped. !STOPPED! process(es) terminated.
) else (
    echo No active RazorMind AI services were found running.
)
echo ============================================================
echo.
