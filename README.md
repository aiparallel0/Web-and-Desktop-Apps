# Receipt Extractor - AI-Powered Text Detection

AI-powered receipt text extraction with **Web Application** and **Electron Desktop Application**.

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Project Overview](#project-overview)
- [External Integration Roadmap](#external-integration-roadmap)
- [Project Structure](#project-structure)
- [Available Models](#available-models)
- [API Reference](#api-reference)
- [Circular Exchange Framework](#circular-exchange-framework)
- [Installation](#installation)
- [Desktop Application](#desktop-application)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

**Using the Unified Launcher (Recommended):**
```bash
./launcher.sh          # Interactive menu
./launcher.sh test     # Run full test suite (~1055 tests)
./launcher.sh dev      # Start development servers
./launcher.sh help     # Show all options
```

**Quick Commands:**
```bash
./launcher.sh test-quick    # Quick tests (faster)
./launcher.sh report        # Generate comprehensive test report
./launcher.sh alternatives  # View deployment options (Docker, Cloud, etc.)
```

**Manual Start:**
```bash
pip install -r requirements.txt
cd web/backend && python app.py     # Backend: http://localhost:5000
cd web/frontend && python -m http.server 3000  # Frontend: http://localhost:3000
```

---

## 📖 Project Overview

Receipt Extractor is an enterprise-grade SaaS platform that uses multiple OCR engines and AI models to extract structured data from receipt images. The application supports:

- **Multi-Model OCR**: Tesseract, EasyOCR, PaddleOCR, Donut, Florence-2
- **Batch Processing**: Process multiple receipts simultaneously
- **Model Finetuning**: Local and cloud-based training capabilities
- **User Management**: Authentication, subscriptions, and usage tracking
- **RESTful API**: Complete backend API with authentication
- **Data Export**: JSON, CSV, TXT formats

**Technology Stack:**
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Backend**: Flask 3.0 (Python), RESTful API
- **Desktop**: Electron 27.0
- **Database**: PostgreSQL (production), SQLite (development)
- **AI/ML**: PyTorch, HuggingFace Transformers, EasyOCR
- **Authentication**: JWT tokens with refresh tokens
- **Framework**: Circular Exchange Framework (CEFR) for auto-tuning

---

## 🔗 External Integration Roadmap

For the comprehensive roadmap detailing planned integrations with external services (Stripe, cloud storage, cloud training, etc.), see **[ROADMAP.md](ROADMAP.md)**.

### Current Implementation Status

✅ **Implemented Features:**
- Multi-model OCR (Tesseract, EasyOCR, PaddleOCL, Donut, Florence-2)
- Local receipt processing and extraction
- Web application with Flask backend
- Electron desktop application
- RESTful API endpoints
- User authentication framework
- Database models (PostgreSQL/SQLite)
- Batch processing capabilities
- Export to JSON, CSV, TXT formats
- Circular Exchange Framework integration

🚧 **Planned Features (see ROADMAP.md):**
- Stripe payment processing
- Cloud storage integration (AWS S3, Google Drive, Dropbox)
- Cloud-based model training (HuggingFace, Replicate, RunPod)
- Advanced analytics and monitoring
- Production deployment guides

---
## 📁 Project Structure

```
├── shared/              # Shared processing modules (4 folders + 4 files)
│   ├── circular_exchange/  # Configuration framework
│   ├── config/             # Configuration files
│   ├── models/             # Model processors
│   └── utils/              # Utilities
├── web/                 # Web application
│   ├── backend/           # Flask API
│   │   ├── app.py         # Main application
│   │   ├── auth.py        # Authentication routes
│   │   ├── receipts.py    # Receipt management routes
│   │   ├── database.py    # Database models & connection
│   │   ├── config.py      # Configuration management (NEW)
│   │   ├── storage/       # Cloud storage integrations (NEW)
│   │   ├── training/      # Cloud training integrations (NEW)
│   │   ├── billing/       # Stripe payment integration (NEW)
│   │   ├── integrations/  # External APIs (NEW)
│   │   ├── telemetry/     # OpenTelemetry & analytics (NEW)
│   │   └── security/      # Security utilities (NEW)
│   └── frontend/          # Web UI
│       ├── index.html
│       ├── app.js
│       ├── styles.css
│       └── pricing.html   # Subscription pricing page (NEW)
├── desktop/             # Electron desktop app
│   ├── main.js
│   ├── renderer.js
│   └── index.html
├── tools/               # Scripts, tests, and test data
│   ├── scripts/           # Processing scripts
│   ├── tests/             # Test suites
│   └── data/              # Test data
├── migrations/          # Database migrations (NEW)
├── docs/                # Documentation (NEW)
│   ├── API.md
│   ├── USER_GUIDE.md
│   └── DEPLOYMENT.md
├── .env.example         # Environment variables template (NEW)
├── Procfile             # Process management for deployment (NEW)
├── railway.json         # Railway configuration (NEW)
├── Dockerfile           # Container configuration (optional) (NEW)
└── requirements.txt     # Python dependencies
```

---

## 🤖 Available Models

| Model | Type | Speed | Description |
|-------|------|-------|-------------|
| `donut_sroie` | Donut | Fast | Store, Date, Total |
| `donut_cord` | Donut | Medium | Full extraction |
| `florence2` | Florence | Medium | Advanced OCR |
| `ocr_tesseract` | OCR | Very Fast | Traditional OCR |
| `ocr_easyocr` | OCR | Fast | Deep learning OCR |
| `ocr_paddleocr` | OCR | Medium | Enterprise OCR |

**Cloud Models** (via HuggingFace API):
- Microsoft TrOCR
- LayoutLM variants
- Custom fine-tuned models

---

## 📡 API Reference

### Authentication Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Register new user |
| `/api/auth/login` | POST | Login and get tokens |
| `/api/auth/refresh` | POST | Refresh access token |
| `/api/auth/logout` | POST | Logout and revoke token |
| `/api/auth/me` | GET | Get current user info |

### Receipt Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/models` | GET | List available models |
| `/api/models/select` | POST | Select active model |
| `/api/extract` | POST | Extract data from receipt |
| `/api/receipts` | GET | List user's receipts |
| `/api/receipts/<id>` | GET | Get receipt details |
| `/api/receipts/<id>` | PATCH | Update receipt |
| `/api/receipts/<id>` | DELETE | Delete receipt |
| `/api/receipts/stats` | GET | Get usage statistics |

### Billing Endpoints (NEW)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/billing/create-checkout` | POST | Create Stripe checkout |
| `/api/billing/subscription` | GET | Get subscription details |
| `/api/billing/cancel` | POST | Cancel subscription |
| `/api/billing/usage` | GET | Get usage stats |
| `/api/billing/webhook` | POST | Stripe webhook handler |

### Cloud Storage Endpoints (NEW)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/cloud-storage/upload` | POST | Upload to cloud storage |
| `/api/cloud-storage/auth/<provider>` | GET | OAuth authorization |
| `/api/cloud-storage/disconnect` | POST | Revoke cloud access |
| `/api/cloud-storage/list` | GET | List cloud files |

### Training Endpoints (NEW)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/finetune` | POST | Start training job |
| `/api/finetune/status/<job_id>` | GET | Get training status |
| `/api/finetune/logs/<job_id>` | GET | Stream training logs |
| `/api/finetune/download/<job_id>` | GET | Download trained model |

---

## 🔄 Circular Exchange Framework

**ALL code MUST integrate with the Circular Exchange Framework.**

The Circular Exchange Framework (CEFR) is a custom auto-tuning system that enables runtime parameter optimization based on production metrics and user feedback.

### Required Pattern

```python
# Step 1: Import
from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration, PackageRegistry
CIRCULAR_EXCHANGE_AVAILABLE = True

# Step 2: Register module
PROJECT_CONFIG.register_module(ModuleRegistration(
    module_id="your.module.name",
    file_path=__file__,
    dependencies=["list", "of", "deps"],
    exports=["ExportedClass"]
))

# Step 3: Use VariablePackage for configuration
registry = PackageRegistry()
registry.create_package(name='module.param', initial_value=0.5, source_module='module')
```

### Framework Components

| Component | Purpose |
|-----------|---------|
| `PROJECT_CONFIG` | Global configuration singleton |
| `VariablePackage` | Observable value containers |
| `PackageRegistry` | Registry for packages |
| `ModuleRegistration` | Module metadata tracking |
| `DataCollector` | Collect test results and metrics |
| `MetricsAnalyzer` | Analyze patterns and performance |
| `RefactoringEngine` | Generate improvement suggestions |
| `FeedbackLoop` | Auto-tune parameters based on metrics |

### Benefits
- Runtime parameter tuning without code changes
- Auto-tuning based on production metrics
- Reactive configuration updates across modules
- Dependency tracking and impact analysis
- Integration with user analytics (Phase 4)

---

## 🧪 Testing

### Test Coverage Summary

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
| **Total** | **~1055** | **All test functions** |

> **Note:** Test counts are dynamically calculated. Run `pytest --collect-only -q` for exact count.

### ⚠️ CRITICAL: Keeping Tests Up-to-Date

**Tests MUST be synchronized with code changes.** Outdated tests that skip or fail due to missing functions are useless.

#### After Each Code Change:

1. **Run tests immediately:**
   ```bash
   ./launcher.sh test-quick    # Quick validation
   ```

2. **Check for skipped tests:**
   ```bash
   pytest tools/tests/ -v 2>&1 | grep SKIPPED
   ```
   
3. **If tests skip due to missing functions:**
   - **DO NOT** use `pytest.skip()` for functions that don't exist
   - **DELETE** or **UPDATE** the test to match actual code
   - Tests should test what EXISTS, not what was planned

4. **Add new tests for new functions:**
   ```bash
   # Pattern: Test actual exports
   from module import actual_function  # NOT hypothetical_function
   def test_actual_function():
       result = actual_function()
       assert result is not None
   ```

#### Test File Organization:

| File | Tests | Status |
|------|-------|--------|
| `test_backend.py` | Backend API routes | ✅ Active |
| `test_backend_routes.py` | JWT, Password, Billing, Security | ✅ Active |
| `test_shared_helpers.py` | Utils (data, helpers, logging, decorators) | ✅ Active |
| `test_coverage_boost.py` | Low-coverage modules | ✅ Active |
| `test_analysis.py` | CEFR analysis modules | ✅ Active |
| `test_integration.py` | Integration tests | ⚠️ Requires external deps |
| `test_billing.py` | Stripe billing | ⚠️ Requires stripe package |

#### Test Principles:

1. **No Skip-for-Missing-Functions** - If a function doesn't exist, remove the test
2. **Direct Imports Only** - Import actual module exports, not hypothetical ones
3. **Sync on Rename** - When renaming functions, update all tests immediately
4. **Coverage-Driven** - Tests should improve coverage, not just exist

#### Verification Commands:
```bash
# Check zero skipped (critical tests)
pytest tools/tests/test_backend_routes.py -v | grep -c SKIPPED  # Should be 0

# Check zero failed
pytest tools/tests/test_shared_helpers.py -v | grep -c FAILED  # Should be 0

# Full coverage report
pytest tools/tests/ --cov=shared --cov=web/backend --cov-report=html
```

### Running Tests

**Using the Unified Launcher (Recommended):**
```bash
./launcher.sh test           # Run full test suite
./launcher.sh test-quick     # Quick tests (faster)
./launcher.sh report         # Generate comprehensive test report with CEFR analysis
```

**Direct pytest commands:**
```bash
# All tests
pytest tools/tests/ -v

# With coverage
pytest tools/tests/ --cov=shared --cov=web.backend --cov-report=html

# By category
pytest tools/tests/shared/          # Shared module tests
pytest tools/tests/circular_exchange/  # CEFR framework tests
pytest tools/tests/backend/         # Backend tests

# Specific test suites
pytest tools/tests/test_billing.py  # Stripe integration tests (requires stripe package)
pytest tools/tests/test_integration.py # Integration tests
```

**Test Coverage:** ~1055 tests covering shared modules, backend routes, CEFR framework, and AI agents

**CI/CD:** GitHub Actions runs tests automatically on push and creates CEF analysis artifacts.

---

## 💻 Installation

### Prerequisites
- Python 3.8+
- Node.js 16+ (desktop app)
- PostgreSQL 13+ (production)
- Redis (optional, for rate limiting and job queue)
- Tesseract OCR (optional)

### Setup

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd Web-and-Desktop-Apps
   ```

2. **Updating the Repository**
   
   > **Important:** Always use `git-sync.py` instead of `git pull` to avoid conflicts with auto-generated files:
   ```bash
   python git-sync.py              # Sync with remote (recommended)
   python git-sync.py --discard    # Discard auto-generated file changes and pull
   ```

3. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

5. **Initialize Database**
   ```bash
   # Create PostgreSQL database
   createdb receipt_extractor

   # Run migrations
   alembic upgrade head

   # Or use SQLite for development
   export USE_SQLITE=true
   ```

6. **Install Tesseract (Optional)**
   ```bash
   # Linux
   sudo apt-get install tesseract-ocr

   # macOS
   brew install tesseract

   # Windows
   # Download from: https://github.com/UB-Mannheim/tesseract/wiki
   ```

7. **Launch Application**
   ```bash
   ./launch.sh
   # Or manually:
   cd web/backend && python app.py
   ```

### GPU Support (Optional)

For faster AI model processing:

```bash
# CUDA 11.8
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Verify
python -c "import torch; print(torch.cuda.is_available())"
```

---

## 🖥️ Desktop Application

Build and run the Electron desktop app:

```bash
cd desktop
npm install
npm start           # Run in development mode
npm run build:win   # Build for Windows
npm run build:mac   # Build for macOS
npm run build:linux # Build for Linux
```

The desktop app provides:
- Native OS integration
- Offline processing (when models are downloaded)
- System tray integration
- Automatic updates (configure with electron-updater)

---

## 🛠️ Troubleshooting

### Git Pull Fails: "Your local changes would be overwritten by merge"

This error occurs when you have local changes to auto-generated files (like `version.json` or HTML files modified by old cache-bust scripts).

**Automatic Fix - Just run start.bat:**
```bash
# Windows: Double-click start.bat
# This automatically runs git-sync before starting the servers
```

**Quick Fix - Use git-sync.py:**
```bash
# From repository root:
python git-sync.py              # Stash changes and pull
python git-sync.py --discard    # Discard auto-generated files and pull
python git-sync.py --status     # Just show what would happen
```

**Manual Fix:**
```bash
# Option 1: Discard changes to specific files
git checkout -- web/frontend/index.html
git checkout -- web/frontend/version.json

# Option 2: Stash all local changes
git stash
git pull
git stash pop  # Restore your changes (may have conflicts)

# Option 3: Delete untracked auto-generated files
rm web/frontend/version.json
git pull
```

**Prevention:** The `version.json` file is now auto-generated and gitignored. HTML files are no longer modified by `cache-bust.py`. The `start.bat` script now automatically runs `git-sync.py` to handle these conflicts before starting.

### Common Issues

| Issue | Solution |
|-------|----------|
| Port in use | `lsof -i :5000` then `kill -9 <PID>` |
| Module not found | `pip install -r requirements.txt` |
| Out of memory | Reduce batch size, unload models, or upgrade server RAM |
| Slow first run | Normal - models download (~500MB total) |
| Database connection error | Check `DATABASE_URL` in .env, ensure PostgreSQL is running |
| Stripe webhook failing | Check webhook secret, ensure public endpoint with HTTPS |
| Cloud storage upload fails | Verify API credentials, check network connectivity |
| Training job stuck | Check cloud provider status, review training logs |

### Common Errors

**"Connection pool exhausted"**
- Increase `DB_POOL_SIZE` and `DB_POOL_MAX_OVERFLOW` in .env
- Check for database connection leaks

**"JWT signature verification failed"**
- Ensure `JWT_SECRET` is consistent across deployments
- Check token expiration settings

**"Stripe webhook signature verification failed"**
- Verify `STRIPE_WEBHOOK_SECRET` matches Stripe Dashboard
- Ensure raw request body is passed to webhook handler

### Test Failures

**OCR Config Test Isolation Issues**
- If tests involving OCR configuration fail unexpectedly, ensure proper config reset:
  ```python
  from shared.models.config import reset_ocr_config
  reset_ocr_config()
  
  import shared.models.ocr as ocr_module
  ocr_module._ocr_config = None
  ```
- The OCR config uses dual caching (singleton + module-level), both must be reset for test isolation

---

## 📚 Additional Resources

### Documentation
- [Flask Documentation](https://flask.palletsprojects.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Stripe API Reference](https://stripe.com/docs/api)
- [HuggingFace Hub Documentation](https://huggingface.co/docs/hub/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)

### Tutorials Referenced
- [Flask Stripe Subscriptions](https://testdriven.io/blog/flask-stripe-subscriptions/)
- [AWS S3 with Flask](https://stackabuse.com/file-management-with-aws-s3-python-and-flask/)
- [Google Drive API Python](https://www.merge.dev/blog/google-drive-api-python)
- [OpenTelemetry Flask Monitoring](https://signoz.io/blog/opentelemetry-flask/)
- [Railway Deployment Guide](https://docs.railway.app/guides/deployments)

### Community & Support
- GitHub Issues: [Report bugs and request features](https://github.com/your-repo/issues)
- Discussions: [Ask questions and share ideas](https://github.com/your-repo/discussions)
- Email: support@receiptextractor.com (configure after deployment)

---

## 📄 License

MIT License - See LICENSE.txt

---

## 🙏 Acknowledgments

Built with:
- **Flask** - Web framework
- **PyTorch** - Deep learning framework
- **HuggingFace Transformers** - Pre-trained models
- **EasyOCR** - OCR engine
- **PostgreSQL** - Database
- **Stripe** - Payment processing
- **OpenTelemetry** - Observability framework

**Special thanks** to the open-source community and all contributors.

---

*Last Updated: 2025-12-03*
*Version: 2.0.0*
