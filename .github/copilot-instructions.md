# GitHub Copilot Instructions - Receipt Extractor

> **Last Updated:** 2025-12-08  
> **Version:** 2.1.0  
> **Purpose:** Comprehensive guide for GitHub Copilot to understand project architecture, conventions, and integration patterns

---

## 📋 Table of Contents

1. [Project Overview](#-project-overview)
2. [Project Structure](#-project-structure)
3. [Circular Exchange Framework (CEFR) - OPTIONAL](#-circular-exchange-framework-cefr---optional)
4. [Testing Requirements](#-testing-requirements)
5. [AI Model Guidelines](#-ai-model-guidelines)
6. [Security & Authentication](#-security--authentication)
7. [Billing & Subscriptions](#-billing--subscriptions)
8. [Telemetry & Analytics](#-telemetry--analytics)
9. [Development Workflow](#-development-workflow)
10. [API Design Principles](#-api-design-principles)
11. [Cloud Integrations](#-cloud-integrations)
12. [Key Documentation Files](#-key-documentation-files)
13. [Common Pitfalls to Avoid](#-common-pitfalls-to-avoid)
14. [Code Generation Guidelines](#-code-generation-guidelines-for-github-copilot)

---

## 🎯 Project Overview

### Technology Stack

**Receipt Extractor** is an enterprise-grade SaaS platform for AI-powered receipt text extraction with Web and Desktop applications.

| Component | Technology | Version |
|-----------|-----------|---------|
| **Backend** | Flask (Python) | 3.0+ |
| **Frontend** | Vanilla JavaScript | ES6+ |
| **Desktop** | Electron | 27.0+ |
| **Database** | PostgreSQL / SQLite | 13+ / 3.x |
| **AI/ML** | PyTorch, HuggingFace Transformers | Latest |
| **Authentication** | JWT with Refresh Tokens | - |
| **Payments** | Stripe | Latest |
| **Telemetry** | OpenTelemetry | 1.22+ |
| **Framework** | Circular Exchange Framework (CEFR) | Custom |

### Language Composition

```
Python:     148 files (Core backend, AI models, CEFR framework)
JavaScript: 43 files  (Frontend, Electron, utilities)
HTML:       17 files  (Web UI, documentation)
CSS:        5 files   (Styling)
```

### Core Objectives

1. **Text Detection Excellence**: Support 7 OCR/AI algorithms with unified output schema
2. **Framework Integration**: Modules MAY optionally integrate with CEFR for auto-tuning (disabled by default)
3. **Production Quality**: ~1055 tests with strict synchronization requirements
4. **Scalable SaaS**: Multi-tier subscriptions, usage tracking, cloud integrations
5. **Developer Experience**: Clear patterns, comprehensive docs, easy onboarding

### Success Metrics

- ✅ Test Coverage: 70%+ on new code, 80%+ on critical modules
- 🟡 CEFR Integration: Optional (ENABLE_CEFR=false by default)
- ✅ Test Synchronization: 0 skipped tests for missing functions
- ✅ API Response Time: <500ms for extraction endpoints
- ✅ Model Accuracy: 90%+ on standard receipt datasets

---

## 📁 Project Structure

```
Web-and-Desktop-Apps/
├── .github/                    # GitHub configuration
│   ├── workflows/              # CI/CD pipelines (testing, deployment)
│   └── copilot-instructions.md # This file
│
├── shared/                     # Shared processing modules ⭐
│   ├── circular_exchange/      # 🔴 MANDATORY CEFR Framework
│   │   ├── core/               # Core components (registry, packages, config)
│   │   ├── analysis/           # Data collection, metrics, intelligence
│   │   ├── refactor/           # Auto-refactoring, feedback loops
│   │   └── persist/            # Persistence, webhooks
│   ├── config/                 # Global configuration
│   ├── models/                 # AI model processors (18 files)
│   │   ├── engine.py           # Main extraction engine
│   │   ├── manager.py          # Model lifecycle management
│   │   ├── schemas.py          # 🔴 Unified DetectionResult schema
│   │   ├── ocr.py              # Traditional OCR (Tesseract, EasyOCR, Paddle)
│   │   ├── craft_detector.py   # CRAFT text detection
│   │   ├── spatial_ocr.py      # Spatial multi-method ensemble
│   │   └── config.py           # Model configuration with CEFR
│   ├── services/               # Business logic services
│   └── utils/                  # Utilities (data, helpers, decorators, logging)
│
├── web/                        # Web application
│   ├── backend/                # Flask REST API
│   │   ├── app.py              # Main Flask application
│   │   ├── auth.py             # Authentication routes
│   │   ├── receipts.py         # Receipt management
│   │   ├── database.py         # SQLAlchemy models
│   │   ├── config.py           # Configuration management
│   │   ├── api/                # API endpoints (websocket, quick_extract)
│   │   ├── storage/            # Cloud storage (S3, GDrive, Dropbox)
│   │   ├── training/           # Cloud training (HF, Replicate, RunPod)
│   │   ├── billing/            # Stripe integration (plans, routes, middleware)
│   │   ├── security/           # Security (rate limiting, validation, headers)
│   │   ├── telemetry/          # OpenTelemetry & CEFR bridge
│   │   └── integrations/       # External APIs (HuggingFace, encryption)
│   └── frontend/               # Web UI
│       ├── index.html          # Main app
│       ├── enhanced-app.js     # Enhanced UI logic
│       ├── pricing.html        # Subscription pricing
│       ├── manifest.json       # PWA manifest
│       ├── service-worker.js   # PWA offline support
│       └── utils/              # Frontend utilities
│
├── desktop/                    # Electron desktop app
│   ├── main.js                 # Electron main process
│   ├── renderer.js             # Renderer process
│   └── index.html              # Desktop UI
│
├── tools/                      # Scripts, tests, benchmarks
│   ├── scripts/                # Utility scripts
│   ├── tests/                  # Test suites (~1055 tests)
│   │   ├── test_backend.py
│   │   ├── test_backend_routes.py
│   │   ├── test_shared_helpers.py
│   │   ├── test_billing.py
│   │   ├── test_integration.py
│   │   ├── shared/             # Shared module tests
│   │   ├── circular_exchange/  # CEFR framework tests
│   │   └── backend/            # Backend tests
│   ├── benchmarks/             # Model comparison suite
│   │   ├── compare_models.py
│   │   ├── data/               # Test datasets
│   │   └── results/            # Benchmark reports
│   └── data/                   # Test data
│
├── migrations/                 # Database migrations (Alembic)
├── docs/                       # Documentation
│   ├── API.md                  # API documentation
│   ├── USER_GUIDE.md           # User guide
│   ├── DEPLOYMENT.md           # Deployment guide
│   └── TESTING.md              # 🔴 Testing principles (CRITICAL)
│
├── examples/                   # Code examples
│   └── spatial_ocr_usage.py
│
├── logs/                       # Application logs
├── launcher.sh                 # 🔴 Unified launcher (REQUIRED for dev)
├── git-sync.py                 # 🔴 Git synchronization (ALWAYS use instead of git pull)
├── start.py                    # Application starter
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── README.md                   # Project overview
├── ROADMAP.md                  # Implementation roadmap
└── TESTING.md                  # Testing guidelines (symlink to docs/)
```

### Key Module Highlights

| Directory | Purpose | CEFR Required |
|-----------|---------|---------------|
| `shared/circular_exchange/` | Auto-tuning framework | N/A (Framework itself) |
| `shared/models/` | AI model processors | ✅ YES |
| `web/backend/` | REST API endpoints | ✅ YES |
| `web/backend/billing/` | Stripe integration | ✅ YES |
| `web/backend/telemetry/` | OpenTelemetry + CEFR bridge | ✅ YES |
| `tools/tests/` | Test suites | ⚠️ Tests use CEFR |

---

## 🟡 Circular Exchange Framework (CEFR) - OPTIONAL

### ℹ️ CEFR is EXPERIMENTAL and OPTIONAL

The Circular Exchange Framework (CEFR) is an **optional experimental** auto-tuning system that enables:
- Runtime parameter optimization
- Production metrics analysis
- Auto-refactoring suggestions
- Reactive configuration updates
- Dependency tracking

**CEFR is disabled by default** (`ENABLE_CEFR=false`). New modules MAY optionally integrate with CEFR if:
- The module has tunable parameters that would benefit from auto-optimization
- You are actively experimenting with runtime configuration
- Team is familiar with CEFR patterns

**For CEFR status and evaluation**: See `docs/architecture/CEFR_STATUS.md`

---

### Optional Integration Pattern (When Enabled)

#### Step 1: Import CEFR Components (Optional)

```python
"""
Your Module Description
"""
import logging

# 🟡 OPTIONAL: Import CEFR components (only if using CEFR)
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration, PackageRegistry
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    # CEFR not available or disabled - module works fine without it
    CIRCULAR_EXCHANGE_AVAILABLE = False

logger = logging.getLogger(__name__)
```

#### Step 2: Register Module (Optional)

```python
# 🟡 OPTIONAL: Register module with PROJECT_CONFIG (only if using CEFR)
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="your.module.name",           # Unique module ID
            file_path=__file__,                     # Current file path
            description="Brief module description",  # What does this module do?
            dependencies=["list", "of", "deps"],    # External dependencies
            exports=["ExportedClass", "function"]   # Public API
        ))
    except Exception as e:
        logger.debug(f"Module registration skipped: {e}")
```

#### Step 3: Use VariablePackage for Configuration (Optional)

```python
# 🟡 OPTIONAL: Use VariablePackage for tunable parameters (only if using CEFR)
if CIRCULAR_EXCHANGE_AVAILABLE:
    registry = PackageRegistry()
    
    # Create tunable configuration parameters
    confidence_threshold = registry.create_package(
        name='module.param.confidence_threshold',
        initial_value=0.7,
        source_module='your.module.name',
        description='Minimum confidence threshold for detection'
    ).get_value()
else:
    # Standard configuration when CEFR not available
    confidence_threshold = 0.7
```

---

### Complete CEFR Integration Example

**Example: OCR Configuration Module with CEFR**

```python
"""
OCR Configuration - Manages OCR engine settings
"""
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

# CEFR Integration
try:
    from shared.circular_exchange import (
        PROJECT_CONFIG, ModuleRegistration, 
        PackageRegistry, VariablePackage
    )
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

logger = logging.getLogger(__name__)

# Register module
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.models.ocr_config",
            file_path=__file__,
            description="OCR engine configuration with auto-tuning",
            dependencies=["easyocr", "pytesseract", "paddleocr"],
            exports=["OCRConfig", "get_ocr_config"]
        ))
    except Exception as e:
        logger.debug(f"Module registration skipped: {e}")


@dataclass
class OCRConfig:
    """OCR configuration with CEFR integration."""
    
    confidence_threshold: float = 0.7
    max_processing_time: int = 30
    enable_preprocessing: bool = True
    
    def __post_init__(self):
        """Initialize with CEFR tunable parameters."""
        if CIRCULAR_EXCHANGE_AVAILABLE:
            registry = PackageRegistry()
            
            # Register tunable parameters
            self.confidence_threshold = registry.create_package(
                name='ocr.confidence_threshold',
                initial_value=self.confidence_threshold,
                source_module='shared.models.ocr_config'
            ).get_value()
            
            self.max_processing_time = registry.create_package(
                name='ocr.max_processing_time',
                initial_value=self.max_processing_time,
                source_module='shared.models.ocr_config'
            ).get_value()


# Singleton instance
_ocr_config: Optional[OCRConfig] = None

def get_ocr_config() -> OCRConfig:
    """Get or create OCR configuration singleton."""
    global _ocr_config
    if _ocr_config is None:
        _ocr_config = OCRConfig()
    return _ocr_config
```

---

### CEFR Components Reference

| Component | Purpose | When to Use |
|-----------|---------|-------------|
| `PROJECT_CONFIG` | Global configuration singleton | Module registration |
| `ModuleRegistration` | Module metadata | Required for all modules |
| `VariablePackage` | Observable value containers | Tunable parameters |
| `PackageRegistry` | Package manager | Configuration management |
| `DataCollector` | Metrics collection | Production data gathering |
| `MetricsAnalyzer` | Pattern analysis | Performance optimization |
| `RefactoringEngine` | Code improvement | Auto-refactoring |
| `FeedbackLoop` | Auto-tuning | Parameter optimization |
| `AutoTuner` | Automatic tuning | Production optimization |
| `ProductionIntegration` | Telemetry bridge | Connect to OpenTelemetry |

---

### Benefits of CEFR Integration

✅ **Runtime Tuning**: Adjust parameters without code changes  
✅ **Auto-Optimization**: System learns from production metrics  
✅ **Reactive Updates**: Configuration changes propagate automatically  
✅ **Dependency Tracking**: Impact analysis for changes  
✅ **Analytics Integration**: Feed data to user analytics  
✅ **Refactoring Suggestions**: AI-powered code improvements  
✅ **A/B Testing**: Compare different configurations  
✅ **Rollback Support**: Automatic rollback on errors  

---

### Use Cases

1. **OCR Confidence Thresholds**: Auto-tune based on accuracy metrics
2. **Batch Processing Sizes**: Optimize for memory and speed
3. **Cache TTL Values**: Adjust based on hit rates
4. **Rate Limiting**: Dynamic adjustment based on load
5. **Model Selection**: Choose best model per receipt type
6. **Preprocessing Steps**: Enable/disable based on image quality

---

## 🧪 Testing Requirements

### Test Coverage Summary

**Total Tests: ~1,055**

| Category | Count | Description |
|----------|-------|-------------|
| Shared Utils Tests | ~170 | Core utilities (data, helpers, image, logging) |
| OCR Tests | ~191 | OCR processing and configuration |
| CEFR Framework Tests | ~322 | Circular Exchange Framework (core, refactor, analysis, persist) |
| Backend Tests | ~50 | Backend API routes |
| Integration Tests | ~28 | Cross-module integration |
| Billing/Security Tests | ~59 | Billing, routes, security |
| Model Tests | ~104 | Model management |
| Infrastructure Tests | ~51 | Infrastructure and setup |

Run `pytest --collect-only -q` for exact count.

---

### 🔴 CRITICAL Testing Principles

#### 1. NO Skip-for-Missing-Functions

❌ **NEVER DO THIS:**
```python
def test_some_function():
    try:
        from module import function_that_doesnt_exist
        # ...
    except ImportError:
        pytest.skip("function not available")  # ← WRONG!
```

✅ **DO THIS:**
```python
def test_some_function():
    from module import function_that_exists  # Import what EXISTS
    result = function_that_exists()
    assert result is not None
```

#### 2. Delete Tests When Functions Are Removed

When `my_function` is removed:
1. Find all tests: `grep -r "my_function" tools/tests/`
2. Delete or update those tests
3. Verify: `pytest tools/tests/ -v`

#### 3. Update Tests When Functions Are Renamed

When `old_function` → `new_function`:
```bash
grep -r "old_function" tools/tests/
sed -i 's/old_function/new_function/g' tools/tests/test_*.py
pytest tools/tests/ -v
```

#### 4. After Every Code Change Workflow

```bash
# 1. Run quick tests
pytest tools/tests/test_backend_routes.py tools/tests/test_shared_helpers.py -v

# 2. Check for skips (should be 0 for core tests)
pytest tools/tests/test_backend_routes.py -v 2>&1 | grep SKIPPED | wc -l

# 3. If tests fail due to missing functions
#    - STOP and fix the test
#    - Either update the import or delete the test
#    - Never leave broken tests

# 4. Add tests for new functions
# See examples below
```

---

### Test Organization

| File | Tests | Module Coverage |
|------|-------|-----------------|
| `test_backend.py` | Backend API | `web.backend.app` |
| `test_backend_routes.py` | JWT, Password, Billing | `web.backend.*` |
| `test_shared_helpers.py` | Utils | `shared.utils.*` |
| `test_coverage_boost.py` | Low-coverage modules | Various |
| `test_analysis.py` | CEFR analysis | `shared.circular_exchange.analysis.*` |
| `test_billing.py` | Stripe billing | `web.backend.billing.*` |
| `test_integration.py` | Integration | Cross-module |

---

### Test Principles

1. **No Skip-for-Missing-Functions**: Delete or update tests for removed functions
2. **Direct Imports Only**: Import actual module exports, not hypothetical ones
3. **Sync on Rename**: Update all tests when renaming functions
4. **Coverage-Driven**: Tests should improve coverage, not just exist
5. **Fast Execution**: Mock external APIs, use in-memory databases
6. **Isolated Tests**: Each test runs independently

---

### Running Tests

```bash
# Using launcher (recommended)
./launcher.sh test           # Full test suite
./launcher.sh test-quick     # Quick validation

# Direct pytest
pytest tools/tests/ -v                              # All tests
pytest tools/tests/ --cov=shared --cov=web/backend  # With coverage
pytest tools/tests/test_billing.py -v               # Specific file
```

---

## 🤖 AI Model Guidelines

### Supported Algorithms (7 Total)

| Algorithm | ID | Type | Speed | Best For |
|-----------|----|----|-------|----------|
| **Tesseract OCR** | `ocr_tesseract` | Traditional OCR | Very Fast | Clear, high-quality receipts |
| **EasyOCR** | `ocr_easyocr` | Deep Learning OCR | Fast | Multilingual, diverse fonts |
| **PaddleOCR** | `ocr_paddle` | Production OCR | Medium | Production, Asian languages |
| **Donut** | `donut_cord` | Transformer | Medium | AI-powered structured extraction |
| **Florence-2** | `florence2` | Vision-Language | Medium | Complex layouts, challenging |
| **CRAFT** | `craft_detector` | Text Detection | Fast | Text region localization |
| **Spatial Multi-Method** | `spatial` | Ensemble | Medium | Maximum accuracy, consensus |

---

### Model Implementation Pattern with CEFR

```python
"""
New Model Processor - Template
"""
import logging
from typing import Dict, Any, List
from dataclasses import dataclass

# CEFR Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration, PackageRegistry
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

# Import unified schema
from shared.models.schemas import DetectionResult, DetectedText, BoundingBox

logger = logging.getLogger(__name__)

# Register module
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.models.new_model",
            file_path=__file__,
            description="New model processor for text detection",
            dependencies=["torch", "transformers"],
            exports=["NewModelProcessor", "process_with_new_model"]
        ))
    except Exception as e:
        logger.debug(f"Module registration skipped: {e}")


class NewModelProcessor:
    """New model processor with CEFR integration."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize processor with CEFR-tunable parameters."""
        self.config = config or {}
        
        # Initialize tunable parameters
        if CIRCULAR_EXCHANGE_AVAILABLE:
            registry = PackageRegistry()
            self.confidence_threshold = registry.create_package(
                name='new_model.confidence_threshold',
                initial_value=0.7,
                source_module='shared.models.new_model'
            ).get_value()
        else:
            self.confidence_threshold = 0.7
    
    def process(self, image_path: str) -> DetectionResult:
        """
        Process image and return DetectionResult.
        
        Args:
            image_path: Path to receipt image
            
        Returns:
            DetectionResult with detected text and bounding boxes
        """
        try:
            # Model-specific processing
            raw_results = self._run_model(image_path)
            
            # Convert to unified schema
            texts = []
            for result in raw_results:
                texts.append(DetectedText(
                    text=result['text'],
                    confidence=result['confidence'],
                    bbox=BoundingBox(
                        x=result['x'],
                        y=result['y'],
                        width=result['width'],
                        height=result['height']
                    )
                ))
            
            return DetectionResult(
                texts=texts,
                metadata={'config': self.config},
                processing_time=0.0,  # Actual time
                model_id="new_model",
                success=True
            )
            
        except Exception as e:
            logger.error(f"Model processing failed: {e}")
            from shared.models.schemas import ErrorCode
            return DetectionResult(
                texts=[],
                metadata={},
                processing_time=0.0,
                model_id="new_model",
                success=False,
                error_code=ErrorCode.PROCESSING_FAILED,
                error_message=str(e)
            )
    
    def _run_model(self, image_path: str) -> List[Dict]:
        """Run model inference (implementation specific)."""
        # Model-specific code here
        pass
```

---

### Unified Output Schema (DetectionResult)

**ALL models MUST return DetectionResult** from `shared/models/schemas.py`:

```python
from shared.models.schemas import DetectionResult, DetectedText, BoundingBox

# Example usage
result = DetectionResult(
    texts=[
        DetectedText(
            text="Total: $42.99",
            confidence=0.95,
            bbox=BoundingBox(x=100, y=200, width=150, height=30)
        )
    ],
    metadata={'engine': 'tesseract', 'version': '5.0'},
    processing_time=0.45,
    model_id="ocr_tesseract",
    success=True
)

# Convert to dict for API response
response = result.to_dict()
```

**Schema Fields:**
- `texts`: List[DetectedText] - Detected text regions (required)
- `metadata`: Dict[str, Any] - Additional information (required)
- `processing_time`: float - Processing duration in seconds (required)
- `model_id`: str - Model identifier (required)
- `success`: bool - Whether processing succeeded (default: True)
- `error_code`: Optional[ErrorCode] - Error code enum if failed
- `error_message`: Optional[str] - Error description

---

## 🔐 Security & Authentication

### JWT Authentication Pattern

```python
from web.backend.auth import create_access_token, create_refresh_token, verify_token
from functools import wraps
from flask import request, jsonify, g

def require_auth(f):
    """Decorator to require JWT authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        try:
            payload = verify_token(token)
            g.user_id = payload['user_id']
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Invalid token'}), 401
    
    return decorated_function

# Usage in routes
@app.route('/api/receipts')
@require_auth
def get_receipts():
    user_id = g.user_id
    # ...
```

### Security Checklist

- ✅ All sensitive endpoints require JWT authentication
- ✅ Passwords hashed with bcrypt (12 rounds minimum)
- ✅ JWT secrets minimum 32 characters
- ✅ Refresh tokens stored in database with expiration
- ✅ Rate limiting on authentication endpoints
- ✅ Input validation on all endpoints
- ✅ SQL injection prevention (use SQLAlchemy ORM)
- ✅ XSS prevention (escape user input)
- ✅ CORS configured for production domain only
- ✅ HTTPS enforced in production
- ✅ Security headers (CSP, X-Frame-Options, HSTS)

---

## 💳 Billing & Subscriptions

### Subscription Plans

| Plan | Price/Month | Receipts | Storage | Features |
|------|------------|----------|---------|----------|
| **Free** | $0 | 10 | 0.1 GB | Basic OCR, Community support |
| **Pro** | $19 | 500 | 5 GB | All models, API access, Email support |
| **Business** | $49 | 2,000 | 20 GB | Priority support, Custom models |
| **Enterprise** | Custom | Unlimited | 100 GB | Dedicated support, On-premise |

### Stripe Integration Pattern

```python
from web.backend.billing.stripe_handler import StripeHandler
from web.backend.billing.plans import SUBSCRIPTION_PLANS
from web.backend.billing.middleware import require_subscription, check_usage_limits

# Create checkout session
@app.route('/api/billing/create-checkout', methods=['POST'])
@require_auth
def create_checkout():
    data = request.json
    plan = data.get('plan')
    
    if plan not in SUBSCRIPTION_PLANS:
        return jsonify({'error': 'Invalid plan'}), 400
    
    user = get_user(g.user_id)
    price_id = SUBSCRIPTION_PLANS[plan]['price_id']
    
    session = StripeHandler.create_checkout_session(
        customer_id=user.stripe_customer_id,
        price_id=price_id,
        success_url=f"{request.host_url}pricing?success=true",
        cancel_url=f"{request.host_url}pricing?canceled=true"
    )
    
    return jsonify({'checkout_url': session.url})

# Enforce subscription requirements
@app.route('/api/extract', methods=['POST'])
@require_auth
@require_subscription(min_plan='pro')  # Requires Pro or higher
def extract_receipt():
    check_usage_limits()  # Check monthly limits
    # ... extraction logic
```

### Webhook Handling

```python
@app.route('/api/billing/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = StripeHandler.construct_webhook_event(payload, sig_header)
        
        # Handle different event types
        if event.type == 'customer.subscription.created':
            # Update user subscription in database
            pass
        elif event.type == 'customer.subscription.updated':
            # Update subscription status
            pass
        elif event.type == 'customer.subscription.deleted':
            # Downgrade to free plan
            pass
        
        return jsonify({'received': True})
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 400
```

---

## 📊 Telemetry & Analytics

### OpenTelemetry Integration

```python
from web.backend.telemetry.otel_config import setup_telemetry
from web.backend.telemetry.custom_metrics import (
    receipt_extractions, extraction_duration, extraction_errors
)

# Initialize in app.py
app = Flask(__name__)
setup_telemetry(app)

# Track metrics in routes
@app.route('/api/extract', methods=['POST'])
def extract():
    start_time = time.time()
    model_id = request.json.get('model_id')
    
    try:
        result = process_receipt(image, model_id)
        
        # Track success metrics
        receipt_extractions.add(1, {"model": model_id, "success": "true"})
        extraction_duration.record(time.time() - start_time, {"model": model_id})
        
        return jsonify(result.to_dict())
    except Exception as e:
        # Track errors
        extraction_errors.add(1, {"error_type": type(e).__name__})
        raise
```

### CEFR Telemetry Bridge

```python
from web.backend.telemetry.cefr_bridge import CEFRBridge

# Initialize bridge
cefr_bridge = CEFRBridge()

# Report extraction to CEFR
cefr_bridge.report_extraction(
    extraction_id=receipt.id,
    model_id=model_id,
    success=True,
    processing_time=0.45,
    confidence=0.92,
    items_count=15,
    user_id=user.id
)

# CEFR uses this data for:
# - Auto-tuning model parameters
# - Identifying underperforming models
# - Suggesting retraining
# - Optimizing preprocessing steps
```

---

## 🛠️ Development Workflow

### Quick Start Commands

```bash
# Using unified launcher (RECOMMENDED)
./launcher.sh              # Interactive menu
./launcher.sh test         # Run full test suite
./launcher.sh dev          # Start development servers
./launcher.sh benchmark    # Run model benchmarks
./launcher.sh report       # Generate test report with CEFR analysis

# Manual start
pip install -r requirements.txt
cd web/backend && python app.py     # Backend: http://localhost:5000
cd web/frontend && python -m http.server 3000  # Frontend: http://localhost:3000
```

### Git Workflow - ALWAYS Use git-sync.py

⚠️ **CRITICAL: Never use `git pull` directly**

```bash
# Sync with remote (RECOMMENDED)
python git-sync.py

# Discard auto-generated files and pull
python git-sync.py --discard

# Just show what would happen
python git-sync.py --status
```

**Why?** The project has auto-generated files (like `version.json`) that can cause merge conflicts. `git-sync.py` handles these automatically.

### Code Quality Standards

```python
# MANDATORY for all Python files:
# 1. Module docstring
"""
Module Name - Brief Description

Longer description of module purpose and usage.
"""

# 2. CEFR integration (see CEFR section above)
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

# 3. Type hints
def process_image(image_path: str, model_id: str) -> DetectionResult:
    """Process image with specified model."""
    pass

# 4. Error handling
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    raise

# 5. Logging
import logging
logger = logging.getLogger(__name__)
logger.info("Processing started")
```

---

## 🌐 API Design Principles

### RESTful Endpoint Patterns

```python
# Collection endpoints
GET    /api/receipts           # List receipts
POST   /api/receipts           # Create receipt

# Individual resource
GET    /api/receipts/<id>      # Get receipt
PATCH  /api/receipts/<id>      # Update receipt
DELETE /api/receipts/<id>      # Delete receipt

# Sub-resources
GET    /api/receipts/<id>/items       # Get receipt items
POST   /api/receipts/<id>/export      # Export receipt

# Actions (use POST)
POST   /api/receipts/<id>/reprocess   # Reprocess receipt
POST   /api/auth/refresh               # Refresh token
```

### Response Format Standards

**Success Response:**
```json
{
  "success": true,
  "data": {
    "id": "receipt_123",
    "items": [...]
  },
  "metadata": {
    "processing_time": 0.45,
    "model": "ocr_tesseract"
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": {
    "code": "invalid_image",
    "message": "Image format not supported",
    "details": {
      "supported_formats": ["jpg", "png", "pdf"]
    }
  }
}
```

**Pagination:**
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "pages": 8
  }
}
```

---

## ☁️ Cloud Integrations

### Storage Providers

| Provider | Module | Features |
|----------|--------|----------|
| **AWS S3** | `web/backend/storage/s3_handler.py` | Presigned URLs, lifecycle policies |
| **Google Drive** | `web/backend/storage/gdrive_handler.py` | OAuth 2.0, folder sync |
| **Dropbox** | `web/backend/storage/dropbox_handler.py` | Temporary links, retry logic |

```python
from web.backend.storage import StorageFactory

# Get storage handler
storage = StorageFactory.get_storage(provider='s3')

# Upload file
url = storage.upload_file(file_path, bucket='receipts', key='user123/receipt.jpg')

# Generate temporary download link (15 min expiry)
download_url = storage.generate_presigned_url(key='user123/receipt.jpg', expires=900)
```

### Training Providers

| Provider | Module | Best For | Cost |
|----------|--------|----------|------|
| **HuggingFace** | `web/backend/training/hf_trainer.py` | Donut, LayoutLM | ~$0.60/hr |
| **Replicate** | `web/backend/training/replicate_trainer.py` | Quick training | ~$0.80/hr |
| **RunPod** | `web/backend/training/runpod_trainer.py` | Custom GPU | ~$0.50-$2/hr |

```python
from web.backend.training import TrainingFactory

# Create training job
trainer = TrainingFactory.get_trainer(provider='huggingface', model_id='donut')
job = trainer.start_training(
    dataset_path='/path/to/dataset',
    config={'epochs': 10, 'learning_rate': 5e-5}
)

# Monitor progress
status = trainer.get_status(job.id)
logs = trainer.get_logs(job.id)

# Download trained model
model_url = trainer.download_model(job.id)
```

### Payment Processing

| Service | Module | Purpose |
|---------|--------|---------|
| **Stripe** | `web/backend/billing/stripe_handler.py` | Subscriptions, payments |

---

## 📚 Key Documentation Files

| File | Purpose | When to Read |
|------|---------|--------------|
| `README.md` | Project overview, quick start | First time setup |
| `ROADMAP.md` | Implementation phases, external integrations | Planning features |
| `docs/TESTING.md` | Testing principles, critical rules | Before writing tests |
| `docs/API.md` | API documentation, endpoints | Backend development |
| `docs/USER_GUIDE.md` | User guide, features | Understanding user workflows |
| `docs/DEPLOYMENT.md` | Deployment guides | Production deployment |
| `.env.example` | Environment variables | Configuration setup |
| `shared/circular_exchange/__init__.py` | CEFR components | Framework integration |
| `shared/models/schemas.py` | Unified output schema | Model development |
| `web/backend/telemetry/cefr_bridge.py` | CEFR telemetry integration | Analytics setup |

---

## ⚠️ Common Pitfalls to Avoid

### 1. ❌ Forgetting CEFR Integration
```python
# WRONG - No CEFR registration
class NewProcessor:
    def process(self, data):
        pass

# RIGHT - With CEFR registration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    PROJECT_CONFIG.register_module(ModuleRegistration(
        module_id="module.new_processor",
        file_path=__file__,
        exports=["NewProcessor"]
    ))
except ImportError:
    pass

class NewProcessor:
    def process(self, data):
        pass
```

### 2. ❌ Not Using Unified Schema
```python
# WRONG - Custom return format
def extract_text(image):
    return {'text': 'Total: $42.99', 'confidence': 0.95}

# RIGHT - Using DetectionResult
from shared.models.schemas import DetectionResult, DetectedText, BoundingBox

def extract_text(image) -> DetectionResult:
    return DetectionResult(
        texts=[DetectedText(
            text='Total: $42.99',
            confidence=0.95,
            bbox=BoundingBox(x=0, y=0, width=100, height=20)
        )],
        metadata={},
        processing_time=0.1,
        model_id="ocr_tesseract",
        success=True
    )
```

### 3. ❌ Using git pull Instead of git-sync.py
```bash
# WRONG
git pull

# RIGHT
python git-sync.py
```

### 4. ❌ Skipping Tests for Missing Functions
```python
# WRONG
def test_removed_function():
    pytest.skip("Function was removed")  # DELETE THIS TEST INSTEAD

# RIGHT - Just delete the test entirely
```

### 5. ❌ Hardcoding Configuration Values
```python
# WRONG
CONFIDENCE_THRESHOLD = 0.7  # Hardcoded

# RIGHT - Use CEFR VariablePackage
from shared.circular_exchange import PackageRegistry

registry = PackageRegistry()
CONFIDENCE_THRESHOLD = registry.create_package(
    name='module.confidence_threshold',
    initial_value=0.7
).get_value()
```

### 6. ❌ Missing Type Hints
```python
# WRONG
def process(data):
    return result

# RIGHT
def process(data: Dict[str, Any]) -> DetectionResult:
    return result
```

### 7. ❌ Poor Error Handling
```python
# WRONG
try:
    result = risky_operation()
except:
    pass

# RIGHT
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    return DetectionResult(
        success=False,
        error_code="processing_failed",
        error_message=str(e)
    )
```

### 8. ❌ Not Checking Authentication
```python
# WRONG - No auth check
@app.route('/api/receipts')
def get_receipts():
    pass

# RIGHT - With auth
@app.route('/api/receipts')
@require_auth
def get_receipts():
    user_id = g.user_id
    pass
```

### 9. ❌ Missing Logging
```python
# WRONG - Silent failures
def process():
    data = load_data()

# RIGHT - With logging
import logging
logger = logging.getLogger(__name__)

def process():
    logger.info("Starting data processing")
    data = load_data()
    logger.info(f"Loaded {len(data)} records")
```

### 10. ❌ Not Using launcher.sh for Testing
```bash
# WRONG - Manual pytest commands
cd tools/tests && pytest -v

# RIGHT - Use launcher
./launcher.sh test
./launcher.sh test-quick
```

---

## 💡 Code Generation Guidelines for GitHub Copilot

### When Generating New Modules

1. **Start with CEFR Integration Template**
   ```python
   """Module description"""
   import logging
   
   try:
       from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
       CIRCULAR_EXCHANGE_AVAILABLE = True
   except ImportError:
       CIRCULAR_EXCHANGE_AVAILABLE = False
   
   logger = logging.getLogger(__name__)
   
   if CIRCULAR_EXCHANGE_AVAILABLE:
       PROJECT_CONFIG.register_module(ModuleRegistration(
           module_id="module.name",
           file_path=__file__,
           exports=[...]
       ))
   ```

2. **Use Type Hints Throughout**
   ```python
   from typing import Dict, List, Optional, Any
   
   def function(param: str, config: Dict[str, Any]) -> Optional[DetectionResult]:
       pass
   ```

3. **Import Unified Schema for Model Code**
   ```python
   from shared.models.schemas import DetectionResult, DetectedText, BoundingBox
   ```

4. **Add Comprehensive Docstrings**
   ```python
   def process_image(image_path: str, model_id: str) -> DetectionResult:
       """
       Process receipt image with specified model.
       
       Args:
           image_path: Path to receipt image file
           model_id: Model identifier (e.g., 'ocr_tesseract')
           
       Returns:
           DetectionResult with detected text and metadata
           
       Raises:
           ValueError: If image_path doesn't exist
           ProcessingError: If model processing fails
       """
       pass
   ```

5. **Include Error Handling**
   ```python
   try:
       result = process()
       return DetectionResult(
           texts=result.texts,
           metadata=result.metadata,
           processing_time=result.processing_time,
           model_id=result.model_id,
           success=True
       )
   except Exception as e:
       logger.error(f"Processing failed: {e}")
       from shared.models.schemas import ErrorCode
       return DetectionResult(
           texts=[],
           metadata={},
           processing_time=0.0,
           model_id="unknown",
           success=False,
           error_code=ErrorCode.PROCESSING_FAILED,
           error_message=str(e)
       )
   ```

### When Modifying Existing Code

1. **Check for CEFR Integration**
   - Verify module is registered
   - Use existing VariablePackages for parameters
   - Don't break CEFR patterns

2. **Update Tests Immediately**
   - Add tests for new functions
   - Update tests for modified functions
   - Delete tests for removed functions
   - Run `pytest` to verify

3. **Maintain Type Consistency**
   - Keep existing type hints
   - Add type hints if missing
   - Use `DetectionResult` for model outputs

4. **Preserve Authentication**
   - Keep `@require_auth` decorators
   - Don't remove security checks
   - Maintain usage limit enforcement

### When Suggesting Refactoring

1. **Check CEFR Dependency Graph**
   ```python
   from shared.circular_exchange import PROJECT_CONFIG
   
   # Get module dependencies
   dependencies = PROJECT_CONFIG.get_module_dependencies("module.name")
   ```

2. **Use CEFR RefactoringEngine**
   ```python
   from shared.circular_exchange import REFACTORING_ENGINE
   
   suggestions = REFACTORING_ENGINE.analyze_code(file_path)
   plan = REFACTORING_ENGINE.create_refactoring_plan(suggestions)
   ```

3. **Follow Existing Patterns**
   - Match coding style in the file
   - Use existing utility functions
   - Don't introduce new dependencies unnecessarily

4. **Update Documentation**
   - Update docstrings
   - Update README if adding major features
   - Update API.md for new endpoints

### Code Review Checklist

Before suggesting code, verify:

- ✅ CEFR integration included
- ✅ Type hints present
- ✅ Unified schema used (DetectionResult)
- ✅ Error handling included
- ✅ Logging statements added
- ✅ Authentication required for protected endpoints
- ✅ Tests written/updated
- ✅ Docstrings comprehensive
- ✅ No hardcoded configuration
- ✅ Follows existing patterns

---

## 🎯 Priority Guidelines

When GitHub Copilot generates code, prioritize in this order:

1. **CEFR Integration** - Absolute requirement
2. **Security** - Authentication, validation, rate limiting
3. **Type Safety** - Type hints, schema validation
4. **Error Handling** - Graceful failures, logging
5. **Testing** - Test coverage, synchronization
6. **Documentation** - Docstrings, comments
7. **Performance** - Optimization, caching
8. **Style** - Consistency, readability

---

## 📝 Quick Reference

### Essential Imports

```python
# CEFR
from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration, PackageRegistry

# Schemas
from shared.models.schemas import DetectionResult, DetectedText, BoundingBox

# Authentication
from web.backend.auth import require_auth, create_access_token

# Billing
from web.backend.billing.middleware import require_subscription, check_usage_limits

# Telemetry
from web.backend.telemetry.custom_metrics import receipt_extractions, extraction_duration
```

### Common Patterns

```python
# Module Registration
PROJECT_CONFIG.register_module(ModuleRegistration(
    module_id="module.name",
    file_path=__file__,
    exports=["ClassName"]
))

# Tunable Parameter
registry = PackageRegistry()
threshold = registry.create_package(
    name='module.threshold',
    initial_value=0.7
).get_value()

# Protected Route
@app.route('/api/endpoint')
@require_auth
@require_subscription(min_plan='pro')
def protected_endpoint():
    user_id = g.user_id
    check_usage_limits()
    # ...

# Return DetectionResult
return DetectionResult(
    texts=[...],
    metadata={},
    processing_time=0.45,
    model_id="model_name",
    success=True
)
```

---

## 🔄 Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | 2025-12-07 | Initial comprehensive guide |

---

## 📞 Support

- **GitHub Issues**: Report bugs and request features
- **Documentation**: See `docs/` directory for detailed guides
- **Testing**: See `docs/TESTING.md` for testing principles
- **CEFR**: See `shared/circular_exchange/__init__.py` for framework details

---

**Remember**: This is a living document. Update it when:
- Adding new mandatory patterns
- Changing CEFR integration requirements
- Adding new testing principles
- Introducing new frameworks or tools
- Discovering common pitfalls

---

*Generated for GitHub Copilot to understand Receipt Extractor project conventions*  
*Last Updated: 2025-12-07 | Version: 2.0.0*
