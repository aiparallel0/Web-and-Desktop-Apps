# Receipt Extractor - Text Detection from Receipts

AI-powered receipt text extraction with support for both **Web Application** and **Electron Desktop Application**.

---

## ⚠️ MANDATORY: Circular Exchange Framework Integration ⚠️

> **FOR ALL AI AGENTS (GitHub Copilot, ChatGPT, Claude, etc.):**
>
> **ALL code in this project MUST be integrated with the Circular Exchange Framework.**
> 
> Before writing any code, read: **[CIRCULAR_EXCHANGE_GUIDE.md](./CIRCULAR_EXCHANGE_GUIDE.md)**
>
> ### Quick Requirements:
> 1. Import from `shared.circular_exchange`
> 2. Register modules with `PROJECT_CONFIG.register_module()`
> 3. Use `VariablePackage` for configurable parameters
> 4. Record results for auto-tuning
>
> **This is a non-negotiable architectural requirement.**

---

## Project Overview

This project provides text detection from receipts using multiple AI models. It consists of:

1. **Web Application** - Flask backend with browser-based frontend for testing and online use
2. **Desktop Application** - Electron-packaged distributable .exe application for offline use
3. **Shared Processing Modules** - Common codebase for model management and extraction

### Key Features

- **Multiple Model Support** - Easy switching between different AI models (like swapping disks)
- **Donut Models** - Transformer-based models for structured receipt parsing
- **Florence-2** - Microsoft's advanced OCR with region detection
- **Tesseract OCR** - Traditional OCR for fast, reliable extraction
- **No Authentication Required** - All models are open-source and public
- **High Accuracy** - Extract items, totals, store names, dates with near 100% accuracy
- **Export Options** - Export results as JSON, CSV, or TXT

## Project Structure

```
├── shared/                    # Shared processing modules
│   ├── models/               # Model processors
│   │   ├── model_manager.py  # Central model management
│   │   ├── donut_processor.py # Donut/Florence processors
│   │   └── ocr_processor.py  # OCR processor
│   ├── utils/                # Common utilities
│   │   ├── data_structures.py
│   │   └── image_processing.py
│   └── config/               # Configuration
│       └── models_config.json
│
├── web-app/                  # Web application
│   ├── backend/              # Flask API
│   │   ├── app.py
│   │   └── requirements.txt
│   └── frontend/             # Web UI
│       ├── index.html
│       ├── css/styles.css
│       └── js/app.js
│
├── desktop-app/              # Electron desktop app
│   ├── main.js               # Electron main process
│   ├── preload.js            # Preload script
│   ├── process_receipt.py    # Python bridge
│   ├── src/                  # UI files
│   │   ├── index.html
│   │   ├── styles.css
│   │   └── renderer.js
│   └── package.json
│
└── README.md
```

## Available Models

All models are **open-source** and require **no authentication**:

| Model ID | Name | Type | Capabilities | Speed |
|----------|------|------|--------------|-------|
| `donut_sroie` | SROIE Donut | Donut | Store, Date, Total, Address | Fast |
| `donut_cord` | CORD Donut | Donut | Full extraction with items | Medium |
| `florence2` | Florence-2 | Florence | Advanced OCR with regions | Medium |
| `ocr_tesseract` | Tesseract OCR | OCR | Traditional OCR | Very Fast |

## Installation

### Prerequisites

- **Python 3.8+** (with pip)
- **Node.js 16+** (for desktop app)
- **Tesseract OCR** (optional, for OCR model)

### Python Dependencies

```bash
pip install torch transformers pillow opencv-python numpy pytesseract flask flask-cors
```

Or use the requirements file:

```bash
pip install -r web-app/backend/requirements.txt
```

### Tesseract Installation (Optional)

**Windows:** Download from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

## Usage

### Web Application

#### 1. Start the Backend API

```bash
cd web-app/backend
python app.py
```

The API will run on `http://localhost:5000`

#### 2. Open the Frontend

Open `web-app/frontend/index.html` in your browser, or serve it with a simple HTTP server:

```bash
cd web-app/frontend
python -m http.server 8000
```

Then navigate to `http://localhost:8000`

#### 3. Using the Web App

1. Select a model from the available options
2. Upload a receipt image (JPG, PNG, BMP, TIFF)
3. Click "Extract Receipt Data"
4. View and export results

### Desktop Application

