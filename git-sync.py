#!/usr/bin/env python3
"""
=============================================================================
GIT SYNC UTILITY
=============================================================================

Safely synchronizes your local repository with the remote by:
1. Stashing or discarding local changes to auto-generated files
2. Pulling latest changes from remote
3. Re-running cache-bust.py to regenerate local files

This solves the common "Your local changes would be overwritten by merge" error
caused by auto-generated files like version.json.

Usage:
    python git-sync.py          # Sync with remote (auto-stash local changes)
    python git-sync.py --discard # Discard local changes instead of stashing
    python git-sync.py --status  # Just show status, don't sync

=============================================================================
"""

import os
import sys
import subprocess
from pathlib import Path

# Get project root (where this script is located)
PROJECT_ROOT = Path(__file__).parent.resolve()

# Files that are commonly modified locally but shouldn't block pulls
# These are either gitignored or auto-generated
AUTO_GENERATED_FILES = [
    "web/frontend/version.json",
]

# Files that may have been modified by old cache-bust.py scripts
# but should now match remote exactly
PREVIOUSLY_MODIFIED_FILES = [
    "web/frontend/index.html",
    "web/frontend/about.html",
    "web/frontend/api.html",
    "web/frontend/contact.html",
    "web/frontend/help.html",
    "web/frontend/pricing.html",
    "web/frontend/privacy.html",
    "web/frontend/status.html",
    "web/frontend/terms.html",
    "desktop/index.html",
]


class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


# Enable ANSI escape codes on Windows 10+ for colored terminal output
# The empty os.system("") call triggers Windows to process virtual terminal sequences
if sys.platform == "win32":
    os.system("")


def print_banner():
    """Print startup banner."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}")
    print("=" * 60)
    print("              GIT SYNC UTILITY")
    print("=" * 60)
    print(f"{Colors.END}")


def print_step(msg):
    print(f"{Colors.BLUE}[STEP]{Colors.END} {msg}")


def print_success(msg):
    print(f"{Colors.GREEN}[OK]{Colors.END} {msg}")


def print_error(msg):
    print(f"{Colors.RED}[ERROR]{Colors.END} {msg}")


def print_warning(msg):
    print(f"{Colors.YELLOW}[WARN]{Colors.END} {msg}")


def run_git(args, check=True, capture=True, timeout=60):
    """Run a git command and return the result.
    
    Args:
        args: Git command arguments (without 'git' prefix)
        check: If True, raise CalledProcessError on non-zero exit
        capture: If True, capture stdout/stderr
        timeout: Maximum seconds to wait for command (default 60)
    
    Returns:
        CompletedProcess object, or a mock result with returncode=-1 on error
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=PROJECT_ROOT,
            capture_output=capture,
            text=True,
            check=check,
            timeout=timeout
        )
        return result
    except subprocess.CalledProcessError as e:
        # Return a consistent result-like object with error info
        return subprocess.CompletedProcess(
            args=e.cmd, returncode=e.returncode, 
            stdout=e.stdout or "", stderr=e.stderr or ""
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            args=["git"] + args, returncode=-1,
            stdout="", stderr="Command timed out"
        )


def get_modified_files():
    """Get list of files with uncommitted changes."""
    result = run_git(["status", "--porcelain"])
    if result.returncode != 0:
        return []
    
    modified = []
    stdout = result.stdout.strip()
    
    # Handle empty output case
    if not stdout:
        return []
    
    for line in stdout.split("\n"):
        if line.strip():
            # Parse status line: "XY filename" or "XY old -> new"
            parts = line.split()
            if len(parts) >= 2:
                status = parts[0]
                filename = parts[1]
                # Handle renamed files
                if "->" in line:
                    filename = parts[-1]
                modified.append((status, filename))
    
    return modified


def categorize_changes(modified_files):
    """Categorize modified files into safe-to-discard and needs-attention."""
    safe_to_discard = []
    needs_attention = []
    
    all_auto_files = set(AUTO_GENERATED_FILES + PREVIOUSLY_MODIFIED_FILES)
    
    for status, filename in modified_files:
        if filename in all_auto_files:
            safe_to_discard.append((status, filename))
        else:
            needs_attention.append((status, filename))
    
    return safe_to_discard, needs_attention


def show_status():
    """Show current git status."""
    modified = get_modified_files()
    
    if not modified:
        print_success("No local changes detected. You can safely run 'git pull'.")
        return True
    
    safe, attention = categorize_changes(modified)
    
    if safe:
        print(f"\n{Colors.YELLOW}Auto-generated files with local changes:{Colors.END}")
        for status, filename in safe:
            print(f"  [{status}] {filename}")
        print(f"\n  These can be safely discarded with: {Colors.CYAN}python git-sync.py --discard{Colors.END}")
    
    if attention:
        print(f"\n{Colors.RED}Files that may need your attention:{Colors.END}")
        for status, filename in attention:
            print(f"  [{status}] {filename}")
        print("\n  Consider committing or stashing these files manually.")
    
    return False


