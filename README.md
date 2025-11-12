# Receipt Extractor - Text Detection from Receipts

AI-powered receipt text extraction with support for both **Web Application** and **Electron Desktop Application**.

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
