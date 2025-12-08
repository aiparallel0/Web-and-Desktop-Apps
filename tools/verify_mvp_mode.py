#!/usr/bin/env python3
"""
MVP Mode Verification Script

This script verifies that the feature flags are working correctly
and demonstrates the difference between MVP mode and Full mode.
"""

import os
import sys


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_cefr():
    """Check CEFR framework status."""
    print("\n📊 CEFR Framework Status:")
    print("-" * 70)
    
    from shared.circular_exchange.core.project_config import _is_cefr_enabled
    enabled = _is_cefr_enabled()
    
    status = "✅ ENABLED" if enabled else "❌ DISABLED"
    print(f"  ENABLE_CEFR = {os.getenv('ENABLE_CEFR', 'not set')} → {status}")
    
    if enabled:
        print("  Features: Auto-tuning, runtime optimization, refactoring suggestions")
    else:
        print("  Mode: MVP - Static configuration only")
    
    return enabled


def check_storage():
    """Check cloud storage providers status."""
    print("\n☁️  Cloud Storage Providers:")
    print("-" * 70)
    
    providers = [
        ('S3 (AWS)', 's3', 'ENABLE_S3_STORAGE'),
        ('Google Drive', 'gdrive', 'ENABLE_GDRIVE_STORAGE'),
        ('Dropbox', 'dropbox', 'ENABLE_DROPBOX_STORAGE'),
    ]
    
    enabled_count = 0
    
    try:
        from web.backend.storage import StorageFactory
        
        for name, provider, flag in providers:
            flag_value = os.getenv(flag, 'not set')
            
            try:
                # Try to get handler - will fail if disabled
                StorageFactory.get_handler(provider)
                # If we get here, provider is enabled (but may lack credentials)
                status = "✅ ENABLED"
                enabled_count += 1
            except ValueError as e:
                if "disabled" in str(e).lower():
                    status = "❌ DISABLED"
                else:
                    status = "⚠️  ENABLED (no credentials)"
                    enabled_count += 1
            except Exception as e:
                status = f"⚠️  ERROR: {type(e).__name__}"
            
            print(f"  {name:20} {flag:30} → {status}")
    except ImportError as e:
        # If we can't import storage module, check environment variables
        print("  ⚠️  Cannot import storage module (missing dependencies)")
        print("  Checking environment variables instead...")
        for name, provider, flag in providers:
            flag_value = os.getenv(flag, 'false').lower()
            if flag_value in ('true', '1', 'yes'):
                status = "✅ ENABLED (via env var)"
                enabled_count += 1
            else:
                status = "❌ DISABLED (via env var)"
            print(f"  {name:20} {flag:30} → {status}")
    
    if enabled_count == 0:
        print("\n  Mode: MVP - Local storage only")
    
    return enabled_count


def check_training():
    """Check cloud training providers status."""
    print("\n🚀 Cloud Training Providers:")
    print("-" * 70)
    
    providers = [
        ('HuggingFace', 'huggingface', 'ENABLE_HF_TRAINING'),
        ('Replicate', 'replicate', 'ENABLE_REPLICATE_TRAINING'),
        ('RunPod', 'runpod', 'ENABLE_RUNPOD_TRAINING'),
    ]
    
    enabled_count = 0
    
    try:
        from web.backend.training import TrainingFactory
        
        for name, provider, flag in providers:
            flag_value = os.getenv(flag, 'not set')
            
            try:
                # Try to get trainer - will fail if disabled
                TrainingFactory.get_trainer(provider)
                # If we get here, provider is enabled (but may lack credentials)
                status = "✅ ENABLED"
                enabled_count += 1
            except ValueError as e:
                if "disabled" in str(e).lower():
                    status = "❌ DISABLED"
                else:
                    status = "⚠️  ENABLED (no credentials)"
                    enabled_count += 1
            except Exception as e:
                status = f"⚠️  ERROR: {type(e).__name__}"
            
            print(f"  {name:20} {flag:30} → {status}")
    except ImportError as e:
        # If we can't import training module, check environment variables
        print("  ⚠️  Cannot import training module (missing dependencies)")
        print("  Checking environment variables instead...")
        for name, provider, flag in providers:
            flag_value = os.getenv(flag, 'false').lower()
            if flag_value in ('true', '1', 'yes'):
                status = "✅ ENABLED (via env var)"
                enabled_count += 1
            else:
                status = "❌ DISABLED (via env var)"
            print(f"  {name:20} {flag:30} → {status}")
    
    if enabled_count == 0:
        print("\n  Mode: MVP - Local training only")
    
    return enabled_count


