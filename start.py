#!/usr/bin/env python3
"""
=============================================================================
Receipt Extractor - ONE-CLICK START
=============================================================================

Cross-platform startup script that automatically:
1. Creates/activates virtual environment
2. Installs dependencies
3. Clears cache (runs cache-bust.py)
4. Starts development servers

Usage:
    python start.py         # Full setup + start servers
    python start.py --quick # Skip venv, just start servers
    python start.py --help  # Show help

Works on Windows, macOS, and Linux.
=============================================================================
"""

import os
import sys
import subprocess
import shutil
import argparse
from pathlib import Path

# Get project root (where this script is located)
PROJECT_ROOT = Path(__file__).parent.resolve()

# Configuration
VENV_DIR = PROJECT_ROOT / "venv"
BACKEND_DIR = PROJECT_ROOT / "web" / "backend"
FRONTEND_DIR = PROJECT_ROOT / "web" / "frontend"
CACHE_BUST_SCRIPT = PROJECT_ROOT / "web" / "cache-bust.py"
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"
BACKEND_PORT = 5000
FRONTEND_PORT = 3000

# Colors for terminal output (works on Windows 10+ and Unix)
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"

# Enable colors on Windows
if sys.platform == "win32":
    os.system("")  # Enable ANSI escape codes on Windows 10+


def print_banner():
    """Print startup banner."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}")
    print("=" * 60)
    print("       RECEIPT EXTRACTOR - ONE-CLICK START")
    print("=" * 60)
    print(f"{Colors.END}")


def print_step(msg):
    """Print a step message."""
    print(f"{Colors.BLUE}[STEP]{Colors.END} {msg}")


def print_success(msg):
    """Print a success message."""
    print(f"{Colors.GREEN}[OK]{Colors.END} {msg}")


def print_error(msg):
    """Print an error message."""
    print(f"{Colors.RED}[ERROR]{Colors.END} {msg}")


def print_warning(msg):
    """Print a warning message."""
    print(f"{Colors.YELLOW}[WARN]{Colors.END} {msg}")


def get_python_executable():
    """Get the Python executable path."""
    if sys.platform == "win32":
        venv_python = VENV_DIR / "Scripts" / "python.exe"
    else:
        venv_python = VENV_DIR / "bin" / "python"
    
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def get_pip_executable():
    """Get the pip executable path."""
    if sys.platform == "win32":
        venv_pip = VENV_DIR / "Scripts" / "pip.exe"
    else:
        venv_pip = VENV_DIR / "bin" / "pip"
    
    if venv_pip.exists():
        return str(venv_pip)
    return None


def create_venv():
    """Create virtual environment if it doesn't exist."""
    if VENV_DIR.exists():
        print_success(f"Virtual environment exists: {VENV_DIR}")
        return True
    
    print_step("Creating virtual environment...")
    try:
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
        print_success(f"Created virtual environment: {VENV_DIR}")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to create virtual environment: {e}")
        return False


