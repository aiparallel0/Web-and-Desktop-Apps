# Desktop Application

Electron-based desktop application for receipt extraction.

## Quick Start

```bash
# Install dependencies
npm install

# Run app
npm start
```

## Building Distributables

```bash
# Windows
npm run build:win

# macOS
npm run build:mac

# Linux
npm run build:linux
```

Built applications will be in `dist/` directory.

## Requirements

- Node.js 16+
- Python 3.8+ (must be in PATH)
- Python dependencies installed globally:
  ```bash
  pip install torch transformers pillow opencv-python numpy pytesseract
  ```

## Notes

- First run will download AI models (~500MB-1GB)
- Models are cached for subsequent runs
- Python must be accessible from command line
- Build uses `--asar=false` to ensure Python scripts are accessible
