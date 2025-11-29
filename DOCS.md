# Receipt Extractor - Complete Documentation

**Version:** 3.0  
**Last Updated:** 2025-11-29

This is the consolidated documentation for the Receipt Extractor application.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Testing Guide](#testing-guide)
3. [Web App Usage](#web-app-usage)
4. [Troubleshooting](#troubleshooting)
5. [Architecture Overview](#architecture-overview)

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

For detailed security and database documentation, see `PRIORITY1_IMPLEMENTATION.md`.

---

## Support

- **Logs:** Check `logs/` directory
- **Test Reports:** See `logs/test-reports/`
- **Configuration:** Edit `shared/config/models_config.json`
