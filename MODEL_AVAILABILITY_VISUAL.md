# Model Availability UI - Visual Comparison

## Before Fix ❌

### Health Check Endpoint
```
GET /api/health
❌ CRASH: AttributeError: 'ModelManager' object has no attribute '_detect_gpu'
```

### Frontend UI (No Availability Checking)
```
┌────────────────────────────────────────────────────────┐
│  Select Extraction Method                              │
├────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Tesseract    │  │ EasyOCR      │  │ PaddleOCR    │ │
│  │ OCR          │  │              │  │              │ │
│  │              │  │              │  │              │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Florence-2   │  │ DONUT        │  │ CRAFT        │ │
│  │              │  │              │  │              │ │
│  │              │  │              │  │              │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└────────────────────────────────────────────────────────┘

PROBLEM: All models appear clickable
❌ No indication which models are actually available
❌ User clicks Florence-2 → Gets cryptic ImportError
❌ No way to know what dependencies are missing
```

## After Fix ✅

### Health Check Endpoint
```
GET /api/health
✅ SUCCESS 200 OK
{
  "status": "healthy",
  "checks": {
    "models": {
      "status": "operational",
      "available": 8,
      "loaded": 0,
      "gpu_available": false  ← Now works!
    }
  }
}
```

### Frontend UI (With Availability Status)
```
┌────────────────────────────────────────────────────────────────┐
│  Select Extraction Method                                      │
├────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ Tesseract OCR    │  │ EasyOCR          │  │ PaddleOCR    │ │
│  │ ⚠ Dependencies...│  │ ⚠ Dependencies...│  │ ⚠ Depend...  │ │
│  │ Fast & reliable  │  │ 80+ languages    │  │ Multilingual │ │
│  │ ┌──────────────┐ │  │ ┌──────────────┐ │  │ ┌──────────┐ │ │
│  │ │Missing:      │ │  │ │Missing:      │ │  │ │Missing:  │ │ │
│  │ │pytesseract,  │ │  │ │easyocr       │ │  │ │paddleocr │ │ │
│  │ │opencv        │ │  │ └──────────────┘ │  │ └──────────┘ │ │
│  │ └──────────────┘ │  │                  │  │              │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│     (grayed out)          (grayed out)          (grayed out)   │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ Florence-2 AI    │  │ DONUT End-to-End │  │ CRAFT Detect │ │
│  │ ⚠ Dependencies...│  │ ⚠ Dependencies...│  │ ⚠ Depend...  │ │
│  │ Vision-Language  │  │ Transformer-based│  │ Text detect  │ │
│  │ ┌──────────────┐ │  │ ┌──────────────┐ │  │ ┌──────────┐ │ │
│  │ │Missing:      │ │  │ │Missing:      │ │  │ │Missing:  │ │ │
│  │ │torch,        │ │  │ │torch,        │ │  │ │torch,    │ │ │
│  │ │transformers  │ │  │ │transformers  │ │  │ │craft-... │ │ │
│  │ └──────────────┘ │  │ └──────────────┘ │  │ └──────────┘ │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│     (grayed out)          (grayed out)          (grayed out)   │
└────────────────────────────────────────────────────────────────┘

✅ Clear visual status for each model
✅ Unavailable models are grayed out and disabled
✅ Shows exactly which dependencies are missing
✅ Cannot click on unavailable models
✅ Clear error if trying to use unavailable model
```

### With All Dependencies Installed
```
┌────────────────────────────────────────────────────────────────┐
│  Select Extraction Method                                      │
├────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ Tesseract OCR    │  │ EasyOCR          │  │ PaddleOCR    │ │
│  │    ✓ Selected    │  │                  │  │              │ │
│  │ Fast & reliable  │  │ 80+ languages    │  │ Multilingual │ │
│  │ for clear rcpts  │  │ ready-to-use     │  │ high accuracy│ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│      (selected)            (available)          (available)    │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ Florence-2 AI    │  │ DONUT End-to-End │  │ CRAFT Detect │ │
│  │                  │  │                  │  │              │ │
│  │ Vision-Language  │  │ Transformer-based│  │ Text detect  │ │
│  │ Model            │  │ doc understand   │  │ regions      │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│      (available)           (available)          (available)    │
└────────────────────────────────────────────────────────────────┘

✅ All models available and clickable
✅ Green "✓ Selected" badge on current model
✅ No missing dependency warnings
✅ All models ready to use
```

## API Response Comparison

### Before: /api/models (No Availability Check)
```json
{
  "success": true,
  "models": [
    {
      "id": "ocr_tesseract",
      "name": "Tesseract OCR",
      "description": "Fast & reliable",
      "type": "ocr"
    },
    {
      "id": "florence2",
      "name": "Florence-2 AI",
      "description": "Vision-Language Model",
      "type": "florence"
    }
  ],
  "default_model": "ocr_tesseract"
}
```
❌ No way to know if models will actually work!

