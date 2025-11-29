# Receipt Extractor - System Analysis Report
**Generated:** 2025-11-29 10:04:06
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
- **Working Directory:** /c/Users/User/Desktop/Web-and-Desktop-Apps

### Hardware Resources
- **Disk Space:** 477G total, 147G used, 330G available

## Dependency Status

### Last Dependency Install Log
```
ERROR: Could not find a version that satisfies the requirement paddlepaddle==2.6.0 (from versions: 2.6.2, 3.0.0b0, 3.0.0b1, 3.0.0b2, 3.0.0rc0, 3.0.0rc1, 3.0.0, 3.1.0, 3.1.1, 3.2.0, 3.2.1, 3.2.2)
ERROR: No matching distribution found for paddlepaddle==2.6.0
```

### Python Packages
```
easyocr                1.7.2
flask-cors             6.0.1
opencv-contrib-python  4.10.0.84
opencv-python          4.12.0.88
opencv-python-headless 4.12.0.88
paddleocr              3.3.2
pillow                 12.0.0
pytest-flask           1.3.0
torch                  2.9.1
torchvision            0.24.1
transformers           4.57.1
```

## GPU Configuration

### GPU Detection Results
```

+==========================================================+
|            GPU SETUP VERIFICATION                       |
+==========================================================+

============================================================
1. Python Version Check
============================================================
✓ Python 3.12
  3.12.10 (tags/v3.12.10:0cc8128, Apr  8 2025, 12:21:36) [MSC v.1943 64 bit (AMD64)]

============================================================
2. PyTorch Installation Check
============================================================
✓ PyTorch 2.9.1+cpu installed
  ⚠️  CPU-only version detected
     Install GPU version with:
     pip install torch --index-url https://download.pytorch.org/whl/cu121

============================================================
3. CUDA Availability Check
============================================================
✗ CUDA is NOT available
  Possible reasons:
  1. CUDA Toolkit not installed
  2. No NVIDIA GPU present
  3. CPU-only PyTorch installed
  4. NVIDIA drivers outdated

  See CUDA_GPU_SETUP.md for installation instructions

============================================================
6. AI/ML Libraries Check
============================================================
✓ PyTorch: 2.9.1+cpu
✓ TorchVision: 0.24.1+cpu
✓ Transformers: 4.57.1
✓ Pillow: 12.0.0
✓ OpenCV: 4.12.0
✓ NumPy: 2.2.6
✓ PaddleOCR: 3.3.2

============================================================
Summary
============================================================
⚠️  GPU acceleration is NOT enabled
  Models will run on CPU (slower)

  To enable GPU:
  1. Check CUDA_GPU_SETUP.md for detailed instructions
  2. Install CUDA Toolkit from nvidia.com
  3. Install GPU PyTorch:
     pip install torch --index-url https://download.pytorch.org/whl/cu121

============================================================
```

## Test Results

**Overall Status:** [NOT RUN OR FAILED]

### Test: api
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.1, pluggy-1.6.0 -- C:\Users\User\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\User\Desktop\Web-and-Desktop-Apps
configfile: pytest.ini
plugins: anyio-4.11.0, cov-7.0.0, flask-1.3.0, mock-3.15.1, requests-mock-1.12.1
collecting ... collected 5 items

tests/web/test_api.py::test_api_requirements_installed PASSED            [ 20%]
tests/web/test_api.py::test_api_health_check PASSED                      [ 40%]
tests/web/test_api.py::test_api_get_models PASSED                        [ 60%]
tests/web/test_api.py::test_api_extract_receipt PASSED                   [ 80%]
tests/web/test_api.py::test_api_invalid_image PASSED                     [100%]

=============================== tests coverage ================================
______________ coverage: platform win32, python 3.12.10-final-0 _______________

