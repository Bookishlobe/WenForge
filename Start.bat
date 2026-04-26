@echo off
setlocal enabledelayedexpansion

:: WenForge Launcher v4 - Desktop mode (Electron)

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"

echo.
echo ========================================
echo   WenForge Launcher
echo   %ROOT%
echo ========================================
echo.

:: ---- Check frontend ----
if not exist "%ROOT%\dist\index.html" (
    echo [WARN] Building frontend...
    call npx.cmd vite build
    if errorlevel 1 (
        echo [FAIL] Build failed
        pause
        exit /b 1
    )
)
echo [ OK ] Frontend built

:: ---- Check python ----
if not exist "%ROOT%\python\main.py" (
    echo [FAIL] python/main.py not found
    pause
    exit /b 1
)
echo [ OK ] Python engine

:: ---- Find Python command ----
set "PYTHON=python"
where python >nul 2>&1 || set "PYTHON=py"
where %PYTHON% >nul 2>&1 || (
    echo [FAIL] Python not found in PATH
    echo   Install Python 3.11+ from https://python.org
    pause
    exit /b 1
)
echo [ OK ] Python command: %PYTHON%

:: ---- Launch Python (write tmp script to avoid quote nesting) ----
echo [1/2] Starting AI engine...
(
echo cd /d "%ROOT%\python"
echo %PYTHON% -m uvicorn main:app --host 127.0.0.1 --port 8765 ^> "%ROOT%\python.log" 2^>^&1
) > "%ROOT%\start_py.bat"
start "WenForge-Python" /MIN cmd /c "%ROOT%\start_py.bat"

:: ---- Wait for Python to start ----
echo [2/2] Waiting for server...
timeout /t 3 >nul

:: ---- Launch Electron (desktop window) ----
set "ELECTRON=%ROOT%\node_modules\electron\dist\electron.exe"
if exist "%ELECTRON%" (
    echo [ OK ] Starting Electron...
    start "" "%ELECTRON%" "%ROOT%"
    echo.
    echo ========================================
    echo   WenForge desktop app launched!
    echo   Close the app window to exit.
    echo   This window can be minimized.
    echo ========================================
    echo.
) else (
    echo [WARN] Electron not found, opening browser instead.
    echo   Run npm install to enable desktop mode.
    echo.
    start "" http://127.0.0.1:8765
    echo ========================================
    echo   WenForge is running in browser!
    echo   http://127.0.0.1:8765
    echo   Close this window to stop the app
    echo ========================================
    echo.
)
exit /b 0
