#!/usr/bin/env python3
"""
=============================================================================
CACHE BUSTING UTILITY
=============================================================================

Generates version hashes based on file content and updates HTML files with
new version strings. Can be run manually or integrated into CI/CD pipelines.

Usage:
    python cache-bust.py                    # Update all HTML files
    python cache-bust.py --check            # Check current version status
    python cache-bust.py --generate-only    # Only update version.json

=============================================================================
"""

import os
import re
import sys
import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime

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

# HTML files to update
HTML_FILES = [
    'index.html',
    'about.html',
    'api.html',
    'contact.html',
    'help.html',
    'pricing.html',
    'privacy.html',
    'terms.html',
    'status.html'
]

# Assets patterns to add version query strings
ASSET_PATTERNS = [
    (r'href="(styles\.css)"', r'href="styles.css?v={version}"'),
    (r'href="styles\.css\?v=[^"]*"', r'href="styles.css?v={version}"'),
    (r'src="(app\.js)"', r'src="app.js?v={version}"'),
    (r'src="app\.js\?v=[^"]*"', r'src="app.js?v={version}"'),
    (r'src="(components/[^"]+\.js)"', r'src="\1?v={version}"'),
    (r'src="(components/[^"]+\.js)\?v=[^"]*"', r'src="\1?v={version}"'),
    (r'href="(manifest\.json)"', r'href="manifest.json?v={version}"'),
    (r'href="manifest\.json\?v=[^"]*"', r'href="manifest.json?v={version}"'),
]


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
    """Read current version from version.json."""
    if VERSION_FILE.exists():
        with open(VERSION_FILE, 'r') as f:
            return json.load(f)
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
        except (ValueError, IndexError):
            pass
    
    version_data = {
        'version': version,
        'build': now.strftime('%Y%m%d'),
        'timestamp': int(now.timestamp() * 1000),
        'hash': version_hash
    }
    
    with open(VERSION_FILE, 'w') as f:
        json.dump(version_data, f, indent=4)
    
    return version_data


def update_html_file(html_path: Path, version: str) -> bool:
    """Update version query strings in an HTML file."""
    if not html_path.exists():
        print(f"  Warning: {html_path.name} not found")
        return False
    
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Update asset references with version query strings
    for pattern, replacement in ASSET_PATTERNS:
        replacement_with_version = replacement.format(version=version)
        # Handle patterns with capture groups
        if r'\1' in replacement_with_version:
            content = re.sub(pattern, replacement_with_version, content)
        else:
            content = re.sub(pattern, replacement_with_version, content)
    
    # Only write if content changed
    if content != original_content:
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False


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
    parser.add_argument('--generate-only', action='store_true', help='Only update version.json')
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
    
    if args.generate_only:
        print("✓ Version file updated (--generate-only mode)")
        return 0
    
    # Update HTML files
    print("\nUpdating HTML files...")
    updated_count = 0
    
    for html_file in HTML_FILES:
        html_path = FRONTEND_DIR / html_file
        if update_html_file(html_path, version_data['hash']):
            print(f"  ✓ Updated: {html_file}")
            updated_count += 1
        else:
            if args.verbose:
                print(f"  - No changes: {html_file}")
    
    print(f"\n✓ Cache busting complete: {updated_count} files updated")
    print(f"  Version: {version_data['version']}")
    print(f"  Hash: {version_data['hash']}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
