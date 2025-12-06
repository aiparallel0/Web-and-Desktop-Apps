# Batch Receipt OCR Processor

## Overview

The batch receipt processor (`batch_receipt_processor.py`) is a robust OCR tool that processes all receipt images in the repository root and exports structured data to a single JSON file. This is designed for development purposes to extract text from multiple receipt images without exceptions.

## Features

✅ **Robust Processing**: Handles exceptions gracefully - continues processing even if individual images fail  
✅ **Comprehensive Extraction**: Extracts items, dates, company names, totals, taxes, addresses, and phone numbers  
✅ **Progress Tracking**: Saves progress every 5 images to prevent data loss  
✅ **Detailed Logging**: Provides progress updates and error reporting  
✅ **JSON Export**: Exports all results to a single, well-structured JSON file  

## Usage

### Basic Usage

```bash
# Process all receipt images in the project root
python tools/scripts/batch_receipt_processor.py
```

This will:
- Find all .jpg/.JPG files in the project root (0.jpg through 19.jpg, etc.)
- Process each image using Tesseract OCR
- Export results to `receipt_extractions.json`

### Advanced Options

```bash
# Specify custom output file
python tools/scripts/batch_receipt_processor.py --output my_receipts.json

# Use a different OCR model
python tools/scripts/batch_receipt_processor.py --model tesseract
python tools/scripts/batch_receipt_processor.py --model easyocr
python tools/scripts/batch_receipt_processor.py --model paddleocr

# Enable verbose debug logging
python tools/scripts/batch_receipt_processor.py --verbose

# Combine options
python tools/scripts/batch_receipt_processor.py --output data.json --model tesseract --verbose
```

### Help

```bash
python tools/scripts/batch_receipt_processor.py --help
```

## Output Format

The output JSON file contains:

### Metadata Section
```json
{
  "metadata": {
    "processed_at": "2025-12-06T09:54:02.727949",
    "model_used": "tesseract",
    "total_images": 20,
    "successful_extractions": 20,
    "failed_extractions": 0,
    "success_rate": 1.0,
    "total_items_extracted": 86,
    "images_with_company_name": 20,
    "images_with_date": 15,
    "images_with_total": 13
  }
}
```

### Receipts Array
```json
{
  "receipts": [
    {
      "image_file": "0.jpg",
      "image_path": "/full/path/to/0.jpg",
      "success": true,
      "error": null,
      "company_name": "WALMART",
      "date": null,
      "total": "5.11",
      "subtotal": "5.11",
      "tax": null,
      "items": [
        {
          "name": "FRAP",
          "quantity": 1,
          "unit_price": null,
          "price": "5.48",
          "category": null,
          "sku": null
        }
      ],
      "address": "ST# 5748 OP# 00000158 TE# 14 TR# 03178",
      "phone": "0000000040",
      "payment_method": null,
      "confidence_score": 1.0,
      "model_used": "Tesseract OCR (PSM 3 (auto) on original)",
      "processing_time_seconds": 9.87,
      "raw_text_preview": null
    }
  ]
}
```

## Extracted Fields

For each receipt, the processor attempts to extract:

| Field | Description | Example |
|-------|-------------|---------|
| `company_name` | Store/merchant name | "WALMART", "TRADER JOE'S" |
| `date` | Transaction date | "06-28-2014", "2024-01-15" |
| `total` | Total amount | "38.68", "5.11" |
| `subtotal` | Subtotal amount | "42.50" |
| `tax` | Tax amount | "3.17" |
| `items` | Array of line items | See below |
| `address` | Store address | "123 Main St, City, ST 12345" |
| `phone` | Store phone number | "555-1234" |
| `payment_method` | Payment method | "VISA", "CASH" |
| `confidence_score` | OCR confidence (0-1) | 0.95, 1.0 |
| `model_used` | OCR model/mode used | "Tesseract OCR (PSM 3)" |
| `processing_time_seconds` | Time to process | 9.87 |

### Line Item Fields

Each item in the `items` array contains:

| Field | Description | Example |
|-------|-------------|---------|
| `name` | Product name | "ORGANIC COFFEE" |
| `quantity` | Quantity purchased | 2 |
| `unit_price` | Price per unit | "3.50" |
| `price` | Total price for item | "7.00" |
| `category` | Product category | "Beverages" |
| `sku` | Stock keeping unit | "SKU123456" |

## Performance

- **Processing Time**: ~30 seconds per image (varies by image size and complexity)
- **Success Rate**: Typically 90-100% for clear receipt images
- **Total Processing Time**: ~10 minutes for 20 receipts

## Progress Tracking

The processor saves progress every 5 images to `receipt_processing_progress.json`. This file is automatically deleted when processing completes successfully.

If processing is interrupted:
1. Check `receipt_processing_progress.json` for partial results
2. Re-run the processor - it will start from the beginning
3. The final `receipt_extractions.json` will only be created when all images are processed

## Error Handling

The processor is designed to continue processing even if individual images fail:

- **Import errors**: Returns metadata with error information
- **Image processing errors**: Logged with traceback, processing continues
- **OCR extraction errors**: Recorded in the receipt's `error` field, processing continues

Example failed receipt:
```json
{
  "image_file": "problematic.jpg",
  "success": false,
  "error": "FileNotFoundError: Image not found",
  "traceback": "...",
  "company_name": null,
  "items": []
}
```

## Requirements

### System Requirements
- Python 3.8+
- Tesseract OCR installed (for tesseract model)
  - Linux: `sudo apt-get install tesseract-ocr`
  - macOS: `brew install tesseract`
  - Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

### Python Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
- pytesseract>=0.3.10
- pillow>=9.0.0
- opencv-python-headless
- numpy

## Integration with CEFR

This script integrates with the Circular Exchange Framework (CEFR) for:
- Module registration and dependency tracking
- Dynamic parameter configuration
- Automatic optimization based on extraction results

## Troubleshooting

### "Tesseract not installed" error
Install Tesseract OCR for your operating system (see Requirements above).

### "No module named 'cv2'" error
Install OpenCV: `pip install opencv-python-headless`

### Processing is very slow
- Reduce image resolution before processing
- Use `--model tesseract` (fastest option)
- The processor tries multiple OCR modes for best results - this is normal

### No receipts found
Ensure .jpg files are in the project root directory, not in subdirectories.

### Low success rate
- Ensure images are clear and well-lit
- Check image orientation (should be upright)
- Try different OCR models
- Enable verbose logging: `--verbose`

## Example Results

After processing 20 receipt images:

```
Results Summary:
  Total Images: 20
  Successful: 20 (100.0%)
  Failed: 0
  Total Items Extracted: 86
  Images with Company Name: 20
  Images with Date: 15
  Images with Total: 13
```

## Development Material

The generated JSON file is intended for development purposes:
- Testing OCR extraction algorithms
- Training machine learning models
- Evaluating extraction accuracy
- Creating test datasets
- Debugging receipt parsing logic

## Related Files

- **Main Script**: `tools/scripts/batch_receipt_processor.py`
- **OCR Processor**: `shared/models/ocr_processor.py`
- **Data Models**: `shared/utils/data.py`
- **OCR Common Utils**: `shared/models/ocr_common.py`

## Support

For issues or questions:
1. Check the troubleshooting section
2. Enable verbose logging: `--verbose`
3. Review the error messages and tracebacks
4. Consult the main README.md for OCR configuration options
