# Repository Analysis Report

**Generated:** 2025-12-08 07:11:51

## 📊 Summary

- **Total Files Analyzed:** 197
- **Python Files:** 154
- **JavaScript Files:** 43
- **Total Functions:** 2967
- **Total Classes:** 613

## ⚠️ Issues Found

- **Missing Implementations:** 173
- **Orphaned Imports:** 241
- **Files Without Tests:** 80
- **Missing Files:** 85
- **Potentially Unused Functions:** 2706
- **Documentation Mismatches:** 14

## 🔴 Missing Implementations

Functions or classes that are imported but not defined in the expected module.

- **File:** `web/backend/auth.py`
  - **Import:** `from routes import auth_bp`
  - **Missing:** `auth_bp` from module `routes`

- **File:** `web/backend/errors.py`
  - **Import:** `from shared.utils.errors import ERROR_METADATA`
  - **Missing:** `ERROR_METADATA` from module `shared.utils.errors`

- **File:** `web/backend/api/websocket.py`
  - **Import:** `from flask_socketio import SocketIO`
  - **Missing:** `SocketIO` from module `flask_socketio`

- **File:** `web/backend/api/websocket.py`
  - **Import:** `from flask_socketio import emit`
  - **Missing:** `emit` from module `flask_socketio`

- **File:** `web/backend/api/websocket.py`
  - **Import:** `from flask_socketio import join_room`
  - **Missing:** `join_room` from module `flask_socketio`

- **File:** `web/backend/api/websocket.py`
  - **Import:** `from flask_socketio import leave_room`
  - **Missing:** `leave_room` from module `flask_socketio`

- **File:** `web/backend/api/websocket.py`
  - **Import:** `from flask_socketio import disconnect`
  - **Missing:** `disconnect` from module `flask_socketio`

- **File:** `web/backend/api/__init__.py`
  - **Import:** `from quick_extract import quick_extract_bp`
  - **Missing:** `quick_extract_bp` from module `quick_extract`

- **File:** `web/backend/billing/middleware.py`
  - **Import:** `from plans import SUBSCRIPTION_PLANS`
  - **Missing:** `SUBSCRIPTION_PLANS` from module `plans`

- **File:** `web/backend/billing/middleware.py`
  - **Import:** `from plans import PLAN_HIERARCHY`
  - **Missing:** `PLAN_HIERARCHY` from module `plans`

- **File:** `web/backend/billing/__init__.py`
  - **Import:** `from plans import SUBSCRIPTION_PLANS`
  - **Missing:** `SUBSCRIPTION_PLANS` from module `plans`

- **File:** `web/backend/billing/__init__.py`
  - **Import:** `from routes import billing_bp`
  - **Missing:** `billing_bp` from module `routes`

- **File:** `web/backend/billing/routes.py`
  - **Import:** `from plans import SUBSCRIPTION_PLANS`
  - **Missing:** `SUBSCRIPTION_PLANS` from module `plans`

- **File:** `web/backend/billing/routes.py`
  - **Import:** `from stripe_handler import STRIPE_AVAILABLE`
  - **Missing:** `STRIPE_AVAILABLE` from module `stripe_handler`

- **File:** `web/backend/storage/gdrive_handler.py`
  - **Import:** `from io import BytesIO`
  - **Missing:** `BytesIO` from module `io`

- **File:** `web/backend/storage/s3_handler.py`
  - **Import:** `from io import BytesIO`
  - **Missing:** `BytesIO` from module `io`

- **File:** `web/backend/storage/dropbox_handler.py`
  - **Import:** `from io import BytesIO`
  - **Missing:** `BytesIO` from module `io`

- **File:** `migrations/versions/002_cloud_storage_fields.py`
  - **Import:** `from alembic import op`
  - **Missing:** `op` from module `alembic`

- **File:** `migrations/versions/001_initial_schema.py`
  - **Import:** `from alembic import op`
  - **Missing:** `op` from module `alembic`

- **File:** `tools/scripts/check_dependencies.py`
  - **Import:** `from __future__ import annotations`
  - **Missing:** `annotations` from module `__future__`

- **File:** `tools/tests/pytest_custom_output.py`
  - **Import:** `from _pytest.terminal import TerminalReporter`
  - **Missing:** `TerminalReporter` from module `_pytest.terminal`

- **File:** `tools/tests/test_shared_helpers.py`
  - **Import:** `from decimal import Decimal`
  - **Missing:** `Decimal` from module `decimal`

- **File:** `tools/tests/test_validation.py`
  - **Import:** `from shared.utils.validation import MAX_FILE_SIZES`
  - **Missing:** `MAX_FILE_SIZES` from module `shared.utils.validation`

