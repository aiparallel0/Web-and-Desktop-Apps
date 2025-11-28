@echo off
REM Comprehensive Test Runner for Windows
REM Runs all Receipt Extractor tests with detailed reporting

echo.
echo ================================================================
echo         Receipt Extractor - Comprehensive Test Suite
echo ================================================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check if pytest is installed
python -m pytest --version >nul 2>&1
if errorlevel 1 (
    echo [WARN] pytest is not installed
    echo Installing pytest...
    python -m pip install pytest pytest-cov pytest-mock
    if errorlevel 1 (
        echo [ERROR] Failed to install pytest
        pause
        exit /b 1
    )
)

echo [INFO] Running comprehensive test suite...
echo.

REM Run the Python test runner
python run_all_tests.py

REM Capture exit code
set TEST_EXIT_CODE=%ERRORLEVEL%

echo.
echo ================================================================
if %TEST_EXIT_CODE%==0 (
    echo [SUCCESS] All tests passed!
) else (
    echo [FAILURE] Some tests failed. Check logs for details.
)
echo ================================================================
echo.
echo Test reports saved to: logs\test-reports\
echo Coverage reports saved to: htmlcov\
echo.

pause
exit /b %TEST_EXIT_CODE%
