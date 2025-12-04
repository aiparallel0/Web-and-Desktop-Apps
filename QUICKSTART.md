# Quick Start Guide

## Using the Test Script

The `run.sh` script provides a simple way to test and work with the Receipt Extractor application.

### Quick Commands

```bash
# Show help
./run.sh help

# Run tests (with coverage)
./run.sh test

# Run quick tests (no coverage, faster)
./run.sh quick

# Start development servers
./run.sh dev

# Clean cache and temp files
./run.sh clean

# Check/install dependencies
./run.sh deps

# Run database migrations
./run.sh migrate

# View test coverage report
./run.sh coverage

# Interactive menu (default)
./run.sh
```

### First Time Setup

1. **Install dependencies:**
   ```bash
   ./run.sh deps
   ```

2. **Run migrations:**
   ```bash
   ./run.sh migrate
   ```

3. **Run tests to verify:**
   ```bash
   ./run.sh test
   ```

4. **Start development servers:**
   ```bash
   ./run.sh dev
   ```

### Development Workflow

**Testing changes:**
```bash
# Make code changes...

# Run quick tests
./run.sh quick

# Or run full tests with coverage
./run.sh test
```

**Running the application:**
```bash
# Start both backend and frontend
./run.sh dev

# Access the app at:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:5000
# - API Health: http://localhost:5000/api/health
```

**Cleaning up:**
```bash
# Clean Python cache and test files
./run.sh clean
```

### Interactive Menu

Run without arguments to access the interactive menu:

```bash
./run.sh
```

Menu options:
- **1**: Run Quick Tests (fast unit tests)
- **2**: Run Full Test Suite (with coverage)
- **3**: Start Dev Servers (backend + frontend)
- **4**: Check Dependencies
- **5**: Clean Cache & Logs
- **6**: Run Database Migrations
- **7**: View Test Coverage Report
- **F**: Launch Full Launcher (./tools/launch.sh)
- **0**: Exit

### Advanced Features

For more advanced features like GPU detection, system health reports, and AI analysis export, use the full launcher:

```bash
./tools/launch.sh
```

### Troubleshooting

**Port already in use:**
```bash
# Find process using port 5000
lsof -i :5000

# Kill process
kill -9 <PID>

# Or use a different port by editing run.sh
```

**Dependencies missing:**
```bash
# Install all dependencies
pip install -r requirements.txt

# Or use the script
./run.sh deps
```

**Tests failing:**
```bash
# Clean cache first
./run.sh clean

# Then run tests
./run.sh test
```

**Database errors:**
```bash
# Run migrations
./run.sh migrate

# Or use SQLite (default for development)
export USE_SQLITE=true
```

### What's the Difference?

**`run.sh` vs `tools/launch.sh`:**

| Feature | run.sh | tools/launch.sh |
|---------|--------|-----------------|
| Purpose | Quick testing & dev | Full-featured launcher |
| Location | Project root | tools/ directory |
| Menu | Simplified | Comprehensive |
| GPU Detection | No | Yes |
| System Reports | No | Yes |
| AI Analysis Export | No | Yes |
| Cache Cleaning | Yes | Yes |
| Test Running | Yes | Yes |
| Server Management | Yes | Yes |

**Use `run.sh` for:**
- Quick testing during development
- Running tests frequently
- Starting dev servers
- Day-to-day development work

**Use `tools/launch.sh` for:**
- First-time setup
- Production-like testing
- System diagnostics
- GPU detection and optimization
- Generating AI analysis reports

### Examples

**Typical development session:**
```bash
# 1. Pull latest changes
git pull

# 2. Update dependencies if needed
./run.sh deps

# 3. Clean old cache
./run.sh clean

# 4. Run tests
./run.sh quick

# 5. Start working
./run.sh dev
```

**Before committing:**
```bash
# 1. Clean cache
./run.sh clean

# 2. Run full test suite
./run.sh test

# 3. Check coverage
./run.sh coverage

# 4. Commit if tests pass
git add .
git commit -m "Your message"
```

**Debugging test failures:**
```bash
# 1. Clean everything
./run.sh clean

# 2. Run tests with verbose output
cd tools/tests
python3 -m pytest -v -s

# Or run specific test
python3 -m pytest shared/test_models.py -v
```

### Tips

1. **Faster testing**: Use `./run.sh quick` for rapid iteration
2. **Coverage**: Run `./run.sh test` before committing
3. **Clean builds**: Run `./run.sh clean` if you see weird errors
4. **Browser auto-open**: The dev server will try to open your browser automatically
5. **Stop servers**: Press `Ctrl+C` to stop all servers gracefully

### Need More Help?

- See **README.md** for project overview
- See **SETUP.md** for detailed setup instructions
- Run `./tools/launch.sh` for full launcher with more options
- Check test logs in `logs/` directory
