#!/usr/bin/env python3
"""
Import Validation Tool

Validates that all imports actually work before deployment.

Usage:
    python tools/cefr/import_validator.py
    
Exit codes:
    0 - All imports validated successfully
    1 - One or more imports failed
"""

import sys
import importlib
from pathlib import Path
from typing import List, Tuple


def validate_critical_imports() -> List[Tuple[str, str]]:
    """
    Test critical imports.
    
    Returns:
        List of (module_name, error_message) for failed imports
    """
    
    critical_modules = [
        # Shared utilities
        'shared.utils.data',
        'shared.utils.helpers',
        'shared.utils.image',
        'shared.utils.logging',
        'shared.utils.pricing',
        'shared.utils.validation',
        
        # Model processing
        'shared.models.manager',
        'shared.models.engine',
        'shared.models.schemas',
        
        # Backend core
        'web.backend.app',
        'web.backend.database',
        'web.backend.config',
        
        # Authentication
        'web.backend.auth',
    ]
    
    failures = []
    
    print("Validating critical imports...")
    print("=" * 60)
    
    for module_name in critical_modules:
        try:
            importlib.import_module(module_name)
            print(f"✅ {module_name}")
        except ImportError as e:
            failures.append((module_name, str(e)))
            print(f"❌ {module_name}: {e}")
        except Exception as e:
            # Other errors (not import errors)
            failures.append((module_name, f"Unexpected error: {str(e)}"))
            print(f"⚠️  {module_name}: Unexpected error: {e}")
    
    return failures


def validate_optional_imports() -> List[Tuple[str, str]]:
    """
    Test optional/nice-to-have imports.
    
    Returns:
        List of (module_name, error_message) for failed imports
    """
    
    optional_modules = [
        # OCR engines (at least one should work)
        ('easyocr', 'EasyOCR'),
        ('pytesseract', 'Tesseract'),
        
        # ML frameworks (optional for production)
        ('torch', 'PyTorch'),
        ('transformers', 'HuggingFace Transformers'),
        
        # System monitoring
        ('psutil', 'psutil'),
    ]
    
    failures = []
    
    print("\nValidating optional imports...")
    print("=" * 60)
    
    for module_name, display_name in optional_modules:
        try:
            importlib.import_module(module_name)
            print(f"✅ {display_name} ({module_name})")
        except ImportError as e:
            failures.append((display_name, str(e)))
            print(f"⚠️  {display_name} ({module_name}): Not installed")
    
    return failures


def main():
    """Main entry point"""
    print("=" * 60)
    print("IMPORT VALIDATION")
    print("=" * 60)
    print()
    
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    # Validate critical imports
    critical_failures = validate_critical_imports()
    
    # Validate optional imports
    optional_failures = validate_optional_imports()
    
    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if critical_failures:
        print(f"❌ {len(critical_failures)} critical import(s) failed:")
        for module, error in critical_failures:
            print(f"   - {module}")
        print()
        print("Action Required: Fix critical import errors before deployment")
        sys.exit(1)
    else:
        print("✅ All critical imports validated")
    
    if optional_failures:
        print(f"⚠️  {len(optional_failures)} optional import(s) not available:")
        for module, error in optional_failures:
            print(f"   - {module}")
        print("\nNote: Optional imports are not required for core functionality")
    
    print()
    print("✅ Import validation complete")
    sys.exit(0)


if __name__ == '__main__':
    main()
