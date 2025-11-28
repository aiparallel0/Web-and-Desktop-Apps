@echo off
REM Automated Test Runner for Windows
REM Clears cache and runs all tests

echo ========================================
echo  Receipt Extractor - Test Runner
echo ========================================
echo.

python run_all_tests.py
if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] All tests passed!
) else (
    echo.
    echo [FAILED] Some tests failed. Check output above.
)

pause