Name                                     Stmts   Miss  Cover   Missing
----------------------------------------------------------------------
shared\__init__.py                           0      0   100%
shared\models\__init__.py                   16     13    19%   10-23
shared\models\base_processor.py             45     45     0%   1-46
shared\models\donut_finetuner.py            99     99     0%   1-146
shared\models\donut_processor.py           339    339     0%   1-341
shared\models\easyocr_processor.py         121    121     0%   1-127
shared\models\model_manager.py             173     79    54%   22-27, 44-51, 56-60, 81-87, 97-99, 107-111, 113-117, 121-127, 132-137, 139-142, 144-151, 153-159, 161-163, 165-168, 173
shared\models\model_trainer.py              82     60    27%   9-12, 15-16, 19, 22-24, 27-32, 35-38, 41-44, 49-68, 72-74, 77-80, 83, 86-88, 91-95
shared\models\ocr_processor.py             193    102    47%   11-12, 24, 34-35, 41, 47-55, 77, 104-109, 112-118, 121-130, 136-169, 172-194, 198-204
shared\models\paddle_processor.py          180    180     0%   1-187
shared\utils\__init__.py                     3      0   100%
shared\utils\data_structures.py             43      6    86%   11, 30, 32-35
shared\utils\image_processing.py           118     60    49%   17-21, 24-26, 28-41, 43-51, 59, 76-77, 81-84, 86-88, 94-95, 102-110, 112-119
shared\utils\logger.py                      54     54     0%   1-55
web-app\backend\app.py                     311    217    30%   31-34, 36-38, 56-57, 61, 64-74, 91, 94-118, 121-125, 128-129, 132-172, 175-185, 188-206, 209-273, 276-280, 283-294, 297-300, 303-310, 313-316
web-app\backend\auth\__init__.py             4      4     0%   4-14
web-app\backend\auth\decorators.py         103    103     0%   4-257
web-app\backend\auth\jwt_handler.py         66     66     0%   4-176
web-app\backend\auth\password.py            34     34     0%   4-89
web-app\backend\database\__init__.py         3      3     0%   4-17
web-app\backend\database\connection.py      52     52     0%   4-144
web-app\backend\database\models.py         132    132     0%   5-288
web-app\backend\validation\__init__.py       2      2     0%   4-19
web-app\backend\validation\schemas.py      115    115     0%   5-221
----------------------------------------------------------------------
TOTAL                                     2288   1886    18%
Coverage HTML written to dir htmlcov
============================== 5 passed in 9.80s ==============================
```

### Test: auth_decorators
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.1, pluggy-1.6.0 -- C:\Users\User\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\User\Desktop\Web-and-Desktop-Apps
configfile: pytest.ini
plugins: anyio-4.11.0, cov-7.0.0, flask-1.3.0, mock-3.15.1, requests-mock-1.12.1
collecting ... collected 26 items

tests/backend/auth/test_decorators.py::TestRequireAuthDecorator::test_require_auth_valid_token ERROR [  3%]
tests/backend/auth/test_decorators.py::TestRequireAuthDecorator::test_require_auth_missing_header FAILED [  7%]
tests/backend/auth/test_decorators.py::TestRequireAuthDecorator::test_require_auth_invalid_header_format FAILED [ 11%]
tests/backend/auth/test_decorators.py::TestRequireAuthDecorator::test_require_auth_expired_token ERROR [ 15%]
tests/backend/auth/test_decorators.py::TestRequireAuthDecorator::test_require_auth_user_not_found ERROR [ 19%]
tests/backend/auth/test_decorators.py::TestRequireAuthDecorator::test_require_auth_inactive_user ERROR [ 23%]
tests/backend/auth/test_decorators.py::TestRequireAuthDecorator::test_require_auth_sets_flask_g_attributes ERROR [ 26%]
tests/backend/auth/test_decorators.py::TestRequireAdminDecorator::test_require_admin_with_admin_user PASSED [ 30%]
tests/backend/auth/test_decorators.py::TestRequireAdminDecorator::test_require_admin_with_regular_user PASSED [ 34%]
tests/backend/auth/test_decorators.py::TestRequireAdminDecorator::test_require_admin_without_authentication PASSED [ 38%]
tests/backend/auth/test_decorators.py::TestRateLimitDecorator::test_rate_limit_within_limit PASSED [ 42%]
tests/backend/auth/test_decorators.py::TestRateLimitDecorator::test_rate_limit_exceeds_limit PASSED [ 46%]
tests/backend/auth/test_decorators.py::TestRateLimitDecorator::test_rate_limit_window_expiry PASSED [ 50%]
tests/backend/auth/test_decorators.py::TestRateLimitDecorator::test_rate_limit_different_users_separate_limits PASSED [ 53%]
tests/backend/auth/test_decorators.py::TestRateLimitDecorator::test_rate_limit_uses_ip_when_no_user_id PASSED [ 57%]
tests/backend/auth/test_decorators.py::TestRequirePlanDecorator::test_require_plan_free_user_free_feature FAILED [ 61%]
tests/backend/auth/test_decorators.py::TestRequirePlanDecorator::test_require_plan_free_user_pro_feature FAILED [ 65%]
tests/backend/auth/test_decorators.py::TestRequirePlanDecorator::test_require_plan_pro_user_pro_feature FAILED [ 69%]
tests/backend/auth/test_decorators.py::TestRequirePlanDecorator::test_require_plan_enterprise_user_any_feature FAILED [ 73%]
tests/backend/auth/test_decorators.py::TestRequirePlanDecorator::test_require_plan_hierarchy FAILED [ 76%]
tests/backend/auth/test_decorators.py::TestCheckUsageLimitDecorator::test_usage_limit_within_limit ERROR [ 80%]
tests/backend/auth/test_decorators.py::TestCheckUsageLimitDecorator::test_usage_limit_at_limit ERROR [ 84%]
tests/backend/auth/test_decorators.py::TestCheckUsageLimitDecorator::test_usage_limit_increments_counter ERROR [ 88%]
tests/backend/auth/test_decorators.py::TestCheckUsageLimitDecorator::test_usage_limit_different_plan_limits ERROR [ 92%]
tests/backend/auth/test_decorators.py::TestDecoratorChaining::test_require_auth_and_require_admin_chained ERROR [ 96%]
tests/backend/auth/test_decorators.py::TestDecoratorChaining::test_require_auth_and_rate_limit_chained ERROR [100%]

=================================== ERRORS ====================================
__ ERROR at setup of TestRequireAuthDecorator.test_require_auth_valid_token ___
tests\conftest.py:71: in db_session
    from database.models import Base
web-app\backend\database\__init__.py:4: in <module>
    from .models import (
web-app\backend\database\models.py:251: in <module>
    class AuditLog(Base):
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_api.py:199: in __init__
    _as_declarative(reg, cls, dict_)
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:245: in _as_declarative
    return _MapperConfig.setup_mapping(registry, cls, dict_, None, {})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:326: in setup_mapping
    return _ClassScanMapperConfig(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:573: in __init__
    self._extract_mappable_attributes()
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:1530: in _extract_mappable_attributes
    raise exc.InvalidRequestError(
E   sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
_ ERROR at setup of TestRequireAuthDecorator.test_require_auth_expired_token __
tests\conftest.py:71: in db_session
    from database.models import Base
web-app\backend\database\__init__.py:4: in <module>
    from .models import (
web-app\backend\database\models.py:251: in <module>
    class AuditLog(Base):
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_api.py:199: in __init__
    _as_declarative(reg, cls, dict_)
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:245: in _as_declarative
    return _MapperConfig.setup_mapping(registry, cls, dict_, None, {})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:326: in setup_mapping
    return _ClassScanMapperConfig(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:573: in __init__
    self._extract_mappable_attributes()
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:1530: in _extract_mappable_attributes
    raise exc.InvalidRequestError(
E   sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
_ ERROR at setup of TestRequireAuthDecorator.test_require_auth_user_not_found _
tests\conftest.py:71: in db_session
    from database.models import Base
web-app\backend\database\__init__.py:4: in <module>
    from .models import (
web-app\backend\database\models.py:251: in <module>
    class AuditLog(Base):
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_api.py:199: in __init__
    _as_declarative(reg, cls, dict_)
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:245: in _as_declarative
    return _MapperConfig.setup_mapping(registry, cls, dict_, None, {})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:326: in setup_mapping
    return _ClassScanMapperConfig(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:573: in __init__
    self._extract_mappable_attributes()
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:1530: in _extract_mappable_attributes
    raise exc.InvalidRequestError(
E   sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
_ ERROR at setup of TestRequireAuthDecorator.test_require_auth_inactive_user __
tests\conftest.py:71: in db_session
    from database.models import Base
web-app\backend\database\__init__.py:4: in <module>
    from .models import (
web-app\backend\database\models.py:251: in <module>
    class AuditLog(Base):
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_api.py:199: in __init__
    _as_declarative(reg, cls, dict_)
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:245: in _as_declarative
    return _MapperConfig.setup_mapping(registry, cls, dict_, None, {})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:326: in setup_mapping
    return _ClassScanMapperConfig(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:573: in __init__
    self._extract_mappable_attributes()
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:1530: in _extract_mappable_attributes
    raise exc.InvalidRequestError(
E   sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
_ ERROR at setup of TestRequireAuthDecorator.test_require_auth_sets_flask_g_attributes _
tests\conftest.py:71: in db_session
    from database.models import Base
web-app\backend\database\__init__.py:4: in <module>
    from .models import (
web-app\backend\database\models.py:251: in <module>
    class AuditLog(Base):
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_api.py:199: in __init__
    _as_declarative(reg, cls, dict_)
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:245: in _as_declarative
    return _MapperConfig.setup_mapping(registry, cls, dict_, None, {})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:326: in setup_mapping
    return _ClassScanMapperConfig(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:573: in __init__
    self._extract_mappable_attributes()
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:1530: in _extract_mappable_attributes
    raise exc.InvalidRequestError(
E   sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
_ ERROR at setup of TestCheckUsageLimitDecorator.test_usage_limit_within_limit _
tests\conftest.py:71: in db_session
    from database.models import Base
web-app\backend\database\__init__.py:4: in <module>
    from .models import (
web-app\backend\database\models.py:251: in <module>
    class AuditLog(Base):
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_api.py:199: in __init__
    _as_declarative(reg, cls, dict_)
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:245: in _as_declarative
    return _MapperConfig.setup_mapping(registry, cls, dict_, None, {})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:326: in setup_mapping
    return _ClassScanMapperConfig(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:573: in __init__
    self._extract_mappable_attributes()
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:1530: in _extract_mappable_attributes
    raise exc.InvalidRequestError(
E   sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
__ ERROR at setup of TestCheckUsageLimitDecorator.test_usage_limit_at_limit ___
tests\conftest.py:71: in db_session
    from database.models import Base
web-app\backend\database\__init__.py:4: in <module>
    from .models import (
web-app\backend\database\models.py:251: in <module>
    class AuditLog(Base):
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_api.py:199: in __init__
    _as_declarative(reg, cls, dict_)
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:245: in _as_declarative
    return _MapperConfig.setup_mapping(registry, cls, dict_, None, {})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:326: in setup_mapping
    return _ClassScanMapperConfig(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:573: in __init__
    self._extract_mappable_attributes()
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:1530: in _extract_mappable_attributes
    raise exc.InvalidRequestError(
E   sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
_ ERROR at setup of TestCheckUsageLimitDecorator.test_usage_limit_increments_counter _
tests\conftest.py:71: in db_session
    from database.models import Base
web-app\backend\database\__init__.py:4: in <module>
    from .models import (
web-app\backend\database\models.py:251: in <module>
    class AuditLog(Base):
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_api.py:199: in __init__
    _as_declarative(reg, cls, dict_)
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:245: in _as_declarative
    return _MapperConfig.setup_mapping(registry, cls, dict_, None, {})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:326: in setup_mapping
    return _ClassScanMapperConfig(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:573: in __init__
    self._extract_mappable_attributes()
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:1530: in _extract_mappable_attributes
    raise exc.InvalidRequestError(
E   sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
_ ERROR at setup of TestCheckUsageLimitDecorator.test_usage_limit_different_plan_limits _
tests\conftest.py:71: in db_session
    from database.models import Base
web-app\backend\database\__init__.py:4: in <module>
    from .models import (
web-app\backend\database\models.py:251: in <module>
    class AuditLog(Base):
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_api.py:199: in __init__
    _as_declarative(reg, cls, dict_)
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:245: in _as_declarative
    return _MapperConfig.setup_mapping(registry, cls, dict_, None, {})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:326: in setup_mapping
    return _ClassScanMapperConfig(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:573: in __init__
    self._extract_mappable_attributes()
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:1530: in _extract_mappable_attributes
    raise exc.InvalidRequestError(
E   sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
_ ERROR at setup of TestDecoratorChaining.test_require_auth_and_require_admin_chained _
tests\conftest.py:71: in db_session
    from database.models import Base
web-app\backend\database\__init__.py:4: in <module>
    from .models import (
web-app\backend\database\models.py:251: in <module>
    class AuditLog(Base):
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_api.py:199: in __init__
    _as_declarative(reg, cls, dict_)
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:245: in _as_declarative
    return _MapperConfig.setup_mapping(registry, cls, dict_, None, {})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:326: in setup_mapping
    return _ClassScanMapperConfig(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:573: in __init__
    self._extract_mappable_attributes()
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:1530: in _extract_mappable_attributes
    raise exc.InvalidRequestError(
E   sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
_ ERROR at setup of TestDecoratorChaining.test_require_auth_and_rate_limit_chained _
tests\conftest.py:71: in db_session
    from database.models import Base
web-app\backend\database\__init__.py:4: in <module>
    from .models import (
web-app\backend\database\models.py:251: in <module>
    class AuditLog(Base):
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_api.py:199: in __init__
    _as_declarative(reg, cls, dict_)
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:245: in _as_declarative
    return _MapperConfig.setup_mapping(registry, cls, dict_, None, {})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:326: in setup_mapping
    return _ClassScanMapperConfig(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:573: in __init__
    self._extract_mappable_attributes()
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:1530: in _extract_mappable_attributes
    raise exc.InvalidRequestError(
E   sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
================================== FAILURES ===================================
__________ TestRequireAuthDecorator.test_require_auth_missing_header __________
tests\backend\auth\test_decorators.py:76: in test_require_auth_missing_header
    response = client.get('/test')
               ^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\werkzeug\test.py:1162: in get
    return self.open(*args, **kw)
           ^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\flask\testing.py:235: in open
    response = super().open(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\werkzeug\test.py:1116: in open
    response_parts = self.run_wsgi_app(request.environ, buffered=buffered)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\werkzeug\test.py:988: in run_wsgi_app
    rv = run_wsgi_app(self.application, environ, buffered=buffered)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\werkzeug\test.py:1264: in run_wsgi_app
    app_rv = app(environ, start_response)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\flask\app.py:1536: in __call__
    return self.wsgi_app(environ, start_response)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\flask\app.py:1514: in wsgi_app
    response = self.handle_exception(e)
               ^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\flask\app.py:1511: in wsgi_app
    response = self.full_dispatch_request()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\flask\app.py:919: in full_dispatch_request
    rv = self.handle_user_exception(e)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\flask\app.py:917: in full_dispatch_request
    rv = self.dispatch_request()
         ^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\flask\app.py:902: in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-app\backend\auth\decorators.py:31: in decorated_function
    from database.connection import get_db_context
web-app\backend\database\__init__.py:4: in <module>
    from .models import (
web-app\backend\database\models.py:251: in <module>
    class AuditLog(Base):
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_api.py:199: in __init__
    _as_declarative(reg, cls, dict_)
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:245: in _as_declarative
    return _MapperConfig.setup_mapping(registry, cls, dict_, None, {})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:326: in setup_mapping
    return _ClassScanMapperConfig(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:573: in __init__
    self._extract_mappable_attributes()
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:1530: in _extract_mappable_attributes
    raise exc.InvalidRequestError(
E   sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
______ TestRequireAuthDecorator.test_require_auth_invalid_header_format _______
tests\backend\auth\test_decorators.py:100: in test_require_auth_invalid_header_format
    response = client.get('/test', headers=headers)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\werkzeug\test.py:1162: in get
    return self.open(*args, **kw)
           ^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\flask\testing.py:235: in open
    response = super().open(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\werkzeug\test.py:1116: in open
    response_parts = self.run_wsgi_app(request.environ, buffered=buffered)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\werkzeug\test.py:988: in run_wsgi_app
    rv = run_wsgi_app(self.application, environ, buffered=buffered)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\werkzeug\test.py:1264: in run_wsgi_app
    app_rv = app(environ, start_response)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\flask\app.py:1536: in __call__
    return self.wsgi_app(environ, start_response)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\flask\app.py:1514: in wsgi_app
    response = self.handle_exception(e)
               ^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\flask\app.py:1511: in wsgi_app
    response = self.full_dispatch_request()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\flask\app.py:919: in full_dispatch_request
    rv = self.handle_user_exception(e)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\flask\app.py:917: in full_dispatch_request
    rv = self.dispatch_request()
         ^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\flask\app.py:902: in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-app\backend\auth\decorators.py:31: in decorated_function
    from database.connection import get_db_context
web-app\backend\database\__init__.py:4: in <module>
    from .models import (
web-app\backend\database\models.py:251: in <module>
    class AuditLog(Base):
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_api.py:199: in __init__
    _as_declarative(reg, cls, dict_)
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:245: in _as_declarative
    return _MapperConfig.setup_mapping(registry, cls, dict_, None, {})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:326: in setup_mapping
    return _ClassScanMapperConfig(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:573: in __init__
    self._extract_mappable_attributes()
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:1530: in _extract_mappable_attributes
    raise exc.InvalidRequestError(
E   sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
______ TestRequirePlanDecorator.test_require_plan_free_user_free_feature ______
tests\backend\auth\test_decorators.py:384: in test_require_plan_free_user_free_feature
    from database.models import SubscriptionPlan
web-app\backend\database\__init__.py:4: in <module>
    from .models import (
web-app\backend\database\models.py:251: in <module>
    class AuditLog(Base):
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_api.py:199: in __init__
    _as_declarative(reg, cls, dict_)
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:245: in _as_declarative
    return _MapperConfig.setup_mapping(registry, cls, dict_, None, {})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:326: in setup_mapping
    return _ClassScanMapperConfig(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:573: in __init__
    self._extract_mappable_attributes()
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:1530: in _extract_mappable_attributes
    raise exc.InvalidRequestError(
E   sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
______ TestRequirePlanDecorator.test_require_plan_free_user_pro_feature _______
tests\backend\auth\test_decorators.py:400: in test_require_plan_free_user_pro_feature
    from database.models import SubscriptionPlan
web-app\backend\database\__init__.py:4: in <module>
    from .models import (
web-app\backend\database\models.py:251: in <module>
    class AuditLog(Base):
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_api.py:199: in __init__
    _as_declarative(reg, cls, dict_)
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:245: in _as_declarative
    return _MapperConfig.setup_mapping(registry, cls, dict_, None, {})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:326: in setup_mapping
    return _ClassScanMapperConfig(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:573: in __init__
    self._extract_mappable_attributes()
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:1530: in _extract_mappable_attributes
    raise exc.InvalidRequestError(
E   sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
_______ TestRequirePlanDecorator.test_require_plan_pro_user_pro_feature _______
tests\backend\auth\test_decorators.py:418: in test_require_plan_pro_user_pro_feature
    from database.models import SubscriptionPlan
web-app\backend\database\__init__.py:4: in <module>
    from .models import (
web-app\backend\database\models.py:251: in <module>
    class AuditLog(Base):
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_api.py:199: in __init__
    _as_declarative(reg, cls, dict_)
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:245: in _as_declarative
    return _MapperConfig.setup_mapping(registry, cls, dict_, None, {})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:326: in setup_mapping
    return _ClassScanMapperConfig(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:573: in __init__
    self._extract_mappable_attributes()
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:1530: in _extract_mappable_attributes
    raise exc.InvalidRequestError(
E   sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
___ TestRequirePlanDecorator.test_require_plan_enterprise_user_any_feature ____
tests\backend\auth\test_decorators.py:434: in test_require_plan_enterprise_user_any_feature
    from database.models import SubscriptionPlan
web-app\backend\database\__init__.py:4: in <module>
    from .models import (
web-app\backend\database\models.py:251: in <module>
    class AuditLog(Base):
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_api.py:199: in __init__
    _as_declarative(reg, cls, dict_)
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:245: in _as_declarative
    return _MapperConfig.setup_mapping(registry, cls, dict_, None, {})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:326: in setup_mapping
    return _ClassScanMapperConfig(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:573: in __init__
    self._extract_mappable_attributes()
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:1530: in _extract_mappable_attributes
    raise exc.InvalidRequestError(
E   sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
____________ TestRequirePlanDecorator.test_require_plan_hierarchy _____________
tests\backend\auth\test_decorators.py:450: in test_require_plan_hierarchy
    from database.models import SubscriptionPlan
web-app\backend\database\__init__.py:4: in <module>
    from .models import (
web-app\backend\database\models.py:251: in <module>
    class AuditLog(Base):
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_api.py:199: in __init__
    _as_declarative(reg, cls, dict_)
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:245: in _as_declarative
    return _MapperConfig.setup_mapping(registry, cls, dict_, None, {})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:326: in setup_mapping
    return _ClassScanMapperConfig(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:573: in __init__
    self._extract_mappable_attributes()
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:1530: in _extract_mappable_attributes
    raise exc.InvalidRequestError(
E   sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
=============================== tests coverage ================================
______________ coverage: platform win32, python 3.12.10-final-0 _______________

Name                                     Stmts   Miss  Cover   Missing
----------------------------------------------------------------------
shared\__init__.py                           0      0   100%
shared\models\__init__.py                   16     16     0%   3-23
shared\models\base_processor.py             45     45     0%   1-46
shared\models\donut_finetuner.py            99     99     0%   1-146
shared\models\donut_processor.py           339    339     0%   1-341
shared\models\easyocr_processor.py         121    121     0%   1-127
shared\models\model_manager.py             173    173     0%   1-174
shared\models\model_trainer.py              82     82     0%   1-95
shared\models\ocr_processor.py             193    193     0%   1-204
shared\models\paddle_processor.py          180    180     0%   1-187
shared\utils\__init__.py                     3      3     0%   1-10
shared\utils\data_structures.py             43     43     0%   1-43
shared\utils\image_processing.py           118    118     0%   1-119
shared\utils\logger.py                      54     54     0%   1-55
web-app\backend\app.py                     311    311     0%   1-317
web-app\backend\auth\__init__.py             4      0   100%
web-app\backend\auth\decorators.py         103     53    49%   32-68, 120, 151, 184-202, 219-257
web-app\backend\auth\jwt_handler.py         66     46    30%   39-52, 65-70, 83-98, 112-121, 135-158, 172-176
web-app\backend\auth\password.py            34     28    18%   20-28, 42-51, 71-89
web-app\backend\database\__init__.py         3      2    33%   15-17
web-app\backend\database\connection.py      52     52     0%   4-144
web-app\backend\database\models.py         132      6    95%   88, 139, 174, 207, 248, 288
web-app\backend\validation\__init__.py       2      2     0%   4-19
web-app\backend\validation\schemas.py      115    115     0%   5-221
----------------------------------------------------------------------
TOTAL                                     2288   2081     9%
Coverage HTML written to dir htmlcov
=========================== short test summary info ===========================
FAILED tests/backend/auth/test_decorators.py::TestRequireAuthDecorator::test_require_auth_missing_header - sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
FAILED tests/backend/auth/test_decorators.py::TestRequireAuthDecorator::test_require_auth_invalid_header_format - sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
FAILED tests/backend/auth/test_decorators.py::TestRequirePlanDecorator::test_require_plan_free_user_free_feature - sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
FAILED tests/backend/auth/test_decorators.py::TestRequirePlanDecorator::test_require_plan_free_user_pro_feature - sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
FAILED tests/backend/auth/test_decorators.py::TestRequirePlanDecorator::test_require_plan_pro_user_pro_feature - sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
FAILED tests/backend/auth/test_decorators.py::TestRequirePlanDecorator::test_require_plan_enterprise_user_any_feature - sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
FAILED tests/backend/auth/test_decorators.py::TestRequirePlanDecorator::test_require_plan_hierarchy - sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
ERROR tests/backend/auth/test_decorators.py::TestRequireAuthDecorator::test_require_auth_valid_token - sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
ERROR tests/backend/auth/test_decorators.py::TestRequireAuthDecorator::test_require_auth_expired_token - sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
ERROR tests/backend/auth/test_decorators.py::TestRequireAuthDecorator::test_require_auth_user_not_found - sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
ERROR tests/backend/auth/test_decorators.py::TestRequireAuthDecorator::test_require_auth_inactive_user - sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
ERROR tests/backend/auth/test_decorators.py::TestRequireAuthDecorator::test_require_auth_sets_flask_g_attributes - sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
ERROR tests/backend/auth/test_decorators.py::TestCheckUsageLimitDecorator::test_usage_limit_within_limit - sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
ERROR tests/backend/auth/test_decorators.py::TestCheckUsageLimitDecorator::test_usage_limit_at_limit - sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
ERROR tests/backend/auth/test_decorators.py::TestCheckUsageLimitDecorator::test_usage_limit_increments_counter - sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
ERROR tests/backend/auth/test_decorators.py::TestCheckUsageLimitDecorator::test_usage_limit_different_plan_limits - sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
ERROR tests/backend/auth/test_decorators.py::TestDecoratorChaining::test_require_auth_and_require_admin_chained - sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
ERROR tests/backend/auth/test_decorators.py::TestDecoratorChaining::test_require_auth_and_rate_limit_chained - sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
============= 7 failed, 8 passed, 35 warnings, 11 errors in 7.62s =============
```

