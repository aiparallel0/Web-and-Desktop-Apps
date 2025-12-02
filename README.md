# Receipt Extractor - AI-Powered Text Detection

AI-powered receipt text extraction with **Web Application** and **Electron Desktop Application**.

## Quick Start

```bash
./launch.sh          # Full launch
./launch.sh --quick  # Quick launch without tests
./launch.sh --test   # Run tests only
```

**Manual Start:**
```bash
pip install -r requirements.txt
cd web/backend && python app.py     # Backend: http://localhost:5000
cd web/frontend && python -m http.server 3000  # Frontend: http://localhost:3000
```

## Project Structure

```
├── shared/              # Shared processing modules (4 folders + 4 files)
│   ├── circular_exchange/  # Configuration framework
│   ├── config/             # Configuration files
│   ├── models/             # Model processors
│   └── utils/              # Utilities
├── web/                 # Web application
│   ├── backend/           # Flask API
│   └── frontend/          # Web UI
├── desktop/             # Electron desktop app
└── tools/               # Scripts, tests, and test data
    ├── scripts/           # Processing scripts
    ├── tests/             # Test suites
    └── data/              # Test data
```

## Available Models

| Model | Type | Speed | Description |
|-------|------|-------|-------------|
| `donut_sroie` | Donut | Fast | Store, Date, Total |
| `donut_cord` | Donut | Medium | Full extraction |
| `florence2` | Florence | Medium | Advanced OCR |
| `ocr_tesseract` | OCR | Very Fast | Traditional OCR |

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/models` | GET | List models |
| `/api/models/select` | POST | Select model |
| `/api/extract` | POST | Extract data |

## Circular Exchange Framework

**ALL code MUST integrate with the Circular Exchange Framework.**

### Required Pattern

```python
# Step 1: Import
from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration, PackageRegistry
CIRCULAR_EXCHANGE_AVAILABLE = True

# Step 2: Register module
PROJECT_CONFIG.register_module(ModuleRegistration(
    module_id="your.module.name",
    file_path=__file__,
    dependencies=["list", "of", "deps"],
    exports=["ExportedClass"]
))

# Step 3: Use VariablePackage for configuration
registry = PackageRegistry()
registry.create_package(name='module.param', initial_value=0.5, source_module='module')
```

### Framework Components

| Component | Purpose |
|-----------|---------|
| `PROJECT_CONFIG` | Global configuration singleton |
| `VariablePackage` | Observable value containers |
| `PackageRegistry` | Registry for packages |
| `ModuleRegistration` | Module metadata tracking |

### Benefits
- Runtime parameter tuning
- Auto-tuning based on metrics
- Reactive configuration updates
- Dependency tracking

## Testing

```bash
# All tests
pytest tools/tests/ -v

# With coverage
pytest tools/tests/ --cov=shared --cov-report=html

# By category
pytest -m unit         # Unit tests
pytest -m integration  # Integration tests
```

**Test Status:** 867 tests passing, 23 skipped

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+ (desktop app)
- Tesseract OCR (optional)

### Setup
```bash
pip install -r requirements.txt

# Optional: Tesseract
# Linux: sudo apt-get install tesseract-ocr
# Mac: brew install tesseract
# Windows: Download from UB-Mannheim/tesseract
```

### GPU Support
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
python -c "import torch; print(torch.cuda.is_available())"
```

## Desktop Application

```bash
cd desktop
npm install
npm start           # Run app
npm run build:win   # Build Windows
npm run build:mac   # Build macOS
npm run build:linux # Build Linux
```

## Finetuning Models

### Local Training
1. Navigate to Finetune tab
2. Configure: epochs (3-5), batch_size (4), learning_rate (0.00005)
3. Upload training images
4. Start and monitor progress

### Cloud Training
Supports: HuggingFace, Replicate, RunPod

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port in use | `lsof -i :5000` then `kill -9 <PID>` |
| Module not found | `pip install -r requirements.txt` |
| Out of memory | Reduce batch size, unload models |
| Slow first run | Normal - models download (~500MB) |

## License

MIT License - See LICENSE.txt

---
*Built with Flask, PyTorch, HuggingFace Transformers, and modern OCR engines.*