- **File:** `tools/tests/test_plan_enhancements.py`
  - **Import:** `from decimal import Decimal`
  - **Missing:** `Decimal` from module `decimal`

- **File:** `tools/tests/integration/test_receipt_workflow.py`
  - **Import:** `from decimal import Decimal`
  - **Missing:** `Decimal` from module `decimal`

- **File:** `tools/tests/circular_exchange/test_persist.py`
  - **Import:** `from shared.circular_exchange.persist.persistence import PERSISTENCE_LAYER`
  - **Missing:** `PERSISTENCE_LAYER` from module `shared.circular_exchange.persist.persistence`

- **File:** `tools/tests/circular_exchange/test_persist.py`
  - **Import:** `from shared.circular_exchange.analysis.data_collector import TestResult`
  - **Missing:** `TestResult` from module `shared.circular_exchange.analysis.data_collector`

- **File:** `tools/tests/circular_exchange/test_persist.py`
  - **Import:** `from shared.circular_exchange.analysis.data_collector import TestStatus`
  - **Missing:** `TestStatus` from module `shared.circular_exchange.analysis.data_collector`

- **File:** `tools/tests/circular_exchange/test_persist.py`
  - **Import:** `from shared.circular_exchange.persist.webhook_notifier import WEBHOOK_NOTIFIER`
  - **Missing:** `WEBHOOK_NOTIFIER` from module `shared.circular_exchange.persist.webhook_notifier`

- **File:** `tools/tests/circular_exchange/test_analysis.py`
  - **Import:** `from shared.circular_exchange.analysis.intelligent_analyzer import INTELLIGENT_ANALYZER`
  - **Missing:** `INTELLIGENT_ANALYZER` from module `shared.circular_exchange.analysis.intelligent_analyzer`

- **File:** `tools/tests/circular_exchange/test_core.py`
  - **Import:** `from shared.circular_exchange.core.project_config import PROJECT_CONFIG`
  - **Missing:** `PROJECT_CONFIG` from module `shared.circular_exchange.core.project_config`

- **File:** `tools/tests/shared/test_ocr.py`
  - **Import:** `from decimal import Decimal`
  - **Missing:** `Decimal` from module `decimal`

- **File:** `tools/tests/shared/test_ocr.py`
  - **Import:** `from decimal import Decimal`
  - **Missing:** `Decimal` from module `decimal`

- **File:** `tools/tests/shared/test_models.py`
  - **Import:** `from decimal import Decimal`
  - **Missing:** `Decimal` from module `decimal`

- **File:** `tools/tests/shared/test_models.py`
  - **Import:** `from decimal import Decimal`
  - **Missing:** `Decimal` from module `decimal`

- **File:** `tools/tests/shared/test_models.py`
  - **Import:** `from decimal import Decimal`
  - **Missing:** `Decimal` from module `decimal`

- **File:** `tools/tests/shared/test_models.py`
  - **Import:** `from decimal import Decimal`
  - **Missing:** `Decimal` from module `decimal`

- **File:** `tools/tests/shared/test_spatial_ocr.py`
  - **Import:** `from decimal import Decimal`
  - **Missing:** `Decimal` from module `decimal`

- **File:** `tools/tests/shared/test_utils.py`
  - **Import:** `from decimal import Decimal`
  - **Missing:** `Decimal` from module `decimal`

- **File:** `tools/tests/shared/test_utils.py`
  - **Import:** `from shared.utils.image import BRIGHTNESS_THRESHOLD`
  - **Missing:** `BRIGHTNESS_THRESHOLD` from module `shared.utils.image`

- **File:** `tools/tests/shared/test_utils.py`
  - **Import:** `from shared.utils.image import CONTRAST_THRESHOLD`
  - **Missing:** `CONTRAST_THRESHOLD` from module `shared.utils.image`

- **File:** `tools/tests/shared/test_utils.py`
  - **Import:** `from decimal import Decimal`
  - **Missing:** `Decimal` from module `decimal`

- **File:** `shared/models/semantic_validation.py`
  - **Import:** `from decimal import Decimal`
  - **Missing:** `Decimal` from module `decimal`

- **File:** `shared/models/semantic_validation.py`
  - **Import:** `from decimal import InvalidOperation`
  - **Missing:** `InvalidOperation` from module `decimal`

- **File:** `shared/models/spatial_ocr.py`
  - **Import:** `from decimal import Decimal`
  - **Missing:** `Decimal` from module `decimal`

- **File:** `shared/models/receipt_prompts.py`
  - **Import:** `from decimal import Decimal`
  - **Missing:** `Decimal` from module `decimal`

