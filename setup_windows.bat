@echo off
REM =============================================================================
REM Windows Setup Script for Receipt Extractor
REM =============================================================================
REM This script sets up the development environment on Windows
REM Run this from Git Bash or Command Prompt with Administrator privileges

echo ========================================
echo Receipt Extractor - Windows Setup
echo ========================================
echo.

REM Check if running with admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script requires Administrator privileges
    echo Please right-click and select "Run as Administrator"
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
    if %errorLevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        echo Make sure Python 3.10+ is installed
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing Python dependencies...
pip install -r requirements.txt
if %errorLevel% neq 0 (
    echo WARNING: Some dependencies failed to install
    echo You may need to install them manually
)

REM Fix symlink issue for Windows
echo.
echo Fixing Windows symlink issues...
if not exist "tools\shared" (
    echo Creating junction for tools\shared...
    mklink /J tools\shared shared
) else (
    echo tools\shared already exists
)

REM Copy .env.example if .env doesn't exist
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo IMPORTANT: Edit .env file with your actual credentials
    echo.
) else (
    echo .env file already exists
)

REM Create alembic.ini in root if it doesn't exist
if not exist "alembic.ini" (
    echo Creating alembic.ini in project root...
    (
        echo [alembic]
        echo script_location = migrations
        echo prepend_sys_path = .
        echo file_template = %%^(year^)d%%^(month^).2d%%^(day^).2d_%%^(hour^).2d%%^(minute^).2d_%%^(rev^)s_%%^(slug^)s
        echo.
        echo [alembic:exclude]
        echo tables = alembic_version
        echo.
        echo sqlalchemy.url = driver://user:pass@localhost/dbname
    ) > alembic.ini
    echo Created alembic.ini
)

REM Check for PostgreSQL
echo.
echo Checking for PostgreSQL...
where psql >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo WARNING: PostgreSQL is not installed or not in PATH
    echo.
    echo Options:
    echo 1. Install PostgreSQL from https://www.postgresql.org/download/windows/
    echo 2. Use SQLite for development instead:
    echo    - Set USE_SQLITE=true in your .env file
    echo.
) else (
    echo PostgreSQL found
    echo.
    echo To create the database, run:
    echo   createdb receipt_extractor
    echo.
)

REM Check for Tesseract OCR
echo Checking for Tesseract OCR...
where tesseract >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo WARNING: Tesseract OCR is not installed
    echo Download from: https://github.com/UB-Mannheim/tesseract/wiki
    echo After installing, add to PATH or set TESSERACT_CMD in .env
    echo.
) else (
    tesseract --version
    echo Tesseract found
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your credentials
echo 2. Create database: createdb receipt_extractor
echo 3. Run migrations: alembic upgrade head
echo 4. Run tests: pytest tools\tests -v
echo 5. Start web app: python web\backend\app.py
echo 6. Start desktop app: npm start (in desktop directory)
echo.
echo For SQLite development (no PostgreSQL needed):
echo - Set USE_SQLITE=true in .env file
echo.

pause
