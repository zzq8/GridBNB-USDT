@echo off
setlocal enableextensions enabledelayedexpansion
for /f "tokens=2 delims=:." %%A in ('chcp') do set "ORIGINAL_CP=%%A"
if defined ORIGINAL_CP set "ORIGINAL_CP=%ORIGINAL_CP: =%"
chcp 65001 >nul

set "ROOT=%~dp0"
pushd "%ROOT%" >nul

echo ============================================================
echo GridBNB-USDT Full-Stack Dev Launcher
echo ============================================================
echo [INFO] Working directory: %ROOT%
echo.
echo [INFO] Configurations are now managed in the Web Console (no config/.env needed)

set "BACKEND_VENV_CMD="
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Found Python virtual environment, activating...
    set "BACKEND_VENV_CMD=call ""%ROOT%.venv\Scripts\activate.bat"" && "
) else (
    echo [WARN] No virtual environment found, using global Python interpreter.
    echo [HINT] Create one with: python -m venv .venv
)

if not exist "web\node_modules" (
    echo [INFO] Frontend dependencies missing. Running npm install once...
    pushd "web" >nul
    call npm install
    if errorlevel 1 (
        echo [ERROR] npm install failed. Please resolve the issue and rerun.
        popd >nul
        goto :cleanup
    )
    popd >nul
)

echo [INFO] Launching backend window...
start "GridBNB Backend" cmd /k "cd /d ""%ROOT%"" && %BACKEND_VENV_CMD%python src\main.py"

echo [INFO] Launching frontend window...
start "GridBNB Frontend" cmd /k "cd /d ""%ROOT%web"" && npm run dev"

echo.
echo [DONE] Backend and frontend are running in separate terminals.
echo [HINT] Close those windows (Ctrl+C) to stop the services.
pause

:cleanup
if defined ORIGINAL_CP (
    chcp %ORIGINAL_CP% >nul
)
popd >nul
endlocal
goto :EOF
