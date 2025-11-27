# Windows Installation Guide

This guide helps Windows users install the Receipt Extractor application and avoid common installation issues.

## Quick Start (Basic OCR Only)

For basic OCR functionality without AI models, you only need the core dependencies:

```bash
cd web-app/backend
pip install -r requirements.txt
python app.py
```

This will install:
- Flask (web framework)
- EasyOCR (primary OCR engine - no external dependencies)
- PaddleOCR and Tesseract (optional OCR engines)
- Image processing libraries (Pillow, OpenCV)

## Common Installation Issues

### Issue 1: Sentencepiece Build Error

**Error Message:**
```
error: subprocess-exited-with-error
FileNotFoundError: [WinError 2] The system cannot find the file specified
ERROR: Failed to build 'sentencepiece' when getting requirements to build wheel
```

**Cause:** Sentencepiece requires C++ build tools which are not included by default on Windows.

**Solutions:**

#### Option A: Use Basic OCR Only (Recommended for Most Users)
The basic installation (see Quick Start above) provides full OCR functionality without needing sentencepiece. This is sufficient for most use cases.

#### Option B: Install Advanced AI Models

If you need the advanced AI models (Donut, Florence-2) or finetuning capabilities:

1. **Install Visual Studio Build Tools**
   - Download from: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
   - During installation, select "Desktop development with C++"
   - This is a 7GB+ download and may take 30-60 minutes

2. **Install PyTorch and Transformers**
   ```bash
   # For CPU-only (works on any computer)
   pip install torch transformers accelerate --index-url https://download.pytorch.org/whl/cpu

   # For GPU support (if you have NVIDIA GPU)
   pip install torch transformers accelerate --index-url https://download.pytorch.org/whl/cu118
   ```

3. **Install Sentencepiece**
   ```bash
   # Try binary wheel first (fastest)
   pip install sentencepiece --only-binary :all:

   # If above fails, after installing Build Tools:
   pip install sentencepiece
   ```

### Issue 2: Tesseract Not Found

**Error:** `pytesseract.pytesseract.TesseractNotFoundError`

**Solution:**
1. Download Tesseract installer: https://github.com/UB-Mannheim/tesseract/wiki
2. Run installer and remember installation path (usually `C:\Program Files\Tesseract-OCR`)
3. Add to system PATH or set environment variable:
   ```bash
   set TESSDATA_PREFIX=C:\Program Files\Tesseract-OCR\tessdata
   ```

**Note:** Tesseract is optional. EasyOCR and PaddleOCR work without it.

### Issue 3: CUDA Out of Memory (for GPU users)

**Error:** `RuntimeError: CUDA out of memory`

**Solutions:**
- Reduce batch size in finetuning settings (try 2 or 1)
- Close other GPU-intensive applications
- Use CPU mode instead (slower but more reliable)

## Installation Options Summary

### Option 1: Basic OCR (Recommended)
**Best for:** Most users who need receipt extraction
**Requirements:** Just Python 3.8+
**Install time:** 5-10 minutes
```bash
pip install -r web-app/backend/requirements.txt
```
**Features:**
- ✅ EasyOCR (primary engine)
- ✅ Tesseract OCR (if installed separately)
- ✅ PaddleOCR
- ✅ Web interface
- ✅ Batch processing
- ❌ AI models (Donut, Florence-2)
- ❌ Model finetuning

### Option 2: Full AI + Finetuning
**Best for:** Advanced users, researchers, custom model training
**Requirements:** Python 3.8+, Visual Studio Build Tools, 16GB+ RAM
**Install time:** 1-2 hours (including Build Tools)
**Additional install:**
```bash
pip install torch transformers accelerate sentencepiece protobuf
```
**Features:**
- ✅ Everything from Option 1
- ✅ AI models (Donut, Florence-2)
- ✅ Model finetuning
- ✅ GPU acceleration (if NVIDIA GPU available)

## Verifying Installation

### Check Python Version
```bash
python --version
# Should show Python 3.8 or higher
```

### Test Basic Installation
```bash
cd web-app/backend
python -c "import flask, easyocr, PIL; print('✓ Basic dependencies OK')"
```

### Test AI Models (if installed)
```bash
python -c "import torch, transformers; print('✓ AI dependencies OK')"
```

### Start the Server
```bash
cd web-app/backend
python app.py
# Should show: "Starting Receipt Extraction API..."
```

## GPU Acceleration (Optional)

For 10-15x faster AI model inference and training:

1. **Check GPU Compatibility**
   - Requires NVIDIA GPU with CUDA support
   - Check: https://developer.nvidia.com/cuda-gpus

2. **Install CUDA Toolkit**
   - Download CUDA 11.8 or 12.1: https://developer.nvidia.com/cuda-downloads
   - Follow installer instructions
   - Reboot after installation

3. **Install GPU PyTorch**
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

4. **Verify GPU**
   ```bash
   python -c "import torch; print('GPU available:', torch.cuda.is_available())"
   # Should show: GPU available: True
   ```

## Troubleshooting

### Port 5000 Already in Use
```bash
# Windows: Find and kill process using port 5000
netstat -ano | findstr :5000
taskkill /PID <process_id> /F
```

### Module Not Found Errors
```bash
# Reinstall all dependencies
pip install --upgrade --force-reinstall -r requirements.txt
```

### Application Won't Start
1. Check Python version: `python --version`
2. Check if port 5000 is available
3. Review error messages in console
4. Check logs in web-app/backend directory

## Performance Tips

### For Fast Extraction
- Use EasyOCR (default) - 1-2 seconds per image
- Runs well on CPU, no GPU needed
- Best balance of speed and accuracy

### For Highest Accuracy
- Use Donut or Florence-2 models (requires AI dependencies)
- Needs GPU for acceptable speed (5-10 seconds with GPU)
- CPU inference is very slow (30-60 seconds)

### For Batch Processing
- Process 10-20 images at once for best throughput
- Use local file upload (faster than cloud)
- Close other applications to free memory

## Getting Help

### Still Having Issues?

1. **Check the logs** - Look for error messages in the console
2. **Verify dependencies** - Run the test commands above
3. **Check system requirements**:
   - Python 3.8 or higher
   - 8GB RAM minimum (16GB recommended)
   - 10GB free disk space
4. **Restart the application** after installing new dependencies
5. **Check firewall settings** - Allow Python/Flask through Windows Firewall

### Which Models Will Work?

After basic installation (`pip install -r requirements.txt`):
- ✅ **EasyOCR** - Works immediately, recommended
- ✅ **PaddleOCR** - Works immediately
- ⚠️  **Tesseract OCR** - Requires separate Tesseract binary installation
- ❌ **Donut CORD** - Requires AI dependencies (torch, transformers, sentencepiece)
- ❌ **Florence-2** - Requires AI dependencies (torch, transformers, sentencepiece)

The application will automatically detect which models are available and only show compatible ones.

## Next Steps

1. Start the backend server: `python app.py`
2. Open frontend: `web-app/frontend/index.html` in your browser
3. Select a model (EasyOCR recommended for first use)
4. Upload a receipt image
5. View extracted data

See README.md for detailed usage instructions.
