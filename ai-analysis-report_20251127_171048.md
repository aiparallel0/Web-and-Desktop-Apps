# Receipt Extractor - System Analysis Report
**Generated:** 2025-11-27 17:10:48
**Purpose:** Comprehensive system state for AI-assisted development

---

## Executive Summary

This report contains complete system diagnostics, test results, error logs,
and configuration details for the Receipt Extractor application.
Use this report to understand the current state and identify issues.

## System Environment

### Platform Information
- **OS:** MINGW64_NT-10.0-26100
- **Kernel:** 3.5.4-1e8cf1a5.x86_64
- **Architecture:** x86_64
- **Python Version:** Python 3.12.10
- **Working Directory:** /c/Users/User/desktop/Web-and-Desktop-Apps

### Hardware Resources
- **Disk Space:** 477G total, 149G used, 328G available

## Dependency Status

### Last Dependency Install Log
```
ERROR: Could not find a version that satisfies the requirement paddlepaddle==2.6.0 (from versions: 2.6.2, 3.0.0b0, 3.0.0b1, 3.0.0b2, 3.0.0rc0, 3.0.0rc1, 3.0.0, 3.1.0, 3.1.1, 3.2.0, 3.2.1, 3.2.2)
ERROR: No matching distribution found for paddlepaddle==2.6.0
```

### Python Packages
```
flask-cors            6.0.1
opencv-contrib-python 4.10.0.84
opencv-python         4.12.0.88
paddleocr             3.3.2
pillow                12.0.0
pytest-flask          1.3.0
torch                 2.9.1
torchvision           0.24.1
transformers          4.57.1
```

## GPU Configuration

GPU check not run. Status: false

## Test Results

**Overall Status:** ⚠️ NOT RUN OR FAILED

### Test: api
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.1, pluggy-1.6.0 -- C:\Users\User\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\User\desktop\Web-and-Desktop-Apps
configfile: pytest.ini
plugins: anyio-4.11.0, cov-7.0.0, flask-1.3.0, mock-3.15.1, requests-mock-1.12.1
collecting ... collected 5 items

tests/web/test_api.py::test_api_health_check SKIPPED (Flask app needs to
be imported)                                                             [ 20%]
tests/web/test_api.py::test_api_extract_receipt SKIPPED (Flask app needs
to be imported)                                                          [ 40%]
tests/web/test_api.py::test_api_get_models SKIPPED (Flask app needs to
be imported)                                                             [ 60%]
tests/web/test_api.py::test_api_invalid_image SKIPPED (Flask app needs
to be imported)                                                          [ 80%]
tests/web/test_api.py::test_api_requirements_installed PASSED            [100%]C:\Users\User\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\coverage\control.py:950: CoverageWarning: No data was collected. (no-data-collected); see https://coverage.readthedocs.io/en/7.12.0/messages.html#warning-no-data-collected
  self._warn("No data was collected.", slug="no-data-collected")


=============================== tests coverage ================================
______________ coverage: platform win32, python 3.12.10-final-0 _______________

