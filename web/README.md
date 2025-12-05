# Web Application

This directory contains the web application components for Receipt Extractor.

## Directory Structure

```
web/
├── backend/          # Flask API server
│   └── app.py        # Main application entry point
├── frontend/         # Web UI (HTML/CSS/JS)
│   └── index.html    # Main web interface
└── cache-bust.py     # Cache busting utility
```

## ⚠️ Important: Run Commands from Repository Root

Most setup and development commands should be run from the **repository root directory**, not from this `web/` subdirectory.

### Setup Instructions

```bash
# Navigate to the repository root (parent of this directory)
cd ..

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Run database migrations
./launcher.sh migrate

# Start development servers
./launcher.sh dev
```

### Quick Reference

| Command | Run From | Description |
|---------|----------|-------------|
| `./launcher.sh dev` | Repository root | Start both backend and frontend servers |
| `./launcher.sh test` | Repository root | Run full test suite |
| `./launcher.sh deps` | Repository root | Install/update dependencies |
| `pip install -r requirements.txt` | Repository root | Install Python dependencies |
| `python cache-bust.py` | This directory (`web/`) | Update cache-busting version strings |

## Cache Busting Utility

The `cache-bust.py` script in this directory updates version strings in HTML files to ensure browsers load fresh assets after updates.

```bash
# Run from the web/ directory
python cache-bust.py                    # Update all HTML files
python cache-bust.py --check            # Check current version status
python cache-bust.py --generate-only    # Only update version.json
```

## Starting Servers Manually

If you prefer to start servers manually instead of using `launcher.sh`:

```bash
# Start backend (from repository root)
cd web/backend && python app.py

# Start frontend (from repository root, in a separate terminal)
cd web/frontend && python -m http.server 3000
```

Access the application:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **Health Check**: http://localhost:5000/api/health

## Full Documentation

For complete setup instructions, environment configuration, and troubleshooting:

- See **[../README.md](../README.md)** for project overview and quick start
- See **[../SETUP.md](../SETUP.md)** for detailed setup instructions
- See **[../QUICKSTART.md](../QUICKSTART.md)** for quick reference commands