- **File:** `shared/models/receipt_prompts.py`
  - **Import:** `from decimal import InvalidOperation`
  - **Missing:** `InvalidOperation` from module `decimal`

- **File:** `shared/models/ocr_common.py`
  - **Import:** `from ocr import SKIP_KEYWORDS`
  - **Missing:** `SKIP_KEYWORDS` from module `ocr`

- **File:** `shared/models/ocr_common.py`
  - **Import:** `from ocr import PRICE_MIN`
  - **Missing:** `PRICE_MIN` from module `ocr`

- **File:** `shared/models/ocr_common.py`
  - **Import:** `from ocr import PRICE_MAX`
  - **Missing:** `PRICE_MAX` from module `ocr`

*...and 123 more*

## 🗑️ Orphaned Imports

Imports that appear to be unused in their files.

- **File:** `examples/spatial_ocr_usage.py`
  - **Unused:** `BoundingBox` from `shared.models.spatial_ocr`

- **File:** `examples/spatial_ocr_usage.py`
  - **Unused:** `TextRegion` from `shared.models.spatial_ocr`

- **File:** `web/cache-bust.py`
  - **Unused:** `os` from ``

- **File:** `tools/validate_production_config.py`
  - **Unused:** `re` from ``

- **File:** `tools/validate_production_config.py`
  - **Unused:** `Tuple` from `typing`

- **File:** `shared/setup.py`
  - **Unused:** `os` from ``

- **File:** `shared/__init__.py`
  - **Unused:** `TYPE_CHECKING` from `typing`

- **File:** `web/backend/database.py`
  - **Unused:** `Optional` from `typing`

- **File:** `web/backend/decorators.py`
  - **Unused:** `timedelta` from `datetime`

- **File:** `web/backend/decorators.py`
  - **Unused:** `hashlib` from ``

- **File:** `web/backend/config.py`
  - **Unused:** `field` from `dataclasses`

- **File:** `web/backend/app.py`
  - **Unused:** `DataAugmenter` from `shared.models.engine`

- **File:** `web/backend/routes.py`
  - **Unused:** `g` from `flask`

- **File:** `web/backend/routes.py`
  - **Unused:** `wraps` from `functools`

- **File:** `web/backend/api/websocket.py`
  - **Unused:** `json` from ``

- **File:** `web/backend/training/hf_trainer.py`
  - **Unused:** `time` from ``

- **File:** `web/backend/training/hf_trainer.py`
  - **Unused:** `TrainingError` from `base`

- **File:** `web/backend/training/runpod_trainer.py`
  - **Unused:** `os` from ``

- **File:** `web/backend/training/runpod_trainer.py`
  - **Unused:** `time` from ``

- **File:** `web/backend/training/runpod_trainer.py`
  - **Unused:** `json` from ``

- **File:** `web/backend/training/runpod_trainer.py`
  - **Unused:** `TrainingError` from `base`

- **File:** `web/backend/training/replicate_trainer.py`
  - **Unused:** `json` from ``

- **File:** `web/backend/training/replicate_trainer.py`
  - **Unused:** `TrainingError` from `base`

- **File:** `web/backend/training/base.py`
  - **Unused:** `os` from ``

- **File:** `web/backend/billing/middleware.py`
  - **Unused:** `SUBSCRIPTION_PLANS` from `plans`

- **File:** `web/backend/billing/routes.py`
  - **Unused:** `os` from ``

- **File:** `web/backend/storage/gdrive_handler.py`
  - **Unused:** `os` from ``

- **File:** `web/backend/storage/s3_handler.py`
  - **Unused:** `os` from ``

- **File:** `web/backend/storage/s3_handler.py`
  - **Unused:** `StorageError` from `base`

- **File:** `web/backend/storage/s3_handler.py`
  - **Unused:** `UploadError` from `base`

- **File:** `web/backend/storage/s3_handler.py`
  - **Unused:** `DownloadError` from `base`

- **File:** `web/backend/storage/s3_handler.py`
  - **Unused:** `DeleteError` from `base`

- **File:** `web/backend/storage/dropbox_handler.py`
  - **Unused:** `BytesIO` from `io`

- **File:** `web/backend/storage/base.py`
  - **Unused:** `os` from ``

- **File:** `web/backend/telemetry/analytics.py`
  - **Unused:** `time` from ``

- **File:** `web/backend/telemetry/analytics.py`
  - **Unused:** `field` from `dataclasses`

- **File:** `web/backend/telemetry/custom_metrics.py`
  - **Unused:** `Optional` from `typing`

- **File:** `web/backend/telemetry/logging_config.py`
  - **Unused:** `Optional` from `typing`

- **File:** `web/backend/security/validation_schemas.py`
  - **Unused:** `Type` from `typing`

