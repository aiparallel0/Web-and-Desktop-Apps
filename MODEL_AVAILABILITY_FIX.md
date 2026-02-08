# Text Detection and Model Availability Fixes

## Summary

This PR fixes critical issues preventing the 8 extraction models from working and adds comprehensive model availability status indicators to the frontend.

## Issues Fixed

### 1. Backend: Fixed ModelManager GPU Detection

**Problem:** Health check endpoint crashed with error: `'ModelManager' object has no attribute '_detect_gpu'`

**Fix:** Changed line 317 in `web/backend/app.py`:
```python
# Before (BROKEN):
'gpu_available': manager._detect_gpu()

# After (FIXED):
'gpu_available': manager.gpu_info.available if hasattr(manager, 'gpu_info') else False
```

**Result:** Health checks now work correctly, returning GPU availability status without errors.

### 2. Frontend: Added Model Availability Status Indicators

**Problem:** Frontend showed all 8 models but didn't indicate which were actually available based on installed dependencies.

**Changes to `web/frontend/components/unified-extractor-controls.js`:**

1. **API Call Update** (Line 100):
   ```javascript
   // Added check_availability=true parameter
   const response = await fetch(`${this.apiBaseUrl}/api/models?check_availability=true`, {
   ```

2. **Model Data Parsing** (Lines 114-122):
   ```javascript
   // Now includes availability status
   this.availableModels = data.models.map(model => ({
       id: model.id || model.model_id,
       name: model.name || model.id,
       description: model.description || '',
       available: model.available !== false,
       status: model.status || (model.available !== false ? 'ready' : 'unavailable'),
       missing_dependencies: model.missing_dependencies || []
   }));
   ```

3. **UI Rendering** (Lines 211-232):
   - Added status badges: "✓ Selected" (green) or "⚠ Dependencies Missing" (red)
   - Gray out unavailable models with reduced opacity
   - Show missing dependencies in red boxes below model cards
   - Add tooltips showing missing dependencies on hover
   - Disable unavailable model cards

4. **CSS Styles Added** (Lines 393-445):
   ```css
   .status-badge { /* Status indicator styling */ }
   .status-badge.selected { /* Green badge for selected */ }
   .status-badge.unavailable { /* Red badge for unavailable */ }
   .model-card.unavailable { /* Gray out unavailable models */ }
   .missing-deps { /* Red box showing missing packages */ }
   ```

5. **Event Handler Update** (Lines 527-538):
   ```javascript
   // Only allow clicking on available models
   this.shadowRoot.querySelectorAll('.model-card:not([disabled])').forEach(card => {
       card.addEventListener('click', (e) => {
           const modelId = e.currentTarget.dataset.modelId;
           const model = this.availableModels.find(m => m.id === modelId);
           
           if (model && model.available !== false) {
               this.selectModel(modelId);
           }
       });
   });
   ```

6. **Extraction Validation** (Lines 625-637):
   ```javascript
   // Prevent extraction with unavailable models
   const selectedModel = this.availableModels.find(m => m.id === this.selectedModelId);
   if (selectedModel && selectedModel.available === false) {
       throw new Error(
           `Model "${selectedModel.name}" is not available. ` +
           `Missing dependencies: ${(selectedModel.missing_dependencies || []).join(', ')}`
       );
   }
   ```

## Backend Architecture (Already Working)

### Model Availability Checking
The backend already had comprehensive model availability checking:

1. **`/api/models?check_availability=true`** - Returns models with availability status
2. **`/api/models/health`** - Detailed health check with dependency status
3. **ModelManager._check_dependencies()** - Checks for:
   - opencv (Tesseract)
   - easyocr (EasyOCR models)
   - paddleocr (PaddleOCR models)
   - torch (AI models)
   - transformers (Florence-2, DONUT)
   - craft-text-detector (CRAFT detector)
   - pytesseract (Tesseract binary)

### Detection Settings Flow
The detection settings (deskew, enhance, column mode) already work correctly:

1. **Frontend sends** (lines 602-605 of unified-extractor-controls.js):
   ```javascript
   formData.append('detection_mode', this.detectionMode);
   formData.append('enable_deskew', String(this.deskewEnabled));
   formData.append('enable_enhancement', String(this.enhanceEnabled));
   formData.append('column_mode', String(this.detectionMode === 'column'));
   ```

2. **Backend parses** (lines 631-634 of app.py):
   ```python
   detection_mode = request.form.get('detection_mode', 'auto')
   enable_deskew = request.form.get('enable_deskew', 'true').lower() in ('true', '1', 'yes')
   enable_enhancement = request.form.get('enable_enhancement', 'true').lower() in ('true', '1', 'yes')
   column_mode = request.form.get('column_mode', 'false').lower() in ('true', '1', 'yes')
   ```

3. **Applied to preprocessing** (lines 664-671 of app.py):
   ```python
   preprocessing_result = preprocess_image_with_settings(
       image,
       detection_mode=detection_mode,
       enable_deskew=enable_deskew,
       enable_enhancement=enable_enhancement,
       column_mode=column_mode,
       manual_regions=manual_regions
   )
   ```