Name                                 Stmts   Miss  Cover   Missing
------------------------------------------------------------------
shared\__init__.py                       0      0   100%
shared\models\__init__.py                5      5     0%   1-6
shared\models\base_processor.py         45     45     0%   1-46
shared\models\donut_finetuner.py       101    101     0%   1-148
shared\models\donut_processor.py       339    339     0%   1-341
shared\models\easyocr_processor.py     121    121     0%   1-127
shared\models\model_manager.py         173    173     0%   1-174
shared\models\model_trainer.py          82     82     0%   1-95
shared\models\ocr_processor.py         193    193     0%   1-204
shared\models\paddle_processor.py      180    180     0%   1-187
shared\utils\__init__.py                 3      3     0%   1-10
shared\utils\data_structures.py         43     43     0%   1-43
shared\utils\image_processing.py       118    118     0%   1-119
shared\utils\logger.py                  54     54     0%   1-55
web-app\backend\app.py                 311    311     0%   1-317
------------------------------------------------------------------
TOTAL                                 1768   1768     0%
Coverage HTML written to dir htmlcov
======================== 1 passed, 4 skipped in 1.92s =========================
```

### Test: health
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.1, pluggy-1.6.0 -- C:\Users\User\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\User\desktop\Web-and-Desktop-Apps
configfile: pytest.ini
plugins: anyio-4.11.0, cov-7.0.0, flask-1.3.0, mock-3.15.1, requests-mock-1.12.1
collecting ... collected 8 items

tests/test_system_health.py::test_python_version PASSED                  [ 12%]
tests/test_system_health.py::test_core_dependencies PASSED               [ 25%]
tests/test_system_health.py::test_tesseract_installation PASSED          [ 37%]
tests/test_system_health.py::test_config_files PASSED                    [ 50%]
tests/test_system_health.py::test_model_manager_initialization PASSED    [ 62%]
tests/test_system_health.py::test_memory_available PASSED                [ 75%]
tests/test_system_health.py::test_disk_space PASSED                      [ 87%]
tests/test_system_health.py::test_cuda_availability PASSED               [100%]

=============================== tests coverage ================================
______________ coverage: platform win32, python 3.12.10-final-0 _______________

Name                                 Stmts   Miss  Cover   Missing
------------------------------------------------------------------
shared\__init__.py                       0      0   100%
shared\models\__init__.py                5      0   100%
shared\models\base_processor.py         45     45     0%   1-46
shared\models\donut_finetuner.py       101    101     0%   1-148
shared\models\donut_processor.py       339    306    10%   16-19, 21, 23, 26-32, 35-54, 57-79, 81-118, 120-130, 132-159, 161-206, 208-246, 248-267, 270-289, 291-327, 329-341
shared\models\easyocr_processor.py     121    121     0%   1-127
shared\models\model_manager.py         173    107    38%   22-27, 44-51, 56-60, 77, 79, 81-87, 89, 91-137, 139-142, 144-151, 153-159, 161-163, 165-168, 170-174
shared\models\model_trainer.py          82     82     0%   1-95
shared\models\ocr_processor.py         193    169    12%   11-12, 20-28, 31-35, 38-55, 58-72, 75-118, 121-130, 133-169, 172-194, 198-204
shared\models\paddle_processor.py      180    160    11%   11-12, 20-28, 31-86, 89-141, 144-177, 181-187
shared\utils\__init__.py                 3      0   100%
shared\utils\data_structures.py         43      7    84%   11, 30, 32-35, 43
shared\utils\image_processing.py       118    106    10%   8-26, 28-41, 43-51, 53-88, 90-110, 112-119
shared\utils\logger.py                  54     54     0%   1-55
web-app\backend\app.py                 311    311     0%   1-317
------------------------------------------------------------------
TOTAL                                 1768   1569    11%
Coverage HTML written to dir htmlcov
======================= 8 passed, 2 warnings in 24.92s ========================
```

### Test: image
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.1, pluggy-1.6.0 -- C:\Users\User\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\User\desktop\Web-and-Desktop-Apps
configfile: pytest.ini
plugins: anyio-4.11.0, cov-7.0.0, flask-1.3.0, mock-3.15.1, requests-mock-1.12.1
collecting ... collected 7 items

tests/shared/test_image_processing.py::test_image_formats_supported PASSED [ 14%]
tests/shared/test_image_processing.py::test_image_validation PASSED      [ 28%]
tests/shared/test_image_processing.py::test_load_and_validate_image PASSED [ 42%]
tests/shared/test_image_processing.py::test_enhance_image PASSED         [ 57%]
tests/shared/test_image_processing.py::test_assess_image_quality PASSED  [ 71%]
tests/shared/test_image_processing.py::test_resize_if_needed PASSED      [ 85%]
tests/shared/test_image_processing.py::test_brightness_and_contrast_thresholds PASSED [100%]

=============================== tests coverage ================================
______________ coverage: platform win32, python 3.12.10-final-0 _______________