- **File:** `migrations/versions/001_initial_schema.py`
  - **Unused:** `postgresql` from `sqlalchemy.dialects`

- **File:** `tools/benchmarks/compare_models.py`
  - **Unused:** `ModelType` from `shared.models.manager`

- **File:** `tools/benchmarks/compare_models.py`
  - **Unused:** `load_and_validate_image` from `shared.utils.image`

- **File:** `tools/scripts/check_dependencies.py`
  - **Unused:** `annotations` from `__future__`

- **File:** `tools/scripts/process_images_cefr.py`
  - **Unused:** `os` from ``

- **File:** `tools/scripts/process_images_cefr.py`
  - **Unused:** `Optional` from `typing`

- **File:** `tools/scripts/batch_receipt_processor.py`
  - **Unused:** `os` from ``

- **File:** `tools/scripts/batch_receipt_processor.py`
  - **Unused:** `Optional` from `typing`

- **File:** `tools/scripts/run_cefr_full.py`
  - **Unused:** `os` from ``

- **File:** `tools/scripts/run_cefr_full.py`
  - **Unused:** `json` from ``

- **File:** `tools/scripts/run_cefr_full.py`
  - **Unused:** `tempfile` from ``

*...and 191 more*

## 🧪 Files Without Tests

Python files with functions/classes that lack corresponding test files.

- **File:** `start.py`
  - Functions: 15, Classes: 1

- **File:** `git-sync.py`
  - Functions: 14, Classes: 1

- **File:** `examples/spatial_ocr_usage.py`
  - Functions: 2, Classes: 0

- **File:** `web/cache-bust.py`
  - Functions: 6, Classes: 0

- **File:** `tools/validate_production_config.py`
  - Functions: 12, Classes: 2

- **File:** `shared/setup.py`
  - Functions: 3, Classes: 0

- **File:** `web/backend/database.py`
  - Functions: 32, Classes: 13

- **File:** `web/backend/jwt_handler.py`
  - Functions: 6, Classes: 0

- **File:** `web/backend/decorators.py`
  - Functions: 7, Classes: 0

- **File:** `web/backend/password.py`
  - Functions: 3, Classes: 0

- **File:** `web/backend/config.py`
  - Functions: 13, Classes: 1

- **File:** `web/backend/app.py`
  - Functions: 30, Classes: 0

- **File:** `web/backend/errors.py`
  - Functions: 3, Classes: 1

- **File:** `web/backend/api/websocket.py`
  - Functions: 7, Classes: 0

- **File:** `web/backend/api/quick_extract.py`
  - Functions: 2, Classes: 0

- **File:** `web/backend/training/hf_trainer.py`
  - Functions: 9, Classes: 1

- **File:** `web/backend/training/runpod_trainer.py`
  - Functions: 10, Classes: 1

- **File:** `web/backend/training/celery_worker.py`
  - Functions: 5, Classes: 1

- **File:** `web/backend/training/replicate_trainer.py`
  - Functions: 10, Classes: 1

- **File:** `web/backend/training/base.py`
  - Functions: 23, Classes: 10

- **File:** `web/backend/billing/plans.py`
  - Functions: 8, Classes: 0

- **File:** `web/backend/billing/middleware.py`
  - Functions: 7, Classes: 1

- **File:** `web/backend/billing/stripe_handler.py`
  - Functions: 14, Classes: 1

- **File:** `web/backend/storage/gdrive_handler.py`
  - Functions: 12, Classes: 1

- **File:** `web/backend/storage/s3_handler.py`
  - Functions: 12, Classes: 1

- **File:** `web/backend/storage/dropbox_handler.py`
  - Functions: 13, Classes: 1

- **File:** `web/backend/storage/base.py`
  - Functions: 13, Classes: 8

- **File:** `web/backend/telemetry/otel_config.py`
  - Functions: 4, Classes: 0

- **File:** `web/backend/telemetry/analytics.py`
  - Functions: 16, Classes: 2

- **File:** `web/backend/telemetry/custom_metrics.py`
  - Functions: 8, Classes: 1

- **File:** `web/backend/telemetry/logging_config.py`
  - Functions: 11, Classes: 4

- **File:** `web/backend/telemetry/cefr_bridge.py`
  - Functions: 11, Classes: 1

- **File:** `web/backend/security/headers.py`
  - Functions: 7, Classes: 1

- **File:** `web/backend/security/validation_schemas.py`
  - Functions: 13, Classes: 1

- **File:** `web/backend/integrations/encryption.py`
  - Functions: 11, Classes: 1

- **File:** `web/backend/integrations/huggingface_api.py`
  - Functions: 11, Classes: 3

