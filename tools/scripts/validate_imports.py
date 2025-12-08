#!/usr/bin/env python3
"""
Import Validation Script

This script validates that all critical module imports work correctly.
Run this before committing to catch import errors early.

Usage:
    python tools/scripts/validate_imports.py
"""

import sys
import importlib.util
from pathlib import Path
from typing import List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


CRITICAL_IMPORTS = [
    # CEFR Framework
    ("shared.circular_exchange", "PROJECT_CONFIG"),
    ("shared.circular_exchange", "ModuleRegistration"),
    ("shared.circular_exchange", "PackageRegistry"),
    
    # Model Schemas
    ("shared.models.schemas", "DetectionResult"),
    ("shared.models.schemas", "DetectedText"),
    ("shared.models.schemas", "BoundingBox"),
    
    # Model Engine/Processors
    ("shared.models.engine", "EasyOCRProcessor"),
    
    # Backend
    ("web.backend.app", "app"),
]


def validate_import(module_name: str, attr_name: str = None) -> Tuple[bool, str]:
    """
    Validate that a module can be imported and optionally check for an attribute.
    
    Args:
        module_name: The module to import (e.g., 'shared.models.engine')
        attr_name: Optional attribute to check (e.g., 'ExtractionEngine')
        
    Returns:
        Tuple of (success, message)
    """
    try:
        module = importlib.import_module(module_name)
        
        if attr_name:
            if not hasattr(module, attr_name):
                return False, f"Module '{module_name}' missing attribute '{attr_name}'"
        
        return True, f"✅ {module_name}" + (f".{attr_name}" if attr_name else "")
    
    except ImportError as e:
        return False, f"❌ Failed to import {module_name}: {e}"
    except Exception as e:
        return False, f"❌ Error importing {module_name}: {e}"


def find_python_files(directory: Path) -> List[Path]:
    """Find all Python files in directory."""
    return list(directory.rglob("*.py"))


def check_syntax(file_path: Path) -> Tuple[bool, str]:
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            compile(f.read(), str(file_path), 'exec')
        return True, f"✅ {file_path.relative_to(project_root)}"
    except SyntaxError as e:
        return False, f"❌ Syntax error in {file_path.relative_to(project_root)}: Line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"❌ Error checking {file_path.relative_to(project_root)}: {e}"


def main():
    """Run import validation."""
    print("🔍 Import Validation Script")
    print("=" * 60)
    
    # Check syntax of critical files first
    print("\n📝 Checking Python syntax...")
    syntax_errors = []
    critical_dirs = [
        project_root / "shared",
        project_root / "web" / "backend",
    ]
    
    for directory in critical_dirs:
        if directory.exists():
            for py_file in find_python_files(directory):
                success, message = check_syntax(py_file)
                if not success:
                    print(message)
                    syntax_errors.append(message)
    
    if syntax_errors:
        print(f"\n❌ Found {len(syntax_errors)} syntax error(s)")
        for error in syntax_errors:
            print(f"  {error}")
        return 1
    else:
        print("✅ All files have valid syntax")
    
    # Test critical imports
    print("\n📦 Validating critical imports...")
    import_failures = []
    
    for module_name, attr_name in CRITICAL_IMPORTS:
        success, message = validate_import(module_name, attr_name)
        print(f"  {message}")
        if not success:
            import_failures.append(message)
    
    # Summary
    print("\n" + "=" * 60)
    if import_failures:
        print(f"❌ Import validation FAILED ({len(import_failures)} errors)")
        print("\nFailed imports:")
        for failure in import_failures:
            print(f"  {failure}")
        return 1
    else:
        print("✅ All critical imports validated successfully")
        return 0


if __name__ == "__main__":
    sys.exit(main())
