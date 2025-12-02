# Test Failure Remediation Steps

## Failing Test
**File:** `tests/shared/test_processors.py`  
**Test Name:** `test_extract_empty_text_lines`  
**Line:** 741

## Failure Summary

```
AssertionError: assert True is False
  where True = ExtractionResult(success=True, data=ReceiptData(store_name='More', ...)).success
```

The test expects `result.success` to be `False` with error "No text detected", but instead receives `success=True` with `store_name='More'`.

---

## Root Cause Analysis

### Problem Overview
The test provides OCR results with very low confidence values (0.05 and 0.08) expecting them to be filtered out. However, due to stale configuration caching from previous tests, the confidence threshold may be auto-tuned to a very low value, allowing these low-confidence texts through.

### Technical Details

1. **Dual Caching Issue**
   - `ocr_config.py` uses a singleton pattern with `OCRConfig._instance` (line 109)
   - `ocr_common.py` has its own module-level cache `_ocr_config` (line 43)
   - The test only resets `OCRConfig._instance`, but NOT the `_ocr_config` cache in `ocr_common.py`

2. **Auto-Tuning Impact**
   - The `OCRConfig` class has auto-tuning that can lower `detection_min_confidence` to as low as 0.1 (constant `AUTO_TUNE_CONFIDENCE_MIN` in ocr_config.py line 60)
   - With auto-retry, the threshold becomes `min_confidence * 0.5`
   - If `min_confidence` is 0.1 (auto-tuned), retry threshold is 0.05
   - This allows text with 0.05 and 0.08 confidence to pass through

3. **Code Flow**
   ```
   EasyOCRProcessor.extract()
   └── get_detection_config()  [ocr_common.py:58]
       └── get_config()  [ocr_common.py:45]
           └── Returns cached _ocr_config (may have stale auto-tuned values)
               └── OCRConfig.get_detection_config()  [ocr_config.py:532]
                   └── Returns detection_min_confidence (possibly 0.1 from auto-tuning)
   ```

### Evidence
- Test setup resets only `OCRConfig._instance = None` (line 727)
- Does NOT call `reset_ocr_config()` which would reset both caches
- The `reset_ocr_config()` function in `ocr_config.py` (lines 902-911) properly resets both the global `_ocr_config` and the singleton instance

---

## Remediation Steps

### Step 1: Update Test Setup
**File:** `tests/shared/test_processors.py`  
**Location:** Lines 721-742

**Current Code:**
```python
@pytest.mark.unit
@patch('shared.models.processors.easyocr')
def test_extract_empty_text_lines(mock_easyocr, easyocr_config):
    """Test parsing with empty text lines after filtering"""
    # Reset OCRConfig before test to ensure clean state
    from shared.models.ocr_config import OCRConfig
    OCRConfig._instance = None
    
    # ... rest of test
```

**Required Change:**
Replace the manual singleton reset with the proper reset function:

```python
@pytest.mark.unit
@patch('shared.models.processors.easyocr')
def test_extract_empty_text_lines(mock_easyocr, easyocr_config):
    """Test parsing with empty text lines after filtering"""
    # Reset OCRConfig before test to ensure clean state
    from shared.models.ocr_config import reset_ocr_config
    reset_ocr_config()
    
    # Additionally, reset the ocr_common module cache
    import shared.models.ocr_common as ocr_common
    ocr_common._ocr_config = None
    
    # ... rest of test
```

### Step 2: Alternative - Add Cleanup Function
**Optional Enhancement - NOT Required**

If the above fix doesn't fully resolve the issue, add a comprehensive reset in `ocr_common.py`:

**File:** `shared/models/ocr_common.py`

Add after line 55:
```python
def reset_config_cache():
    """Reset the module-level config cache for test isolation."""
    global _ocr_config
    _ocr_config = None
```

Then update `ocr_config.py` `reset_ocr_config()` to also call this:
```python
def reset_ocr_config() -> None:
    global _ocr_config
    _ocr_config = None
    OCRConfig.reset_instance()
    
    # Also reset ocr_common module cache
    try:
        from . import ocr_common
        ocr_common._ocr_config = None
    except ImportError:
        pass
```

### Step 3: Verify Fix
After making the changes:

1. Run the specific failing test:
   ```bash
   pytest tests/shared/test_processors.py::test_extract_empty_text_lines -v
   ```

2. Run the full test suite to ensure no regressions:
   ```bash
   pytest tests/shared/test_processors.py -v
   ```

3. Expected outcome:
   - `test_extract_empty_text_lines` should pass
   - All other tests should continue to pass

---

## Files to Modify

| File | Action | Lines |
|------|--------|-------|
| `tests/shared/test_processors.py` | Modify | 725-728 |
| `shared/models/ocr_common.py` | Optional Add | After line 55 |
| `shared/models/ocr_config.py` | Optional Modify | 902-911 |

---

## Verification Checklist

- [ ] Test `test_extract_empty_text_lines` passes
- [ ] All 878 other tests continue to pass
- [ ] No new warnings introduced
- [ ] Configuration isolation works correctly between tests

---

## Risk Assessment

**Low Risk** - The changes are localized to:
1. Test setup code (primary fix)
2. Optional: Configuration reset functions (defensive enhancement)

The fix addresses proper test isolation without changing production logic.
