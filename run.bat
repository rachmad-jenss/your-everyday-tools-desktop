@echo off
setlocal

cd /d "%~dp0"

set "EVERYTOOLS_PY="

where py >nul 2>nul
if not errorlevel 1 (
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
    if not errorlevel 1 set "EVERYTOOLS_PY=py -3"
)

if not defined EVERYTOOLS_PY (
    where python >nul 2>nul
    if not errorlevel 1 (
        python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
        if not errorlevel 1 set "EVERYTOOLS_PY=python"
    )
)

if not defined EVERYTOOLS_PY (
    echo.
    echo   Python 3.10 or newer is required, but was not found.
    echo.
    echo   Download and install Python from:
    echo       https://www.python.org/downloads/
    echo.
    echo   During install, make sure to check "Add python.exe to PATH".
    echo.
    pause
    exit /b 1
)

%EVERYTOOLS_PY% "scripts\launcher.py" %*
set "EXITCODE=%ERRORLEVEL%"

echo.
if not "%EXITCODE%"=="0" (
    echo   EveryTools stopped with an error. See the messages above.
) else (
    echo   EveryTools stopped.
)
echo.
pause
exit /b %EXITCODE%