Name                                 Stmts   Miss  Cover   Missing
------------------------------------------------------------------
shared\__init__.py                       0      0   100%
shared\models\__init__.py                5      5     0%   1-6
shared\models\base_processor.py         45     45     0%   1-46
shared\models\donut_finetuner.py       101    101     0%   1-148
shared\models\donut_processor.py       339    339     0%   1-341
shared\models\easyocr_processor.py     121    121     0%   1-127
shared\models\model_manager.py         173    173     0%   1-174
shared\models\model_trainer.py          82     82     0%   1-95
shared\models\ocr_processor.py         193    193     0%   1-204
shared\models\paddle_processor.py      180    180     0%   1-187
shared\utils\__init__.py                 3      0   100%
shared\utils\data_structures.py         43      7    84%   11, 30, 32-35, 43
shared\utils\image_processing.py       118     70    41%   17-21, 24-26, 39-41, 49-51, 53-88, 90-110
shared\utils\logger.py                  54     54     0%   1-55
web-app\backend\app.py                 311    311     0%   1-317
------------------------------------------------------------------
TOTAL                                 1768   1681     5%
Coverage HTML written to dir htmlcov
============================== 7 passed in 1.90s ==============================
```

### Test: models
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.1, pluggy-1.6.0 -- C:\Users\User\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\User\desktop\Web-and-Desktop-Apps
configfile: pytest.ini
plugins: anyio-4.11.0, cov-7.0.0, flask-1.3.0, mock-3.15.1, requests-mock-1.12.1
collecting ... collected 11 items

tests/shared/test_model_manager.py::test_models_config_exists PASSED     [  9%]
tests/shared/test_model_manager.py::test_models_config_valid_json PASSED [ 18%]
tests/shared/test_model_manager.py::test_models_config_has_required_models PASSED [ 27%]
tests/shared/test_model_manager.py::test_default_model_exists PASSED     [ 36%]
tests/shared/test_model_manager.py::test_model_schema PASSED             [ 45%]
tests/shared/test_model_manager.py::test_model_manager_initialization PASSED [ 54%]
tests/shared/test_model_manager.py::test_model_manager_get_available_models PASSED [ 63%]
tests/shared/test_model_manager.py::test_model_manager_get_default_model PASSED [ 72%]
tests/shared/test_model_manager.py::test_model_manager_select_model PASSED [ 81%]
tests/shared/test_model_manager.py::test_model_manager_get_model_info PASSED [ 90%]
tests/shared/test_model_manager.py::test_model_manager_filter_by_capability PASSED [100%]

=============================== tests coverage ================================
______________ coverage: platform win32, python 3.12.10-final-0 _______________

Name                                 Stmts   Miss  Cover   Missing
------------------------------------------------------------------
shared\__init__.py                       0      0   100%
shared\models\__init__.py                5      0   100%
shared\models\base_processor.py         45     45     0%   1-46
shared\models\donut_finetuner.py       101    101     0%   1-148
shared\models\donut_processor.py       339    306    10%   16-19, 21, 23, 26-32, 35-54, 57-79, 81-118, 120-130, 132-159, 161-206, 208-246, 248-267, 270-289, 291-327, 329-341
shared\models\easyocr_processor.py     121    121     0%   1-127
shared\models\model_manager.py         173     93    46%   22-27, 44-51, 56-60, 91-137, 139-142, 144-151, 153-159, 161-163, 170-174
shared\models\model_trainer.py          82     82     0%   1-95
shared\models\ocr_processor.py         193    169    12%   11-12, 20-28, 31-35, 38-55, 58-72, 75-118, 121-130, 133-169, 172-194, 198-204
shared\models\paddle_processor.py      180    160    11%   11-12, 20-28, 31-86, 89-141, 144-177, 181-187
shared\utils\__init__.py                 3      0   100%
shared\utils\data_structures.py         43      7    84%   11, 30, 32-35, 43
shared\utils\image_processing.py       118    106    10%   8-26, 28-41, 43-51, 53-88, 90-110, 112-119
shared\utils\logger.py                  54     54     0%   1-55
web-app\backend\app.py                 311    311     0%   1-317
------------------------------------------------------------------
TOTAL                                 1768   1555    12%
Coverage HTML written to dir htmlcov
============================= 11 passed in 24.90s =============================
```

### Test: ocr
```
Usage: python test_ocr_simple.py <image_path>
```

## Application Logs