def check_models():
    """Check that all 7 OCR models are available."""
    print("\n🔍 OCR Models Availability:")
    print("-" * 70)
    
    import os.path
    
    models = {
        'Tesseract OCR': 'shared/models/ocr.py',
        'EasyOCR': 'shared/models/ocr.py',
        'PaddleOCR': 'shared/models/ocr.py',
        'Donut (CORD)': 'shared/models/engine.py',
        'Florence-2': 'shared/models/engine.py',
        'CRAFT Detector': 'shared/models/craft_detector.py',
        'Spatial Multi-Method': 'shared/models/spatial_ocr.py'
    }
    
    all_present = True
    for name, path in models.items():
        if os.path.exists(path):
            print(f"  ✅ {name:25} ({path})")
        else:
            print(f"  ❌ {name:25} - FILE MISSING!")
            all_present = False
    
    if all_present:
        print("\n  Status: All 7 OCR models are available ✅")
    else:
        print("\n  Status: Some models are missing! ❌")
    
    return all_present


def main():
    """Main verification function."""
    print_header("Receipt Extractor - Feature Flags Verification")
    
    print("\nThis script verifies the feature flag configuration.")
    print("It shows which features are enabled/disabled.")
    
    # Check all features
    cefr_enabled = check_cefr()
    storage_enabled = check_storage()
    training_enabled = check_training()
    models_ok = check_models()
    
    # Determine mode
    print_header("Configuration Summary")
    
    total_cloud_features = storage_enabled + training_enabled
    
    if cefr_enabled == False and total_cloud_features == 0:
        mode = "MVP MODE"
        description = "Local processing only, no cloud integrations"
        emoji = "🎯"
    elif cefr_enabled and total_cloud_features >= 6:
        mode = "FULL MODE"
        description = "All features enabled, full cloud integration"
        emoji = "🚀"
    else:
        mode = "HYBRID MODE"
        description = f"Selective features ({total_cloud_features} cloud providers enabled)"
        emoji = "⚙️"
    
    print(f"\n  {emoji}  {mode}")
    print(f"  {description}")
    
    print("\n  Feature Status:")
    print(f"    • CEFR Framework:      {'✅ Enabled' if cefr_enabled else '❌ Disabled'}")
    print(f"    • Cloud Storage:       {storage_enabled}/3 providers enabled")
    print(f"    • Cloud Training:      {training_enabled}/3 providers enabled")
    print(f"    • OCR Models:          {'✅ All 7 available' if models_ok else '❌ Some missing'}")
    
    # Recommendations
    print("\n  Recommendations:")
    if mode == "MVP MODE":
        print("    ✅ Perfect for local development and testing")
        print("    ✅ No cloud credentials required")
        print("    ✅ Zero cloud service costs")
        print()
        print("    To enable cloud features:")
        print("      1. Edit .env file")
        print("      2. Set ENABLE_<FEATURE>=true")
        print("      3. Add required credentials")
        print("      4. Restart the application")
    elif mode == "FULL MODE":
        print("    ✅ All features available")
        print("    ⚠️  Ensure cloud credentials are configured")
        print("    ⚠️  Monitor cloud service costs")
    else:
        print("    ℹ️  Using selective features")
        print("    ℹ️  Consider enabling more features as needed")
    
    print_header("Verification Complete")
    
    if not models_ok:
        print("\n⚠️  WARNING: Some OCR models are missing!")
        return 1
    
    print(f"\n✅ All checks passed! Running in {mode}.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
