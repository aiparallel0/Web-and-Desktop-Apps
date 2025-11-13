# Debugging SROIE Donut Extraction Issues

## Summary

This document describes debugging improvements made to the SROIE Donut model extraction pipeline to diagnose why receipt extraction was failing (returning all null values with 0% confidence).

## Issues Fixed

### 1. **Missing Confidence Calculation**
**Problem**: The `DonutProcessor` was not calculating confidence scores, leaving it at the default value of 0.0.

**Fix**: Added `_calculate_confidence()` method to `DonutProcessor` class that calculates confidence based on extracted fields:
- SROIE model (basic fields):
  - Store name: +30 points
  - Total: +30 points
  - Address: +20 points
  - Date: +20 points
  - Max: 100 points

- Models with items (CORD, etc.):
  - Items: up to 45 points
  - Store name: +15 points
  - Total: +25 points (with coverage bonus)
  - Date: +5 points
  - Max: 100 points

**Location**: `/home/user/Web-and-Desktop-Apps/shared/models/donut_processor.py:204-242`

### 2. **Silent Parsing Failures**
**Problem**: When JSON parsing failed, it silently returned an empty dictionary with only debug-level logging.

**Fix**:
- Added warning-level logging when parsing fails
- Added detailed error messages for different failure modes
- Added check for empty model output
- Log attempts to extract JSON from non-JSON text

**Location**: `/home/user/Web-and-Desktop-Apps/shared/models/donut_processor.py:70-99`

### 3. **No Model Output Diagnostics**
**Problem**: When model produced no parseable output, there was no way to see what the raw output was.

**Fix**:
- Added logging of raw model output sequence
- Added logging of parsed data structure
- Added warnings when parsed data is empty
- Added diagnostic notes to extraction results

**Location**: `/home/user/Web-and-Desktop-Apps/shared/models/donut_processor.py:158-179`

### 4. **Limited Model Loading Validation**
**Problem**: No validation that model loaded correctly or logging of model configuration.

**Fix**:
- Added logging of model device (CPU/GPU)
- Added logging of max sequence length
- Added logging of task prompt
- Added logging of tokenizer vocabulary size

**Location**: `/home/user/Web-and-Desktop-Apps/shared/models/donut_processor.py:105-121`

## How to Use Enhanced Logging

### Enable Detailed Logging

Set logging level to INFO or DEBUG to see all diagnostic information:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

### Expected Log Output for Successful Extraction

```
INFO - Loading Donut model: philschmid/donut-base-sroie
INFO - Model loaded on cuda
INFO - Model max length: 1536
INFO - Task prompt: <s_sroie>
INFO - Tokenizer vocab size: 57532
INFO - Loaded image: 800x1200
INFO - Image enhancement applied
INFO - Raw model output: {"company": "STARBUCKS", "date": "01/01/2020", "address": "123 MAIN ST", "total": "10.50"}
INFO - Parsed data: {'company': 'STARBUCKS', 'date': '01/01/2020', 'address': '123 MAIN ST', 'total': '10.50'}
```

### Expected Log Output for Failed Extraction

```
INFO - Raw model output:
WARNING - Empty output from model
WARNING - Model output could not be parsed or is empty
WARNING - Raw sequence was: ...
```

or

```
INFO - Raw model output: some text without json
WARNING - Failed to parse as direct JSON: Expecting value: line 1 column 1 (char 0)
WARNING - No JSON object found in output
```

## Common Failure Modes and Diagnostics

### Mode 0: Plain Text Instead of JSON (MOST COMMON)
**Symptoms**:
- Notes: "Model produced plain text instead of JSON - used fallback extraction"
- Some fields may be populated from fallback extraction
- Confidence: 20-80% depending on what was extracted

**Logs to check**:
```
INFO - Raw model output: AVE DAILAS TX 75206 STOPE #403 - (469) 334-0614...
WARNING - Failed to parse as direct JSON
INFO - Attempting fallback text extraction from plain text output
INFO - Fallback extraction found: {'address': '...', 'total': '...'}
```

**Root cause**:
The `philschmid/donut-base-sroie` model sometimes produces plain text OCR output instead of structured JSON. This is a known issue with certain Donut model checkpoints.

