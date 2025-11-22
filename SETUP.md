# Receipt Extractor - Complete Setup Guide

## 🚀 Quick Start

### 1. Install Python Dependencies

```bash
# Install all OCR engines (RECOMMENDED)
pip install -r requirements.txt

# OR install only the essentials
pip install pillow opencv-python numpy pytesseract easyocr
```

### 2. Install Tesseract (for Tesseract OCR engine)

**Windows:**
- Download and install from: https://github.com/UB-Mannheim/tesseract/wiki
- Add to PATH or the app will auto-detect common installation locations

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

### 3. Install Node Dependencies

```bash
npm install
```

### 4. Run the Application

```bash
# Desktop app
npm start

# Web app
cd web-app/backend
python app.py
# Then open web-app/frontend/index.html in your browser
```

## 📦 Available OCR Engines

### 1. **Tesseract OCR** (Default)
- ⚡ **Fastest** (1-2 seconds)
- 📦 Requires external installation
- ✅ Best for clear, printed receipts
- 🔧 Install: See step 2 above

### 2. **EasyOCR** (RECOMMENDED)
- 🎯 **Most Accurate**
- 📦 No external dependencies needed
- ⏱️ Speed: 2-4 seconds
- 🌍 Supports 80+ languages
- 🔧 Install: `pip install easyocr`

### 3. **PaddleOCR** (Enterprise)
- 🏆 **Production-Ready**
- 📦 Requires PaddlePaddle
- ⏱️ Speed: 2-3 seconds
- 🌍 Multilingual support
- 🔧 Install: `pip install paddleocr paddlepaddle`

### 4. **Florence-2 AI** (Advanced)
- 🤖 **AI-Powered**
- 📦 Requires PyTorch & Transformers
- ⏱️ Speed: 3-5 seconds
- 🧠 Advanced region detection
- 🔧 Install: `pip install torch transformers`

## 🎯 Choose Your Setup

### Minimal Setup (Tesseract Only)
```bash
pip install pillow opencv-python numpy pytesseract
# Install Tesseract binary separately
npm install
npm start
```

### Recommended Setup (EasyOCR)
```bash
pip install pillow opencv-python numpy easyocr
npm install
npm start
```

### Full Setup (All Engines)
```bash
pip install -r requirements.txt
npm install
npm start
```

## 🔧 Troubleshooting

### "Tesseract not found"
- Make sure Tesseract is installed and in your PATH
- On Windows, the app auto-detects common installation paths
- Try reinstalling from https://github.com/UB-Mannheim/tesseract/wiki

### "Module not found" errors
```bash
pip install --upgrade -r requirements.txt
```

### EasyOCR slow first run
- EasyOCR downloads models on first use (~50MB)
- Subsequent runs will be fast

### PaddleOCR issues
```bash
# Try reinstalling
pip uninstall paddleocr paddlepaddle
pip install paddleocr paddlepaddle
```

## 📝 What's New

### Complete Overhaul (Latest Version)

✅ **Fixed ALL button issues** - Extract, Save, and all buttons now work reliably
✅ **New OCR engines** - Added EasyOCR, PaddleOCR, kept Tesseract
✅ **Simplified models** - Removed broken Donut models, kept only working ones
✅ **Better error handling** - Clear messages when dependencies missing
✅ **Debug logging** - Enable DEBUG=true in renderer.js for troubleshooting
✅ **Robust text detection** - Pre-trained, production-ready OCR models
✅ **Fast & reliable** - All models tested and working

### Model Comparison

| Model | Speed | Accuracy | Setup | Best For |
|-------|-------|----------|-------|----------|
| Tesseract | ⚡⚡⚡ | ⭐⭐⭐ | Manual | Clear receipts |
| EasyOCR | ⚡⚡ | ⭐⭐⭐⭐ | Automatic | General use (RECOMMENDED) |
| PaddleOCR | ⚡⚡ | ⭐⭐⭐⭐ | Manual | Enterprise/Production |
| Florence-2 | ⚡ | ⭐⭐⭐⭐⭐ | Manual | Best accuracy |

## 🎨 Features

- ✅ Multiple OCR engines with auto-switching
- ✅ Drag & drop support
- ✅ Batch processing
- ✅ JSON, CSV, TXT export
- ✅ Dark/Light themes
- ✅ Keyboard shortcuts
- ✅ Session statistics
- ✅ Receipt history
- ✅ Multi-language support (with EasyOCR/Paddle)

## 📚 Usage

1. **Select an engine** - Choose from Tesseract, EasyOCR, PaddleOCR, or Florence-2
2. **Select/Drop image** - Choose a receipt image or drag & drop
3. **Extract** - Click Execute button or press Ctrl+E
4. **Review** - Check extracted data
5. **Export** - Save as JSON, CSV, or TXT

## 🔑 Keyboard Shortcuts

- `Ctrl+O` - Select image
- `Ctrl+E` - Extract receipt
- `Ctrl+S` - Save results
- `Ctrl+J` - Toggle JSON view

## 💡 Tips

1. **For best results:** Use EasyOCR (no setup needed, great accuracy)
2. **For speed:** Use Tesseract (requires installation)
3. **For production:** Use PaddleOCR (enterprise-grade)
4. **For accuracy:** Use Florence-2 (AI-powered)

## 🐛 Still Having Issues?

1. Enable debug logging: Set `DEBUG = true` in `renderer.js`
2. Check console logs in DevTools (Ctrl+Shift+I)
3. Verify Python dependencies: `pip list`
4. Test Tesseract: `tesseract --version`
5. Try switching to EasyOCR (no external deps needed)

---

**Need Help?** Open an issue on GitHub with debug logs!