### Backend Log (Last 100 lines)
```
2025-11-27 16:43:56,827 - __main__ - INFO - Available models: 6
 * Serving Flask app 'app'
 * Debug mode: off
2025-11-27 16:43:56,840 - werkzeug - INFO - [31m[1mWARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.[0m
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://161.9.81.136:5000
2025-11-27 16:43:56,840 - werkzeug - INFO - [33mPress CTRL+C to quit[0m
2025-11-27 16:52:44,156 - __main__ - INFO - Batch processing 5 images with 6 models
2025-11-27 16:52:44,157 - shared.models.model_manager - INFO - Loading processor for ocr_tesseract (type: ocr)
2025-11-27 16:52:44,157 - shared.models.ocr_processor - INFO - Searching Tesseract...
2025-11-27 16:52:44,163 - shared.models.ocr_processor - INFO - Tesseract: C:\Program Files\Tesseract-OCR\tesseract.exe
2025-11-27 16:52:44,227 - shared.models.ocr_processor - INFO - Tesseract v5.5.0.20241111
2025-11-27 16:52:44,227 - shared.models.model_manager - INFO - \u2713 Loaded and cached processor for ocr_tesseract
2025-11-27 16:52:44,227 - utils.image_processing - INFO - Loading image from: C:\Users\User\AppData\Local\Temp\tmp5wfbib9e.jpg (size: 128440 bytes)
2025-11-27 16:52:44,349 - utils.image_processing - INFO - Loaded image successfully: 612x1023
2025-11-27 16:52:44,375 - utils.image_processing - INFO - Image array shape: (1023, 612, 3)
2025-11-27 16:52:44,424 - utils.image_processing - INFO - Skew angle 0.00� is negligible, skipping correction
2025-11-27 16:52:44,957 - utils.image_processing - INFO - Aggressive OCR preprocessing complete
2025-11-27 16:52:45,794 - shared.models.ocr_processor - INFO - OCR complete: PSM 4, len=159
2025-11-27 16:52:54,843 - shared.models.model_manager - INFO - Loading processor for ocr_easyocr (type: easyocr)
2025-11-27 16:52:54,843 - shared.models.model_manager - ERROR - \u274c Failed to load processor ocr_easyocr: EasyOCR not installed: pip install easyocr
2025-11-27 16:52:54,843 - __main__ - ERROR - Model ocr_easyocr failed on New_folder_0.jpg: EasyOCR not installed: pip install easyocr
2025-11-27 16:52:54,843 - shared.models.model_manager - INFO - Loading processor for ocr_paddle (type: paddle)
2025-11-27 16:52:54,843 - shared.models.paddle_processor - INFO - Initializing PaddleOCR...
INFO: Could not find files for the given pattern(s).
C:\Users\User\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\paddle\utils\cpp_extension\extension_utils.py:718: UserWarning: No ccache found. Please be aware that recompiling all source files may be required. You can download and install ccache from: https://github.com/ccache/ccache/blob/master/doc/INSTALL.md
  warnings.warn(warning_message)
[32mCreating model: ('PP-LCNet_x1_0_doc_ori', None)[0m
[32mModel files already exist. Using cached files. To redownload, please delete the directory manually: `C:\Users\User\.paddlex\official_models\PP-LCNet_x1_0_doc_ori`.[0m
WARNING: Logging before InitGoogleLogging() is written to STDERR
I1127 16:52:57.252945 19152 onednn_context.cc:81] oneDNN v3.6.2
[32mCreating model: ('UVDoc', None)[0m
[32mModel files already exist. Using cached files. To redownload, please delete the directory manually: `C:\Users\User\.paddlex\official_models\UVDoc`.[0m
[32mCreating model: ('PP-LCNet_x1_0_textline_ori', None)[0m
[32mModel files already exist. Using cached files. To redownload, please delete the directory manually: `C:\Users\User\.paddlex\official_models\PP-LCNet_x1_0_textline_ori`.[0m
[32mCreating model: ('PP-OCRv5_server_det', None)[0m
[32mModel files already exist. Using cached files. To redownload, please delete the directory manually: `C:\Users\User\.paddlex\official_models\PP-OCRv5_server_det`.[0m
[32mCreating model: ('en_PP-OCRv5_mobile_rec', None)[0m
[32mModel files already exist. Using cached files. To redownload, please delete the directory manually: `C:\Users\User\.paddlex\official_models\en_PP-OCRv5_mobile_rec`.[0m
2025-11-27 16:53:36,255 - shared.models.donut_processor - WARNING - Failed to parse as direct JSON: Expecting value: line 1 column 1 (char 0)
2025-11-27 16:53:36,255 - shared.models.donut_processor - WARNING - No JSON object found in output
2025-11-27 16:53:36,255 - shared.models.donut_processor - WARNING - Model output could not be parsed as JSON
2025-11-27 16:53:36,255 - shared.models.donut_processor - WARNING - Raw sequence was: <s_menu><s_nm> ALWAYS LOW PRICES.</s_nm><s_price> Always.</s_price><sep/><s_nm> SUPERCENTER</s_nm><sep/><s_nm> OPEN 24 HOURS</s_nm><s_unitprice> MANAGER . TBA</s_nm><s_unitprice> 515 ) 986 - 1783</s_u...
2025-11-27 16:53:36,257 - shared.models.donut_processor - WARNING - Failed to parse as direct JSON: Expecting value: line 1 column 1 (char 0)
2025-11-27 16:53:36,257 - shared.models.donut_processor - WARNING - No JSON object found in output
2025-11-27 16:53:36,746 - shared.models.donut_processor - ERROR - Load attempt 1 failed: You are trying to access a gated repo.
Make sure to have access to it at https://huggingface.co/AdamCodd/donut-receipts-extract.
401 Client Error. (Request ID: Root=1-692857e0-5113025f37f578456ca4cfcd;74bf40b3-e764-4a5e-90f4-b7e5bc8cb512)

Cannot access gated repo for url https://huggingface.co/AdamCodd/donut-receipts-extract/resolve/main/preprocessor_config.json.
Access to model AdamCodd/donut-receipts-extract is restricted. You must have access to it and be authenticated to access it. Please log in.
2025-11-27 16:53:38,041 - shared.models.donut_processor - ERROR - Load attempt 2 failed: You are trying to access a gated repo.
Make sure to have access to it at https://huggingface.co/AdamCodd/donut-receipts-extract.
401 Client Error. (Request ID: Root=1-692857e1-2549cf82423e3417008c389d;4515ca35-6758-48a7-8971-001cc0eea8a3)

Cannot access gated repo for url https://huggingface.co/AdamCodd/donut-receipts-extract/resolve/main/preprocessor_config.json.
Access to model AdamCodd/donut-receipts-extract is restricted. You must have access to it and be authenticated to access it. Please log in.
2025-11-27 16:53:40,335 - shared.models.donut_processor - ERROR - Load attempt 3 failed: You are trying to access a gated repo.
Make sure to have access to it at https://huggingface.co/AdamCodd/donut-receipts-extract.
401 Client Error. (Request ID: Root=1-692857e3-55d9a0f65af71ad779c6c131;7a242750-7940-4f93-93d1-a88a4861ec57)

Cannot access gated repo for url https://huggingface.co/AdamCodd/donut-receipts-extract/resolve/main/preprocessor_config.json.
Access to model AdamCodd/donut-receipts-extract is restricted. You must have access to it and be authenticated to access it. Please log in.
2025-11-27 16:53:40,335 - shared.models.donut_processor - ERROR - Failed to load AdamCodd/donut-receipts-extract after 3 attempts.
This could be due to:
  - Network connection issues (check internet)
  - HuggingFace service unavailable
  - Insufficient disk space (models can be 500MB-1GB)
  - Model not found or access denied
Last error: You are trying to access a gated repo.
Make sure to have access to it at https://huggingface.co/AdamCodd/donut-receipts-extract.
401 Client Error. (Request ID: Root=1-692857e3-55d9a0f65af71ad779c6c131;7a242750-7940-4f93-93d1-a88a4861ec57)

Cannot access gated repo for url https://huggingface.co/AdamCodd/donut-receipts-extract/resolve/main/preprocessor_config.json.
Access to model AdamCodd/donut-receipts-extract is restricted. You must have access to it and be authenticated to access it. Please log in.
2025-11-27 16:53:40,335 - shared.models.model_manager - ERROR - \u274c Failed to load processor donut_receipts: Failed to load AdamCodd/donut-receipts-extract after 3 attempts.
This could be due to:
  - Network connection issues (check internet)
  - HuggingFace service unavailable
  - Insufficient disk space (models can be 500MB-1GB)
  - Model not found or access denied
Last error: You are trying to access a gated repo.
Make sure to have access to it at https://huggingface.co/AdamCodd/donut-receipts-extract.
401 Client Error. (Request ID: Root=1-692857e3-55d9a0f65af71ad779c6c131;7a242750-7940-4f93-93d1-a88a4861ec57)

Cannot access gated repo for url https://huggingface.co/AdamCodd/donut-receipts-extract/resolve/main/preprocessor_config.json.
Access to model AdamCodd/donut-receipts-extract is restricted. You must have access to it and be authenticated to access it. Please log in.
2025-11-27 16:53:40,335 - __main__ - ERROR - Model donut_receipts failed on New_folder_0.jpg: Failed to load AdamCodd/donut-receipts-extract after 3 attempts.
This could be due to:
  - Network connection issues (check internet)
  - HuggingFace service unavailable
  - Insufficient disk space (models can be 500MB-1GB)
  - Model not found or access denied
Last error: You are trying to access a gated repo.
Make sure to have access to it at https://huggingface.co/AdamCodd/donut-receipts-extract.
401 Client Error. (Request ID: Root=1-692857e3-55d9a0f65af71ad779c6c131;7a242750-7940-4f93-93d1-a88a4861ec57)

Cannot access gated repo for url https://huggingface.co/AdamCodd/donut-receipts-extract/resolve/main/preprocessor_config.json.
Access to model AdamCodd/donut-receipts-extract is restricted. You must have access to it and be authenticated to access it. Please log in.
```