### Test: base_processor
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.1, pluggy-1.6.0 -- C:\Users\User\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\User\Desktop\Web-and-Desktop-Apps
configfile: pytest.ini
plugins: anyio-4.11.0, cov-7.0.0, flask-1.3.0, mock-3.15.1, requests-mock-1.12.1
collecting ... collected 21 items

tests/shared/test_base_processor.py::test_base_processor_initialization PASSED [  4%]
tests/shared/test_base_processor.py::test_base_processor_initialization_defaults PASSED [  9%]
tests/shared/test_base_processor.py::test_initialize_success PASSED      [ 14%]
tests/shared/test_base_processor.py::test_initialize_with_retry_success PASSED [ 19%]
tests/shared/test_base_processor.py::test_initialize_health_check_failure PASSED [ 23%]
tests/shared/test_base_processor.py::test_initialize_load_failure PASSED [ 28%]
tests/shared/test_base_processor.py::test_initialize_retry_timing PASSED [ 33%]
tests/shared/test_base_processor.py::test_ensure_healthy_success PASSED  [ 38%]
tests/shared/test_base_processor.py::test_ensure_healthy_not_initialized PASSED [ 42%]
tests/shared/test_base_processor.py::test_ensure_healthy_health_check_fails PASSED [ 47%]
tests/shared/test_base_processor.py::test_ensure_healthy_updates_timestamp PASSED [ 52%]
tests/shared/test_base_processor.py::test_get_status_not_initialized PASSED [ 57%]
tests/shared/test_base_processor.py::test_get_status_initialized_healthy PASSED [ 61%]
tests/shared/test_base_processor.py::test_get_status_initialized_unhealthy PASSED [ 66%]
tests/shared/test_base_processor.py::test_get_status_with_error PASSED   [ 71%]
tests/shared/test_base_processor.py::test_processor_initialization_error_exception PASSED [ 76%]
tests/shared/test_base_processor.py::test_processor_health_check_error_exception PASSED [ 80%]
tests/shared/test_base_processor.py::test_abstract_methods_not_implemented PASSED [ 85%]
tests/shared/test_base_processor.py::test_initialize_zero_retries PASSED [ 90%]
tests/shared/test_base_processor.py::test_concurrent_initialization PASSED [ 95%]
tests/shared/test_base_processor.py::test_health_check_count PASSED      [100%]

=============================== tests coverage ================================
______________ coverage: platform win32, python 3.12.10-final-0 _______________

Name                                     Stmts   Miss  Cover   Missing
----------------------------------------------------------------------
shared\__init__.py                           0      0   100%
shared\models\__init__.py                   16     13    19%   10-23
shared\models\base_processor.py             45      3    93%   15, 18, 21
shared\models\donut_finetuner.py            99     99     0%   1-146
shared\models\donut_processor.py           339    339     0%   1-341
shared\models\easyocr_processor.py         121    121     0%   1-127
shared\models\model_manager.py             173    150    13%   8-15, 17-27, 29-38, 40-60, 62-70, 72-75, 77, 79, 81-87, 89, 91-137, 139-142, 144-151, 153-159, 161-163, 165-168, 170-174
shared\models\model_trainer.py              82     82     0%   1-95
shared\models\ocr_processor.py             193    193     0%   1-204
shared\models\paddle_processor.py          180    180     0%   1-187
shared\utils\__init__.py                     3      3     0%   1-10
shared\utils\data_structures.py             43     43     0%   1-43
shared\utils\image_processing.py           118    118     0%   1-119
shared\utils\logger.py                      54     54     0%   1-55
web-app\backend\app.py                     311    311     0%   1-317
web-app\backend\auth\__init__.py             4      4     0%   4-14
web-app\backend\auth\decorators.py         103    103     0%   4-257
web-app\backend\auth\jwt_handler.py         66     66     0%   4-176
web-app\backend\auth\password.py            34     34     0%   4-89
web-app\backend\database\__init__.py         3      3     0%   4-17
web-app\backend\database\connection.py      52     52     0%   4-144
web-app\backend\database\models.py         132    132     0%   5-288
web-app\backend\validation\__init__.py       2      2     0%   4-19
web-app\backend\validation\schemas.py      115    115     0%   5-221
----------------------------------------------------------------------
TOTAL                                     2288   2220     3%
Coverage HTML written to dir htmlcov
============================= 21 passed in 4.02s ==============================
```

### Test: db_connection
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.1, pluggy-1.6.0 -- C:\Users\User\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\User\Desktop\Web-and-Desktop-Apps
configfile: pytest.ini
plugins: anyio-4.11.0, cov-7.0.0, flask-1.3.0, mock-3.15.1, requests-mock-1.12.1
collecting ... collected 0 items / 1 error

=================================== ERRORS ====================================
_________ ERROR collecting tests/backend/database/test_connection.py __________
tests\backend\database\test_connection.py:16: in <module>
    from database.connection import (
web-app\backend\database\__init__.py:4: in <module>
    from .models import (
web-app\backend\database\models.py:251: in <module>
    class AuditLog(Base):
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_api.py:199: in __init__
    _as_declarative(reg, cls, dict_)
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:245: in _as_declarative
    return _MapperConfig.setup_mapping(registry, cls, dict_, None, {})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:326: in setup_mapping
    return _ClassScanMapperConfig(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:573: in __init__
    self._extract_mappable_attributes()
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:1530: in _extract_mappable_attributes
    raise exc.InvalidRequestError(
E   sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
=========================== short test summary info ===========================
ERROR tests/backend/database/test_connection.py - sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
========================= 1 warning, 1 error in 0.64s =========================
```

### Test: db_models
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.1, pluggy-1.6.0 -- C:\Users\User\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\User\Desktop\Web-and-Desktop-Apps
configfile: pytest.ini
plugins: anyio-4.11.0, cov-7.0.0, flask-1.3.0, mock-3.15.1, requests-mock-1.12.1
collecting ... collected 0 items / 1 error

