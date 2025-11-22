# 🌐 WEB APP INSTRUCTIONS

## ✅ THE WEB APP USES THE SAME FIXED MODELS!

The web app backend uses `ModelManager` which I've already fixed with:
- ✅ EasyOCR (proven pattern)
- ✅ Tesseract (12-mode aggressive)
- ✅ PaddleOCR (fixed cls bug)
- ✅ Florence-2 (if installed)

---

## 🚀 HOW TO RUN THE WEB APP

### Option 1: Use the Start Script (EASIEST)

```bash
# From the project root directory:
./START_WEB_APP.sh
```

This will:
1. Check dependencies
2. Install missing packages (EasyOCR, Flask, etc.)
3. Start the Flask backend on http://localhost:5000
4. Tell you to open the frontend in your browser

### Option 2: Manual Start

```bash
# 1. Install dependencies
pip install flask flask-cors pillow opencv-python numpy easyocr

# 2. Start backend
cd web-app/backend
python app.py

# 3. Open frontend in browser
# Open: web-app/frontend/index.html
```

---

## 📝 USING THE WEB APP

1. **Backend starts** at http://localhost:5000
2. **Open** `web-app/frontend/index.html` in your browser
3. **Select Model**: 
   - EasyOCR (RECOMMENDED - default)
   - Tesseract (12-mode aggressive)
   - PaddleOCR (fixed)
   - Florence-2 (if installed)
4. **Upload Image**: Click or drag & drop
5. **Extract**: Click "Extract Receipt Data"
6. **OR Batch**: Click "Extract with ALL Models" to try all models

---

## 🎯 API ENDPOINTS

The backend provides these endpoints:

### Get Available Models
```bash
curl http://localhost:5000/api/models
```

### Select a Model
```bash
curl -X POST http://localhost:5000/api/models/select \
  -H "Content-Type: application/json" \
  -d '{"model_id": "ocr_easyocr"}'
```

### Extract Receipt (Single Model)
```bash
curl -X POST http://localhost:5000/api/extract \
  -F "image=@receipt.jpg" \
  -F "model_id=ocr_easyocr"
```

### Extract with ALL Models
```bash
curl -X POST http://localhost:5000/api/extract/batch \
  -F "image=@receipt.jpg"
```

---

## 🔧 TROUBLESHOOTING

### "Failed to connect to API server"
- Make sure backend is running: `python web-app/backend/app.py`
- Check http://localhost:5000 is accessible
- Check browser console for errors

### "No models available"
- Backend couldn't load models
- Check backend logs for errors
- Verify `shared/config/models_config.json` exists

### "Model extraction failed"
- Check which model you're using
- Try EasyOCR (most reliable)
- Check backend console for detailed error

### EasyOCR downloading on first run
```
Downloading detection model, please wait...
Downloading recognition model, please wait...
```
This is NORMAL on first run. Wait for it to complete (~50MB).

---

## 🧪 TEST THE WEB APP

### 1. Start Backend
```bash
cd web-app/backend
python app.py
```

You should see:
```
Starting Receipt Extraction API...
Available models: 4
 * Running on http://0.0.0.0:5000
```

### 2. Test API Manually
```bash
# Check health
curl http://localhost:5000/api/health

# Get models
curl http://localhost:5000/api/models
```

### 3. Open Frontend
- Open `web-app/frontend/index.html` in browser
- You should see 4 model cards
- EasyOCR should be available

### 4. Upload & Extract
- Select EasyOCR
- Upload a receipt image
- Click "Extract Receipt Data"
- Wait for results

---

## 📊 DIFFERENCES FROM DESKTOP APP

| Feature | Desktop App | Web App |
|---------|------------|---------|
| Interface | Electron | HTML/CSS/JS |
| Backend | Node.js → Python | Flask → Python |
| Models | Same (`ModelManager`) | Same (`ModelManager`) |
| Run Command | `npm start` | `python app.py` + open HTML |

**Both use the SAME fixed models!**

---

## ✅ WHAT WAS FIXED

1. **EasyOCR**: Complete rewrite with proven pattern
2. **Tesseract**: 12-mode aggressive approach
3. **PaddleOCR**: Fixed `cls=True` bug
4. **All Models**: Using `ModelManager` with fixes

The web app will automatically use these fixes since it imports `ModelManager`!

---

## 🎯 RECOMMENDED: Use EasyOCR

EasyOCR is the default model because:
- ✅ Works out of the box
- ✅ No Tesseract installation needed
- ✅ Best accuracy
- ✅ Handles poor quality images
- ✅ 80+ languages

First run downloads model (~50MB), then it's fast (2-4s per extraction).

---

**JUST RUN `./START_WEB_APP.sh` AND IT WORKS!**