### Frontend Log (Last 50 lines)
```
```

## Configuration Files

### Models Configuration
```json
{
  "available_models": {
    "ocr_tesseract": {
      "id": "ocr_tesseract",
      "name": "Tesseract OCR",
      "type": "ocr",
      "description": "Fast & reliable Tesseract OCR with rule-based parsing - Best for clear receipts",
      "requires_auth": false,
      "requires_tesseract": true,
      "capabilities": {
        "store_name": true,
        "date": true,
        "total": true,
        "address": true,
        "items": true,
        "phone": true
      }
    },
    "ocr_easyocr": {
      "id": "ocr_easyocr",
      "name": "EasyOCR",
      "type": "easyocr",
      "description": "Ready-to-use OCR with 80+ languages - Excellent accuracy, no installation needed",
      "requires_auth": false,
      "capabilities": {
        "store_name": true,
        "date": true,
        "total": true,
        "address": true,
        "items": true,
        "phone": true
      }
    },
    "ocr_paddle": {
      "id": "ocr_paddle",
      "name": "PaddleOCR",
      "type": "paddle",
      "description": "PaddlePaddle OCR - Multilingual, high accuracy, production-ready",
      "requires_auth": false,
      "requires_paddleocr": true,
      "capabilities": {
        "store_name": true,
        "date": true,
        "total": true,
        "address": true,
        "items": true,
        "phone": true
      }
    },
    "donut_cord": {
      "id": "donut_cord",
      "name": "Donut CORD",
      "type": "donut",
      "huggingface_id": "naver-clova-ix/donut-base-finetuned-cord-v2",
      "task_prompt": "<s_cord-v2>",
      "description": "Donut model fine-tuned on CORD v2 dataset - Fast AI-powered receipt extraction",
      "requires_auth": false,
      "capabilities": {
        "store_name": true,
        "date": true,
        "total": true,
        "address": true,
        "items": true,
        "phone": true,
        "advanced_parsing": true
      }
    },
    "florence2": {
      "id": "florence2",
      "name": "Florence-2 AI",
      "type": "florence",
      "huggingface_id": "microsoft/Florence-2-large",
      "task_prompt": "<OCR_WITH_REGION>",
      "description": "Microsoft Florence-2 - Advanced AI with region detection & OCR",
      "requires_auth": false,
      "capabilities": {
        "store_name": true,
        "date": true,
        "total": true,
        "address": true,
        "items": true,
        "phone": true,
        "advanced_parsing": true
      }
    }
  },
  "default_model": "ocr_easyocr",
  "recommended_model": "donut_cord",
  "best_for_finetuning": "donut_cord"
}
```

