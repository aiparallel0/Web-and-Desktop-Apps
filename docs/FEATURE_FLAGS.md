# Feature Flags - Receipt Extractor

> **Version:** 1.0.0  
> **Last Updated:** 2025-12-08  
> **Purpose:** Control optional features for MVP vs full deployment

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Quick Start - MVP Mode](#quick-start---mvp-mode)
3. [Quick Start - Full Mode](#quick-start---full-mode)
4. [Available Feature Flags](#available-feature-flags)
5. [Configuration Priority](#configuration-priority)
6. [Feature Details](#feature-details)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## Overview

Receipt Extractor uses feature flags to enable or disable optional cloud integrations and advanced features. This allows you to:

- **MVP Mode**: Launch quickly with minimal dependencies (local-only features)
- **Full Mode**: Enable all cloud integrations and advanced capabilities
- **Hybrid Mode**: Enable only the features you need

**Default Configuration**: All optional features are **disabled** by default for easy MVP deployment.

---

## Quick Start - MVP Mode

**MVP Mode** runs with all cloud features disabled, using only local processing.

### Step 1: Copy Environment Files

```bash
cp .env.example .env
cp web/backend/.env.example web/backend/.env
```

### Step 2: Verify MVP Settings

The default `.env.example` already has MVP settings. Verify these lines:

```bash
# CEFR Framework - Disabled for MVP
ENABLE_CEFR=false

# Cloud Storage - Disabled for MVP
ENABLE_S3_STORAGE=false
ENABLE_GDRIVE_STORAGE=false
ENABLE_DROPBOX_STORAGE=false

# Cloud Training - Disabled for MVP
ENABLE_HF_TRAINING=false
ENABLE_REPLICATE_TRAINING=false
ENABLE_RUNPOD_TRAINING=false
```

### Step 3: Start the Application

```bash
./launcher.sh dev
# OR
python start.py
```

### What's Included in MVP Mode

✅ **Enabled Features:**
- All 7 OCR models (Tesseract, EasyOCR, PaddleOCR, Donut, Florence-2, CRAFT, Spatial)
- Local receipt processing
- Web and Desktop applications
- User authentication (JWT)
- Database (SQLite or PostgreSQL)
- Batch processing
- Export to JSON/CSV/TXT
- Real-time progress tracking

❌ **Disabled Features:**
- Circular Exchange Framework (CEFR) auto-tuning
- AWS S3 cloud storage
- Google Drive integration
- Dropbox integration
- HuggingFace cloud training
- Replicate cloud training
- RunPod cloud training

---

## Quick Start - Full Mode

**Full Mode** enables all cloud integrations and advanced features.

### Step 1: Copy Environment Files

```bash
cp .env.example .env
cp web/backend/.env.example web/backend/.env
```

### Step 2: Enable All Features

Edit `.env` and `web/backend/.env` to enable features:

```bash
# CEFR Framework - Enable for auto-tuning
ENABLE_CEFR=true

# Cloud Storage - Enable as needed
ENABLE_S3_STORAGE=true
ENABLE_GDRIVE_STORAGE=true
ENABLE_DROPBOX_STORAGE=true

# Cloud Training - Enable as needed
ENABLE_HF_TRAINING=true
ENABLE_REPLICATE_TRAINING=true
ENABLE_RUNPOD_TRAINING=true
```

### Step 3: Configure Cloud Credentials

Add your API keys and credentials to `.env`:

```bash
# AWS S3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET=your-bucket-name

# Google Drive
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Dropbox
DROPBOX_APP_KEY=your-app-key
DROPBOX_APP_SECRET=your-app-secret

# HuggingFace
HUGGINGFACE_TOKEN=hf_xxxxxxxxxxxxx

# Replicate
REPLICATE_API_TOKEN=r8_xxxxxxxxxxxxx

# RunPod
RUNPOD_API_KEY=xxxxxxxxxxxxx
```

### Step 4: Start the Application

```bash
./launcher.sh dev
```

---

## Available Feature Flags

### CEFR Framework

| Flag | Default | Description | Dependencies |
|------|---------|-------------|--------------|
| `ENABLE_CEFR` | `false` | Enable Circular Exchange Framework for auto-tuning and runtime optimization | None |

**When to Enable:**
- You want automatic parameter tuning based on production metrics
- You need runtime configuration updates without code changes
- You want AI-powered refactoring suggestions

**When to Disable (MVP):**
- You want minimal complexity
- You don't need auto-tuning features
- You prefer static configuration

---

### Cloud Storage

| Flag | Default | Description | Dependencies |
|------|---------|-------------|--------------|
| `ENABLE_S3_STORAGE` | `false` | Enable AWS S3 storage integration | AWS credentials |
| `ENABLE_GDRIVE_STORAGE` | `false` | Enable Google Drive integration | Google OAuth credentials |
| `ENABLE_DROPBOX_STORAGE` | `false` | Enable Dropbox integration | Dropbox app credentials |

**Required Credentials:**

**S3 Storage:**
```bash
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET=...
AWS_REGION=us-east-1
```

**Google Drive:**
```bash
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_DRIVE_REDIRECT_URI=http://localhost:5000/auth/google/callback
```

**Dropbox:**
```bash
DROPBOX_APP_KEY=...
DROPBOX_APP_SECRET=...
```

**Error Handling:**

When a disabled storage provider is requested, you'll receive:

```json
{
  "error": "S3 storage is disabled. Set ENABLE_S3_STORAGE=true in .env to enable this feature."
}
```

---

### Cloud Training

| Flag | Default | Description | Dependencies |
|------|---------|-------------|--------------|
| `ENABLE_HF_TRAINING` | `false` | Enable HuggingFace cloud training | HuggingFace API token |
| `ENABLE_REPLICATE_TRAINING` | `false` | Enable Replicate cloud training | Replicate API token |
| `ENABLE_RUNPOD_TRAINING` | `false` | Enable RunPod GPU training | RunPod API key |

**Required Credentials:**

**HuggingFace:**
```bash
HUGGINGFACE_TOKEN=hf_xxxxxxxxxxxxx
```

**Replicate:**
```bash
REPLICATE_API_TOKEN=r8_xxxxxxxxxxxxx
```

**RunPod:**
```bash
RUNPOD_API_KEY=xxxxxxxxxxxxx
```

**Training Costs:**
- HuggingFace: Free tier available, ~$0.60/hour for A10G GPU
- Replicate: ~$0.80/hour for training
- RunPod: ~$0.50-$2.00/hour depending on GPU type

**Error Handling:**

When a disabled training provider is requested, you'll receive:

```json
{
  "error": "HUGGINGFACE training is disabled. Set ENABLE_HF_TRAINING=true in .env to enable this feature."
}
```

---

## Configuration Priority

Feature flags are read from environment variables with the following priority:

1. **Environment Variables** (highest priority)
   - Set directly in your shell: `export ENABLE_CEFR=true`
   
2. **`.env` File**
   - Root `.env` file or `web/backend/.env`
   
3. **Default Values** (lowest priority)
   - Built-in defaults: `false` for all optional features

### Example

```bash
# Priority 1: Shell environment (highest)
export ENABLE_CEFR=true

# Priority 2: .env file
ENABLE_CEFR=false  # This will be overridden by shell env

# Priority 3: Code defaults
# If not set anywhere, defaults to false
```

---

## Feature Details

### CEFR Framework (Circular Exchange Framework)

**Purpose:** Auto-tuning and runtime optimization framework

**What it does:**
- Automatically tunes model parameters based on production metrics
- Provides runtime configuration updates without code changes
- Generates AI-powered refactoring suggestions
- Tracks dependency changes across modules
- Enables A/B testing of configurations

**Performance Impact:**
- Minimal overhead when enabled
- No impact when disabled

**Files Affected:**
- `shared/circular_exchange/core/project_config.py`
- All modules that register with CEFR

**Disabling CEFR:**
When disabled, the framework initialization is skipped:
- Module registration returns immediately
- No configuration packages are created
- No performance monitoring
- No auto-tuning

---

### Cloud Storage Integration

**Purpose:** Store receipt images and data in cloud storage

**Supported Providers:**

1. **AWS S3**
   - Presigned URLs for secure access
   - Lifecycle policies for automatic cleanup
   - Supports versioning and encryption
   
2. **Google Drive**
   - OAuth 2.0 authentication
   - Folder synchronization
   - Shared link generation
   
3. **Dropbox**
   - Temporary download links
   - Retry logic for reliability
   - Webhook support

**Usage Example:**

```python
from web.backend.storage import StorageFactory

# This will raise ValueError if ENABLE_S3_STORAGE=false
try:
    storage = StorageFactory.get_handler('s3')
    url = storage.upload_file(file_path, 's3://bucket/key')
except ValueError as e:
    print(f"Storage disabled: {e}")
```

**MVP Alternative:**
- Store files locally in `uploads/` directory
- Use database to track file locations
- Implement manual cleanup policies

---

### Cloud Training Integration

**Purpose:** Train and fine-tune models using cloud GPU providers

**Supported Providers:**

1. **HuggingFace Spaces**
   - Free tier available
   - Easy model sharing
   - Integrated with HF Hub
   - GPU types: T4, A10G, A100
   
2. **Replicate**
   - Pay-per-use pricing
   - Quick training setup
   - Good for experimentation
   - GPU types: T4, A40, A100
   
3. **RunPod**
   - Cost-effective GPUs
   - Serverless options
   - Wide GPU selection
   - GPU types: A4000, A6000, A100, H100

**Usage Example:**

```python
from web.backend.training import TrainingFactory

# This will raise ValueError if ENABLE_HF_TRAINING=false
try:
    trainer = TrainingFactory.get_trainer('huggingface')
    job = trainer.start_training(config, dataset)
except ValueError as e:
    print(f"Training disabled: {e}")
```

**MVP Alternative:**
- Train models locally using PyTorch
- Use smaller batch sizes
- Consider CPU-only training for small datasets

---

## Testing

### Test with MVP Mode (All Flags Disabled)

```bash
# Ensure .env has all flags set to false
export ENABLE_CEFR=false
export ENABLE_S3_STORAGE=false
export ENABLE_GDRIVE_STORAGE=false
export ENABLE_DROPBOX_STORAGE=false
export ENABLE_HF_TRAINING=false
export ENABLE_REPLICATE_TRAINING=false
export ENABLE_RUNPOD_TRAINING=false

# Run tests
./launcher.sh test
```

### Test with Full Mode (All Flags Enabled)

```bash
# Enable all features
export ENABLE_CEFR=true
export ENABLE_S3_STORAGE=true
export ENABLE_GDRIVE_STORAGE=true
export ENABLE_DROPBOX_STORAGE=true
export ENABLE_HF_TRAINING=true
export ENABLE_REPLICATE_TRAINING=true
export ENABLE_RUNPOD_TRAINING=true

# Configure credentials in .env

# Run tests
./launcher.sh test
```

### Test Mixed Configuration

```bash
# Example: Enable CEFR but disable cloud features
export ENABLE_CEFR=true
export ENABLE_S3_STORAGE=false
export ENABLE_GDRIVE_STORAGE=false
export ENABLE_DROPBOX_STORAGE=false
export ENABLE_HF_TRAINING=true
export ENABLE_REPLICATE_TRAINING=false
export ENABLE_RUNPOD_TRAINING=false

# Run tests
./launcher.sh test
```

### Verify Feature Status

```python
# Check if features are enabled
from web.backend.storage import StorageFactory
from web.backend.training import TrainingFactory

# Check storage providers
print("S3 available:", StorageFactory.is_provider_available('s3'))
print("GDrive available:", StorageFactory.is_provider_available('gdrive'))
print("Dropbox available:", StorageFactory.is_provider_available('dropbox'))

# Check training providers
print("HuggingFace available:", TrainingFactory.is_provider_available('huggingface'))
print("Replicate available:", TrainingFactory.is_provider_available('replicate'))
print("RunPod available:", TrainingFactory.is_provider_available('runpod'))
```

---

## Troubleshooting

### Issue: "Feature disabled" Error

**Problem:**
```
ValueError: S3 storage is disabled. Set ENABLE_S3_STORAGE=true in .env to enable this feature.
```

**Solution:**
1. Edit `.env` or `web/backend/.env`
2. Set `ENABLE_S3_STORAGE=true`
3. Add required credentials (AWS_ACCESS_KEY_ID, etc.)
4. Restart the application

---

### Issue: CEFR Not Initializing

**Problem:**
CEFR framework doesn't seem to be working even with `ENABLE_CEFR=true`

**Solution:**
1. Check that environment variable is properly set:
   ```bash
   echo $ENABLE_CEFR  # Should print: true
   ```
2. Verify `.env` file is in the correct location
3. Restart the application to reload environment
4. Check logs for CEFR initialization messages:
   ```
   INFO - CEFR Framework is enabled. Initializing...
   ```

---

### Issue: Can't Find .env File

**Problem:**
Application isn't reading feature flags from `.env`

**Solution:**
1. Ensure `.env` exists in project root:
   ```bash
   ls -la .env
   ```
2. Copy from example if missing:
   ```bash
   cp .env.example .env
   ```
3. For backend, also check `web/backend/.env`:
   ```bash
   cp web/backend/.env.example web/backend/.env
   ```

---

### Issue: Feature Enabled but Not Working

**Problem:**
Feature is enabled but still getting errors

**Solution:**
1. **Check credentials are configured:**
   ```bash
   # For S3
   echo $AWS_ACCESS_KEY_ID
   echo $AWS_SECRET_ACCESS_KEY
   
   # For HuggingFace
   echo $HUGGINGFACE_TOKEN
   ```

2. **Verify credentials are valid:**
   - Test AWS credentials: `aws s3 ls` (requires AWS CLI)
   - Test HuggingFace token: Check https://huggingface.co/settings/tokens
   
3. **Check application logs:**
   ```bash
   tail -f logs/application.log
   ```

---

### Issue: Tests Failing with Feature Flags

**Problem:**
Tests pass with all features disabled but fail when enabled

**Solution:**
1. **Ensure test credentials are set:**
   - Use test/sandbox accounts for cloud services
   - Never use production credentials in tests
   
2. **Mock external services in tests:**
   ```python
   # In conftest.py or test file
   @pytest.fixture
   def mock_s3():
       with mock.patch('boto3.client'):
           yield
   ```

3. **Skip tests that require credentials:**
   ```python
   @pytest.mark.skipif(
       not os.getenv('ENABLE_S3_STORAGE') == 'true',
       reason="S3 storage not enabled"
   )
   def test_s3_upload():
       pass
   ```

---

## Best Practices

### Development Environment

```bash
# Use MVP mode for local development
ENABLE_CEFR=false
ENABLE_S3_STORAGE=false
ENABLE_GDRIVE_STORAGE=false
ENABLE_DROPBOX_STORAGE=false
ENABLE_HF_TRAINING=false
ENABLE_REPLICATE_TRAINING=false
ENABLE_RUNPOD_TRAINING=false
```

### Staging Environment

```bash
# Enable features you want to test
ENABLE_CEFR=true
ENABLE_S3_STORAGE=true  # Use test bucket
ENABLE_GDRIVE_STORAGE=false
ENABLE_DROPBOX_STORAGE=false
ENABLE_HF_TRAINING=true  # Use test account
ENABLE_REPLICATE_TRAINING=false
ENABLE_RUNPOD_TRAINING=false
```

### Production Environment

```bash
# Enable all required features with production credentials
ENABLE_CEFR=true
ENABLE_S3_STORAGE=true
ENABLE_GDRIVE_STORAGE=true
ENABLE_DROPBOX_STORAGE=true
ENABLE_HF_TRAINING=true
ENABLE_REPLICATE_TRAINING=true
ENABLE_RUNPOD_TRAINING=true
```

### Security Recommendations

1. **Never commit credentials:**
   - Add `.env` to `.gitignore` (already done)
   - Use environment-specific `.env` files
   
2. **Use least-privilege access:**
   - Create IAM users with minimal required permissions
   - Use read-only tokens where possible
   
3. **Rotate credentials regularly:**
   - Change API keys every 90 days
   - Revoke unused credentials
   
4. **Monitor usage:**
   - Set up billing alerts for cloud services
   - Track API usage to detect anomalies

---

## Migration Guide

### From No Feature Flags to MVP Mode

If you have an existing deployment without feature flags:

1. **Backup your current .env:**
   ```bash
   cp .env .env.backup
   ```

2. **Update .env with feature flags:**
   ```bash
   # Add to .env
   ENABLE_CEFR=false
   ENABLE_S3_STORAGE=false
   ENABLE_GDRIVE_STORAGE=false
   ENABLE_DROPBOX_STORAGE=false
   ENABLE_HF_TRAINING=false
   ENABLE_REPLICATE_TRAINING=false
   ENABLE_RUNPOD_TRAINING=false
   ```

3. **Test the application:**
   ```bash
   ./launcher.sh test
   ```

4. **Gradually enable features:**
   - Enable one feature at a time
   - Test after each change
   - Monitor for issues

### From MVP Mode to Full Mode

1. **Enable features one at a time:**
   ```bash
   # Start with CEFR
   ENABLE_CEFR=true
   
   # Test
   ./launcher.sh test
   
   # Then enable storage
   ENABLE_S3_STORAGE=true
   
   # Test again
   ./launcher.sh test
   ```

2. **Configure credentials as you go:**
   - Add credentials for each enabled feature
   - Test integration before moving to next feature

3. **Monitor performance:**
   - Watch for increased resource usage
   - Check logs for errors
   - Monitor API costs

---

## FAQ

**Q: Do I need to enable CEFR for the app to work?**  
A: No. CEFR is optional and disabled by default. All core features work without it.

**Q: Can I enable cloud storage but disable cloud training?**  
A: Yes. All feature flags are independent. Enable only what you need.

**Q: What happens if I request a disabled feature?**  
A: You'll receive a clear error message indicating the feature is disabled and how to enable it.

**Q: Are feature flags checked at startup or runtime?**  
A: They're checked when the feature is first requested, allowing for dynamic configuration.

**Q: Can I change feature flags without restarting?**  
A: No. You must restart the application after changing feature flags in `.env`.

**Q: Do feature flags affect the 7 OCR models?**  
A: No. All 7 OCR models are always available regardless of feature flag settings.

---

## Related Documentation

- [README.md](../README.md) - Project overview and quick start
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
- [ROADMAP.md](../ROADMAP.md) - Planned features and integrations
- [API.md](API.md) - API documentation

---

**Need Help?**

If you encounter issues with feature flags:
1. Check this documentation
2. Review application logs
3. Open an issue on GitHub with:
   - Your `.env` configuration (redact credentials!)
   - Error messages
   - Application logs