=================================== ERRORS ====================================
___________ ERROR collecting tests/backend/database/test_models.py ____________
tests\backend\database\test_models.py:15: in <module>
    from database.models import (
web-app\backend\database\__init__.py:4: in <module>
    from .models import (
web-app\backend\database\models.py:251: in <module>
    class AuditLog(Base):
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_api.py:199: in __init__
    _as_declarative(reg, cls, dict_)
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:245: in _as_declarative
    return _MapperConfig.setup_mapping(registry, cls, dict_, None, {})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:326: in setup_mapping
    return _ClassScanMapperConfig(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:573: in __init__
    self._extract_mappable_attributes()
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:1530: in _extract_mappable_attributes
    raise exc.InvalidRequestError(
E   sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
=========================== short test summary info ===========================
ERROR tests/backend/database/test_models.py - sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
========================= 1 warning, 1 error in 0.65s =========================
```

### Test: donut_finetuner
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.1, pluggy-1.6.0 -- C:\Users\User\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\User\Desktop\Web-and-Desktop-Apps
configfile: pytest.ini
plugins: anyio-4.11.0, cov-7.0.0, flask-1.3.0, mock-3.15.1, requests-mock-1.12.1
collecting ... collected 9 items

tests/shared/models/test_donut_finetuner.py::TestReceiptDataset::test_dataset_length PASSED [ 11%]
tests/shared/models/test_donut_finetuner.py::TestReceiptDataset::test_dataset_getitem PASSED [ 22%]
tests/shared/models/test_donut_finetuner.py::TestDonutFinetuner::test_finetuner_initialization PASSED [ 33%]
tests/shared/models/test_donut_finetuner.py::TestDonutFinetuner::test_finetuner_cuda_detection PASSED [ 44%]
tests/shared/models/test_donut_finetuner.py::TestDonutFinetuner::test_finetuner_model_selection PASSED [ 55%]
tests/shared/models/test_donut_finetuner.py::TestDonutFinetuner::test_finetuner_image_size_configuration PASSED [ 66%]
tests/shared/models/test_donut_finetuner.py::TestDonutFinetunerTraining::test_train_method_exists PASSED [ 77%]
tests/shared/models/test_donut_finetuner.py::TestDonutFinetunerSaving::test_save_model_method_exists PASSED [ 88%]
tests/shared/models/test_donut_finetuner.py::TestDonutFinetunerErrorHandling::test_model_loading_failure PASSED [100%]

=============================== tests coverage ================================
______________ coverage: platform win32, python 3.12.10-final-0 _______________

Name                                     Stmts   Miss  Cover   Missing
----------------------------------------------------------------------
shared\__init__.py                           0      0   100%
shared\models\__init__.py                   16     13    19%   10-23
shared\models\base_processor.py             45     45     0%   1-46
shared\models\donut_finetuner.py            99     53    46%   39-40, 55-114, 117-124, 127-146
shared\models\donut_processor.py           339    339     0%   1-341
shared\models\easyocr_processor.py         121    121     0%   1-127
shared\models\model_manager.py             173    150    13%   8-15, 17-27, 29-38, 40-60, 62-70, 72-75, 77, 79, 81-87, 89, 91-137, 139-142, 144-151, 153-159, 161-163, 165-168, 170-174
shared\models\model_trainer.py              82     82     0%   1-95
shared\models\ocr_processor.py             193    193     0%   1-204
shared\models\paddle_processor.py          180    180     0%   1-187
shared\utils\__init__.py                     3      3     0%   1-10
shared\utils\data_structures.py             43     43     0%   1-43
shared\utils\image_processing.py           118    118     0%   1-119
shared\utils\logger.py                      54     54     0%   1-55
web-app\backend\app.py                     311    311     0%   1-317
web-app\backend\auth\__init__.py             4      4     0%   4-14
web-app\backend\auth\decorators.py         103    103     0%   4-257
web-app\backend\auth\jwt_handler.py         66     66     0%   4-176
web-app\backend\auth\password.py            34     34     0%   4-89
web-app\backend\database\__init__.py         3      3     0%   4-17
web-app\backend\database\connection.py      52     52     0%   4-144
web-app\backend\database\models.py         132    132     0%   5-288
web-app\backend\validation\__init__.py       2      2     0%   4-19
web-app\backend\validation\schemas.py      115    115     0%   5-221
----------------------------------------------------------------------
TOTAL                                     2288   2216     3%
Coverage HTML written to dir htmlcov
============================= 9 passed in 12.09s ==============================
```

### Test: donut_processor
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.1, pluggy-1.6.0 -- C:\Users\User\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\User\Desktop\Web-and-Desktop-Apps
configfile: pytest.ini
plugins: anyio-4.11.0, cov-7.0.0, flask-1.3.0, mock-3.15.1, requests-mock-1.12.1
collecting ... collected 20 items

tests/shared/test_donut_processor.py::test_donut_processor_initialization PASSED [  5%]
tests/shared/test_donut_processor.py::test_donut_processor_gpu_detection PASSED [ 10%]
tests/shared/test_donut_processor.py::test_donut_processor_load_retry PASSED [ 15%]
tests/shared/test_donut_processor.py::test_donut_processor_load_failure PASSED [ 20%]
tests/shared/test_donut_processor.py::test_normalize_price_valid PASSED  [ 25%]
tests/shared/test_donut_processor.py::test_normalize_price_invalid PASSED [ 30%]
tests/shared/test_donut_processor.py::test_parse_json_output_valid PASSED [ 35%]
tests/shared/test_donut_processor.py::test_parse_json_output_invalid PASSED [ 40%]
tests/shared/test_donut_processor.py::test_donut_extract_success PASSED  [ 45%]
tests/shared/test_donut_processor.py::test_donut_extract_fallback_text PASSED [ 50%]
tests/shared/test_donut_processor.py::test_donut_extract_exception PASSED [ 55%]
tests/shared/test_donut_processor.py::test_safe_extract_string PASSED    [ 60%]
tests/shared/test_donut_processor.py::test_calculate_confidence_sroie PASSED [ 65%]
tests/shared/test_donut_processor.py::test_extract_from_text PASSED      [ 70%]
tests/shared/test_donut_processor.py::test_extract_from_text_cord PASSED [ 75%]
tests/shared/test_donut_processor.py::test_florence_processor_initialization PASSED [ 80%]
tests/shared/test_donut_processor.py::test_florence_processor_load_failure PASSED [ 85%]
tests/shared/test_donut_processor.py::test_build_receipt_data PASSED     [ 90%]
tests/shared/test_donut_processor.py::test_build_receipt_data_complex_total PASSED [ 95%]
tests/shared/test_donut_processor.py::test_build_receipt_data_alternate_fields PASSED [100%]

=============================== tests coverage ================================
______________ coverage: platform win32, python 3.12.10-final-0 _______________

Name                                     Stmts   Miss  Cover   Missing
----------------------------------------------------------------------
shared\__init__.py                           0      0   100%
shared\models\__init__.py                   16     13    19%   10-23
shared\models\base_processor.py             45     45     0%   1-46
shared\models\donut_finetuner.py            99     99     0%   1-146
shared\models\donut_processor.py           339     72    79%   21, 23, 53, 101-103, 130, 172-176, 196-199, 201-205, 265, 291-327, 329-341
shared\models\easyocr_processor.py         121    121     0%   1-127
shared\models\model_manager.py             173    150    13%   8-15, 17-27, 29-38, 40-60, 62-70, 72-75, 77, 79, 81-87, 89, 91-137, 139-142, 144-151, 153-159, 161-163, 165-168, 170-174
shared\models\model_trainer.py              82     82     0%   1-95
shared\models\ocr_processor.py             193    193     0%   1-204
shared\models\paddle_processor.py          180    180     0%   1-187
shared\utils\__init__.py                     3      0   100%
shared\utils\data_structures.py             43      7    84%   11, 30, 32-35, 43
shared\utils\image_processing.py           118    106    10%   8-26, 28-41, 43-51, 53-88, 90-110, 112-119
shared\utils\logger.py                      54     54     0%   1-55
web-app\backend\app.py                     311    311     0%   1-317
web-app\backend\auth\__init__.py             4      4     0%   4-14
web-app\backend\auth\decorators.py         103    103     0%   4-257
web-app\backend\auth\jwt_handler.py         66     66     0%   4-176
web-app\backend\auth\password.py            34     34     0%   4-89
web-app\backend\database\__init__.py         3      3     0%   4-17
web-app\backend\database\connection.py      52     52     0%   4-144
web-app\backend\database\models.py         132    132     0%   5-288
web-app\backend\validation\__init__.py       2      2     0%   4-19
web-app\backend\validation\schemas.py      115    115     0%   5-221
----------------------------------------------------------------------
TOTAL                                     2288   1944    15%
Coverage HTML written to dir htmlcov
============================= 20 passed in 11.95s =============================
```

### Test: easyocr_processor
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.1, pluggy-1.6.0 -- C:\Users\User\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\User\Desktop\Web-and-Desktop-Apps
configfile: pytest.ini
plugins: anyio-4.11.0, cov-7.0.0, flask-1.3.0, mock-3.15.1, requests-mock-1.12.1
collecting ... collected 20 items

tests/shared/test_easyocr_processor.py::test_easyocr_processor_initialization_success PASSED [  5%]
tests/shared/test_easyocr_processor.py::test_easyocr_processor_initialization_no_module PASSED [ 10%]
tests/shared/test_easyocr_processor.py::test_easyocr_processor_initialization_failure PASSED [ 15%]
tests/shared/test_easyocr_processor.py::test_extract_success PASSED      [ 20%]
tests/shared/test_easyocr_processor.py::test_extract_no_text_detected PASSED [ 25%]
tests/shared/test_easyocr_processor.py::test_extract_low_confidence_filtered PASSED [ 30%]
tests/shared/test_easyocr_processor.py::test_extract_no_easyocr_module PASSED [ 35%]
tests/shared/test_easyocr_processor.py::test_extract_reader_not_initialized PASSED [ 40%]
tests/shared/test_easyocr_processor.py::test_extract_exception_handling PASSED [ 45%]
tests/shared/test_easyocr_processor.py::test_parse_receipt_store_name_detection PASSED [ 50%]
tests/shared/test_easyocr_processor.py::test_parse_receipt_date_patterns PASSED [ 55%]
tests/shared/test_easyocr_processor.py::test_parse_receipt_total_patterns PASSED [ 60%]
tests/shared/test_easyocr_processor.py::test_extract_line_items PASSED   [ 65%]
tests/shared/test_easyocr_processor.py::test_extract_skip_keywords PASSED [ 70%]
tests/shared/test_easyocr_processor.py::test_extract_address_detection PASSED [ 75%]
tests/shared/test_easyocr_processor.py::test_extract_phone_detection PASSED [ 80%]
tests/shared/test_easyocr_processor.py::test_normalize_price_valid PASSED [ 85%]
tests/shared/test_easyocr_processor.py::test_normalize_price_invalid PASSED [ 90%]
tests/shared/test_easyocr_processor.py::test_extract_empty_text_lines PASSED [ 95%]
tests/shared/test_easyocr_processor.py::test_duplicate_items_filtered PASSED [100%]

=============================== tests coverage ================================
______________ coverage: platform win32, python 3.12.10-final-0 _______________

Name                                     Stmts   Miss  Cover   Missing
----------------------------------------------------------------------
shared\__init__.py                           0      0   100%
shared\models\__init__.py                   16     13    19%   10-23
shared\models\base_processor.py             45     45     0%   1-46
shared\models\donut_finetuner.py            99     99     0%   1-146
shared\models\donut_processor.py           339    339     0%   1-341
shared\models\easyocr_processor.py         121      6    95%   8-9, 32, 58-59, 67
shared\models\model_manager.py             173    150    13%   8-15, 17-27, 29-38, 40-60, 62-70, 72-75, 77, 79, 81-87, 89, 91-137, 139-142, 144-151, 153-159, 161-163, 165-168, 170-174
shared\models\model_trainer.py              82     82     0%   1-95
shared\models\ocr_processor.py             193    193     0%   1-204
shared\models\paddle_processor.py          180    180     0%   1-187
shared\utils\__init__.py                     3      0   100%
shared\utils\data_structures.py             43      7    84%   11, 30, 32-35, 43
shared\utils\image_processing.py           118    106    10%   8-26, 28-41, 43-51, 53-88, 90-110, 112-119
shared\utils\logger.py                      54     54     0%   1-55
web-app\backend\app.py                     311    311     0%   1-317
web-app\backend\auth\__init__.py             4      4     0%   4-14
web-app\backend\auth\decorators.py         103    103     0%   4-257
web-app\backend\auth\jwt_handler.py         66     66     0%   4-176
web-app\backend\auth\password.py            34     34     0%   4-89
web-app\backend\database\__init__.py         3      3     0%   4-17
web-app\backend\database\connection.py      52     52     0%   4-144
web-app\backend\database\models.py         132    132     0%   5-288
web-app\backend\validation\__init__.py       2      2     0%   4-19
web-app\backend\validation\schemas.py      115    115     0%   5-221
----------------------------------------------------------------------
TOTAL                                     2288   2096     8%
Coverage HTML written to dir htmlcov
============================= 20 passed in 8.62s ==============================
```

### Test: flask_app
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.1, pluggy-1.6.0 -- C:\Users\User\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\User\Desktop\Web-and-Desktop-Apps
configfile: pytest.ini
plugins: anyio-4.11.0, cov-7.0.0, flask-1.3.0, mock-3.15.1, requests-mock-1.12.1
collecting ... collected 31 items

tests/backend/test_app.py::TestHealthEndpoint::test_health_check_basic PASSED [  3%]
tests/backend/test_app.py::TestHealthEndpoint::test_health_check_includes_service_info PASSED [  6%]
tests/backend/test_app.py::TestHealthEndpoint::test_health_check_with_system_metrics PASSED [  9%]
tests/backend/test_app.py::TestModelsEndpoints::test_get_models PASSED   [ 12%]
tests/backend/test_app.py::TestModelsEndpoints::test_select_model_valid PASSED [ 16%]
tests/backend/test_app.py::TestModelsEndpoints::test_select_model_missing_id PASSED [ 19%]
tests/backend/test_app.py::TestModelsEndpoints::test_select_model_invalid_characters PASSED [ 22%]
tests/backend/test_app.py::TestModelsEndpoints::test_select_model_too_long PASSED [ 25%]
tests/backend/test_app.py::TestModelsEndpoints::test_unload_models PASSED [ 29%]
tests/backend/test_app.py::TestExtractEndpoint::test_extract_receipt_no_image PASSED [ 32%]
tests/backend/test_app.py::TestExtractEndpoint::test_extract_receipt_empty_filename PASSED [ 35%]
tests/backend/test_app.py::TestExtractEndpoint::test_extract_receipt_invalid_file_type PASSED [ 38%]
tests/backend/test_app.py::TestExtractEndpoint::test_extract_receipt_valid_image PASSED [ 41%]
tests/backend/test_app.py::TestBatchExtraction::test_batch_extract_no_image PASSED [ 45%]
tests/backend/test_app.py::TestBatchExtraction::test_batch_extract_multi_no_images PASSED [ 48%]
tests/backend/test_app.py::TestFinetuningEndpoints::test_prepare_finetune_missing_model_id PASSED [ 51%]
tests/backend/test_app.py::TestFinetuningEndpoints::test_prepare_finetune_valid PASSED [ 54%]
tests/backend/test_app.py::TestFinetuningEndpoints::test_finetune_status_not_found PASSED [ 58%]
tests/backend/test_app.py::TestFinetuningEndpoints::test_list_finetune_jobs PASSED [ 61%]
tests/backend/test_app.py::TestErrorHandlers::test_413_file_too_large FAILED [ 64%]
tests/backend/test_app.py::TestErrorHandlers::test_404_not_found PASSED  [ 67%]
tests/backend/test_app.py::TestFileValidation::test_allowed_file_valid_extensions PASSED [ 70%]
tests/backend/test_app.py::TestFileValidation::test_allowed_file_invalid_extensions PASSED [ 74%]
tests/backend/test_app.py::TestFileValidation::test_allowed_file_case_insensitive PASSED [ 77%]
tests/backend/test_app.py::TestSecurityConsiderations::test_filename_sanitization PASSED [ 80%]
tests/backend/test_app.py::TestSecurityConsiderations::test_cors_enabled PASSED [ 83%]
tests/backend/test_app.py::TestSecurityConsiderations::test_max_content_length_configured PASSED [ 87%]
tests/backend/test_app.py::TestTempFileCleanup::test_safe_delete_temp_file_exists PASSED [ 90%]
tests/backend/test_app.py::TestTempFileCleanup::test_safe_delete_temp_file_not_exists PASSED [ 93%]
tests/backend/test_app.py::TestErrorResponseFormat::test_create_error_response_format FAILED [ 96%]
tests/backend/test_app.py::TestErrorResponseFormat::test_create_error_response_with_details FAILED [100%]

================================== FAILURES ===================================
__________________ TestErrorHandlers.test_413_file_too_large __________________
tests\backend\test_app.py:286: in test_413_file_too_large
    assert response.status_code == 413
E   assert 500 == 413
E    +  where 500 = <WrapperTestResponse streamed [500 INTERNAL SERVER ERROR]>.status_code
------------------------------ Captured log call ------------------------------
ERROR    app:app.py:91 Extraction error: 413 Request Entity Too Large: The data value transmitted exceeds the capacity limit.
Traceback (most recent call last):
  File "C:\Users\User\Desktop\Web-and-Desktop-Apps\tests\backend\..\..\web-app\backend\app.py", line 78, in extract_receipt
    if 'image'not in request.files:return jsonify({'success':False,'error':'No image file provided'}),400
                     ^^^^^^^^^^^^^
  File "C:\Users\User\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\werkzeug\utils.py", line 107, in __get__
    value = self.fget(obj)  # type: ignore
            ^^^^^^^^^^^^^^
  File "C:\Users\User\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\werkzeug\wrappers\request.py", line 497, in files
    self._load_form_data()
  File "C:\Users\User\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\flask\wrappers.py", line 198, in _load_form_data
    super()._load_form_data()
  File "C:\Users\User\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\werkzeug\wrappers\request.py", line 272, in _load_form_data
    self._get_stream_for_parsing(),
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\User\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\werkzeug\wrappers\request.py", line 299, in _get_stream_for_parsing
    return self.stream
           ^^^^^^^^^^^
  File "C:\Users\User\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\werkzeug\utils.py", line 107, in __get__
    value = self.fget(obj)  # type: ignore
            ^^^^^^^^^^^^^^
  File "C:\Users\User\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\werkzeug\wrappers\request.py", line 351, in stream
    return get_input_stream(
           ^^^^^^^^^^^^^^^^^
  File "C:\Users\User\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\werkzeug\wsgi.py", line 173, in get_input_stream
    raise RequestEntityTooLarge()
werkzeug.exceptions.RequestEntityTooLarge: 413 Request Entity Too Large: The data value transmitted exceeds the capacity limit.
__________ TestErrorResponseFormat.test_create_error_response_format __________
tests\backend\test_app.py:412: in test_create_error_response_format
    response, status_code = create_error_response(
web-app\backend\app.py:38: in create_error_response
    return jsonify(response),status_code
           ^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\flask\json\__init__.py:170: in jsonify
    return current_app.json.response(*args, **kwargs)  # type: ignore[return-value]
           ^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\werkzeug\local.py:318: in __get__
    obj = instance._get_current_object()
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\werkzeug\local.py:519: in _get_current_object
    raise RuntimeError(unbound_message) from None
E   RuntimeError: Working outside of application context.
E   
E   This typically means that you attempted to use functionality that needed
E   the current application. To solve this, set up an application context
E   with app.app_context(). See the documentation for more information.
_______ TestErrorResponseFormat.test_create_error_response_with_details _______
tests\backend\test_app.py:433: in test_create_error_response_with_details
    response, status_code = create_error_response(
web-app\backend\app.py:38: in create_error_response
    return jsonify(response),status_code
           ^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\flask\json\__init__.py:170: in jsonify
    return current_app.json.response(*args, **kwargs)  # type: ignore[return-value]
           ^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\werkzeug\local.py:318: in __get__
    obj = instance._get_current_object()
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\werkzeug\local.py:519: in _get_current_object
    raise RuntimeError(unbound_message) from None
E   RuntimeError: Working outside of application context.
E   
E   This typically means that you attempted to use functionality that needed
E   the current application. To solve this, set up an application context
E   with app.app_context(). See the documentation for more information.
=============================== tests coverage ================================
______________ coverage: platform win32, python 3.12.10-final-0 _______________

Name                                     Stmts   Miss  Cover   Missing
----------------------------------------------------------------------
shared\__init__.py                           0      0   100%
shared\models\__init__.py                   16     13    19%   10-23
shared\models\base_processor.py             45     45     0%   1-46
shared\models\donut_finetuner.py            99     99     0%   1-146
shared\models\donut_processor.py           339    339     0%   1-341
shared\models\easyocr_processor.py         121    121     0%   1-127
shared\models\model_manager.py             173     67    61%   22-27, 44-51, 56-60, 85-87, 97-99, 107-111, 113-117, 121-127, 132-137, 139-142, 144-151, 161-163, 165-168
shared\models\model_trainer.py              82     60    27%   9-12, 15-16, 19, 22-24, 27-32, 35-38, 41-44, 49-68, 72-74, 77-80, 83, 86-88, 91-95
shared\models\ocr_processor.py             193    102    47%   11-12, 24, 34-35, 41, 47-55, 77, 104-109, 112-118, 121-130, 136-169, 172-194, 198-204
shared\models\paddle_processor.py          180    180     0%   1-187
shared\utils\__init__.py                     3      0   100%
shared\utils\data_structures.py             43      6    86%   11, 30, 32-35
shared\utils\image_processing.py           118     60    49%   17-21, 24-26, 28-41, 43-51, 59, 76-77, 81-84, 86-88, 94-95, 102-110, 112-119
shared\utils\logger.py                      54     54     0%   1-55
web-app\backend\app.py                     311    183    41%   31-34, 56-57, 61, 74, 96-118, 121-125, 129, 134-172, 185, 188-206, 209-273, 278-280, 283-294, 300, 303-310, 313-316
web-app\backend\auth\__init__.py             4      4     0%   4-14
web-app\backend\auth\decorators.py         103    103     0%   4-257
web-app\backend\auth\jwt_handler.py         66     66     0%   4-176
web-app\backend\auth\password.py            34     34     0%   4-89
web-app\backend\database\__init__.py         3      3     0%   4-17
web-app\backend\database\connection.py      52     52     0%   4-144
web-app\backend\database\models.py         132    132     0%   5-288
web-app\backend\validation\__init__.py       2      2     0%   4-19
web-app\backend\validation\schemas.py      115    115     0%   5-221
----------------------------------------------------------------------
TOTAL                                     2288   1840    20%
Coverage HTML written to dir htmlcov
=========================== short test summary info ===========================
FAILED tests/backend/test_app.py::TestErrorHandlers::test_413_file_too_large - assert 500 == 413
 +  where 500 = <WrapperTestResponse streamed [500 INTERNAL SERVER ERROR]>.status_code
FAILED tests/backend/test_app.py::TestErrorResponseFormat::test_create_error_response_format - RuntimeError: Working outside of application context.

This typically means that you attempted to use functionality that needed
the current application. To solve this, set up an application context
with app.app_context(). See the documentation for more information.
FAILED tests/backend/test_app.py::TestErrorResponseFormat::test_create_error_response_with_details - RuntimeError: Working outside of application context.

This typically means that you attempted to use functionality that needed
the current application. To solve this, set up an application context
with app.app_context(). See the documentation for more information.
======================== 3 failed, 28 passed in 10.45s ========================
```

### Test: health
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.1, pluggy-1.6.0 -- C:\Users\User\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\User\Desktop\Web-and-Desktop-Apps
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

Name                                     Stmts   Miss  Cover   Missing
----------------------------------------------------------------------
shared\__init__.py                           0      0   100%
shared\models\__init__.py                   16     13    19%   10-23
shared\models\base_processor.py             45     45     0%   1-46
shared\models\donut_finetuner.py            99     99     0%   1-146
shared\models\donut_processor.py           339    339     0%   1-341
shared\models\easyocr_processor.py         121    121     0%   1-127
shared\models\model_manager.py             173    107    38%   22-27, 44-51, 56-60, 77, 79, 81-87, 89, 91-137, 139-142, 144-151, 153-159, 161-163, 165-168, 170-174
shared\models\model_trainer.py              82     82     0%   1-95
shared\models\ocr_processor.py             193    193     0%   1-204
shared\models\paddle_processor.py          180    180     0%   1-187
shared\utils\__init__.py                     3      3     0%   1-10
shared\utils\data_structures.py             43     43     0%   1-43
shared\utils\image_processing.py           118    118     0%   1-119
shared\utils\logger.py                      54     54     0%   1-55
web-app\backend\app.py                     311    311     0%   1-317
web-app\backend\auth\__init__.py             4      4     0%   4-14
web-app\backend\auth\decorators.py         103    103     0%   4-257
web-app\backend\auth\jwt_handler.py         66     66     0%   4-176
web-app\backend\auth\password.py            34     34     0%   4-89
web-app\backend\database\__init__.py         3      3     0%   4-17
web-app\backend\database\connection.py      52     52     0%   4-144
web-app\backend\database\models.py         132    132     0%   5-288
web-app\backend\validation\__init__.py       2      2     0%   4-19
web-app\backend\validation\schemas.py      115    115     0%   5-221
----------------------------------------------------------------------
TOTAL                                     2288   2219     3%
Coverage HTML written to dir htmlcov
======================== 8 passed, 2 warnings in 7.74s ========================
```

### Test: image
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.1, pluggy-1.6.0 -- C:\Users\User\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\User\Desktop\Web-and-Desktop-Apps
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

Name                                     Stmts   Miss  Cover   Missing
----------------------------------------------------------------------
shared\__init__.py                           0      0   100%
shared\models\__init__.py                   16     16     0%   3-23
shared\models\base_processor.py             45     45     0%   1-46
shared\models\donut_finetuner.py            99     99     0%   1-146
shared\models\donut_processor.py           339    339     0%   1-341
shared\models\easyocr_processor.py         121    121     0%   1-127
shared\models\model_manager.py             173    173     0%   1-174
shared\models\model_trainer.py              82     82     0%   1-95
shared\models\ocr_processor.py             193    193     0%   1-204
shared\models\paddle_processor.py          180    180     0%   1-187
shared\utils\__init__.py                     3      0   100%
shared\utils\data_structures.py             43      7    84%   11, 30, 32-35, 43
shared\utils\image_processing.py           118     70    41%   17-21, 24-26, 39-41, 49-51, 53-88, 90-110
shared\utils\logger.py                      54     54     0%   1-55
web-app\backend\app.py                     311    311     0%   1-317
web-app\backend\auth\__init__.py             4      4     0%   4-14
web-app\backend\auth\decorators.py         103    103     0%   4-257
web-app\backend\auth\jwt_handler.py         66     66     0%   4-176
web-app\backend\auth\password.py            34     34     0%   4-89
web-app\backend\database\__init__.py         3      3     0%   4-17
web-app\backend\database\connection.py      52     52     0%   4-144
web-app\backend\database\models.py         132    132     0%   5-288
web-app\backend\validation\__init__.py       2      2     0%   4-19
web-app\backend\validation\schemas.py      115    115     0%   5-221
----------------------------------------------------------------------
TOTAL                                     2288   2201     4%
Coverage HTML written to dir htmlcov
============================== 7 passed in 1.46s ==============================
```

### Test: jwt_auth
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.1, pluggy-1.6.0 -- C:\Users\User\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\User\Desktop\Web-and-Desktop-Apps
configfile: pytest.ini
plugins: anyio-4.11.0, cov-7.0.0, flask-1.3.0, mock-3.15.1, requests-mock-1.12.1
collecting ... collected 36 items

tests/backend/auth/test_jwt_handler.py::TestCreateAccessToken::test_create_access_token_success PASSED [  2%]
tests/backend/auth/test_jwt_handler.py::TestCreateAccessToken::test_create_access_token_with_admin_flag PASSED [  5%]
tests/backend/auth/test_jwt_handler.py::TestCreateAccessToken::test_access_token_contains_correct_claims PASSED [  8%]
tests/backend/auth/test_jwt_handler.py::TestCreateAccessToken::test_access_token_expiry_time PASSED [ 11%]
tests/backend/auth/test_jwt_handler.py::TestCreateAccessToken::test_create_access_token_different_users_different_tokens PASSED [ 13%]
tests/backend/auth/test_jwt_handler.py::TestCreateAccessToken::test_create_access_token_same_user_different_tokens FAILED [ 16%]
tests/backend/auth/test_jwt_handler.py::TestCreateRefreshToken::test_create_refresh_token_generates_token_and_hash PASSED [ 19%]
tests/backend/auth/test_jwt_handler.py::TestCreateRefreshToken::test_create_refresh_token_unique PASSED [ 22%]
tests/backend/auth/test_jwt_handler.py::TestCreateRefreshToken::test_refresh_token_hash_is_deterministic PASSED [ 25%]
tests/backend/auth/test_jwt_handler.py::TestCreateRefreshToken::test_refresh_token_length_and_format PASSED [ 27%]
tests/backend/auth/test_jwt_handler.py::TestVerifyAccessToken::test_verify_valid_access_token PASSED [ 30%]
tests/backend/auth/test_jwt_handler.py::TestVerifyAccessToken::test_verify_expired_access_token PASSED [ 33%]
tests/backend/auth/test_jwt_handler.py::TestVerifyAccessToken::test_verify_invalid_signature PASSED [ 36%]
tests/backend/auth/test_jwt_handler.py::TestVerifyAccessToken::test_verify_wrong_token_type PASSED [ 38%]
tests/backend/auth/test_jwt_handler.py::TestVerifyAccessToken::test_verify_malformed_token PASSED [ 41%]
tests/backend/auth/test_jwt_handler.py::TestVerifyRefreshToken::test_verify_refresh_token_correct_hash PASSED [ 44%]
tests/backend/auth/test_jwt_handler.py::TestVerifyRefreshToken::test_verify_refresh_token_wrong_hash PASSED [ 47%]
tests/backend/auth/test_jwt_handler.py::TestVerifyRefreshToken::test_verify_refresh_token_wrong_token PASSED [ 50%]
tests/backend/auth/test_jwt_handler.py::TestVerifyRefreshToken::test_verify_refresh_token_timing_attack_resistance PASSED [ 52%]
tests/backend/auth/test_jwt_handler.py::TestVerifyRefreshToken::test_verify_refresh_token_exception_handling PASSED [ 55%]
tests/backend/auth/test_jwt_handler.py::TestRevokeRefreshToken::test_revoke_refresh_token_success ERROR [ 58%]
tests/backend/auth/test_jwt_handler.py::TestRevokeRefreshToken::test_revoke_nonexistent_token ERROR [ 61%]
tests/backend/auth/test_jwt_handler.py::TestRevokeRefreshToken::test_revoke_token_database_error ERROR [ 63%]
tests/backend/auth/test_jwt_handler.py::TestDecodeTokenWithoutVerification::test_decode_token_without_verification PASSED [ 66%]
tests/backend/auth/test_jwt_handler.py::TestDecodeTokenWithoutVerification::test_decode_expired_token_without_verification PASSED [ 69%]
tests/backend/auth/test_jwt_handler.py::TestDecodeTokenWithoutVerification::test_decode_invalid_signature_without_verification PASSED [ 72%]
tests/backend/auth/test_jwt_handler.py::TestDecodeTokenWithoutVerification::test_decode_malformed_token_returns_none PASSED [ 75%]
tests/backend/auth/test_jwt_handler.py::TestDecodeTokenWithoutVerification::test_decode_token_exception_handling PASSED [ 77%]
tests/backend/auth/test_jwt_handler.py::TestJWTConfiguration::test_jwt_secret_exists PASSED [ 80%]
tests/backend/auth/test_jwt_handler.py::TestJWTConfiguration::test_jwt_algorithm_is_hs256 PASSED [ 83%]
tests/backend/auth/test_jwt_handler.py::TestJWTConfiguration::test_access_token_expiry_configured PASSED [ 86%]
tests/backend/auth/test_jwt_handler.py::TestJWTConfiguration::test_refresh_token_expiry_configured PASSED [ 88%]
tests/backend/auth/test_jwt_handler.py::TestTokenSecurity::test_tokens_use_cryptographically_secure_randomness PASSED [ 91%]
tests/backend/auth/test_jwt_handler.py::TestTokenSecurity::test_refresh_token_hash_uses_sha256 PASSED [ 94%]
tests/backend/auth/test_jwt_handler.py::TestTokenSecurity::test_access_token_not_too_long_lived PASSED [ 97%]
tests/backend/auth/test_jwt_handler.py::TestTokenSecurity::test_different_users_cannot_forge_tokens PASSED [100%]

=================================== ERRORS ====================================
_ ERROR at setup of TestRevokeRefreshToken.test_revoke_refresh_token_success __
tests\conftest.py:71: in db_session
    from database.models import Base
web-app\backend\database\__init__.py:4: in <module>
    from .models import (
web-app\backend\database\models.py:251: in <module>
    class AuditLog(Base):
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_api.py:199: in __init__
    _as_declarative(reg, cls, dict_)
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:245: in _as_declarative
    return _MapperConfig.setup_mapping(registry, cls, dict_, None, {})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:326: in setup_mapping
    return _ClassScanMapperConfig(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:573: in __init__
    self._extract_mappable_attributes()
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:1530: in _extract_mappable_attributes
    raise exc.InvalidRequestError(
E   sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
___ ERROR at setup of TestRevokeRefreshToken.test_revoke_nonexistent_token ____
tests\conftest.py:71: in db_session
    from database.models import Base
web-app\backend\database\__init__.py:4: in <module>
    from .models import (
web-app\backend\database\models.py:251: in <module>
    class AuditLog(Base):
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_api.py:199: in __init__
    _as_declarative(reg, cls, dict_)
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:245: in _as_declarative
    return _MapperConfig.setup_mapping(registry, cls, dict_, None, {})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:326: in setup_mapping
    return _ClassScanMapperConfig(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:573: in __init__
    self._extract_mappable_attributes()
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:1530: in _extract_mappable_attributes
    raise exc.InvalidRequestError(
E   sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
__ ERROR at setup of TestRevokeRefreshToken.test_revoke_token_database_error __
tests\conftest.py:71: in db_session
    from database.models import Base
web-app\backend\database\__init__.py:4: in <module>
    from .models import (
web-app\backend\database\models.py:251: in <module>
    class AuditLog(Base):
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_api.py:199: in __init__
    _as_declarative(reg, cls, dict_)
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:245: in _as_declarative
    return _MapperConfig.setup_mapping(registry, cls, dict_, None, {})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:326: in setup_mapping
    return _ClassScanMapperConfig(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:573: in __init__
    self._extract_mappable_attributes()
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\sqlalchemy\orm\decl_base.py:1530: in _extract_mappable_attributes
    raise exc.InvalidRequestError(
E   sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
================================== FAILURES ===================================
__ TestCreateAccessToken.test_create_access_token_same_user_different_tokens __
tests\backend\auth\test_jwt_handler.py:100: in test_create_access_token_same_user_different_tokens
    assert token1 != token2
E   AssertionError: assert 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlci0xIiwiZW1haWwiOiJ1c2VyMUBleGFtcGxlLmNvbSIsImlzX2FkbWluIjpmYWxzZSwiaWF0IjoxNzY0Mzk1NjcxLCJleHAiOjE3NjQzOTY1NzEsInR5cGUiOiJhY2Nlc3MifQ.tFuET0xNQT-Xl8xlQSfpwUJEN-Zkc0BjTcv8IX54-KE' != 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlci0xIiwiZW1haWwiOiJ1c2VyMUBleGFtcGxlLmNvbSIsImlzX2FkbWluIjpmYWxzZSwiaWF0IjoxNzY0Mzk1NjcxLCJleHAiOjE3NjQzOTY1NzEsInR5cGUiOiJhY2Nlc3MifQ.tFuET0xNQT-Xl8xlQSfpwUJEN-Zkc0BjTcv8IX54-KE'
=============================== tests coverage ================================
______________ coverage: platform win32, python 3.12.10-final-0 _______________

Name                                     Stmts   Miss  Cover   Missing
----------------------------------------------------------------------
shared\__init__.py                           0      0   100%
shared\models\__init__.py                   16     16     0%   3-23
shared\models\base_processor.py             45     45     0%   1-46
shared\models\donut_finetuner.py            99     99     0%   1-146
shared\models\donut_processor.py           339    339     0%   1-341
shared\models\easyocr_processor.py         121    121     0%   1-127
shared\models\model_manager.py             173    173     0%   1-174
shared\models\model_trainer.py              82     82     0%   1-95
shared\models\ocr_processor.py             193    193     0%   1-204
shared\models\paddle_processor.py          180    180     0%   1-187
shared\utils\__init__.py                     3      3     0%   1-10
shared\utils\data_structures.py             43     43     0%   1-43
shared\utils\image_processing.py           118    118     0%   1-119
shared\utils\logger.py                      54     54     0%   1-55
web-app\backend\app.py                     311    311     0%   1-317
web-app\backend\auth\__init__.py             4      0   100%
web-app\backend\auth\decorators.py         103     90    13%   28-70, 86-93, 113-165, 184-202, 219-257
web-app\backend\auth\jwt_handler.py         66     15    77%   135-158
web-app\backend\auth\password.py            34     28    18%   20-28, 42-51, 71-89
web-app\backend\database\__init__.py         3      2    33%   15-17
web-app\backend\database\connection.py      52     52     0%   4-144
web-app\backend\database\models.py         132      6    95%   88, 139, 174, 207, 248, 288
web-app\backend\validation\__init__.py       2      2     0%   4-19
web-app\backend\validation\schemas.py      115    115     0%   5-221
----------------------------------------------------------------------
TOTAL                                     2288   2087     9%
Coverage HTML written to dir htmlcov
=========================== short test summary info ===========================
FAILED tests/backend/auth/test_jwt_handler.py::TestCreateAccessToken::test_create_access_token_same_user_different_tokens - AssertionError: assert 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlci0xIiwiZW1haWwiOiJ1c2VyMUBleGFtcGxlLmNvbSIsImlzX2FkbWluIjpmYWxzZSwiaWF0IjoxNzY0Mzk1NjcxLCJleHAiOjE3NjQzOTY1NzEsInR5cGUiOiJhY2Nlc3MifQ.tFuET0xNQT-Xl8xlQSfpwUJEN-Zkc0BjTcv8IX54-KE' != 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlci0xIiwiZW1haWwiOiJ1c2VyMUBleGFtcGxlLmNvbSIsImlzX2FkbWluIjpmYWxzZSwiaWF0IjoxNzY0Mzk1NjcxLCJleHAiOjE3NjQzOTY1NzEsInR5cGUiOiJhY2Nlc3MifQ.tFuET0xNQT-Xl8xlQSfpwUJEN-Zkc0BjTcv8IX54-KE'
ERROR tests/backend/auth/test_jwt_handler.py::TestRevokeRefreshToken::test_revoke_refresh_token_success - sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
ERROR tests/backend/auth/test_jwt_handler.py::TestRevokeRefreshToken::test_revoke_nonexistent_token - sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
ERROR tests/backend/auth/test_jwt_handler.py::TestRevokeRefreshToken::test_revoke_token_database_error - sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
============= 1 failed, 32 passed, 16 warnings, 3 errors in 2.91s =============
```

### Test: logger_utils
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.1, pluggy-1.6.0 -- C:\Users\User\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\User\Desktop\Web-and-Desktop-Apps
configfile: pytest.ini
plugins: anyio-4.11.0, cov-7.0.0, flask-1.3.0, mock-3.15.1, requests-mock-1.12.1
collecting ... collected 24 items

tests/shared/utils/test_logger.py::TestStructuredFormatter::test_structured_formatter_creates_json PASSED [  4%]
tests/shared/utils/test_logger.py::TestStructuredFormatter::test_structured_formatter_includes_required_fields PASSED [  8%]
tests/shared/utils/test_logger.py::TestStructuredFormatter::test_structured_formatter_log_levels PASSED [ 12%]
tests/shared/utils/test_logger.py::TestStructuredFormatter::test_structured_formatter_with_exception PASSED [ 16%]
tests/shared/utils/test_logger.py::TestStructuredFormatter::test_structured_formatter_with_extra_fields PASSED [ 20%]
tests/shared/utils/test_logger.py::TestColoredFormatter::test_colored_formatter_adds_colors PASSED [ 25%]
tests/shared/utils/test_logger.py::TestColoredFormatter::test_colored_formatter_resets_color PASSED [ 29%]
tests/shared/utils/test_logger.py::TestColoredFormatter::test_colored_formatter_preserves_levelname PASSED [ 33%]
tests/shared/utils/test_logger.py::TestSetupLogger::test_setup_logger_creates_logger PASSED [ 37%]
tests/shared/utils/test_logger.py::TestSetupLogger::test_setup_logger_creates_log_file PASSED [ 41%]
tests/shared/utils/test_logger.py::TestSetupLogger::test_setup_logger_log_levels PASSED [ 45%]
tests/shared/utils/test_logger.py::TestSetupLogger::test_setup_logger_json_format PASSED [ 50%]
tests/shared/utils/test_logger.py::TestSetupLogger::test_setup_logger_console_output PASSED [ 54%]
tests/shared/utils/test_logger.py::TestSetupLogger::test_setup_logger_idempotent PASSED [ 58%]
tests/shared/utils/test_logger.py::TestSetupLogger::test_setup_logger_creates_log_directory PASSED [ 62%]
tests/shared/utils/test_logger.py::TestSetupLogger::test_setup_logger_rotating_file_handler PASSED [ 66%]
tests/shared/utils/test_logger.py::TestGetLogger::test_get_logger_returns_logger PASSED [ 70%]
tests/shared/utils/test_logger.py::TestGetLogger::test_get_logger_same_name_same_logger PASSED [ 75%]
tests/shared/utils/test_logger.py::TestGetLogger::test_get_logger_different_names PASSED [ 79%]
tests/shared/utils/test_logger.py::TestLogWithContext::test_log_with_context_adds_extra_fields FAILED [ 83%]
tests/shared/utils/test_logger.py::TestLogWithContext::test_log_with_context_different_levels FAILED [ 87%]
tests/shared/utils/test_logger.py::TestLoggerIntegration::test_full_logging_workflow PASSED [ 91%]
tests/shared/utils/test_logger.py::TestLoggerIntegration::test_logger_handles_unicode PASSED [ 95%]
tests/shared/utils/test_logger.py::TestLoggerIntegration::test_logger_exception_logging PASSED [100%]

================================== FAILURES ===================================
_________ TestLogWithContext.test_log_with_context_adds_extra_fields __________
tests\shared\utils\test_logger.py:393: in test_log_with_context_adds_extra_fields
    log_with_context(
shared\utils\logger.py:45: in log_with_context
    getattr(logger,level)(message,extra=extra)
C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.12_3.12.2800.0_x64__qbz5n2kfra8p0\Lib\logging\__init__.py:1539: in info
    self._log(INFO, msg, args, **kwargs)
C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.12_3.12.2800.0_x64__qbz5n2kfra8p0\Lib\logging\__init__.py:1684: in _log
    self.handle(record)
C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.12_3.12.2800.0_x64__qbz5n2kfra8p0\Lib\logging\__init__.py:1700: in handle
    self.callHandlers(record)
C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.12_3.12.2800.0_x64__qbz5n2kfra8p0\Lib\logging\__init__.py:1761: in callHandlers
    if record.levelno >= hdlr.level:
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: '>=' not supported between instances of 'int' and 'Mock'
__________ TestLogWithContext.test_log_with_context_different_levels __________
tests\shared\utils\test_logger.py:423: in test_log_with_context_different_levels
    log_with_context(
shared\utils\logger.py:45: in log_with_context
    getattr(logger,level)(message,extra=extra)
C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.12_3.12.2800.0_x64__qbz5n2kfra8p0\Lib\logging\__init__.py:1527: in debug
    self._log(DEBUG, msg, args, **kwargs)
C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.12_3.12.2800.0_x64__qbz5n2kfra8p0\Lib\logging\__init__.py:1684: in _log
    self.handle(record)
C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.12_3.12.2800.0_x64__qbz5n2kfra8p0\Lib\logging\__init__.py:1700: in handle
    self.callHandlers(record)
C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.12_3.12.2800.0_x64__qbz5n2kfra8p0\Lib\logging\__init__.py:1761: in callHandlers
    if record.levelno >= hdlr.level:
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: '>=' not supported between instances of 'int' and 'Mock'
=============================== tests coverage ================================
______________ coverage: platform win32, python 3.12.10-final-0 _______________

Name                                     Stmts   Miss  Cover   Missing
----------------------------------------------------------------------
shared\__init__.py                           0      0   100%
shared\models\__init__.py                   16     16     0%   3-23
shared\models\base_processor.py             45     45     0%   1-46
shared\models\donut_finetuner.py            99     99     0%   1-146
shared\models\donut_processor.py           339    339     0%   1-341
shared\models\easyocr_processor.py         121    121     0%   1-127
shared\models\model_manager.py             173    173     0%   1-174
shared\models\model_trainer.py              82     82     0%   1-95
shared\models\ocr_processor.py             193    193     0%   1-204
shared\models\paddle_processor.py          180    180     0%   1-187
shared\utils\__init__.py                     3      0   100%
shared\utils\data_structures.py             43      7    84%   11, 30, 32-35, 43
shared\utils\image_processing.py           118    106    10%   8-26, 28-41, 43-51, 53-88, 90-110, 112-119
shared\utils\logger.py                      54      9    83%   47-55
web-app\backend\app.py                     311    311     0%   1-317
web-app\backend\auth\__init__.py             4      4     0%   4-14
web-app\backend\auth\decorators.py         103    103     0%   4-257
web-app\backend\auth\jwt_handler.py         66     66     0%   4-176
web-app\backend\auth\password.py            34     34     0%   4-89
web-app\backend\database\__init__.py         3      3     0%   4-17
web-app\backend\database\connection.py      52     52     0%   4-144
web-app\backend\database\models.py         132    132     0%   5-288
web-app\backend\validation\__init__.py       2      2     0%   4-19
web-app\backend\validation\schemas.py      115    115     0%   5-221
----------------------------------------------------------------------
TOTAL                                     2288   2192     4%
Coverage HTML written to dir htmlcov
=========================== short test summary info ===========================
FAILED tests/shared/utils/test_logger.py::TestLogWithContext::test_log_with_context_adds_extra_fields - TypeError: '>=' not supported between instances of 'int' and 'Mock'
FAILED tests/shared/utils/test_logger.py::TestLogWithContext::test_log_with_context_different_levels - TypeError: '>=' not supported between instances of 'int' and 'Mock'
================== 2 failed, 22 passed, 19 warnings in 1.81s ==================
```

### Test: models
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.1, pluggy-1.6.0 -- C:\Users\User\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\User\Desktop\Web-and-Desktop-Apps
configfile: pytest.ini
plugins: anyio-4.11.0, cov-7.0.0, flask-1.3.0, mock-3.15.1, requests-mock-1.12.1
collecting ... collected 30 items

tests/shared/test_model_manager.py::test_models_config_exists PASSED     [  3%]
tests/shared/test_model_manager.py::test_models_config_valid_json PASSED [  6%]
tests/shared/test_model_manager.py::test_models_config_has_required_models PASSED [ 10%]
tests/shared/test_model_manager.py::test_default_model_exists PASSED     [ 13%]
tests/shared/test_model_manager.py::test_model_schema PASSED             [ 16%]
tests/shared/test_model_manager.py::test_model_manager_initialization PASSED [ 20%]
tests/shared/test_model_manager.py::test_model_manager_get_available_models PASSED [ 23%]
tests/shared/test_model_manager.py::test_model_manager_get_default_model PASSED [ 26%]
tests/shared/test_model_manager.py::test_model_manager_select_model PASSED [ 30%]
tests/shared/test_model_manager.py::test_model_manager_get_model_info PASSED [ 33%]
tests/shared/test_model_manager.py::test_model_manager_filter_by_capability PASSED [ 36%]
tests/shared/test_model_manager.py::test_model_manager_config_validation PASSED [ 40%]
tests/shared/test_model_manager.py::test_model_manager_config_validation_model_schema PASSED [ 43%]
tests/shared/test_model_manager.py::test_model_manager_default_model_validation PASSED [ 46%]
tests/shared/test_model_manager.py::test_model_manager_get_processor_default PASSED [ 50%]
tests/shared/test_model_manager.py::test_model_manager_get_processor_specific_model PASSED [ 53%]
tests/shared/test_model_manager.py::test_model_manager_unload_model PASSED [ 56%]
tests/shared/test_model_manager.py::test_model_manager_unload_all_models PASSED [ 60%]
tests/shared/test_model_manager.py::test_model_manager_get_resource_stats PASSED [ 63%]
tests/shared/test_model_manager.py::test_model_manager_get_model_capabilities PASSED [ 66%]
tests/shared/test_model_manager.py::test_model_manager_load_config_error_handling PASSED [ 70%]
tests/shared/test_model_manager.py::test_model_manager_processor_caching PASSED [ 73%]
tests/shared/test_model_manager.py::test_model_manager_max_loaded_models_eviction PASSED [ 76%]
tests/shared/test_model_manager.py::test_model_manager_get_processor_invalid_model PASSED [ 80%]
tests/shared/test_model_manager.py::test_model_manager_threading_lock PASSED [ 83%]
tests/shared/test_model_manager.py::test_model_manager_gpu_check PASSED  [ 86%]
tests/shared/test_model_manager.py::test_model_manager_initialization_with_custom_max_models PASSED [ 90%]
tests/shared/test_model_manager.py::test_model_manager_processor_types PASSED [ 93%]
tests/shared/test_model_manager.py::test_model_manager_processor_import_error_handling PASSED [ 96%]
tests/shared/test_model_manager.py::test_model_manager_select_model_updates_current PASSED [100%]

=============================== tests coverage ================================
______________ coverage: platform win32, python 3.12.10-final-0 _______________

Name                                     Stmts   Miss  Cover   Missing
----------------------------------------------------------------------
shared\__init__.py                           0      0   100%
shared\models\__init__.py                   16     13    19%   10-23
shared\models\base_processor.py             45     45     0%   1-46
shared\models\donut_finetuner.py            99     99     0%   1-146
shared\models\donut_processor.py           339    289    15%   21, 23, 26-32, 35-54, 70-79, 81-118, 120-130, 132-159, 161-206, 208-246, 248-267, 270-289, 291-327, 329-341
shared\models\easyocr_processor.py         121    121     0%   1-127
shared\models\model_manager.py             173     36    79%   44-51, 56-60, 94-95, 110-111, 113-117, 121-127, 132-137, 173
shared\models\model_trainer.py              82     82     0%   1-95
shared\models\ocr_processor.py             193    150    22%   11-12, 24, 34-35, 41, 47-55, 58-72, 75-118, 121-130, 133-169, 172-194, 198-204
shared\models\paddle_processor.py          180    180     0%   1-187
shared\utils\__init__.py                     3      0   100%
shared\utils\data_structures.py             43      7    84%   11, 30, 32-35, 43
shared\utils\image_processing.py           118    106    10%   8-26, 28-41, 43-51, 53-88, 90-110, 112-119
shared\utils\logger.py                      54     54     0%   1-55
web-app\backend\app.py                     311    311     0%   1-317
web-app\backend\auth\__init__.py             4      4     0%   4-14
web-app\backend\auth\decorators.py         103    103     0%   4-257
web-app\backend\auth\jwt_handler.py         66     66     0%   4-176
web-app\backend\auth\password.py            34     34     0%   4-89
web-app\backend\database\__init__.py         3      3     0%   4-17
web-app\backend\database\connection.py      52     52     0%   4-144
web-app\backend\database\models.py         132    132     0%   5-288
web-app\backend\validation\__init__.py       2      2     0%   4-19
web-app\backend\validation\schemas.py      115    115     0%   5-221
----------------------------------------------------------------------
TOTAL                                     2288   2004    12%
Coverage HTML written to dir htmlcov
======================= 30 passed, 2 warnings in 18.45s =======================
sys:1: DeprecationWarning: builtin type swigvarlink has no __module__ attribute
```

### Test: ocr
```
Usage: python test_ocr_simple.py <image_path>
```

### Test: paddle_processor
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.1, pluggy-1.6.0 -- C:\Users\User\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\User\Desktop\Web-and-Desktop-Apps
configfile: pytest.ini
plugins: anyio-4.11.0, cov-7.0.0, flask-1.3.0, mock-3.15.1, requests-mock-1.12.1
collecting ... collected 20 items

tests/shared/test_paddle_processor.py::test_paddle_processor_initialization_success PASSED [  5%]
tests/shared/test_paddle_processor.py::test_paddle_processor_initialization_failure PASSED [ 10%]
tests/shared/test_paddle_processor.py::test_extract_success PASSED       [ 15%]
tests/shared/test_paddle_processor.py::test_extract_no_results PASSED    [ 20%]
tests/shared/test_paddle_processor.py::test_extract_empty_results PASSED [ 25%]
tests/shared/test_paddle_processor.py::test_extract_retry_with_original_image PASSED [ 30%]
tests/shared/test_paddle_processor.py::test_extract_grayscale_to_rgb_conversion PASSED [ 35%]
tests/shared/test_paddle_processor.py::test_extract_exception_handling PASSED [ 40%]
tests/shared/test_paddle_processor.py::test_extract_low_confidence_filtered PASSED [ 45%]
tests/shared/test_paddle_processor.py::test_extract_date_patterns PASSED [ 50%]
tests/shared/test_paddle_processor.py::test_extract_total_patterns PASSED [ 55%]
tests/shared/test_paddle_processor.py::test_extract_line_items PASSED    [ 60%]
tests/shared/test_paddle_processor.py::test_extract_skip_keywords PASSED [ 65%]
tests/shared/test_paddle_processor.py::test_extract_address_detection PASSED [ 70%]
tests/shared/test_paddle_processor.py::test_extract_phone_detection PASSED [ 75%]
tests/shared/test_paddle_processor.py::test_normalize_price_valid PASSED [ 80%]
tests/shared/test_paddle_processor.py::test_normalize_price_invalid PASSED [ 85%]
tests/shared/test_paddle_processor.py::test_extract_confidence_score_calculation PASSED [ 90%]
tests/shared/test_paddle_processor.py::test_extract_malformed_result_handling PASSED [ 95%]
tests/shared/test_paddle_processor.py::test_extract_quantity_parsing PASSED [100%]

=============================== tests coverage ================================
______________ coverage: platform win32, python 3.12.10-final-0 _______________

Name                                     Stmts   Miss  Cover   Missing
----------------------------------------------------------------------
shared\__init__.py                           0      0   100%
shared\models\__init__.py                   16     13    19%   10-23
shared\models\base_processor.py             45     45     0%   1-46
shared\models\donut_finetuner.py            99     99     0%   1-146
shared\models\donut_processor.py           339    339     0%   1-341
shared\models\easyocr_processor.py         121    121     0%   1-127
shared\models\model_manager.py             173    150    13%   8-15, 17-27, 29-38, 40-60, 62-70, 72-75, 77, 79, 81-87, 89, 91-137, 139-142, 144-151, 153-159, 161-163, 165-168, 170-174
shared\models\model_trainer.py              82     82     0%   1-95
shared\models\ocr_processor.py             193    193     0%   1-204
shared\models\paddle_processor.py          180     20    89%   11-12, 62-63, 67, 74-75, 91-92, 101-102, 167-175
shared\utils\__init__.py                     3      0   100%
shared\utils\data_structures.py             43      7    84%   11, 30, 32-35, 43
shared\utils\image_processing.py           118    106    10%   8-26, 28-41, 43-51, 53-88, 90-110, 112-119
shared\utils\logger.py                      54     54     0%   1-55
web-app\backend\app.py                     311    311     0%   1-317
web-app\backend\auth\__init__.py             4      4     0%   4-14
web-app\backend\auth\decorators.py         103    103     0%   4-257
web-app\backend\auth\jwt_handler.py         66     66     0%   4-176
web-app\backend\auth\password.py            34     34     0%   4-89
web-app\backend\database\__init__.py         3      3     0%   4-17
web-app\backend\database\connection.py      52     52     0%   4-144
web-app\backend\database\models.py         132    132     0%   5-288
web-app\backend\validation\__init__.py       2      2     0%   4-19
web-app\backend\validation\schemas.py      115    115     0%   5-221
----------------------------------------------------------------------
TOTAL                                     2288   2051    10%
Coverage HTML written to dir htmlcov
============================= 20 passed in 14.17s =============================
```

### Test: password_security
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.1, pluggy-1.6.0 -- C:\Users\User\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\User\Desktop\Web-and-Desktop-Apps
configfile: pytest.ini
plugins: anyio-4.11.0, cov-7.0.0, flask-1.3.0, mock-3.15.1, requests-mock-1.12.1
collecting ... collected 34 items

tests/backend/auth/test_password.py::TestHashPassword::test_hash_password_creates_valid_bcrypt_hash PASSED [  2%]
tests/backend/auth/test_password.py::TestHashPassword::test_hash_password_empty_raises_error PASSED [  5%]
tests/backend/auth/test_password.py::TestHashPassword::test_hash_password_none_raises_error PASSED [  8%]
tests/backend/auth/test_password.py::TestHashPassword::test_hash_password_different_each_time PASSED [ 11%]
tests/backend/auth/test_password.py::TestHashPassword::test_hash_password_unicode_support PASSED [ 14%]
tests/backend/auth/test_password.py::TestHashPassword::test_hash_password_various_lengths FAILED [ 17%]
tests/backend/auth/test_password.py::TestHashPassword::test_hash_password_special_characters PASSED [ 20%]
tests/backend/auth/test_password.py::TestHashPassword::test_hash_password_uses_appropriate_rounds PASSED [ 23%]
tests/backend/auth/test_password.py::TestVerifyPassword::test_verify_password_correct PASSED [ 26%]
tests/backend/auth/test_password.py::TestVerifyPassword::test_verify_password_incorrect PASSED [ 29%]
tests/backend/auth/test_password.py::TestVerifyPassword::test_verify_password_case_sensitive PASSED [ 32%]
tests/backend/auth/test_password.py::TestVerifyPassword::test_verify_password_empty_credentials PASSED [ 35%]
tests/backend/auth/test_password.py::TestVerifyPassword::test_verify_password_none_credentials PASSED [ 38%]
tests/backend/auth/test_password.py::TestVerifyPassword::test_verify_password_exception_handling PASSED [ 41%]
tests/backend/auth/test_password.py::TestVerifyPassword::test_verify_password_multiple_attempts PASSED [ 44%]
tests/backend/auth/test_password.py::TestVerifyPassword::test_verify_password_whitespace_matters PASSED [ 47%]
tests/backend/auth/test_password.py::TestIsPasswordStrong::test_is_password_strong_valid PASSED [ 50%]
tests/backend/auth/test_password.py::TestIsPasswordStrong::test_is_password_strong_too_short PASSED [ 52%]
tests/backend/auth/test_password.py::TestIsPasswordStrong::test_is_password_strong_no_uppercase PASSED [ 55%]
tests/backend/auth/test_password.py::TestIsPasswordStrong::test_is_password_strong_no_lowercase PASSED [ 58%]
tests/backend/auth/test_password.py::TestIsPasswordStrong::test_is_password_strong_no_number PASSED [ 61%]
tests/backend/auth/test_password.py::TestIsPasswordStrong::test_is_password_strong_no_special_char PASSED [ 64%]
tests/backend/auth/test_password.py::TestIsPasswordStrong::test_is_password_strong_multiple_issues PASSED [ 67%]
tests/backend/auth/test_password.py::TestIsPasswordStrong::test_is_password_strong_all_requirements PASSED [ 70%]
tests/backend/auth/test_password.py::TestIsPasswordStrong::test_is_password_strong_exact_length PASSED [ 73%]
tests/backend/auth/test_password.py::TestIsPasswordStrong::test_is_password_strong_various_special_chars PASSED [ 76%]
tests/backend/auth/test_password.py::TestIsPasswordStrong::test_is_password_strong_unicode_special_chars_not_counted PASSED [ 79%]
tests/backend/auth/test_password.py::TestIsPasswordStrong::test_is_password_strong_very_long_password PASSED [ 82%]
tests/backend/auth/test_password.py::TestIsPasswordStrong::test_is_password_strong_minimum_requirements_only PASSED [ 85%]
tests/backend/auth/test_password.py::TestPasswordSecurityBestPractices::test_password_not_stored_in_plain_text PASSED [ 88%]
tests/backend/auth/test_password.py::TestPasswordSecurityBestPractices::test_hash_is_one_way PASSED [ 91%]
tests/backend/auth/test_password.py::TestPasswordSecurityBestPractices::test_timing_attack_resistance PASSED [ 94%]
tests/backend/auth/test_password.py::TestPasswordSecurityBestPractices::test_salt_is_unique_per_hash PASSED [ 97%]
tests/backend/auth/test_password.py::TestPasswordSecurityBestPractices::test_bcrypt_rounds_is_secure PASSED [100%]

================================== FAILURES ===================================
_____________ TestHashPassword.test_hash_password_various_lengths _____________
tests\backend\auth\test_password.py:83: in test_hash_password_various_lengths
    hashed = hash_password(password)
             ^^^^^^^^^^^^^^^^^^^^^^^
web-app\backend\auth\password.py:26: in hash_password
    hashed = bcrypt.hashpw(password_bytes, salt)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   ValueError: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])
=============================== tests coverage ================================
______________ coverage: platform win32, python 3.12.10-final-0 _______________

Name                                     Stmts   Miss  Cover   Missing
----------------------------------------------------------------------
shared\__init__.py                           0      0   100%
shared\models\__init__.py                   16     16     0%   3-23
shared\models\base_processor.py             45     45     0%   1-46
shared\models\donut_finetuner.py            99     99     0%   1-146
shared\models\donut_processor.py           339    339     0%   1-341
shared\models\easyocr_processor.py         121    121     0%   1-127
shared\models\model_manager.py             173    173     0%   1-174
shared\models\model_trainer.py              82     82     0%   1-95
shared\models\ocr_processor.py             193    193     0%   1-204
shared\models\paddle_processor.py          180    180     0%   1-187
shared\utils\__init__.py                     3      3     0%   1-10
shared\utils\data_structures.py             43     43     0%   1-43
shared\utils\image_processing.py           118    118     0%   1-119
shared\utils\logger.py                      54     54     0%   1-55
web-app\backend\app.py                     311    311     0%   1-317
web-app\backend\auth\__init__.py             4      0   100%
web-app\backend\auth\decorators.py         103     90    13%   28-70, 86-93, 113-165, 184-202, 219-257
web-app\backend\auth\jwt_handler.py         66     46    30%   39-52, 65-70, 83-98, 112-121, 135-158, 172-176
web-app\backend\auth\password.py            34      0   100%
web-app\backend\database\__init__.py         3      3     0%   4-17
web-app\backend\database\connection.py      52     52     0%   4-144
web-app\backend\database\models.py         132    132     0%   5-288
web-app\backend\validation\__init__.py       2      2     0%   4-19
web-app\backend\validation\schemas.py      115    115     0%   5-221
----------------------------------------------------------------------
TOTAL                                     2288   2217     3%
Coverage HTML written to dir htmlcov
=========================== short test summary info ===========================
FAILED tests/backend/auth/test_password.py::TestHashPassword::test_hash_password_various_lengths - ValueError: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])
======================== 1 failed, 33 passed in 21.60s ========================
```

### Test: test_system_health
```
=== System Health Tests ===
Timestamp: 2025-11-29T08:09:27.264407
Command: C:\Users\User\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe -m pytest tests/test_system_health.py -v --tb=short --cov=shared --cov=web-app/backend --cov-report=term-missing --cov-report html:htmlcov/test_system_health

============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.1, pluggy-1.6.0 -- C:\Users\User\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\User\Desktop\Web-and-Desktop-Apps
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

Name                                     Stmts   Miss  Cover   Missing
----------------------------------------------------------------------
shared\__init__.py                           0      0   100%
shared\models\__init__.py                   16     13    19%   10-23
shared\models\base_processor.py             45     45     0%   1-46
shared\models\donut_finetuner.py            99     99     0%   1-146
shared\models\donut_processor.py           339    339     0%   1-341
shared\models\easyocr_processor.py         121    121     0%   1-127
shared\models\model_manager.py             173    107    38%   22-27, 44-51, 56-60, 77, 79, 81-87, 89, 91-137, 139-142, 144-151, 153-159, 161-163, 165-168, 170-174
shared\models\model_trainer.py              82     82     0%   1-95
shared\models\ocr_processor.py             193    193     0%   1-204
shared\models\paddle_processor.py          180    180     0%   1-187
shared\utils\__init__.py                     3      3     0%   1-10
shared\utils\data_structures.py             43     43     0%   1-43
shared\utils\image_processing.py           118    118     0%   1-119
shared\utils\logger.py                      54     54     0%   1-55
web-app\backend\app.py                     311    311     0%   1-317
web-app\backend\auth\__init__.py             4      4     0%   4-14
web-app\backend\auth\decorators.py         103    103     0%   4-257
web-app\backend\auth\jwt_handler.py         66     66     0%   4-176
web-app\backend\auth\password.py            34     34     0%   4-89
web-app\backend\database\__init__.py         3      3     0%   4-17
web-app\backend\database\connection.py      52     52     0%   4-144
web-app\backend\database\models.py         132    132     0%   5-288
web-app\backend\validation\__init__.py       2      2     0%   4-19
web-app\backend\validation\schemas.py      115    115     0%   5-221
----------------------------------------------------------------------
TOTAL                                     2288   2219     3%
Coverage HTML written to dir htmlcov/test_system_health
======================== 8 passed, 2 warnings in 8.52s ========================


=== STDERR ===
```

### Test: validation_schemas
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.1, pluggy-1.6.0 -- C:\Users\User\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\User\Desktop\Web-and-Desktop-Apps
configfile: pytest.ini
plugins: anyio-4.11.0, cov-7.0.0, flask-1.3.0, mock-3.15.1, requests-mock-1.12.1
collecting ... collected 0 items / 1 error

=================================== ERRORS ====================================
__________ ERROR collecting tests/backend/validation/test_schemas.py __________
ImportError while importing test module 'C:\Users\User\Desktop\Web-and-Desktop-Apps\tests\backend\validation\test_schemas.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\pydantic\networks.py:965: in import_email_validator
    import email_validator
E   ModuleNotFoundError: No module named 'email_validator'

The above exception was the direct cause of the following exception:
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\_pytest\python.py:507: in importtestmodule
    mod = import_path(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\_pytest\pathlib.py:587: in import_path
    importlib.import_module(module_name)
C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.12_3.12.2800.0_x64__qbz5n2kfra8p0\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
<frozen importlib._bootstrap>:1387: in _gcd_import
    ???
<frozen importlib._bootstrap>:1360: in _find_and_load
    ???
<frozen importlib._bootstrap>:1331: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:935: in _load_unlocked
    ???
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\_pytest\assertion\rewrite.py:197: in exec_module
    exec(co, module.__dict__)
tests\backend\validation\test_schemas.py:14: in <module>
    from validation.schemas import (
web-app\backend\validation\__init__.py:4: in <module>
    from .schemas import (
web-app\backend\validation\schemas.py:11: in <module>
    class UserRegisterSchema(BaseModel):
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\pydantic\_internal\_model_construction.py:255: in __new__
    complete_model_class(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\pydantic\_internal\_model_construction.py:648: in complete_model_class
    schema = gen_schema.generate_schema(cls)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\pydantic\_internal\_generate_schema.py:729: in generate_schema
    schema = self._generate_schema_inner(obj)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\pydantic\_internal\_generate_schema.py:1023: in _generate_schema_inner
    return self._model_schema(obj)
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\pydantic\_internal\_generate_schema.py:856: in _model_schema
    {k: self._generate_md_field_schema(k, v, decorators) for k, v in fields.items()},
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\pydantic\_internal\_generate_schema.py:1228: in _generate_md_field_schema
    schema, metadata = self._common_field_schema(name, field_info, decorators)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\pydantic\_internal\_generate_schema.py:1282: in _common_field_schema
    schema = self._apply_annotations(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\pydantic\_internal\_generate_schema.py:2227: in _apply_annotations
    schema = get_inner_schema(source_type)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\pydantic\_internal\_schema_generation_shared.py:83: in __call__
    schema = self._handler(source_type)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\pydantic\_internal\_generate_schema.py:2203: in inner_handler
    schema = self._generate_schema_from_get_schema_method(obj, source_type)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\pydantic\_internal\_generate_schema.py:919: in _generate_schema_from_get_schema_method
    schema = get_schema(
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\pydantic\networks.py:1005: in __get_pydantic_core_schema__
    import_email_validator()
..\..\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\pydantic\networks.py:967: in import_email_validator
    raise ImportError("email-validator is not installed, run `pip install 'pydantic[email]'`") from e
E   ImportError: email-validator is not installed, run `pip install 'pydantic[email]'`
=========================== short test summary info ===========================
ERROR tests/backend/validation/test_schemas.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
======================== 2 warnings, 1 error in 1.27s =========================
```

## Application Logs

### Backend Log (Last 100 lines)
```
2025-11-29 08:20:47,233 - shared.models.model_manager - INFO - Configuration validation passed
2025-11-29 08:20:47,233 - shared.models.model_manager - INFO - Loaded 5 model configurations
2025-11-29 08:20:59,742 - shared.models.model_manager - INFO - \u2139\ufe0f  GPU NOT AVAILABLE - Running on CPU
2025-11-29 08:20:59,742 - shared.models.model_manager - INFO -    AI models will be slower (10-60 seconds per receipt)
2025-11-29 08:20:59,742 - shared.models.model_manager - INFO -    OCR engines (EasyOCR, Tesseract, PaddleOCR) still work fine on CPU
2025-11-29 08:20:59,748 - __main__ - INFO - Starting Receipt Extraction API...
2025-11-29 08:20:59,748 - __main__ - INFO - Available models: 5
 * Serving Flask app 'app'
 * Debug mode: off
2025-11-29 08:20:59,866 - werkzeug - INFO - [31m[1mWARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.[0m
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://161.9.124.229:5000
2025-11-29 08:20:59,866 - werkzeug - INFO - [33mPress CTRL+C to quit[0m
2025-11-29 08:21:06,320 - werkzeug - INFO - 127.0.0.1 - - [29/Nov/2025 08:21:06] "GET /api/models HTTP/1.1" 200 -
2025-11-29 08:21:07,084 - werkzeug - INFO - 127.0.0.1 - - [29/Nov/2025 08:21:07] "GET /api/models HTTP/1.1" 200 -
2025-11-29 08:21:12,204 - shared.models.model_manager - INFO - Loading processor for ocr_tesseract (type: ocr)
2025-11-29 08:21:18,583 - shared.models.ocr_processor - INFO - Searching Tesseract...
2025-11-29 08:21:18,586 - shared.models.ocr_processor - INFO - Tesseract: C:\Program Files\Tesseract-OCR\tesseract.exe
2025-11-29 08:21:19,462 - shared.models.ocr_processor - INFO - Tesseract v5.5.0.20241111
2025-11-29 08:21:19,462 - shared.models.model_manager - INFO - \u2713 Loaded and cached processor for ocr_tesseract
2025-11-29 08:21:19,462 - __main__ - INFO - Processing image with model: None
2025-11-29 08:21:19,462 - utils.image_processing - INFO - Loading image from: C:\Users\User\AppData\Local\Temp\tmplq3eoxdn.jpg (size: 246647 bytes)
2025-11-29 08:21:19,725 - utils.image_processing - INFO - Loaded image successfully: 737x745
2025-11-29 08:21:19,735 - utils.image_processing - INFO - Image array shape: (745, 737, 3)
2025-11-29 08:21:19,742 - utils.image_processing - INFO - Upscaled image from 737x745 to 1483x1500
2025-11-29 08:21:19,916 - utils.image_processing - INFO - Skew angle 0.00� is negligible, skipping correction
2025-11-29 08:21:20,988 - utils.image_processing - INFO - Aggressive OCR preprocessing complete
2025-11-29 08:21:23,021 - shared.models.ocr_processor - INFO - OCR complete: PSM 4, len=529
2025-11-29 08:21:34,286 - werkzeug - INFO - 127.0.0.1 - - [29/Nov/2025 08:21:34] "POST /api/extract HTTP/1.1" 200 -
```

### Frontend Log (Last 50 lines)
```
::1 - - [29/Nov/2025 08:20:57] "GET / HTTP/1.1" 200 -
::1 - - [29/Nov/2025 08:20:57] "GET /css/styles.css HTTP/1.1" 200 -
::1 - - [29/Nov/2025 08:20:57] "GET /js/app.js HTTP/1.1" 200 -
::1 - - [29/Nov/2025 08:20:57] code 404, message File not found
::1 - - [29/Nov/2025 08:20:57] "GET /favicon.ico HTTP/1.1" 404 -
::1 - - [29/Nov/2025 08:21:06] "GET / HTTP/1.1" 304 -
::1 - - [29/Nov/2025 08:21:06] "GET / HTTP/1.1" 304 -
Serving HTTP on :: port 3000 (http://[::]:3000/) ...

Keyboard interrupt received, exiting.
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
  "default_model": "ocr_tesseract",
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
./run_all_tests.py
./run_donut_tests.py
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
./tests/backend/test_app.py
./tests/backend/__init__.py
./tests/conftest.py
./tests/shared/test_base_processor.py
./tests/shared/test_donut_processor.py
./tests/shared/test_easyocr_processor.py
./tests/shared/test_image_processing.py
./tests/shared/test_model_manager.py
./tests/shared/test_paddle_processor.py
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