## File Structure

```
./check_dependencies.py
./check_gpu.py
./desktop-app/assets/generate_icons.py
./desktop-app/process_receipt.py
./shared/models/base_processor.py
./shared/models/donut_finetuner.py
./shared/models/donut_processor.py
./shared/models/easyocr_processor.py
./shared/models/model_manager.py
./shared/models/model_trainer.py
./shared/models/ocr_processor.py
./shared/models/paddle_processor.py
./shared/models/__init__.py
./shared/utils/data_structures.py
./shared/utils/image_processing.py
./shared/utils/logger.py
./shared/utils/__init__.py
./shared/__init__.py
./start_app.py
./tests/conftest.py
./tests/shared/test_image_processing.py
./tests/shared/test_model_manager.py
./tests/shared/__init__.py
./tests/test_system_health.py
./tests/web/test_api.py
./tests/web/__init__.py
./tests/__init__.py
./test_ocr_simple.py
./web-app/backend/app.py
```

## Current Issues & Errors

### Recent Errors from Logs
```
2025-11-27 16:52:54,843 - shared.models.model_manager - ERROR - \u274c Failed to load processor ocr_easyocr: EasyOCR not installed: pip install easyocr
2025-11-27 16:52:54,843 - __main__ - ERROR - Model ocr_easyocr failed on New_folder_0.jpg: EasyOCR not installed: pip install easyocr
2025-11-27 16:53:36,255 - shared.models.donut_processor - WARNING - Failed to parse as direct JSON: Expecting value: line 1 column 1 (char 0)
2025-11-27 16:53:36,257 - shared.models.donut_processor - WARNING - Failed to parse as direct JSON: Expecting value: line 1 column 1 (char 0)
2025-11-27 16:53:36,746 - shared.models.donut_processor - ERROR - Load attempt 1 failed: You are trying to access a gated repo.
401 Client Error. (Request ID: Root=1-692857e0-5113025f37f578456ca4cfcd;74bf40b3-e764-4a5e-90f4-b7e5bc8cb512)
2025-11-27 16:53:38,041 - shared.models.donut_processor - ERROR - Load attempt 2 failed: You are trying to access a gated repo.
401 Client Error. (Request ID: Root=1-692857e1-2549cf82423e3417008c389d;4515ca35-6758-48a7-8971-001cc0eea8a3)
2025-11-27 16:53:40,335 - shared.models.donut_processor - ERROR - Load attempt 3 failed: You are trying to access a gated repo.
401 Client Error. (Request ID: Root=1-692857e3-55d9a0f65af71ad779c6c131;7a242750-7940-4f93-93d1-a88a4861ec57)
2025-11-27 16:53:40,335 - shared.models.donut_processor - ERROR - Failed to load AdamCodd/donut-receipts-extract after 3 attempts.
Last error: You are trying to access a gated repo.
401 Client Error. (Request ID: Root=1-692857e3-55d9a0f65af71ad779c6c131;7a242750-7940-4f93-93d1-a88a4861ec57)
2025-11-27 16:53:40,335 - shared.models.model_manager - ERROR - \u274c Failed to load processor donut_receipts: Failed to load AdamCodd/donut-receipts-extract after 3 attempts.
Last error: You are trying to access a gated repo.
401 Client Error. (Request ID: Root=1-692857e3-55d9a0f65af71ad779c6c131;7a242750-7940-4f93-93d1-a88a4861ec57)
2025-11-27 16:53:40,335 - __main__ - ERROR - Model donut_receipts failed on New_folder_0.jpg: Failed to load AdamCodd/donut-receipts-extract after 3 attempts.
Last error: You are trying to access a gated repo.
401 Client Error. (Request ID: Root=1-692857e3-55d9a0f65af71ad779c6c131;7a242750-7940-4f93-93d1-a88a4861ec57)
```

## Recommendations for AI Agent

### Priority Actions
1. Review test results and fix any failing tests
2. Check error logs for runtime issues
3. Verify all dependencies are installed correctly
4. Ensure GPU is configured if AI models are needed
5. Review configuration files for correct settings

### Common Development Tasks
- **Add new model:** Update `shared/config/models_config.json`
- **Fix test failures:** Check `tests/` directory
- **Debug backend:** Review `logs/backend.log`
- **Update dependencies:** Modify `web-app/backend/requirements.txt`

### Files to Focus On
- `web-app/backend/app.py` - Main API server
- `shared/models/model_manager.py` - Model loading logic
- `shared/models/donut_processor.py` - Donut model processing
- `shared/models/paddle_processor.py` - PaddleOCR processing
- `tests/` - Test suite

---

**End of Report**

This report was generated automatically by the Receipt Extractor launcher.
Use it with AI coding assistants like Claude Code for efficient debugging and development.
