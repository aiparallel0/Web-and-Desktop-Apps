@echo off
REM All-in-one setup and test script

if "%1"=="setup" goto setup
if "%1"=="test" goto test
if "%1"=="extract" goto extract
if "%1"=="models" goto models
goto help

:setup
echo Installing dependencies...
pip install torch transformers pillow opencv-python numpy pytesseract
npm install
echo Done
goto end

:test
echo Testing Python...
python -c "import torch, transformers, PIL, cv2, numpy; print('OK')"
goto end

:extract
if "%2"=="" (
  echo Usage: dev.bat extract ^<image^> [model]
  goto end
)
set MODEL=%3
if "%MODEL%"=="" set MODEL=sroie
if "%MODEL%"=="ocr" (
  python extract_ocr.py %2
) else (
  python extract_donut.py %2 --model %MODEL%
)
goto end

:models
echo Downloading models...
python test.py --download
goto end

:help
echo Receipt Extractor - Dev Script
echo.
echo Usage:
echo   dev.bat setup                Install all dependencies
echo   dev.bat test                 Test Python environment
echo   dev.bat extract ^<img^> [model]   Test extraction
echo   dev.bat models               Download models
echo.
echo Development:
echo   npm start                    Run app
echo   npm run build                Build app

:end
