# Receipt Extractor - Setup Guide

Complete setup guide for Windows, macOS, and Linux.

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/Web-and-Desktop-Apps.git
cd Web-and-Desktop-Apps

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your settings

# 5. Run tests
pytest tools/tests -v

# 6. Start the application
python web/backend/app.py
```

---

## Detailed Setup

### Prerequisites

1. **Python 3.10 or higher**
   - Download from: https://www.python.org/downloads/
   - Verify: `python --version`

2. **PostgreSQL** (Optional - can use SQLite instead)
   - **Windows**: https://www.postgresql.org/download/windows/
   - **macOS**: `brew install postgresql@15`
   - **Linux**: `sudo apt-get install postgresql postgresql-contrib`
   - Verify: `psql --version`

3. **Tesseract OCR** (Optional - required only for Tesseract model)
   - **Windows**: https://github.com/UB-Mannheim/tesseract/wiki
   - **macOS**: `brew install tesseract`
   - **Linux**: `sudo apt-get install tesseract-ocr`
   - Verify: `tesseract --version`

4. **Node.js** (Optional - only for desktop app)
   - Download from: https://nodejs.org/ (LTS version)
   - Verify: `node --version`

### Step-by-Step Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Web-and-Desktop-Apps.git
cd Web-and-Desktop-Apps
```

#### 2. Create Virtual Environment

```bash
# Create venv
python -m venv venv

# Activate venv
# Windows (Command Prompt):
venv\Scripts\activate.bat

# Windows (PowerShell):
venv\Scripts\Activate.ps1

# Windows (Git Bash) / Linux / macOS:
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

**Optional Dependencies:**

```bash
# For AWS S3 storage
pip install boto3>=1.34.0

# For Google Drive storage
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

# For Dropbox storage
pip install dropbox>=11.36.0

# For PaddleOCR support
pip install paddlepaddle paddleocr

# For development
pip install -r requirements-dev.txt
```

#### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your favorite editor
```

**Important .env Settings:**

```bash
# Database (choose one)
DATABASE_URL=postgresql://user:password@localhost/receipt_extractor
# OR for development:
USE_SQLITE=true

# Flask
FLASK_SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Optional: Cloud Storage
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_S3_BUCKET=your-bucket-name
AWS_REGION=us-east-1

# Optional: Tesseract (if not in PATH)
TESSERACT_CMD=/path/to/tesseract

# Optional: Stripe (for billing)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
```

#### 5. Set Up Database

**Option A: PostgreSQL (Production)**

```bash
# Create database
createdb receipt_extractor

# Run migrations
alembic upgrade head
```

**Option B: SQLite (Development - Easier)**

```bash
# Just set in .env:
USE_SQLITE=true

# Run migrations
alembic upgrade head
```

The SQLite database file will be created at `./receipts.db`

#### 6. Run Tests

```bash
# Run all tests
pytest tools/tests -v

# Run with coverage
pytest tools/tests --cov=shared --cov=web/backend --cov-report=html

# Run specific test categories
pytest tools/tests -m unit
pytest tools/tests -m integration
pytest tools/tests -k "test_models"

# Skip slow tests
pytest tools/tests -m "not slow"
```

**View coverage report:**
```bash
# Coverage report is generated in htmlcov/
# Open in browser:
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

#### 7. Run the Application

**Web Backend:**
```bash
python web/backend/app.py
```
API will be available at: http://localhost:5000

**Desktop App:**
```bash
cd desktop
npm install
npm start
```

---

## Common Issues and Solutions

### Issue: `createdb: command not found`

**Solution:** PostgreSQL is not installed or not in PATH.

- **Windows**: Add PostgreSQL bin directory to PATH
  - Usually: `C:\Program Files\PostgreSQL\15\bin`
- **Or use SQLite**: Set `USE_SQLITE=true` in `.env`

### Issue: `FAILED: No 'script_location' key found in configuration`

**Solution:** Alembic configuration file missing in project root.

```bash
# Copy migrations alembic.ini or create one:
cp migrations/alembic.ini alembic.ini

# Edit alembic.ini to set:
script_location = migrations
```

### Issue: `boto3 not available` in S3 tests

**Solution:** This is expected if you haven't installed boto3.

```bash
# Install boto3:
pip install boto3>=1.34.0

# Or the tests will automatically skip if boto3 is not available
```

### Issue: `ModuleNotFoundError: No module named 'sqlalchemy'`

**Solution:** Dependencies not installed in virtual environment.

```bash
# Make sure venv is activated:
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies:
pip install -r requirements.txt
```

### Issue: Import errors or "module not found"

**Solution:** Path issues or missing dependencies.

```bash
# Reinstall in development mode:
pip install -e .

# Or set PYTHONPATH:
export PYTHONPATH="${PYTHONPATH}:${PWD}"  # Linux/macOS
set PYTHONPATH=%PYTHONPATH%;%CD%  # Windows CMD
```

---

## Development Workflow

### Running Tests During Development

```bash
# Run tests in watch mode (requires pytest-watch)
pip install pytest-watch
ptw tools/tests

# Run specific test file
pytest tools/tests/shared/test_models.py -v

# Run tests matching pattern
pytest tools/tests -k "test_florence" -v

# Run with debugging output
pytest tools/tests -v -s
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# View current version
alembic current
```

### Code Quality

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run linter
flake8 shared/ web/backend/

# Format code
black shared/ web/backend/ tools/tests/

# Type checking
mypy shared/ web/backend/

# Security check
bandit -r shared/ web/backend/
```

---

## Project Structure

```
Web-and-Desktop-Apps/
├── shared/                    # Shared Python modules
│   ├── models/               # OCR models (Florence, Donut, etc.)
│   ├── circular_exchange/    # Circular Exchange Framework
│   ├── utils/                # Utility functions
│   ├── services/             # Cloud services
│   └── config/               # Configuration files
│       └── models_config.json
├── web/
│   └── backend/              # Flask backend API
│       ├── storage/          # S3, GDrive, Dropbox handlers
│       ├── training/         # Model training infrastructure
│       ├── billing/          # Stripe integration
│       ├── security/         # Rate limiting, validation
│       └── telemetry/        # Monitoring & analytics
├── desktop/                  # Electron desktop app
├── migrations/               # Database migrations
├── tools/
│   ├── tests/               # Test suite
│   │   ├── shared/          # Shared module tests
│   │   ├── backend/         # Backend tests
│   │   └── circular_exchange/
│   └── scripts/             # Utility scripts
├── alembic.ini              # Database migration config
└── .env                     # Environment configuration
```

---

## Next Steps

1. ✅ Clone the repository
2. ✅ Install dependencies
3. ✅ Configure your `.env` file
4. ✅ Run tests to verify installation
5. 📖 Read the [API Documentation](docs/API.md)
6. 🚀 Start building!

For more information:
- **API Docs**: See `docs/API.md`
- **Contributing**: See `CONTRIBUTING.md`
- **Architecture**: See `docs/ARCHITECTURE.md`

---

## Support

If you encounter issues:

1. Check this guide's "Common Issues" section
2. Search existing GitHub issues
3. Create a new issue with:
   - Your OS and Python version
   - Full error message
   - Steps to reproduce

---

## License

See [LICENSE](LICENSE) file for details.