### After: /api/models?check_availability=true
```json
{
  "success": true,
  "models": [
    {
      "id": "ocr_tesseract",
      "name": "Tesseract OCR",
      "description": "Fast & reliable",
      "type": "ocr",
      "available": false,
      "status": "missing_dependencies",
      "missing_dependencies": ["pytesseract", "opencv-python-headless"],
      "error": "Missing: pytesseract, opencv-python-headless"
    },
    {
      "id": "florence2",
      "name": "Florence-2 AI",
      "description": "Vision-Language Model",
      "type": "florence",
      "available": false,
      "status": "missing_dependencies",
      "missing_dependencies": ["torch", "transformers"],
      "error": "Missing: torch, transformers"
    }
  ],
  "default_model": "ocr_tesseract",
  "working_count": 0
}
```
✅ Clear status for each model
✅ Exact list of missing dependencies
✅ Count of working models

## Code Flow Comparison

### Before (No Availability Checking)
```
User clicks model → Frontend sends request → Backend tries to load model
                                                          ↓
                                              ImportError: No module named 'torch'
                                                          ↓
                                              User sees: "Extraction failed"
                                              ❌ No guidance on what to do
```

### After (With Availability Checking)
```
Page loads → Frontend calls /api/models?check_availability=true
                                    ↓
                    Backend checks: torch, transformers, craft, easyocr...
                                    ↓
            Returns: available=false, missing_dependencies=['torch', ...]
                                    ↓
          Frontend renders: Grayed out cards with missing deps
                                    ↓
      User sees: "⚠ Dependencies Missing: torch, transformers"
                                    ↓
✅ User knows exactly what to install: pip install torch transformers
```

## User Experience Comparison

### Before
```
User Flow:
1. Opens app
2. Sees all 8 models
3. Clicks "Florence-2 AI" (looks cool!)
4. Uploads receipt
5. Clicks "Extract"
6. ❌ ERROR: "Extraction failed"
7. ❌ No idea what went wrong
8. 😞 User gives up
```

### After
```
User Flow:
1. Opens app
2. Sees all 8 models
3. Florence-2 is grayed out with "⚠ Dependencies Missing"
4. Hovers over → Tooltip shows "Missing: torch, transformers"
5. Tries to click → Nothing happens (disabled)
6. Looks at models → Tesseract shows "⚠ Dependencies Missing"
7. ✅ Sees clear message: "Missing: pytesseract, opencv"
8. Runs: pip install pytesseract opencv-python-headless
9. Refreshes page
10. ✅ Tesseract now shows as available
11. Clicks Tesseract → Shows "✓ Selected"
12. Uploads receipt → Extraction works!
13. 😊 Happy user
```

## Installation Guide Display

### Before
```
No guidance - user has to figure out dependencies
```

### After
```
When hovering over unavailable Florence-2:
┌────────────────────────────────────────┐
│ Florence-2 AI                          │
│ ⚠ Dependencies Missing                 │
│                                        │
│ Microsoft Vision-Language Model        │
│ ┌────────────────────────────────────┐ │
│ │ Missing: torch, transformers       │ │
│ │                                    │ │
│ │ To enable this model, run:         │ │
│ │ pip install torch transformers     │ │
│ │          accelerate sentencepiece  │ │
│ └────────────────────────────────────┘ │
└────────────────────────────────────────┘
    (tooltip on hover)
```

## Architecture Diagram

### Backend Dependency Checking
```
ModelManager._check_dependencies()
    ↓
    ├─→ Check opencv → ✗ Not installed
    ├─→ Check easyocr → ✗ Not installed
    ├─→ Check paddleocr → ✗ Not installed
    ├─→ Check torch → ✗ Not installed
    ├─→ Check transformers → ✗ Not installed
    ├─→ Check craft-text-detector → ✗ Not installed
    └─→ Check pytesseract → ✗ Not installed
    ↓
get_available_models(check_availability=True)
    ↓
    For each model:
    ├─→ ocr_tesseract → Needs opencv + pytesseract → ✗ Unavailable
    ├─→ ocr_easyocr → Needs easyocr → ✗ Unavailable
    ├─→ ocr_paddle → Needs paddleocr → ✗ Unavailable
    ├─→ florence2 → Needs torch + transformers → ✗ Unavailable
    ├─→ donut_cord → Needs torch + transformers → ✗ Unavailable
    └─→ craft_detector → Needs torch + craft → ✗ Unavailable
    ↓
Return to frontend with availability flags
```

### Frontend Display Logic
```
Fetch models with availability
    ↓
For each model in UI:
    ├─→ if available === false:
    │       ├─→ Add class "unavailable"
    │       ├─→ Add "⚠ Dependencies Missing" badge
    │       ├─→ Show missing_dependencies list
    │       ├─→ Set disabled attribute
    │       └─→ Gray out with opacity: 0.7
    │
    └─→ if available === true:
            ├─→ Clickable
            └─→ if selected:
                    └─→ Add "✓ Selected" badge
```

## Summary

| Aspect | Before ❌ | After ✅ |
|--------|-----------|----------|
| **Health Check** | Crashes on `_detect_gpu()` | Works correctly |
| **Model Status** | All shown as available | Shows actual availability |
| **Missing Deps** | No indication | Clear list displayed |
| **UI Feedback** | Generic error on fail | Specific dependency errors |
| **User Guidance** | None | Exact pip install commands |
| **Click Behavior** | All clickable | Only available clickable |
| **Visual Indication** | All same appearance | Grayed out unavailable |
| **Error Prevention** | Fails at extraction | Prevented before extraction |

The fix transforms the user experience from confusing errors to clear, actionable guidance! 🎯