def install_dependencies():
    """Install dependencies from requirements.txt."""
    pip = get_pip_executable()
    if not pip:
        print_error("pip not found in virtual environment")
        return False
    
    if not REQUIREMENTS_FILE.exists():
        print_warning(f"requirements.txt not found at {REQUIREMENTS_FILE}")
        return True  # Continue anyway
    
    print_step("Installing dependencies (this may take a few minutes)...")
    try:
        # Upgrade pip first
        subprocess.run([pip, "install", "--upgrade", "pip"], 
                      capture_output=True, check=False)
        
        # Install requirements
        result = subprocess.run(
            [pip, "install", "-r", str(REQUIREMENTS_FILE)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_success("Dependencies installed successfully")
            return True
        else:
            print_warning("Some dependencies may have failed to install")
            print_warning("Core functionality should still work")
            return True
    except Exception as e:
        print_error(f"Failed to install dependencies: {e}")
        return False


def run_cache_bust():
    """Run the cache busting script."""
    if not CACHE_BUST_SCRIPT.exists():
        print_warning(f"cache-bust.py not found at {CACHE_BUST_SCRIPT}")
        return True  # Continue anyway
    
    print_step("Running cache bust...")
    python = get_python_executable()
    
    try:
        result = subprocess.run(
            [python, str(CACHE_BUST_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(CACHE_BUST_SCRIPT.parent)
        )
        
        if "No changes detected" in result.stdout or result.returncode == 0:
            print_success("Cache bust complete")
        else:
            print_success("Cache updated with new version")
        
        return True
    except Exception as e:
        print_warning(f"Cache bust failed (non-critical): {e}")
        return True  # Continue anyway


def clean_pycache():
    """Clean Python cache files."""
    print_step("Cleaning Python cache...")
    
    count = 0
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # Skip venv directory
        if "venv" in root or ".git" in root:
            continue
        
        # Remove __pycache__ directories
        if "__pycache__" in dirs:
            pycache_path = Path(root) / "__pycache__"
            try:
                shutil.rmtree(pycache_path)
                count += 1
            except Exception:
                pass
        
        # Remove .pyc files
        for f in files:
            if f.endswith(".pyc"):
                try:
                    os.remove(Path(root) / f)
                    count += 1
                except Exception:
                    pass
    
    # Remove pytest cache
    for cache_dir in [".pytest_cache", "htmlcov"]:
        cache_path = PROJECT_ROOT / cache_dir
        if cache_path.exists():
            try:
                shutil.rmtree(cache_path)
                count += 1
            except Exception:
                pass
    
    print_success(f"Cleaned {count} cache items")


def start_backend():
    """Start the Flask backend server."""
    print_step("Starting backend server...")
    
    python = get_python_executable()
    app_file = BACKEND_DIR / "app.py"
    
    if not app_file.exists():
        print_error(f"Backend app.py not found at {app_file}")
        return None
    
    # Set environment for SQLite (development mode)
    env = os.environ.copy()
    env["USE_SQLITE"] = "true"
    
    try:
        # Create logs directory
        logs_dir = PROJECT_ROOT / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Start backend
        if sys.platform == "win32":
            # Windows: use CREATE_NEW_PROCESS_GROUP for proper Ctrl+C handling
            process = subprocess.Popen(
                [python, str(app_file)],
                cwd=str(BACKEND_DIR),
                env=env,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            # Unix: use preexec_fn for new session
            process = subprocess.Popen(
                [python, str(app_file)],
                cwd=str(BACKEND_DIR),
                env=env,
                start_new_session=True
            )
        
        print_success(f"Backend starting on http://localhost:{BACKEND_PORT}")
        return process
    except Exception as e:
        print_error(f"Failed to start backend: {e}")
        return None


def start_frontend():
    """Start the frontend HTTP server."""
    print_step("Starting frontend server...")
    
    python = get_python_executable()
    
    if not FRONTEND_DIR.exists():
        print_error(f"Frontend directory not found: {FRONTEND_DIR}")
        return None
    
    try:
        if sys.platform == "win32":
            process = subprocess.Popen(
                [python, "-m", "http.server", str(FRONTEND_PORT)],
                cwd=str(FRONTEND_DIR),
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            process = subprocess.Popen(
                [python, "-m", "http.server", str(FRONTEND_PORT)],
                cwd=str(FRONTEND_DIR),
                start_new_session=True
            )
        
        print_success(f"Frontend starting on http://localhost:{FRONTEND_PORT}")
        return process
    except Exception as e:
        print_error(f"Failed to start frontend: {e}")
        return None


def open_browser():
    """Open the frontend in the default browser."""
    import webbrowser
    url = f"http://localhost:{FRONTEND_PORT}"
    
    print_step("Opening browser...")
    try:
        webbrowser.open(url)
        print_success(f"Opened {url}")
    except Exception:
        print_warning(f"Could not open browser. Visit: {url}")


def main():
    """Main startup sequence."""
    parser = argparse.ArgumentParser(description="Receipt Extractor - One-Click Start")
    parser.add_argument("--quick", action="store_true", 
                       help="Skip venv creation, just start servers")
    parser.add_argument("--no-browser", action="store_true",
                       help="Don't open browser automatically")
    parser.add_argument("--clean-only", action="store_true",
                       help="Only clean cache, don't start servers")
    args = parser.parse_args()
    
    print_banner()
    
    # Change to project root
    os.chdir(PROJECT_ROOT)
    print(f"Project root: {PROJECT_ROOT}\n")
    
    # Clean cache first
    clean_pycache()
    
    # Run cache bust
    run_cache_bust()
    
    if args.clean_only:
        print(f"\n{Colors.GREEN}{Colors.BOLD}Cache cleaned successfully!{Colors.END}")
        return 0
    
    # Setup virtual environment (unless --quick)
    if not args.quick:
        if not create_venv():
            print_error("Failed to create virtual environment")
            return 1
        
        if not install_dependencies():
            print_warning("Some dependencies failed, but continuing...")
    
    # Start servers
    print(f"\n{Colors.BOLD}Starting servers...{Colors.END}\n")
    
    backend_process = start_backend()
    if not backend_process:
        print_error("Failed to start backend")
        return 1
    
    # Give backend time to start
    import time
    time.sleep(2)
    
    frontend_process = start_frontend()
    if not frontend_process:
        print_error("Failed to start frontend")
        backend_process.terminate()
        return 1
    
    # Give frontend time to start
    time.sleep(1)
    
    # Open browser
    if not args.no_browser:
        open_browser()
    
    # Print success message
    print(f"\n{Colors.GREEN}{Colors.BOLD}")
    print("=" * 60)
    print("             SERVERS RUNNING!")
    print("=" * 60)
    print(f"{Colors.END}")
    print(f"  Frontend:  {Colors.CYAN}http://localhost:{FRONTEND_PORT}{Colors.END}")
    print(f"  Backend:   {Colors.CYAN}http://localhost:{BACKEND_PORT}{Colors.END}")
    print(f"  API Health:{Colors.CYAN}http://localhost:{BACKEND_PORT}/api/health{Colors.END}")
    print()
    print(f"{Colors.YELLOW}{Colors.BOLD}Press Ctrl+C to stop all servers{Colors.END}")
    print()
    
    # Wait for Ctrl+C
    try:
        while True:
            # Check if processes are still running
            if backend_process.poll() is not None:
                print_error("Backend server stopped unexpectedly")
                break
            if frontend_process.poll() is not None:
                print_error("Frontend server stopped unexpectedly")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Shutting down...{Colors.END}")
    finally:
        # Clean up processes
        for process in [backend_process, frontend_process]:
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except Exception:
                    try:
                        process.kill()
                    except Exception:
                        pass
        
        print(f"{Colors.GREEN}Servers stopped. Goodbye!{Colors.END}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