def discard_auto_generated():
    """Discard changes to auto-generated files."""
    modified = get_modified_files()
    safe, attention = categorize_changes(modified)
    
    if not safe:
        print_success("No auto-generated files need to be reset.")
        return True
    
    print_step("Discarding changes to auto-generated files...")
    
    for status, filename in safe:
        filepath = PROJECT_ROOT / filename
        
        if status in ("??", "A"):  # Untracked or new file
            if filepath.exists():
                try:
                    filepath.unlink()
                    print_success(f"Deleted: {filename}")
                except Exception as e:
                    print_error(f"Could not delete {filename}: {e}")
        else:  # Modified tracked file
            result = run_git(["checkout", "--", filename], check=False)
            if result.returncode == 0:
                print_success(f"Reset: {filename}")
            else:
                print_error(f"Could not reset {filename}")
    
    return True


def stash_changes():
    """Stash all local changes."""
    print_step("Stashing local changes...")
    result = run_git(["stash", "push", "-m", "Auto-stash before git-sync"], check=False)
    
    if result.returncode == 0:
        if "No local changes to save" in result.stdout:
            print_success("No changes to stash")
        else:
            print_success("Changes stashed")
        return True
    else:
        print_error("Failed to stash changes")
        return False


def pull_latest():
    """Pull latest changes from remote."""
    print_step("Pulling latest changes...")
    result = run_git(["pull"], check=False)
    
    if result.returncode == 0:
        print_success("Pull successful")
        if result.stdout:
            print(result.stdout)
        return True
    else:
        print_error("Pull failed")
        if result.stderr:
            print(result.stderr)
        return False


def run_cache_bust():
    """Run cache-bust.py to regenerate version.json."""
    cache_bust_script = PROJECT_ROOT / "web" / "cache-bust.py"
    
    if not cache_bust_script.exists():
        return True  # Skip if script doesn't exist
    
    print_step("Regenerating cache files...")
    
    try:
        result = subprocess.run(
            [sys.executable, str(cache_bust_script)],
            cwd=str(cache_bust_script.parent),
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout for cache-bust
        )
        
        if result.returncode == 0:
            print_success("Cache files regenerated")
        return True
    except subprocess.TimeoutExpired:
        print_warning("Cache regeneration timed out (non-critical)")
        return True
    except Exception as e:
        print_warning(f"Cache regeneration skipped: {e}")
        return True


def main():
    """Main sync sequence."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Sync local repository with remote, handling auto-generated files"
    )
    parser.add_argument("--discard", action="store_true",
                       help="Discard (not stash) changes to auto-generated files")
    parser.add_argument("--status", action="store_true",
                       help="Just show status, don't sync")
    parser.add_argument("--force", action="store_true",
                       help="Force sync even if there are other uncommitted changes")
    args = parser.parse_args()
    
    print_banner()
    os.chdir(PROJECT_ROOT)
    
    # Check if we're in a git repository
    if not (PROJECT_ROOT / ".git").exists():
        print_error("Not a git repository!")
        return 1
    
    # Status-only mode
    if args.status:
        show_status()
        return 0
    
    # Check for modified files
    modified = get_modified_files()
    
    if not modified:
        print_success("No local changes. Pulling latest...")
        if pull_latest():
            run_cache_bust()
            print(f"\n{Colors.GREEN}{Colors.BOLD}Sync complete!{Colors.END}")
            return 0
        return 1
    
    safe, attention = categorize_changes(modified)
    
    # If there are files needing attention and not forcing
    if attention and not args.force:
        print_warning("You have uncommitted changes to files that may be important:")
        for status, filename in attention:
            print(f"  [{status}] {filename}")
        print(f"\nOptions:")
        print(f"  1. Commit or manually stash your changes first")
        print(f"  2. Run with {Colors.CYAN}--force{Colors.END} to stash all changes")
        print(f"  3. Run with {Colors.CYAN}--discard{Colors.END} to discard only auto-generated files")
        return 1
    
    # Handle auto-generated files
    if args.discard and safe:
        if not discard_auto_generated():
            return 1
    elif modified:
        if not stash_changes():
            return 1
    
    # Pull latest
    if not pull_latest():
        print_warning("Pull failed. You may need to resolve conflicts manually.")
        return 1
    
    # Regenerate cache files
    run_cache_bust()
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}Sync complete!{Colors.END}")
    
    # Remind about stash
    if not args.discard and modified:
        print(f"\n{Colors.YELLOW}Note:{Colors.END} Your previous changes were stashed.")
        print(f"  To recover: {Colors.CYAN}git stash pop{Colors.END}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