**Solution**:
The fallback text extraction automatically kicks in and uses regex patterns to extract:
- Address (by finding ZIP codes)
- Total (by finding price patterns)
- Date (by finding date patterns)
- Store name (from text before address)

This provides partial extraction even when the model doesn't produce proper JSON.

**Recommendations**:
1. Try the CORD model instead: `donut_cord` (better structured output)
2. Try Florence-2 model: `florence2` (more reliable OCR)
3. Try Tesseract OCR: `ocr_tesseract` (traditional OCR with rule-based extraction)

### Mode 1: Empty Model Output
**Symptoms**:
- All fields are null
- Confidence: 0
- Notes: "Model produced no parseable output"

**Logs to check**:
```
WARNING - Empty output from model
```

**Possible causes**:
- Model not loaded correctly
- Image preprocessing issue
- Model weights corrupted

### Mode 2: Non-JSON Output
**Symptoms**:
- All fields are null
- Confidence: 0
- Notes: "Model produced no parseable output"

**Logs to check**:
```
WARNING - Failed to parse as direct JSON
WARNING - No JSON object found in output
```

**Possible causes**:
- Wrong task prompt
- Model producing text instead of structured output
- Model not fine-tuned for SROIE format

### Mode 3: JSON with Wrong Keys
**Symptoms**:
- All fields are null
- Confidence: 0
- Notes: "Model output parsed but no fields matched expected format"

**Logs to check**:
```
INFO - Parsed data: {'some_key': 'value', 'other_key': 'value'}
```

**Possible causes**:
- Model using different key names than expected
- Need to update `_build_receipt_data()` to handle alternative key names

### Mode 4: Partial Extraction
**Symptoms**:
- Some fields populated, others null
- Confidence: 30-70%
- No error notes

**This is expected behavior** - SROIE model may not extract all fields from every receipt.

## Testing the Fixes

### Option 1: Use the Debug Test Script

```bash
python3 debug_test.py path/to/receipt/image.jpg
```

This will show:
- Model loading information
- Extraction progress with detailed logging
- Final extracted data in JSON format

### Option 2: Use the Web API

Start the backend:
```bash
cd web-app/backend
python3 app.py
```

Check logs for detailed diagnostic output when making requests to `/api/extract`.

### Option 3: Use the Desktop App

The desktop app will also show enhanced logging in the console.

## Verifying the Confidence Calculation

After extraction, check the confidence score:

- **0%**: No data extracted (investigate using logs)
- **20-50%**: Partial extraction (1-2 fields)
- **60-80%**: Good extraction (3 fields)
- **100%**: Perfect extraction (all 4 SROIE fields)

## Expected SROIE Output Format

The SROIE model should produce JSON with these keys:

```json
{
  "company": "Store name here",
  "date": "DD/MM/YYYY",
  "address": "Full address here",
  "total": "XX.XX"
}
```

The `_build_receipt_data()` method maps these to:
- `company` → `receipt.store_name`
- `date` → `receipt.transaction_date`
- `address` → `receipt.store_address`
- `total` → `receipt.total` (normalized to Decimal)

## Next Steps for Further Debugging

If extraction still fails after these improvements:

1. **Check model output**: Look at the "Raw model output" log entry
2. **Verify JSON structure**: Compare logged parsed_data with expected format
3. **Test with known good images**: Use SROIE dataset samples
4. **Try alternative models**: Test with CORD or Florence-2 models
5. **Check image quality**: Use `assess_image_quality()` to verify image is readable

## Files Modified

- `/home/user/Web-and-Desktop-Apps/shared/models/donut_processor.py`
  - Added confidence calculation
  - Enhanced logging throughout extraction pipeline
  - Improved error handling for JSON parsing
  - Added diagnostic notes to extraction results

## Related Files

- `/home/user/Web-and-Desktop-Apps/shared/utils/data_structures.py` - Receipt data structures
- `/home/user/Web-and-Desktop-Apps/shared/utils/image_processing.py` - Image preprocessing
- `/home/user/Web-and-Desktop-Apps/shared/models/model_manager.py` - Model loading and management
- `/home/user/Web-and-Desktop-Apps/web-app/backend/app.py` - Flask API endpoint