#### 1. Install Dependencies

```bash
cd desktop-app
npm install
```

#### 2. Run the Desktop App

```bash
npm start
```

#### 3. Build Distribution

**Windows:**
```bash
npm run build:win
```

**macOS:**
```bash
npm run build:mac
```

**Linux:**
```bash
npm run build:linux
```

Built application will be in `desktop-app/dist/`

## API Endpoints (Web App)

### GET `/api/health`
Health check

### GET `/api/models`
Get list of available models

### POST `/api/models/select`
Select a model
```json
{
  "model_id": "donut_sroie"
}
```

### POST `/api/extract`
Extract receipt data from image
- Form data: `image` (file), `model_id` (optional)
- Returns: Extraction result with all detected data

### GET `/api/models/<model_id>/info`
Get detailed information about a specific model

### POST `/api/models/unload`
Unload all models from memory

## Model Management

The Model Manager provides an interface for easy model switching:

```python
from shared.models.model_manager import ModelManager

# Initialize
manager = ModelManager()

# Get available models
models = manager.get_available_models()

# Select a model
manager.select_model('donut_cord')

# Get processor
processor = manager.get_processor()

# Extract from image
result = processor.extract('receipt.jpg')
print(result.to_dict())
```

## Adding New Models

To add a new model, edit `shared/config/models_config.json`:

```json
{
  "available_models": {
    "your_model_id": {
      "id": "your_model_id",
      "name": "Your Model Name",
      "type": "donut|florence|ocr",
      "huggingface_id": "org/model-name",
      "task_prompt": "<task_prompt>",
      "description": "Model description",
      "requires_auth": false,
      "capabilities": {
        "store_name": true,
        "date": true,
        "total": true,
        "items": true
      }
    }
  }
}
```

## Troubleshooting

### Web App

**API not responding:**
- Check backend is running on port 5000
- Verify CORS is enabled
- Check firewall settings

**Model loading slow:**
- First run downloads models (~500MB-1GB)
- Subsequent runs use cached models
- Check disk space and internet connection

### Desktop App

**Python not found:**
- Install Python 3.8+
- Add Python to system PATH
- Restart terminal/app

**Extraction fails:**
- Check Python dependencies installed
- Verify image file is valid
- Check model is downloaded

**Build fails:**
- Run `npm install` in desktop-app directory
- Check Node.js version (16+)
- Install electron-packager globally if needed

### General

**Out of memory:**
- Unload models when switching: `manager.unload_all_models()`
- Use lighter models (SROIE Donut, OCR)
- Reduce image size before processing

**Low accuracy:**
- Try different models (Florence-2 recommended)
- Ensure image quality is good
- Use image enhancement options

## Development

### Running Tests

```bash
# Test extraction with specific model
python -c "
from shared.models.model_manager import ModelManager
manager = ModelManager()
processor = manager.get_processor('donut_sroie')
result = processor.extract('test_receipt.jpg')
print(result.to_dict())
"
```

### Adding Custom Processors

1. Create processor in `shared/models/`
2. Inherit from appropriate base class
3. Implement `extract()` method
4. Register in `model_manager.py`

## License

MIT License - See LICENSE.txt for details

## Credits

- **Donut Models:** Naver Clova, HuggingFace community
- **Florence-2:** Microsoft Research
- **Tesseract:** Google, open-source community
# Receipt Extractor - Complete Documentation

**Version:** 3.0  
**Last Updated:** 2025-11-29

