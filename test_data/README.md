# Test Data for Receipt Extractor

This directory contains sample receipt images and their expected extraction results for testing and validation.

## Directory Structure

```
test_data/
├── receipts/              # Sample receipt images
│   ├── grocery_001.jpg
│   ├── restaurant_001.jpg
│   ├── retail_001.jpg
│   └── international_001.jpg
├── expected_outputs/      # Expected extraction results (JSON)
│   ├── grocery_001.json
│   ├── restaurant_001.json
│   ├── retail_001.json
│   └── international_001.json
└── README.md             # This file
```

## Adding Sample Receipts

### Receipt Image Guidelines

1. **Format:** JPG, PNG, or TIFF
2. **Resolution:** At least 1000x1000px for best results
3. **Quality:** Clear, well-lit, minimal blur
4. **Coverage:** Include various receipt types:
   - Grocery stores
   - Restaurants/cafes
   - Retail shops
   - Gas stations
   - International receipts (different languages)

### Naming Convention

Use descriptive names that indicate the receipt type:

```
<category>_<number>.<extension>

Examples:
- grocery_001.jpg
- grocery_002.png
- restaurant_001.jpg
- restaurant_starbucks_001.jpg
- retail_target_001.jpg
- gas_station_001.jpg
- international_french_001.jpg
```

## Creating Expected Outputs

For each receipt image, create a corresponding JSON file with the expected extraction result.

### JSON Format

```json
{
  "store": {
    "name": "Store Name",
    "address": "123 Main St, City, State 12345",
    "phone": "(555) 123-4567"
  },
  "date": "2024-01-15",
  "items": [
    {
      "name": "Product Name",
      "quantity": 1,
      "unit_price": 5.99,
      "total_price": 5.99
    }
  ],
  "totals": {
    "subtotal": 5.99,
    "tax": 0.48,
    "total": 6.47
  },
  "payment_method": "Credit Card",
  "category": "grocery"
}
```

### Expected Output Guidelines

1. **Accuracy:** Manually verify all data from the receipt
2. **Completeness:** Include all extractable information
3. **Consistency:** Use consistent formatting across all files
4. **Notes:** Add comments if certain fields are intentionally left empty

## Using Test Data

### Manual Testing

1. Run the desktop app or web app
2. Upload a test receipt from `receipts/`
3. Compare the extraction result with the corresponding file in `expected_outputs/`
4. Calculate accuracy metrics

### Automated Testing

```python
# Example test using pytest
import json
from pathlib import Path

def test_receipt_extraction():
    receipt_path = 'test_data/receipts/grocery_001.jpg'
    expected_path = 'test_data/expected_outputs/grocery_001.json'

    # Extract receipt
    result = extract_receipt(receipt_path, model='florence2')

    # Load expected output
    with open(expected_path) as f:
        expected = json.load(f)

    # Compare results
    assert result['store']['name'] == expected['store']['name']
    assert result['totals']['total'] == expected['totals']['total']
    assert len(result['items']) == len(expected['items'])
```

## Model Accuracy Benchmarking

Use test data to benchmark different models:

```bash
# Run accuracy test script (to be created)
python scripts/benchmark_accuracy.py --test-dir test_data/
```

This will:
1. Extract all receipts using each available model
2. Compare results against expected outputs
3. Calculate precision, recall, and F1 scores
4. Generate accuracy report

## Current Status

- **Total Receipts:** 0
- **Coverage:**
  - ⬜ Grocery: 0
  - ⬜ Restaurant: 0
  - ⬜ Retail: 0
  - ⬜ Gas Station: 0
  - ⬜ International: 0

## Privacy & Legal Considerations

⚠️ **IMPORTANT:** Only include receipts that:

1. **No Personal Info:** Remove/blur sensitive data (credit card numbers, personal names, etc.)
2. **Legal to Share:** Only use receipts you have permission to share
3. **No Copyrighted Content:** Avoid receipts with copyrighted logos/branding if distributing publicly
4. **Anonymize:** Consider using synthetic/generated receipts for public repos

## Sample Data Sources

### Create Your Own
- Take photos of your own receipts (anonymize first)
- Generate synthetic receipts using templates

### Public Datasets
- [SROIE Dataset](https://rrc.cvc.uab.es/?ch=13) - Scanned Receipts OCR and Information Extraction
- [CORD Dataset](https://github.com/clovaai/cord) - Consolidated Receipt Dataset
- [Receipt Dataset](https://expressexpense.com/receipt-ocr-dataset) - Public receipt dataset

### Generate Synthetic Data
- Use receipt template generators
- Create mock receipts using design tools (Figma, Canva)
- Ensure realistic formatting and layouts

## Next Steps

1. ✅ Directory structure created
2. ⬜ Add at least 5 sample receipts per category
3. ⬜ Create corresponding expected outputs
4. ⬜ Write benchmark script
5. ⬜ Document accuracy results in project README

## Contributing

To contribute test data:

1. Add receipt images to `receipts/`
2. Create corresponding JSON files in `expected_outputs/`
3. Update this README with new sample counts
4. Submit a pull request with clear descriptions
5. Ensure all privacy guidelines are followed
