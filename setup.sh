#!/bin/bash
# =============================================================================
# Cross-Platform Setup Script for Receipt Extractor
# =============================================================================
# Works on Linux, macOS, and Windows (Git Bash/WSL)

set -e  # Exit on error

echo "========================================"
echo "Receipt Extractor - Development Setup"
echo "========================================"
echo ""

# Detect OS
OS="Unknown"
case "$(uname -s)" in
    Linux*)     OS="Linux";;
    Darwin*)    OS="Mac";;
    CYGWIN*|MINGW*|MSYS*)    OS="Windows";;
esac

echo "Detected OS: $OS"
echo ""

# Check Python version
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "ERROR: Python is not installed"
    echo "Please install Python 3.10 or higher"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "Found Python $PYTHON_VERSION"

# Check Python version is 3.10+
PYTHON_MAJOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.minor)')

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo "ERROR: Python 3.10+ is required (found $PYTHON_VERSION)"
    exit 1
fi

echo "✓ Python version is compatible"
echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    $PYTHON_CMD -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
if [ "$OS" = "Windows" ]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip -q

# Install dependencies
echo "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✓ Dependencies installed"
else
    echo "WARNING: requirements.txt not found"
fi

# Fix symlink issues (especially for Windows)
echo ""
echo "Setting up directory structure..."

if [ "$OS" = "Windows" ]; then
    # On Windows, create junction or copy if symlink fails
    if [ ! -e "tools/shared" ]; then
        echo "Creating tools/shared link for Windows..."
        # Try symlink first (requires Developer Mode on Windows 10+)
        if ln -s ../shared tools/shared 2>/dev/null; then
            echo "✓ Symlink created successfully"
        else
            # Fallback: create junction using cmd
            echo "Symlink failed, creating junction..."
            cmd //c "mklink /J tools\shared shared" || {
                echo "WARNING: Could not create junction. Tests may fail."
                echo "Run this script as Administrator or enable Developer Mode"
            }
        fi
    else
        echo "✓ tools/shared already exists"
    fi
else
    # Linux/Mac: standard symlink
    if [ ! -L "tools/shared" ] && [ ! -d "tools/shared" ]; then
        echo "Creating tools/shared symlink..."
        ln -s ../shared tools/shared
        echo "✓ Symlink created"
    else
        echo "✓ tools/shared already exists"
    fi
fi

# Create .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your actual credentials"
else
    echo "✓ .env file already exists"
fi

# Create alembic.ini in root
if [ ! -f "alembic.ini" ]; then
    echo ""
    echo "Creating alembic.ini in project root..."
    cat > alembic.ini << 'EOF'
[alembic]
script_location = migrations
prepend_sys_path = .
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s

[alembic:exclude]
tables = alembic_version

sqlalchemy.url = driver://user:pass@localhost/dbname

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOF
    echo "✓ Created alembic.ini"
else
    echo "✓ alembic.ini already exists"
fi

# Check for PostgreSQL
echo ""
echo "Checking for PostgreSQL..."
if command -v psql &> /dev/null; then
    echo "✓ PostgreSQL is installed"
    PSQL_VERSION=$(psql --version | awk '{print $3}')
    echo "  Version: $PSQL_VERSION"
    echo ""
    echo "To create the database, run:"
    echo "  createdb receipt_extractor"
else
    echo "⚠️  PostgreSQL is not installed or not in PATH"
    echo ""
    echo "Options:"
    echo "1. Install PostgreSQL:"
    if [ "$OS" = "Mac" ]; then
        echo "   brew install postgresql@15"
    elif [ "$OS" = "Linux" ]; then
        echo "   sudo apt-get install postgresql postgresql-contrib"
    elif [ "$OS" = "Windows" ]; then
        echo "   Download from: https://www.postgresql.org/download/windows/"
    fi
    echo ""
    echo "2. Use SQLite for development:"
    echo "   - Set USE_SQLITE=true in your .env file"
fi

# Check for Tesseract OCR
echo ""
echo "Checking for Tesseract OCR..."
if command -v tesseract &> /dev/null; then
    echo "✓ Tesseract is installed"
    TESSERACT_VERSION=$(tesseract --version 2>&1 | head -1)
    echo "  $TESSERACT_VERSION"
else
    echo "⚠️  Tesseract OCR is not installed"
    echo ""
    echo "Install Tesseract:"
    if [ "$OS" = "Mac" ]; then
        echo "  brew install tesseract"
    elif [ "$OS" = "Linux" ]; then
        echo "  sudo apt-get install tesseract-ocr"
    elif [ "$OS" = "Windows" ]; then
        echo "  Download from: https://github.com/UB-Mannheim/tesseract/wiki"
    fi
fi

# Check for Node.js (for desktop app)
echo ""
echo "Checking for Node.js (for desktop app)..."
if command -v node &> /dev/null; then
    echo "✓ Node.js is installed"
    NODE_VERSION=$(node --version)
    echo "  Version: $NODE_VERSION"
else
    echo "⚠️  Node.js is not installed"
    echo "  Install from: https://nodejs.org/ (LTS version recommended)"
fi

# Summary
echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env file with your credentials:"
echo "   nano .env  # or use your favorite editor"
echo ""
echo "2. Set up database:"
echo "   Option A (PostgreSQL):"
echo "     createdb receipt_extractor"
echo "     alembic upgrade head"
echo "   Option B (SQLite - easier for development):"
echo "     Set USE_SQLITE=true in .env"
echo "     alembic upgrade head"
echo ""
echo "3. Run tests:"
echo "   pytest tools/tests -v"
echo ""
echo "4. Start the web backend:"
echo "   python web/backend/app.py"
echo ""
echo "5. Start the desktop app (optional):"
echo "   cd desktop"
echo "   npm install"
echo "   npm start"
echo ""
echo "For more information, see README.md"
echo ""