## Dependencies

All required dependencies are already in `requirements.txt`:
- ✅ torch>=2.0.0
- ✅ torchvision>=0.15.0
- ✅ transformers>=4.30.0
- ✅ accelerate>=0.26.0
- ✅ sentencepiece>=0.1.99
- ✅ craft-text-detector>=0.4.3
- ✅ easyocr>=1.7.0
- ✅ paddleocr>=2.7.0
- ✅ pytesseract>=0.3.10

## The 8 Extraction Models

1. **Tesseract OCR** (`ocr_tesseract`)
   - Requires: pytesseract, opencv-python-headless
   - Type: Traditional OCR

2. **EasyOCR with Regex** (`ocr_easyocr`)
   - Requires: easyocr
   - Type: Deep Learning OCR

3. **EasyOCR with Spatial Bounding Boxes** (`ocr_easyocr_spatial`)
   - Requires: easyocr
   - Type: Deep Learning OCR with structure

4. **PaddleOCR with Regex** (`ocr_paddle`)
   - Requires: paddleocr, paddlepaddle
   - Type: Production OCR

5. **PaddleOCR with Spatial Bounding Boxes** (`ocr_paddle_spatial`)
   - Requires: paddleocr, paddlepaddle
   - Type: Production OCR with structure

6. **Florence-2 AI** (`florence2`)
   - Requires: torch, transformers, accelerate, sentencepiece
   - Type: Vision-Language Model

7. **DONUT End-to-End** (`donut_cord`)
   - Requires: torch, transformers, accelerate, sentencepiece
   - Type: Transformer-based Document Understanding

8. **CRAFT Text Detector** (`craft_detector`)
   - Requires: torch, craft-text-detector
   - Type: Text Detection

## Testing

### Backend Tests
```bash
cd /home/runner/work/Web-and-Desktop-Apps/Web-and-Desktop-Apps

# Test ModelManager initialization
python -c "from shared.models.manager import ModelManager; m = ModelManager(); print('GPU:', m.gpu_info)"

# Test model availability checking
python -c "
from shared.models.manager import ModelManager
m = ModelManager()
models = m.get_available_models(check_availability=True)
print(f'Total: {len(models)}')
print(f'Available: {sum(1 for x in models if x.get(\"available\"))}')
"

# Test health check code
python -c "
from shared.models.manager import ModelManager
m = ModelManager()
gpu_available = m.gpu_info.available if hasattr(m, 'gpu_info') else False
print('GPU available:', gpu_available)
"
```

### Frontend Test Page
Open `web/frontend/test-model-availability.html` to see:
- Available models with green "✓ Selected" badges
- Unavailable models with red "⚠ Dependencies Missing" badges
- Missing dependency lists
- Proper graying out and disabling

## Error Handling

### Before
- ❌ Health check crashed on missing _detect_gpu()
- ❌ Frontend showed all models as available
- ❌ No indication of missing dependencies
- ❌ Users could select unavailable models
- ❌ Extraction failed with cryptic import errors

### After
- ✅ Health check returns proper status
- ✅ Frontend shows availability status
- ✅ Clear missing dependency messages
- ✅ Unavailable models are disabled
- ✅ Clear error message when trying to use unavailable model

## Visual Changes

### Model Cards - Available
```
┌─────────────────────────────┐
│ Tesseract OCR    ✓ Selected │
│                             │
│ Fast & reliable for clear   │
│ receipts                    │
└─────────────────────────────┘
```

### Model Cards - Unavailable
```
┌─────────────────────────────┐
│ Florence-2 AI               │
│           ⚠ Dependencies... │
│                             │
│ Microsoft Vision-Language   │
│ Model                       │
│ ┌─────────────────────────┐ │
│ │ Missing: torch,         │ │
│ │ transformers            │ │
│ └─────────────────────────┘ │
└─────────────────────────────┘
  (grayed out, cannot click)
```

## Files Changed

1. `web/backend/app.py`
   - Line 317: Fixed GPU detection method call

2. `web/frontend/components/unified-extractor-controls.js`
   - Line 100: Added check_availability parameter
   - Lines 114-122: Parse availability data
   - Lines 211-232: Render status badges and missing deps
   - Lines 393-445: Added CSS for status indicators
   - Lines 527-538: Prevent clicking unavailable models
   - Lines 625-637: Validate model availability before extraction

3. `web/frontend/test-model-availability.html` (NEW)
   - Test page demonstrating the new UI

## Next Steps

To get all models working:
1. Install dependencies: `pip install -r requirements.txt`
2. For GPU acceleration: Install CUDA-enabled PyTorch
3. For Tesseract: Install tesseract binary (`apt-get install tesseract-ocr`)

## Backwards Compatibility

✅ All changes are backwards compatible:
- API still returns same structure, just adds availability fields
- Old frontend code will work (just won't show availability)
- Detection settings flow unchanged
- No breaking changes to any APIs
