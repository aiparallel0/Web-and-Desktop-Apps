# Model Benchmarking Suite

This directory contains tools for benchmarking and comparing the 7 text detection algorithms in the Receipt Extractor system.

## Algorithms Tested

1. **Tesseract OCR** - Traditional OCR engine
2. **EasyOCR** - Deep learning OCR with 80+ languages
3. **PaddleOCR** - Production-ready multilingual OCR
4. **Donut** - End-to-end transformer model
5. **Florence-2** - Microsoft's vision-language model
6. **CRAFT** - Character Region Awareness For Text detection
7. **Spatial Multi-Method** - Ensemble approach with spatial analysis

## Usage

### Basic Benchmark

Run benchmark on all models with test images in `data/`:

```bash
python tools/benchmarks/compare_models.py
```

### Custom Dataset

Specify a different dataset directory:

```bash
python tools/benchmarks/compare_models.py --dataset /path/to/images
```

### Specific Models

Test only specific models:

```bash
python tools/benchmarks/compare_models.py --models ocr_tesseract ocr_easyocr craft_detector
```

### Output Formats

Generate JSON and/or HTML reports:

```bash
# Both formats (default)
python tools/benchmarks/compare_models.py --format both

# JSON only
python tools/benchmarks/compare_models.py --format json

# HTML only
python tools/benchmarks/compare_models.py --format html
```

### Integration with Launcher

Run via the unified launcher script:

```bash
./launcher.sh benchmark
```

## Metrics

The benchmark suite calculates the following metrics:

### Performance Metrics
- **Processing Time**: Time to process each image
- **Throughput**: Images per second
- **Success Rate**: Percentage of images processed without errors

### Accuracy Metrics (when ground truth available)
- **Precision**: Ratio of correctly detected text to all detected text
- **Recall**: Ratio of correctly detected text to all ground truth text
- **F1 Score**: Harmonic mean of precision and recall
- **CER (Character Error Rate)**: Levenshtein distance normalized by ground truth length

## Test Dataset

### Structure

```
tools/benchmarks/data/
├── ground_truth.json          # Ground truth annotations
├── sample_receipt_1.jpg       # Test image 1
├── sample_receipt_2.jpg       # Test image 2
└── ...
```

### Ground Truth Format

The `ground_truth.json` file contains annotations in the following format:

```json
[
  {
    "image_name": "sample_receipt_1.jpg",
    "text_regions": [
      {
        "text": "STORE NAME",
        "bbox": {"x": 100, "y": 50, "width": 200, "height": 40}
      },
      {
        "text": "Total: $45.67",
        "bbox": {"x": 100, "y": 400, "width": 150, "height": 30}
      }
    ],
    "metadata": {
      "description": "Sample receipt",
      "difficulty": "easy"
    }
  }
]
```

### Adding Test Images

1. Place test images in `tools/benchmarks/data/`
2. Add corresponding ground truth to `ground_truth.json`
3. Run benchmark

**Note**: Ground truth is optional. If not provided, the benchmark will only measure performance metrics (processing time, success rate), not accuracy metrics.

## Output

### JSON Report

Saved to `tools/benchmarks/results/benchmark_YYYYMMDD_HHMMSS.json`

Contains:
- Detailed metrics for each model on each image
- Aggregate statistics per model
- Timing information
- Accuracy metrics (if ground truth available)

### HTML Report

Saved to `tools/benchmarks/results/benchmark_YYYYMMDD_HHMMSS.html`

Contains:
- Visual comparison table
- Model-by-model detailed results
- Color-coded success/failure indicators
- Easy to share and view in browser

## Example Output

```
==============================================================
Benchmarking model: ocr_tesseract
==============================================================
Processing image 1/10: receipt_001.jpg
  Result: SUCCESS (0.45s)
Processing image 2/10: receipt_002.jpg
  Result: SUCCESS (0.52s)
...

Model ocr_tesseract Summary:
  Success rate: 9/10
  Avg processing time: 0.48s
  Avg F1 score: 0.856
  Avg CER: 0.124
```

## Notes

- First run may be slower as models are downloaded
- GPU acceleration significantly improves AI model performance
- Some models may require additional dependencies (see main README)
- Benchmark results are saved with timestamps for version tracking
