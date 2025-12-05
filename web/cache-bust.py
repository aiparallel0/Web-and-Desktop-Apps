#!/usr/bin/env python3
"""
=============================================================================
CACHE BUSTING UTILITY
=============================================================================

Generates version hashes based on file content and updates version.json.
The version.json file is used for runtime version checking in the app.

Cache busting for static assets is handled by the service worker, not by
version query strings in HTML files. This design prevents merge conflicts
when developers run this script locally.

Usage:
    python cache-bust.py                    # Update version.json
    python cache-bust.py --check            # Check current version status
    python cache-bust.py --generate-only    # Only update version.json (same as default)

=============================================================================
"""

import os
import sys
import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime

# Configure stdout to handle Unicode gracefully on Windows
# This fixes UnicodeEncodeError on systems with limited encodings (e.g., cp1254)
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    try:
        sys.stdout.reconfigure(errors='replace')
    except AttributeError:
        # Python < 3.7 fallback: wrap stdout with the same encoding but error handling
        import io
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer,
            encoding=sys.stdout.encoding,
            errors='replace'
        )

# Configuration
FRONTEND_DIR = Path(__file__).parent / 'frontend'
VERSION_FILE = FRONTEND_DIR / 'version.json'

# Files to hash for version generation
ASSETS_TO_HASH = [
    'styles.css',
    'app.js',
    'components/upload-zone.js',
    'components/progress-bar.js',
    'components/results-view.js',
    'service-worker.js'
]

# Note: HTML files are no longer updated with version query strings.
# Cache busting is now handled by the service worker which uses APP_VERSION.
# This prevents merge conflicts when developers run cache-bust.py locally.
# The version.json file provides runtime version checking for the app.


def calculate_file_hash(file_path: Path) -> str:
    """Calculate MD5 hash of a file's content."""
    if not file_path.exists():
        return 'missing'
    
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        hasher.update(f.read())
    return hasher.hexdigest()[:8]


def calculate_version_hash() -> str:
    """Calculate a combined hash from all asset files."""
    combined_hash = hashlib.md5()
    
    for asset in ASSETS_TO_HASH:
        asset_path = FRONTEND_DIR / asset
        if asset_path.exists():
            with open(asset_path, 'rb') as f:
                combined_hash.update(f.read())
    
    return combined_hash.hexdigest()[:8]


def get_current_version() -> dict:
    """Read current version from version.json.
    
    If version.json doesn't exist, it will be created from version.json.example.
    This file is auto-generated and not tracked in git to prevent merge conflicts.
    """
    if VERSION_FILE.exists():
        with open(VERSION_FILE, 'r') as f:
            return json.load(f)
    
    # Create version.json from template if it doesn't exist
    example_file = Path(str(VERSION_FILE) + '.example')
    if example_file.exists():
        with open(example_file, 'r') as f:
            template = json.load(f)
        with open(VERSION_FILE, 'w') as f:
            json.dump(template, f, indent=4)
        print(f"  Created version.json from template")
        return template
    
    return None


def update_version_file(version_hash: str) -> dict:
    """Update version.json with new hash and timestamp."""
    now = datetime.now()
    
    current = get_current_version() or {}
    version = current.get('version', '2.0.0')
    
    # Parse version and increment patch number if hash changed
    if current.get('hash') != version_hash:
        try:
            parts = version.split('.')
            parts[-1] = str(int(parts[-1]) + 1)
            version = '.'.join(parts)
        except (ValueError, IndexError) as e:
            # Log version parsing failure and use default
            print(f"  Warning: Could not parse version '{version}', using default: {e}")
            version = '2.0.1'
    
    version_data = {
        'version': version,
        'build': now.strftime('%Y%m%d'),
        'timestamp': int(now.timestamp() * 1000),
        'hash': version_hash
    }
    
    with open(VERSION_FILE, 'w') as f:
        json.dump(version_data, f, indent=4)
    
    return version_data


def check_status():
    """Check and display current version status."""
    print("Cache Busting Status Check")
    print("=" * 50)
    
    current = get_current_version()
    if current:
        print(f"Current version: {current.get('version')}")
        print(f"Build date: {current.get('build')}")
        print(f"Hash: {current.get('hash')}")
    else:
        print("No version.json found")
    
    print("\nAsset hashes:")
    for asset in ASSETS_TO_HASH:
        asset_path = FRONTEND_DIR / asset
        file_hash = calculate_file_hash(asset_path)
        status = '✓' if asset_path.exists() else '✗'
        print(f"  {status} {asset}: {file_hash}")
    
    new_hash = calculate_version_hash()
    print(f"\nCombined hash: {new_hash}")
    
    if current and current.get('hash') == new_hash:
        print("\n✓ Version is up to date")
    else:
        print("\n⚠ Version hash has changed - update recommended")


def main():
    parser = argparse.ArgumentParser(description='Cache busting utility for Receipt Extractor')
    parser.add_argument('--check', action='store_true', help='Check current version status')
    parser.add_argument('--generate-only', action='store_true', help='Only update version.json (same as default behavior)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.check:
        check_status()
        return 0
    
    print("Cache Busting Utility")
    print("=" * 50)
    
    # Calculate new version hash
    version_hash = calculate_version_hash()
    print(f"Calculated version hash: {version_hash}")
    
    # Check if update is needed
    current = get_current_version()
    if current and current.get('hash') == version_hash:
        print("✓ No changes detected, version is up to date")
        return 0
    
    # Update version.json
    version_data = update_version_file(version_hash)
    print(f"Updated version.json: v{version_data['version']} (build {version_data['build']})")
    
    # Note: HTML files are no longer updated to prevent merge conflicts.
    # Cache busting is handled by the service worker using APP_VERSION.
    
    print(f"\n✓ Cache busting complete")
    print(f"  Version: {version_data['version']}")
    print(f"  Hash: {version_data['hash']}")
    print(f"\nNote: HTML files are not modified. Cache busting is handled by the service worker.")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