- **File:** `tools/benchmarks/compare_models.py`
  - Functions: 10, Classes: 4

- **File:** `tools/scripts/check_dependencies.py`
  - Functions: 6, Classes: 0

- **File:** `tools/scripts/process_images_cefr.py`
  - Functions: 6, Classes: 0

- **File:** `tools/scripts/batch_receipt_processor.py`
  - Functions: 6, Classes: 0

- **File:** `tools/scripts/run_automated_cef_pipeline.py`
  - Functions: 15, Classes: 5

- **File:** `tools/scripts/run_cefr_full.py`
  - Functions: 12, Classes: 0

- **File:** `tools/scripts/repo_screener.py`
  - Functions: 17, Classes: 3

- **File:** `shared/models/semantic_validation.py`
  - Functions: 19, Classes: 5

- **File:** `shared/models/ocr_finetuner.py`
  - Functions: 8, Classes: 2

- **File:** `shared/models/receipt_prompts.py`
  - Functions: 7, Classes: 2

- **File:** `shared/models/adaptive_preprocessing.py`
  - Functions: 21, Classes: 4

- **File:** `shared/models/florence_finetuner.py`
  - Functions: 9, Classes: 2

- **File:** `shared/models/manager.py`
  - Functions: 30, Classes: 8

- **File:** `shared/models/ocr_processor.py`
  - Functions: 8, Classes: 1

*...and 30 more*

## 📁 Missing Files

Files that are imported but don't exist in the repository.

- **Module:** `password`
  - **Referenced in:** `web/backend/auth.py`
  - **Expected at:** `password/__init__.py`, `password.py`

- **Module:** `jwt_handler`
  - **Referenced in:** `web/backend/auth.py`
  - **Expected at:** `jwt_handler/__init__.py`, `jwt_handler.py`

- **Module:** `decorators`
  - **Referenced in:** `web/backend/auth.py`
  - **Expected at:** `decorators/__init__.py`, `decorators.py`

- **Module:** `routes`
  - **Referenced in:** `web/backend/auth.py`
  - **Expected at:** `routes/__init__.py`, `routes.py`

- **Module:** `sqlalchemy`
  - **Referenced in:** `web/backend/database.py`
  - **Expected at:** `sqlalchemy/__init__.py`, `sqlalchemy.py`

- **Module:** `sqlalchemy.orm`
  - **Referenced in:** `web/backend/database.py`
  - **Expected at:** `sqlalchemy/orm/__init__.py`, `sqlalchemy/orm.py`

- **Module:** `sqlalchemy.pool`
  - **Referenced in:** `web/backend/database.py`
  - **Expected at:** `sqlalchemy/pool/__init__.py`, `sqlalchemy/pool.py`

- **Module:** `contextlib`
  - **Referenced in:** `web/backend/database.py`
  - **Expected at:** `contextlib/__init__.py`, `contextlib.py`

- **Module:** `sqlalchemy.types`
  - **Referenced in:** `web/backend/database.py`
  - **Expected at:** `sqlalchemy/types/__init__.py`, `sqlalchemy/types.py`

- **Module:** `functools`
  - **Referenced in:** `web/backend/decorators.py`
  - **Expected at:** `functools/__init__.py`, `functools.py`

- **Module:** `flask_cors`
  - **Referenced in:** `web/backend/app.py`
  - **Expected at:** `flask_cors/__init__.py`, `flask_cors.py`

- **Module:** `werkzeug.utils`
  - **Referenced in:** `web/backend/app.py`
  - **Expected at:** `werkzeug/utils/__init__.py`, `werkzeug/utils.py`

- **Module:** `flask_socketio`
  - **Referenced in:** `web/backend/api/websocket.py`
  - **Expected at:** `flask_socketio/__init__.py`, `flask_socketio.py`

- **Module:** `quick_extract`
  - **Referenced in:** `web/backend/api/__init__.py`
  - **Expected at:** `quick_extract/__init__.py`, `quick_extract.py`

- **Module:** `base`
  - **Referenced in:** `web/backend/training/hf_trainer.py`
  - **Expected at:** `base/__init__.py`, `base.py`

- **Module:** `hf_trainer`
  - **Referenced in:** `web/backend/training/__init__.py`
  - **Expected at:** `hf_trainer/__init__.py`, `hf_trainer.py`

- **Module:** `replicate_trainer`
  - **Referenced in:** `web/backend/training/__init__.py`
  - **Expected at:** `replicate_trainer/__init__.py`, `replicate_trainer.py`

- **Module:** `runpod_trainer`
  - **Referenced in:** `web/backend/training/__init__.py`
  - **Expected at:** `runpod_trainer/__init__.py`, `runpod_trainer.py`

