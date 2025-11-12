# Setup Guide

Complete setup instructions for Receipt Extractor project.

## System Requirements

### Required
- **Python 3.8+** with pip
- **Git** (for cloning repository)
- **4GB+ RAM** (8GB+ recommended for AI models)
- **5GB+ disk space** (for models and dependencies)

### Optional
- **Node.js 16+** (for desktop app)
- **Tesseract OCR** (for OCR model)
- **CUDA-capable GPU** (for faster processing)

## Installation Steps

### 1. Clone Repository

```bash
git clone <repository-url>
cd Web-and-Desktop-Apps
```

### 2. Install Python Dependencies

```bash
pip install -r web-app/backend/requirements.txt
```

Or install manually:
```bash
pip install torch transformers pillow opencv-python numpy pytesseract flask flask-cors
```

### 3. Verify Installation

Test the shared modules:
```bash
python -c "from shared.models.model_manager import ModelManager; print('OK')"
```

## Web Application Setup

### Backend

```bash
cd web-app/backend
python app.py
```

Server will start on `http://localhost:5000`

### Frontend

```bash
cd web-app/frontend
python -m http.server 8000
```

Navigate to `http://localhost:8000`

## Desktop Application Setup

### 1. Install Node Dependencies

```bash
cd desktop-app
npm install
```

### 2. Run Desktop App

```bash
npm start
```

### 3. Build Executable (Optional)

**Windows:**
```bash
npm run build:win
```

Output: `desktop-app/dist/ReceiptExtractor-win32-x64/`

**macOS:**
```bash
npm run build:mac
```

**Linux:**
```bash
npm run build:linux
```

## Tesseract OCR Installation (Optional)

### Windows
1. Download installer from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run installer (default path: `C:\Program Files\Tesseract-OCR`)
3. Add to PATH or let the app auto-detect

### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

### macOS
```bash
brew install tesseract
```

## GPU Acceleration (Optional)

For CUDA support (NVIDIA GPUs only):

```bash
# Uninstall CPU-only PyTorch
pip uninstall torch

# Install CUDA-enabled PyTorch (example for CUDA 11.8)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

Check CUDA availability:
```bash
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
```

## First Run

### Download Models

Models are automatically downloaded on first use. First extraction will take 2-5 minutes depending on internet speed.

Models are cached in:
- **Linux/Mac:** `~/.cache/huggingface/`
- **Windows:** `C:\Users\<username>\.cache\huggingface\`

### Test Extraction

```bash
# Using Python directly
python desktop-app/process_receipt.py path/to/receipt.jpg

# Using web API
curl -X POST -F "image=@receipt.jpg" http://localhost:5000/api/extract
```

## Troubleshooting

### Import Errors

```bash
# Reinstall dependencies
pip install -r web-app/backend/requirements.txt --force-reinstall
```

### Model Download Issues

- Check internet connection
- Verify disk space (need ~2GB free)
- Try manual download:
  ```python
  from transformers import DonutProcessor, VisionEncoderDecoderModel
  DonutProcessor.from_pretrained("philschmid/donut-base-sroie")
  VisionEncoderDecoderModel.from_pretrained("philschmid/donut-base-sroie")
  ```

### Python Not Found (Desktop App)

- Add Python to system PATH
- Restart terminal/app after PATH changes
- Verify: `python --version` or `python3 --version`

### Port Already in Use

Change port in `web-app/backend/app.py`:
```python
app.run(host='0.0.0.0', port=5001, debug=True)  # Change 5000 to 5001
```

Also update frontend `js/app.js`:
```javascript
const API_BASE_URL = 'http://localhost:5001/api';  // Match backend port
```

## Development Setup

### Enable Debug Mode

**Web Backend:**
Already enabled in development. Check `app.py`:
```python
app.run(host='0.0.0.0', port=5000, debug=True)
```

**Desktop App:**
Automatically opens DevTools in development mode.

### Hot Reload

Web backend has auto-reload enabled with Flask debug mode.

For frontend changes, simply refresh browser.

Desktop app requires restart for changes.

## Production Deployment

### Web Application

Use a production WSGI server:

```bash
pip install gunicorn

# Run with gunicorn
cd web-app/backend
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Desktop Application

Build distributables as shown above. Distribute the entire folder from `dist/`.

## Support

For issues or questions, check:
1. Main README.md
2. Troubleshooting section above
3. Individual component READMEs in subdirectories
