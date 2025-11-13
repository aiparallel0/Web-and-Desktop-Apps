@echo off
echo ========================================
echo    Receipt Extractor Web App Launcher
echo ========================================
echo.

REM Get the directory where the script is located
cd /d "%~dp0"

echo Starting Backend API on port 5000...
start "Receipt API Backend" cmd /k "cd web-app\backend && python app.py"

echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo Starting Frontend Server on port 3000...
start "Receipt Frontend" cmd /k "cd web-app\frontend && python -m http.server 3000"

echo Waiting for frontend to start...
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo    Application Started Successfully!
echo ========================================
echo.
echo Backend API:  http://localhost:5000
echo Frontend App: http://localhost:3000
echo.
echo Opening browser...
start http://localhost:3000

echo.
echo Press any key to stop both servers...
pause >nul

echo Stopping servers...
taskkill /FI "WindowTitle eq Receipt API Backend*" /T /F >nul 2>&1
taskkill /FI "WindowTitle eq Receipt Frontend*" /T /F >nul 2>&1

echo.
echo Servers stopped. Goodbye!
timeout /t 2 /nobreak >nul