This is the consolidated documentation for the Receipt Extractor application.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Testing Guide](#testing-guide)
4. [Web App Usage](#web-app-usage)
5. [GPU Setup](#gpu-setup)
6. [Architecture](#architecture)
7. [API Reference](#api-reference)
8. [Troubleshooting](#troubleshooting)
9. [OCR Quality Guide](#ocr-quality-guide)
10. [Development Guide](#development-guide)

---

## Quick Start

### Using the Unified Launcher (Recommended)

```bash
# Linux/Mac
./launch.sh

# Or with options:
./launch.sh --quick    # Quick launch without tests
./launch.sh --test     # Run tests only
./launch.sh --clean    # Clean Python cache only
```

### Windows

```cmd
# Run all tests
run_tests.bat

# Or use Python directly
python run_all_tests.py
```

### Manual Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start backend
cd web-app/backend
python app.py

# 3. Start frontend (new terminal)
cd web-app/frontend  
python -m http.server 3000

# 4. Open browser
# Navigate to http://localhost:3000
```

---

## Testing Guide

### Automated Test Runner

The unified launcher script (`launch.sh`) includes built-in test execution with automatic cache cleaning.

```bash
# Run full test suite with cache cleanup
./launch.sh --test

# Or using Python directly
python run_all_tests.py
```

### Test Suites

| Test File | Description | Status |
|-----------|-------------|--------|
| `test_system_health.py` | System validation | ✅ |
| `test_image_processing.py` | Image utilities | ✅ |
| `test_model_manager.py` | Model loading | ✅ |
| `test_base_processor.py` | Base processor | ✅ |
| `test_easyocr_processor.py` | EasyOCR tests | ✅ |
| `test_paddle_processor.py` | PaddleOCR tests | ✅ |
| `test_donut_processor.py` | Donut model tests | ✅ |
| `test_api.py` | API endpoints | ✅ |

### Cache Cleaning

Cache is cleaned automatically before tests, but you can also do it manually:

```bash
# Using launcher
./launch.sh --clean

# Or manually
rm -rf __pycache__ .pytest_cache .coverage htmlcov
find . -name "*.pyc" -delete
```

### Coverage Reports

```bash
# Run tests with coverage
pytest tests/ -v --cov=shared --cov=web-app/backend --cov-report=html

# View HTML report
open htmlcov/index.html  # Mac
start htmlcov/index.html # Windows
xdg-open htmlcov/index.html # Linux
```

---

## Web App Usage

### Starting the Application

```bash
./launch.sh   # Select option 1 (Quick Launch) or 2 (Full Launch)
```

### Access URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | Web interface |
| **Backend** | http://localhost:5000 | API server |
| **Health Check** | http://localhost:5000/api/health | System status |
| **Models** | http://localhost:5000/api/models | Available models |

### API Endpoints

```bash
# Get available models
curl http://localhost:5000/api/models

# Select a model
curl -X POST http://localhost:5000/api/models/select \
  -H "Content-Type: application/json" \
  -d '{"model_id": "easyocr"}'

# Extract receipt data
curl -X POST http://localhost:5000/api/extract \
  -F "image=@receipt.jpg" \
  -F "model_id=easyocr"

# Extract with ALL models
curl -X POST http://localhost:5000/api/extract/batch \
  -F "image=@receipt.jpg"
```

### Available OCR Models

| Model | Speed | Accuracy | Setup |
|-------|-------|----------|-------|
| EasyOCR | ⚡⚡ | ⭐⭐⭐⭐ | Automatic (Recommended) |
| Tesseract | ⚡⚡⚡ | ⭐⭐⭐ | Requires installation |
| PaddleOCR | ⚡⚡ | ⭐⭐⭐⭐ | Requires installation |
| Florence-2 | ⚡ | ⭐⭐⭐⭐⭐ | Requires PyTorch |

---

## Troubleshooting

### Common Issues

#### "Port already in use"
```bash
# Find and kill process on port 5000
lsof -i :5000
kill -9 <PID>

# Or use different port
python -m http.server 8080
```

#### "Module not found"
```bash
pip install -r requirements.txt
pip install pytest pytest-cov pytest-mock
```

#### "Tesseract not found"
- **Windows:** Download from https://github.com/UB-Mannheim/tesseract/wiki
- **Mac:** `brew install tesseract`
- **Linux:** `sudo apt-get install tesseract-ocr`

#### EasyOCR First Run (Slow)
Normal behavior - downloads models (~50MB) on first use.

#### Memory Issues
```bash
# Unload models
curl -X POST http://localhost:5000/api/models/unload
```

### Debug Mode

```bash
# Enable debug logging
export FLASK_DEBUG=1
python app.py
```

---

## Architecture Overview

### Project Structure

```
├── launch.sh           # Unified launcher script
├── shared/             # Shared processing modules
│   ├── models/         # OCR processors
│   ├── utils/          # Utilities
│   └── config/         # Configuration
├── web-app/            # Web application
│   ├── backend/        # Flask API
│   └── frontend/       # HTML/CSS/JS
├── desktop-app/        # Electron desktop app
├── tests/              # Test suites
└── DOCS.md             # This documentation
```

### Key Files

| File | Purpose |
|------|---------|
| `launch.sh` | Unified launcher with cache cleaning |
| `run_all_tests.py` | Test runner |
| `shared/models/model_manager.py` | Model management |
| `web-app/backend/app.py` | Flask API |
| `shared/config/models_config.json` | Model configuration |

### Security Features

- JWT token authentication
- Password hashing with bcrypt
- Input validation with Pydantic
- Rate limiting decorators
- SQL injection prevention (ORM)

---

## GPU Setup

### Prerequisites

- NVIDIA GPU (GTX 1050 or newer)
- CUDA Toolkit 12.1
- 4GB+ VRAM

### Installation

```bash
# Windows: Download CUDA from https://developer.nvidia.com/cuda-downloads
# Linux:
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update && sudo apt-get -y install cuda-toolkit-12-1

# Install GPU PyTorch
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Verify

```bash
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

### Performance Improvement

| Model | CPU | GPU | Speedup |
|-------|-----|-----|---------|
| EasyOCR | 45s | 3s | 15x |
| Donut | 20s | 2s | 10x |
| Florence-2 | 60s | 4s | 15x |

---

## API Reference

### Authentication Endpoints

```bash
# Register
POST /api/auth/register
{"email": "user@example.com", "password": "SecurePass123!"}

# Login
POST /api/auth/login
{"email": "user@example.com", "password": "SecurePass123!"}

# Logout
POST /api/auth/logout
{"refresh_token": "..."}

# Refresh Token
POST /api/auth/refresh
{"refresh_token": "..."}

# Get Profile
GET /api/auth/me
Authorization: Bearer <token>
```

### Receipts Endpoints

```bash
# List Receipts
GET /api/receipts
Authorization: Bearer <token>

# Get Receipt
GET /api/receipts/<id>
Authorization: Bearer <token>

# Update Receipt
PATCH /api/receipts/<id>
Authorization: Bearer <token>
{"store_name": "...", "total_amount": 25.99}

# Delete Receipt
DELETE /api/receipts/<id>
Authorization: Bearer <token>

# Get Statistics
GET /api/receipts/stats
Authorization: Bearer <token>
```

### Extraction Endpoints

```bash
# Single extraction
POST /api/extract
multipart/form-data: image, model_id

# Batch extraction (all models)
POST /api/extract/batch
multipart/form-data: image
```

---

## OCR Quality Guide

### Image Preprocessing Pipeline

1. Upscale (if < 1000px) → 1500px minimum
2. Deskew (auto-rotate)
3. Denoise
4. CLAHE (enhance faded text)
5. Bilateral Filter
6. Otsu Binarization
7. Morphological Cleanup
8. Invert if dark background

### Quality Tips

- **Resolution**: 300+ DPI recommended
- **Lighting**: Even, no glare
- **Orientation**: Straight, flat
- **For faded thermal receipts**: Use EasyOCR

### Model Selection Guide

| Image Type | Best Model |
|------------|------------|
| Clear, printed | Tesseract |
| Handwritten | EasyOCR |
| Complex layout | Florence-2 |
| Multi-language | PaddleOCR |

---

## Development Guide

### Database Setup (PostgreSQL)

```bash
# Create database
sudo -u postgres createdb receipt_extractor
sudo -u postgres createuser receipt_user -P

# Set environment
DATABASE_URL=postgresql://receipt_user:password@localhost:5432/receipt_extractor
JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

### Running Tests

```bash
# All tests
./launch.sh --test

# With coverage
pytest tests/ --cov=shared --cov=web-app/backend --cov-report=html

# Specific tests
pytest tests/backend/auth/ -v
```

### Project Structure (Max Depth 3)

```
├── launch.sh           # Unified launcher
├── README.md           # Project readme
├── DOCS.md             # All documentation (this file)
├── requirements.txt    # Dependencies
├── pytest.ini          # Test config
├── shared/             # Shared code
│   ├── models/         # OCR processors
│   ├── utils/          # Utilities
│   └── config/         # Configuration
├── web-app/            # Web application
│   ├── backend/        # Flask API
│   └── frontend/       # Web UI
├── desktop-app/        # Electron app
├── tests/              # All tests
└── test_data/          # Test images
```

---

## Support

- **Logs:** Check `logs/` directory
- **Test Reports:** `logs/test-reports/`
- **Configuration:** `shared/config/models_config.json`
