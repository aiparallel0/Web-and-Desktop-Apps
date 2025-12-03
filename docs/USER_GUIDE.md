# Receipt Extractor User Guide

## Introduction

Receipt Extractor Pro is an AI-powered platform for extracting structured data from receipt images. This guide covers all features and usage scenarios.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Single Receipt Extraction](#single-receipt-extraction)
3. [Batch Processing](#batch-processing)
4. [Model Selection](#model-selection)
5. [Model Finetuning](#model-finetuning)
6. [Exporting Data](#exporting-data)
7. [Cloud Storage Integration](#cloud-storage-integration)
8. [Subscription Plans](#subscription-plans)
9. [Troubleshooting](#troubleshooting)

---

## Getting Started

### System Requirements

- Modern web browser (Chrome, Firefox, Safari, Edge)
- Internet connection
- For local processing: 4GB RAM minimum, 8GB+ recommended

### Creating an Account

1. Navigate to the Receipt Extractor website
2. Click "Sign Up"
3. Enter your email and create a strong password
4. Verify your email address
5. Complete your profile (optional)

### Quick Start

1. Log in to your account
2. Click "Extract" tab
3. Upload a receipt image (drag & drop or click to select)
4. Click "Extract Receipt Data"
5. View and export your results

---

## Single Receipt Extraction

### Uploading Images

**Supported Formats:**
- JPEG/JPG
- PNG
- BMP
- TIFF
- WebP

**Maximum File Size:** 100MB (varies by plan)

**Best Practices:**
- Use clear, well-lit images
- Ensure text is legible
- Avoid blurry or skewed images
- Crop to show just the receipt

### Understanding Results

After extraction, you'll see:

**Store Information:**
- Store name
- Address
- Phone number

**Transaction Details:**
- Date and time
- Total amount
- Tax amount
- Payment method

**Line Items:**
- Item name
- Quantity
- Unit price
- Total price

**Confidence Score:** 
Shows how confident the AI is in its extraction (0-100%)

### Editing Results

If extraction isn't perfect, you can:
1. Click on any field to edit
2. Make corrections
3. Save changes

This feedback helps improve future extractions.

---

## Batch Processing

Process multiple receipts at once for higher efficiency.

### Local Batch Upload

1. Go to "Batch Processing" tab
2. Click "Select Multiple Images"
3. Choose your receipt images (up to 100 at once)
4. Select processing options:
   - Single model or all models
   - Output format
5. Click "Process All Images"

### Using All Models

Enable "Extract with ALL models" to:
- Compare results from different AI models
- Get the best possible extraction
- Identify which model works best for your receipts

### Batch Results

Results are displayed as:
- Summary view (quick overview)
- Detailed view (per-receipt)
- Export all results as JSON/CSV

---

## Model Selection

Receipt Extractor offers multiple AI models optimized for different scenarios.

### Available Models

| Model | Best For | Speed |
|-------|----------|-------|
| **EasyOCR** | General receipts, printed text | Fast |
| **Tesseract** | Clear, typed text | Very Fast |
| **Donut CORD** | Complex layouts, structured data | Medium |
| **Florence V2** | Multi-language, diverse formats | Slower |
| **PaddleOCR** | Chinese/Asian text | Fast |

### Choosing the Right Model

**For standard US receipts:** EasyOCR or Tesseract

**For complex receipts:** Donut CORD

**For international receipts:** Florence V2 or PaddleOCR

**For handwritten notes:** Florence V2

### Model Performance Tips

1. Try different models if extraction quality is poor
2. Use "Extract with ALL models" to find the best one
3. Consider finetuning for consistent receipt types

---

## Model Finetuning

Improve extraction accuracy by training models on your specific receipts.

### When to Finetune

- Processing similar receipt types regularly
- Need higher accuracy for specific stores
- Working with unique receipt formats

### Preparing Training Data

1. Collect 20-50 sample receipts
2. Ensure variety within your receipt type
3. Include both good and challenging examples

### Starting a Finetuning Job

1. Go to "Finetune Model" tab
2. Select base model (recommended: Donut CORD)
3. Choose training mode:
   - **Local:** Uses your computer's GPU
   - **Cloud:** Uses remote GPU services

### Training Configuration

| Parameter | Recommended | Description |
|-----------|-------------|-------------|
| Epochs | 3-5 | Number of training passes |
| Batch Size | 4-8 | Images per batch |
| Learning Rate | 0.00005 | Training speed |

### Monitoring Training

- Progress bar shows completion percentage
- Training metrics displayed in real-time
- Estimated time remaining

### Using Finetuned Models

1. Click "Export Model" when training completes
2. Download the model ZIP file
3. Contact support to deploy custom model

---

## Exporting Data

### Export Formats

**JSON:**
- Complete structured data
- Best for programmatic use
- Includes all metadata

**CSV:**
- Spreadsheet compatible
- Line items as rows
- Easy to import to Excel

**TXT:**
- Human-readable format
- Simple text report

### Batch Export

For batch processing:
1. Process all images
2. Click "Export All Results"
3. Choose format
4. Download file

### API Export

For automation, use the API:
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "image=@receipt.jpg" \
  https://api.receiptextractor.com/api/extract
```

---

## Cloud Storage Integration

Connect cloud storage to process receipts directly.

### Supported Providers

- **Google Drive** - OAuth authentication
- **Dropbox** - App access token
- **AWS S3** - Access key credentials

### Setup

1. Go to Batch Processing > Cloud Storage
2. Click your provider
3. Authorize access (OAuth) or enter credentials
4. Browse and select files

### Security

- Credentials are encrypted at rest
- OAuth tokens expire automatically
- You can revoke access anytime

---

## Subscription Plans

### Free Plan
- 10 receipts/month
- Basic models only
- Community support

### Pro Plan ($19/month)
- 500 receipts/month
- All models
- API access
- Email support

### Business Plan ($49/month)
- 2,000 receipts/month
- Priority processing
- Custom model finetuning
- Priority support

### Enterprise
- Unlimited processing
- Dedicated support
- SLA guarantee
- Custom integrations

### Upgrading

1. Go to Account > Subscription
2. Click "Upgrade"
3. Select new plan
4. Complete payment

---

## Troubleshooting

### Poor Extraction Quality

**Problem:** Extracted data is incomplete or incorrect

**Solutions:**
1. Try a different model
2. Improve image quality
3. Crop to receipt area only
4. Consider finetuning for your receipt type

### Upload Failures

**Problem:** Image won't upload

**Check:**
- File format (JPG, PNG, BMP, TIFF)
- File size (under 100MB)
- Internet connection

### Slow Processing

**Problem:** Extraction takes too long

**Solutions:**
- Use a faster model (EasyOCR, Tesseract)
- Reduce image size
- Check your internet connection

### Authentication Issues

**Problem:** Can't log in or token expired

**Solutions:**
1. Clear browser cache
2. Try password reset
3. Check if cookies are enabled
4. Contact support

### Rate Limit Exceeded

**Problem:** 429 error

**Solutions:**
- Wait for limit to reset
- Upgrade your plan
- Batch your requests

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + O` | Open file picker |
| `Ctrl/Cmd + E` | Extract current image |
| `Ctrl/Cmd + S` | Save/Export results |
| `Tab` | Navigate between tabs |
| `Esc` | Close modals |

---

## Support

### Getting Help

- **Documentation:** docs.receiptextractor.com
- **Email:** support@receiptextractor.com
- **Community:** community.receiptextractor.com

### Reporting Issues

When reporting issues, include:
1. Screenshot of the problem
2. Receipt image (if applicable)
3. Model used
4. Error message

---

## Privacy & Security

- All data is encrypted in transit (TLS 1.3)
- Images are deleted after processing (optional retention)
- SOC 2 Type II compliant
- GDPR compliant

See our Privacy Policy for details.
