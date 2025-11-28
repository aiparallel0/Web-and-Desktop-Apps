@echo off
REM Quick DonutProcessor Test Runner for Windows
REM Automatically clears cache and runs DonutProcessor tests

echo ========================================
echo  DonutProcessor Test Runner
echo ========================================
echo.

python run_donut_tests.py
if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] All DonutProcessor tests passed!
) else (
    echo.
    echo [FAILED] Some tests failed. Check output above.
)

pause