- **Module:** `abc`
  - **Referenced in:** `web/backend/training/base.py`
  - **Expected at:** `abc/__init__.py`, `abc.py`

- **Module:** `enum`
  - **Referenced in:** `web/backend/training/base.py`
  - **Expected at:** `enum/__init__.py`, `enum.py`

- **Module:** `plans`
  - **Referenced in:** `web/backend/billing/middleware.py`
  - **Expected at:** `plans/__init__.py`, `plans.py`

- **Module:** `stripe_handler`
  - **Referenced in:** `web/backend/billing/__init__.py`
  - **Expected at:** `stripe_handler/__init__.py`, `stripe_handler.py`

- **Module:** `middleware`
  - **Referenced in:** `web/backend/billing/__init__.py`
  - **Expected at:** `middleware/__init__.py`, `middleware.py`

- **Module:** `io`
  - **Referenced in:** `web/backend/storage/gdrive_handler.py`
  - **Expected at:** `io/__init__.py`, `io.py`

- **Module:** `s3_handler`
  - **Referenced in:** `web/backend/storage/__init__.py`
  - **Expected at:** `s3_handler/__init__.py`, `s3_handler.py`

- **Module:** `gdrive_handler`
  - **Referenced in:** `web/backend/storage/__init__.py`
  - **Expected at:** `gdrive_handler/__init__.py`, `gdrive_handler.py`

- **Module:** `dropbox_handler`
  - **Referenced in:** `web/backend/storage/__init__.py`
  - **Expected at:** `dropbox_handler/__init__.py`, `dropbox_handler.py`

- **Module:** `otel_config`
  - **Referenced in:** `web/backend/telemetry/custom_metrics.py`
  - **Expected at:** `otel_config/__init__.py`, `otel_config.py`

- **Module:** `custom_metrics`
  - **Referenced in:** `web/backend/telemetry/__init__.py`
  - **Expected at:** `custom_metrics/__init__.py`, `custom_metrics.py`

- **Module:** `analytics`
  - **Referenced in:** `web/backend/telemetry/__init__.py`
  - **Expected at:** `analytics/__init__.py`, `analytics.py`

- **Module:** `logging_config`
  - **Referenced in:** `web/backend/telemetry/__init__.py`
  - **Expected at:** `logging_config/__init__.py`, `logging_config.py`

- **Module:** `cefr_bridge`
  - **Referenced in:** `web/backend/telemetry/__init__.py`
  - **Expected at:** `cefr_bridge/__init__.py`, `cefr_bridge.py`

- **Module:** `rate_limiting`
  - **Referenced in:** `web/backend/security/__init__.py`
  - **Expected at:** `rate_limiting/__init__.py`, `rate_limiting.py`

- **Module:** `validation_schemas`
  - **Referenced in:** `web/backend/security/__init__.py`
  - **Expected at:** `validation_schemas/__init__.py`, `validation_schemas.py`

- **Module:** `headers`
  - **Referenced in:** `web/backend/security/__init__.py`
  - **Expected at:** `headers/__init__.py`, `headers.py`

- **Module:** `huggingface_api`
  - **Referenced in:** `web/backend/integrations/__init__.py`
  - **Expected at:** `huggingface_api/__init__.py`, `huggingface_api.py`

- **Module:** `encryption`
  - **Referenced in:** `web/backend/integrations/__init__.py`
  - **Expected at:** `encryption/__init__.py`, `encryption.py`

- **Module:** `alembic`
  - **Referenced in:** `migrations/versions/002_cloud_storage_fields.py`
  - **Expected at:** `alembic/__init__.py`, `alembic.py`

- **Module:** `sqlalchemy.dialects`
  - **Referenced in:** `migrations/versions/001_initial_schema.py`
  - **Expected at:** `sqlalchemy/dialects/__init__.py`, `sqlalchemy/dialects.py`

- **Module:** `__future__`
  - **Referenced in:** `tools/scripts/check_dependencies.py`
  - **Expected at:** `__future__/__init__.py`, `__future__.py`

- **Module:** `_pytest.terminal`
  - **Referenced in:** `tools/tests/pytest_custom_output.py`
  - **Expected at:** `_pytest/terminal/__init__.py`, `_pytest/terminal.py`

- **Module:** `decimal`
  - **Referenced in:** `tools/tests/test_shared_helpers.py`
  - **Expected at:** `decimal/__init__.py`, `decimal.py`

- **Module:** `engine`
  - **Referenced in:** `shared/models/processors.py`
  - **Expected at:** `engine/__init__.py`, `engine.py`

