#!/usr/bin/env python3
"""
CEFR Boilerplate Cleanup Script

Removes CEFR registration boilerplate from all Python files.
Patterns removed:
1. try/except ImportError blocks for CIRCULAR_EXCHANGE_AVAILABLE
2. if CIRCULAR_EXCHANGE_AVAILABLE: try: PROJECT_CONFIG.register_module(...) blocks
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

def read_file(filepath: Path) -> str:
    """Read file content."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(filepath: Path, content: str) -> None:
    """Write file content."""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def remove_cefr_import_block(content: str) -> Tuple[str, bool]:
    """
    Remove the CEFR import try/except block.
    
    Pattern:
    # Circular Exchange Framework Integration
    try:
        from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
        CIRCULAR_EXCHANGE_AVAILABLE = True
    except ImportError:
        CIRCULAR_EXCHANGE_AVAILABLE = False
    """
    pattern = re.compile(
        r'# Circular Exchange Framework Integration\s*\n'
        r'try:\s*\n'
        r'\s+from shared\.circular_exchange import [^\n]+\n'
        r'\s+CIRCULAR_EXCHANGE_AVAILABLE = True\s*\n'
        r'except ImportError:\s*\n'
        r'\s+CIRCULAR_EXCHANGE_AVAILABLE = False\s*\n',
        re.MULTILINE
    )
    
    new_content = pattern.sub('', content)
    changed = new_content != content
    
    return new_content, changed

def remove_cefr_registration_block(content: str) -> Tuple[str, bool]:
    """
    Remove the CEFR registration if block.
    
    Pattern:
    """
    # Match the registration block - need to handle nested parentheses
    lines = content.split('\n')
    new_lines = []
    i = 0
    changed = False
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this is the start of a registration block
        # Keep the line
        new_lines.append(line)
        i += 1
    
    new_content = '\n'.join(new_lines)
    return new_content, changed

def remove_standalone_circular_exchange_available_checks(content: str) -> Tuple[str, bool]:
    """Remove any remaining standalone CIRCULAR_EXCHANGE_AVAILABLE references."""
    # Remove variable assignments
    pattern1 = re.compile(
        r'\s*CIRCULAR_EXCHANGE_AVAILABLE\s*=\s*(True|False)\s*\n',
        re.MULTILINE
    )
    content = pattern1.sub('', content)
    
    return content, True

def cleanup_extra_blank_lines(content: str) -> str:
    """Remove excessive blank lines (more than 2 consecutive)."""
    # Replace 3+ consecutive newlines with just 2
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content

def process_file(filepath: Path, dry_run: bool = False) -> Tuple[bool, str]:
    """
    Process a single file to remove CEFR boilerplate.
    
    Returns:
        Tuple of (changed, message)
    """
    try:
        content = read_file(filepath)
        original_content = content
        
        # Apply removals
        content, changed1 = remove_cefr_import_block(content)
        content, changed2 = remove_cefr_registration_block(content)
        
        # Cleanup extra blank lines
        content = cleanup_extra_blank_lines(content)
        
        changed = changed1 or changed2 or (content != original_content)
        
        if changed:
            if not dry_run:
                write_file(filepath, content)
                return True, f"✓ Cleaned {filepath}"
            else:
                return True, f"Would clean {filepath}"
        else:
            return False, f"- No changes needed for {filepath}"
            
    except Exception as e:
        return False, f"✗ Error processing {filepath}: {e}"

def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    
    # Read list of files with CEFR boilerplate
    files_to_process = []
    
    # Get all Python files with CEFR boilerplate
    import subprocess
    result = subprocess.run(
        ['grep', '-rl', 'CIRCULAR_EXCHANGE_AVAILABLE', '--include=*.py', '.'],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        files_to_process = [
            project_root / line.strip() 
            for line in result.stdout.split('\n') 
            if line.strip() and not line.startswith('tools/cleanup_cefr_boilerplate.py')
        ]
    
    # Exclude files in circular_exchange directory itself
    files_to_process = [
        f for f in files_to_process 
        if 'circular_exchange' not in str(f.relative_to(project_root)).split('/')
    ]
    
    if not files_to_process:
        print("No files found with CEFR boilerplate.")
        return 0
    
    print(f"Found {len(files_to_process)} files with CEFR boilerplate")
    print("=" * 80)
    
    # Process files
    dry_run = '--dry-run' in sys.argv
    if dry_run:
        print("DRY RUN MODE - No files will be modified")
        print("=" * 80)
    
    changed_count = 0
    for filepath in files_to_process:
        changed, message = process_file(filepath, dry_run=dry_run)
        print(message)
        if changed:
            changed_count += 1
    
    print("=" * 80)
    print(f"Summary: {changed_count}/{len(files_to_process)} files {'would be' if dry_run else 'were'} modified")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
