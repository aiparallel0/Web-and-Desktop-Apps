@echo off
REM =============================================================================
REM Receipt Extractor - ONE-CLICK START for Windows
REM =============================================================================
REM 
REM Double-click this file to:
REM   1. Set up virtual environment
REM   2. Install dependencies
REM   3. Clear cache
REM   4. Start servers
REM
REM Or run from command prompt:
REM   start.bat         - Full setup + start
REM   start.bat quick   - Skip venv, just start
REM   start.bat clean   - Only clean cache
REM
REM =============================================================================

title Receipt Extractor - Starting...

REM Change to script directory (project root)
cd /d "%~dp0"

echo.
echo ============================================================
echo        RECEIPT EXTRACTOR - ONE-CLICK START
echo ============================================================
echo.

REM Check for Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Run the Python startup script
if "%1"=="quick" (
    python start.py --quick
) else if "%1"=="clean" (
    python start.py --clean-only
) else (
    python start.py
)

REM Keep window open if there was an error
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Something went wrong. Check the output above.
    pause
)