- **Module:** `ocr`
  - **Referenced in:** `shared/models/ocr_common.py`
  - **Expected at:** `ocr/__init__.py`, `ocr.py`

- **Module:** `concurrent.futures`
  - **Referenced in:** `shared/models/manager.py`
  - **Expected at:** `concurrent/futures/__init__.py`, `concurrent/futures.py`

- **Module:** `ocr_common`
  - **Referenced in:** `shared/models/ocr_processor.py`
  - **Expected at:** `ocr_common/__init__.py`, `ocr_common.py`

- **Module:** `data`
  - **Referenced in:** `shared/utils/__init__.py`
  - **Expected at:** `data/__init__.py`, `data.py`

- **Module:** `image`
  - **Referenced in:** `shared/utils/__init__.py`
  - **Expected at:** `image/__init__.py`, `image.py`

- **Module:** `helpers`
  - **Referenced in:** `shared/utils/__init__.py`
  - **Expected at:** `helpers/__init__.py`, `helpers.py`

- **Module:** `queue`
  - **Referenced in:** `shared/utils/progress.py`
  - **Expected at:** `queue/__init__.py`, `queue.py`

*...and 35 more*

## 🔧 Potentially Unused Functions

Functions that appear to be defined but never called (heuristic analysis).

- **File:** `start.py`
  - **Function:** `print_banner`

- **File:** `start.py`
  - **Function:** `print_step`

- **File:** `start.py`
  - **Function:** `print_success`

- **File:** `start.py`
  - **Function:** `print_error`

- **File:** `start.py`
  - **Function:** `print_warning`

- **File:** `start.py`
  - **Function:** `get_python_executable`

- **File:** `start.py`
  - **Function:** `get_pip_executable`

- **File:** `start.py`
  - **Function:** `create_venv`

- **File:** `start.py`
  - **Function:** `install_dependencies`

- **File:** `start.py`
  - **Function:** `run_cache_bust`

- **File:** `start.py`
  - **Function:** `clean_pycache`

- **File:** `start.py`
  - **Function:** `start_backend`

- **File:** `start.py`
  - **Function:** `start_frontend`

- **File:** `start.py`
  - **Function:** `open_browser`

- **File:** `git-sync.py`
  - **Function:** `print_banner`

- **File:** `git-sync.py`
  - **Function:** `print_step`

- **File:** `git-sync.py`
  - **Function:** `print_success`

- **File:** `git-sync.py`
  - **Function:** `print_error`

- **File:** `git-sync.py`
  - **Function:** `print_warning`

- **File:** `git-sync.py`
  - **Function:** `run_git`

- **File:** `git-sync.py`
  - **Function:** `get_modified_files`

- **File:** `git-sync.py`
  - **Function:** `categorize_changes`

- **File:** `git-sync.py`
  - **Function:** `show_status`

- **File:** `git-sync.py`
  - **Function:** `discard_auto_generated`

- **File:** `git-sync.py`
  - **Function:** `stash_changes`

- **File:** `git-sync.py`
  - **Function:** `pull_latest`

- **File:** `git-sync.py`
  - **Function:** `run_cache_bust`

- **File:** `examples/spatial_ocr_usage.py`
  - **Function:** `example_basic_usage`

- **File:** `examples/spatial_ocr_usage.py`
  - **Function:** `example_via_model_manager`

- **File:** `web/cache-bust.py`
  - **Function:** `calculate_file_hash`

- **File:** `web/cache-bust.py`
  - **Function:** `calculate_version_hash`

- **File:** `web/cache-bust.py`
  - **Function:** `get_current_version`

- **File:** `web/cache-bust.py`
  - **Function:** `update_version_file`

- **File:** `web/cache-bust.py`
  - **Function:** `check_status`

- **File:** `tools/validate_production_config.py`
  - **Function:** `ValidationError.__init__`

- **File:** `tools/validate_production_config.py`
  - **Function:** `ProductionValidator.__init__`

- **File:** `tools/validate_production_config.py`
  - **Function:** `ProductionValidator.load_env`

- **File:** `tools/validate_production_config.py`
  - **Function:** `ProductionValidator.get_env`

- **File:** `tools/validate_production_config.py`
  - **Function:** `ProductionValidator.validate_jwt_secret`

- **File:** `tools/validate_production_config.py`
  - **Function:** `ProductionValidator.validate_flask_config`

- **File:** `tools/validate_production_config.py`
  - **Function:** `ProductionValidator.validate_database_config`

- **File:** `tools/validate_production_config.py`
  - **Function:** `ProductionValidator.validate_stripe_config`

- **File:** `tools/validate_production_config.py`
  - **Function:** `ProductionValidator.validate_https_config`

- **File:** `tools/validate_production_config.py`
  - **Function:** `ProductionValidator.validate_cors_config`

