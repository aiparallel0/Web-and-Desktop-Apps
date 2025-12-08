# Example Receipt Images

This directory contains sample receipt images for testing and demonstration purposes.

## Contents

- **0.jpg - 19.jpg**: Sample receipt images in various formats and qualities
- Used for testing OCR extraction algorithms
- Used for benchmarking model performance
- Used for integration testing

## Usage

### Testing Individual Images

```python
from shared.models.engine import EasyOCRProcessor
from PIL import Image

# Load and process a receipt
processor = EasyOCRProcessor()
image_path = "examples/receipts/0.jpg"
result = processor.process(image_path)

print(f"Extracted text: {result.texts}")
```

### Running Benchmarks

```bash
# Compare models on all example receipts
python tools/benchmarks/compare_models.py --input examples/receipts/
```

### Integration Testing

The integration test suite uses these images to validate:
- End-to-end extraction workflow
- Multiple model comparisons
- API response formats
- Error handling with various image qualities

## Image Details

- **Total Images**: 20
- **Size Range**: 126KB - 5.4MB
- **Format**: JPEG
- **Quality**: Varies from clear to challenging (blur, skew, low contrast)

## Note

These images are for development and testing only. Do not commit additional large binary files to this repository. For production datasets, use:
- Git LFS (Large File Storage)
- External storage (S3, Google Drive, etc.)
- Dataset hosting services (HuggingFace Datasets, etc.)