- **File:** `tools/validate_production_config.py`
  - **Function:** `ProductionValidator.validate_all`

- **File:** `desktop/process_receipt.py`
  - **Function:** `extract_receipt`

- **File:** `shared/setup.py`
  - **Function:** `check_package`

- **File:** `shared/setup.py`
  - **Function:** `install_package`

- **File:** `shared/setup.py`
  - **Function:** `check_and_install`

- **File:** `web/backend/database.py`
  - **Function:** `get_engine`

*...and 2656 more*

## 📝 Documentation Mismatches

References in documentation that don't match the actual code.

- **Type:** README reference
  - **Name:** `DB_POOL_SIZE`
  - **Issue:** Referenced in README but not found in code

- **Type:** README reference
  - **Name:** `craft_detector`
  - **Issue:** Referenced in README but not found in code

- **Type:** README reference
  - **Name:** `donut_sroie`
  - **Issue:** Referenced in README but not found in code

- **Type:** README reference
  - **Name:** `ocr_easyocr`
  - **Issue:** Referenced in README but not found in code

- **Type:** README reference
  - **Name:** `PROJECT_CONFIG`
  - **Issue:** Referenced in README but not found in code

- **Type:** README reference
  - **Name:** `DB_POOL_MAX_OVERFLOW`
  - **Issue:** Referenced in README but not found in code

- **Type:** README reference
  - **Name:** `spatial_multi`
  - **Issue:** Referenced in README but not found in code

- **Type:** README reference
  - **Name:** `JWT_SECRET`
  - **Issue:** Referenced in README but not found in code

- **Type:** README reference
  - **Name:** `ocr_paddle`
  - **Issue:** Referenced in README but not found in code

- **Type:** README reference
  - **Name:** `DATABASE_URL`
  - **Issue:** Referenced in README but not found in code

- **Type:** README reference
  - **Name:** `donut_cord`
  - **Issue:** Referenced in README but not found in code

- **Type:** README reference
  - **Name:** `ocr_paddleocr`
  - **Issue:** Referenced in README but not found in code

- **Type:** README reference
  - **Name:** `STRIPE_WEBHOOK_SECRET`
  - **Issue:** Referenced in README but not found in code

- **Type:** README reference
  - **Name:** `ocr_tesseract`
  - **Issue:** Referenced in README but not found in code

## 📄 File Analysis Details

### Files by Category

- **Backend Files:** 44
- **Frontend/Desktop Files:** 44
- **Shared Module Files:** 67
- **Test Files:** 37

### Top 20 Files by Line Count

| File | Lines | Functions | Classes | Has Tests |
|------|-------|-----------|---------|----------|
| `tools/tests/shared/test_models.py` | 2418 | 121 | 7 | ✅ |
| `tools/tests/shared/test_utils.py` | 2245 | 170 | 38 | ✅ |
| `tools/tests/shared/test_ocr.py` | 2178 | 241 | 52 | ✅ |
| `tools/tests/circular_exchange/test_core.py` | 2041 | 156 | 31 | ✅ |
| `shared/models/engine.py` | 1808 | 63 | 14 | ❌ |
| `shared/models/ocr.py` | 1647 | 30 | 0 | ✅ |
| `tools/tests/circular_exchange/test_refactor.py` | 1354 | 88 | 17 | ✅ |
| `shared/circular_exchange/analysis/intelligent_analyzer.py` | 1214 | 51 | 12 | ❌ |
| `tools/tests/circular_exchange/test_analysis.py` | 1200 | 66 | 12 | ✅ |
| `desktop/renderer.js` | 1161 | 37 | 0 | ❌ |
| `tools/tests/test_shared_helpers.py` | 1116 | 88 | 8 | ✅ |
| `web/frontend/js/utils.js` | 1101 | 3 | 0 | ✅ |
| `shared/models/spatial_ocr.py` | 1093 | 36 | 6 | ✅ |
| `web/backend/database.py` | 1043 | 32 | 13 | ❌ |
| `web/frontend/js/ui-components.js` | 1005 | 1 | 1 | ❌ |
| `shared/circular_exchange/refactor/autonomous_refactor.py` | 982 | 42 | 13 | ❌ |
| `web/backend/app.py` | 948 | 30 | 0 | ❌ |
| `web/frontend/components/unified-extractor-controls.js` | 946 | 0 | 1 | ❌ |
| `shared/circular_exchange/refactor/feedback_loop.py` | 943 | 38 | 9 | ❌ |
| `web/frontend/js/form-validation.js` | 931 | 0 | 4 | ❌ |


---

*This report was automatically generated by the Repository Screening Tool.*
