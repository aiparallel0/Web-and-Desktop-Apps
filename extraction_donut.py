#!/usr/bin/env python3
"""
EXTRACTION_DONUT.PY - Enhanced Receipt Extraction API
Simple API wrapper around expansion_donut for programmatic use
Provides easy-to-use functions for batch processing and integration
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional, Union
from dataclasses import asdict

# Import from expansion_donut
from expansion_donut import (
    HybridDonutExtractor,
    ReceiptData,
    MODEL_CONFIGS
)

class ExtractionAPI:
    """
    Simple API for receipt extraction with caching and batch support
    """

    def __init__(self, primary_model: str = 'sroie', enable_multi_model: bool = False,
                 cache_models: bool = True):
        """
        Initialize extraction API

        Args:
            primary_model: Primary model to use
            enable_multi_model: Enable fallback to other models
            cache_models: Keep models in memory for faster repeated extractions
        """
        self.primary_model = primary_model
        self.enable_multi_model = enable_multi_model
        self.cache_models = cache_models
        self.extractor = None

        if self.cache_models:
            self._initialize_extractor()

    def _initialize_extractor(self):
        """Initialize the extractor"""
        models_to_load = (list(MODEL_CONFIGS.keys())
                         if self.enable_multi_model
                         else [self.primary_model])
        self.extractor = HybridDonutExtractor(
            model_keys=models_to_load,
            primary_model=self.primary_model
        )

    def extract_single(self, image_path: str, mode: str = 'fast') -> Dict:
        """
        Extract data from a single receipt

        Args:
            image_path: Path to receipt image
            mode: 'fast' or 'quality'

        Returns:
            Dictionary containing extracted data
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Initialize extractor if not cached
        if self.extractor is None:
            self._initialize_extractor()

        # Extract
        receipt = self.extractor.extract_with_fallback(image_path, mode=mode)

        return receipt.to_dict()

    def extract_batch(self, image_paths: List[str], mode: str = 'fast',
                     save_individual: bool = False,
                     output_dir: Optional[str] = None) -> Dict:
        """
        Extract data from multiple receipts

        Args:
            image_paths: List of paths to receipt images
            mode: 'fast' or 'quality'
            save_individual: Save individual JSON files for each receipt
            output_dir: Directory to save results (default: current directory)

        Returns:
            Dictionary with batch results
        """
        results = {
            'total': len(image_paths),
            'successful': 0,
            'failed': 0,
            'receipts': []
        }

        # Initialize extractor once for batch
        if self.extractor is None:
            self._initialize_extractor()

        for idx, image_path in enumerate(image_paths):
            print(f"\n[{idx + 1}/{len(image_paths)}] Processing: {os.path.basename(image_path)}")

            try:
                receipt_data = self.extract_single(image_path, mode=mode)
                results['receipts'].append({
                    'image_path': image_path,
                    'success': True,
                    'data': receipt_data
                })
                results['successful'] += 1

                # Save individual file if requested
                if save_individual:
                    output_path = self._get_output_path(image_path, output_dir)
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(receipt_data, f, indent=2)
                    print(f"   💾 Saved to: {output_path}")

            except Exception as e:
                print(f"   ❌ Failed: {e}")
                results['receipts'].append({
                    'image_path': image_path,
                    'success': False,
                    'error': str(e)
                })
                results['failed'] += 1

        return results

    def extract_directory(self, directory: str, pattern: str = "*.{jpg,jpeg,png}",
                         mode: str = 'fast', save_individual: bool = True,
                         output_dir: Optional[str] = None) -> Dict:
        """
        Extract data from all images in a directory

        Args:
            directory: Directory containing receipt images
            pattern: Glob pattern for image files
            mode: 'fast' or 'quality'
            save_individual: Save individual JSON files
            output_dir: Output directory (default: same as input)

        Returns:
            Dictionary with batch results
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        # Find all images
        image_paths = []
        for ext in ['jpg', 'jpeg', 'png', 'JPG', 'JPEG', 'PNG']:
            image_paths.extend(dir_path.glob(f"*.{ext}"))

        if not image_paths:
            raise ValueError(f"No images found in {directory}")

        print(f"📁 Found {len(image_paths)} images in {directory}")

        # Use output_dir as directory if not specified
        if output_dir is None:
            output_dir = directory

        return self.extract_batch(
            [str(p) for p in image_paths],
            mode=mode,
            save_individual=save_individual,
            output_dir=output_dir
        )

    def _get_output_path(self, image_path: str, output_dir: Optional[str] = None) -> str:
        """Generate output path for extracted data"""
        if output_dir is None:
            output_dir = os.path.dirname(image_path)

        filename = os.path.splitext(os.path.basename(image_path))[0]
        model_suffix = 'hybrid' if self.enable_multi_model else self.primary_model
        return os.path.join(output_dir, f"{filename}_{model_suffix}_extracted.json")

    def get_available_models(self) -> List[Dict]:
        """Get list of available models"""
        return [
            {
                'key': key,
                'name': config['name'],
                'description': config['description'],
                'type': config['type'],
                'priority': config.get('priority', 999)
            }
            for key, config in MODEL_CONFIGS.items()
        ]

    def compare_models(self, image_path: str, models: List[str] = None) -> Dict:
        """
        Compare extraction results across multiple models

        Args:
            image_path: Path to receipt image
            models: List of model keys to compare (None = all available)

        Returns:
            Dictionary with comparison results
        """
        if models is None:
            models = list(MODEL_CONFIGS.keys())

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        results = {
            'image_path': image_path,
            'models': {}
        }

        for model_key in models:
            print(f"\n🔍 Testing model: {model_key.upper()}")
            try:
                # Create temporary extractor for this model
                temp_extractor = HybridDonutExtractor(
                    model_keys=[model_key],
                    primary_model=model_key
                )
                receipt = temp_extractor.extract_with_fallback(image_path, mode='fast')

                results['models'][model_key] = {
                    'success': True,
                    'data': receipt.to_dict(),
                    'confidence': receipt.confidence_score,
                    'items_count': len(receipt.items),
                    'has_total': receipt.total is not None
                }
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                results['models'][model_key] = {
                    'success': False,
                    'error': str(e)
                }

        # Determine best model
        successful = {k: v for k, v in results['models'].items() if v.get('success')}
        if successful:
            best_model = max(successful.items(), key=lambda x: x[1].get('confidence', 0))
            results['best_model'] = best_model[0]
            results['best_confidence'] = best_model[1].get('confidence', 0)

        return results


# ==================== CONVENIENCE FUNCTIONS ====================

def quick_extract(image_path: str, model: str = 'sroie') -> Dict:
    """
    Quick extraction with default settings

    Args:
        image_path: Path to receipt image
        model: Model to use (default: sroie)

    Returns:
        Extracted data dictionary
    """
    api = ExtractionAPI(primary_model=model, cache_models=False)
    return api.extract_single(image_path)


def batch_extract(image_paths: List[str], model: str = 'sroie',
                 save_files: bool = True) -> Dict:
    """
    Quick batch extraction

    Args:
        image_paths: List of image paths
        model: Model to use
        save_files: Save individual JSON files

    Returns:
        Batch results dictionary
    """
    api = ExtractionAPI(primary_model=model)
    return api.extract_batch(image_paths, save_individual=save_files)


def extract_to_csv(image_paths: List[str], output_file: str,
                  model: str = 'sroie') -> None:
    """
    Extract receipts and save to CSV

    Args:
        image_paths: List of image paths
        output_file: Output CSV file path
        model: Model to use
    """
    import csv

    api = ExtractionAPI(primary_model=model)
    results = api.extract_batch(image_paths)

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Image', 'Store', 'Date', 'Total', 'Items Count',
                        'Category', 'Confidence', 'Success'])

        for result in results['receipts']:
            if result['success']:
                data = result['data']
                writer.writerow([
                    result['image_path'],
                    data.get('store', {}).get('name', ''),
                    data.get('date', ''),
                    data.get('totals', {}).get('total', ''),
                    data.get('item_count', 0),
                    data.get('category', ''),
                    data.get('confidence', ''),
                    'Yes'
                ])
            else:
                writer.writerow([
                    result['image_path'],
                    '', '', '', '', '', '',
                    f"No - {result['error']}"
                ])

    print(f"\n💾 Saved CSV to: {output_file}")


# ==================== CLI INTERFACE ====================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Receipt Extraction API - Batch processing and utilities'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Single extraction
    single = subparsers.add_parser('single', help='Extract single receipt')
    single.add_argument('image', help='Path to receipt image')
    single.add_argument('--model', default='sroie', help='Model to use')
    single.add_argument('--quality', action='store_true', help='Use quality mode')
    single.add_argument('--output', help='Output JSON file')

    # Batch extraction
    batch = subparsers.add_parser('batch', help='Extract multiple receipts')
    batch.add_argument('images', nargs='+', help='Paths to receipt images')
    batch.add_argument('--model', default='sroie', help='Model to use')
    batch.add_argument('--quality', action='store_true', help='Use quality mode')
    batch.add_argument('--output-dir', help='Output directory for JSON files')
    batch.add_argument('--summary', help='Save summary JSON file')

    # Directory extraction
    directory = subparsers.add_parser('directory', help='Extract all receipts in directory')
    directory.add_argument('dir', help='Directory containing receipt images')
    directory.add_argument('--model', default='sroie', help='Model to use')
    directory.add_argument('--quality', action='store_true', help='Use quality mode')
    directory.add_argument('--output-dir', help='Output directory')

    # CSV export
    csv_export = subparsers.add_parser('csv', help='Extract and save to CSV')
    csv_export.add_argument('images', nargs='+', help='Paths to receipt images')
    csv_export.add_argument('--output', required=True, help='Output CSV file')
    csv_export.add_argument('--model', default='sroie', help='Model to use')

    # Compare models
    compare = subparsers.add_parser('compare', help='Compare models on single image')
    compare.add_argument('image', help='Path to receipt image')
    compare.add_argument('--models', nargs='+', help='Models to compare')
    compare.add_argument('--output', help='Output comparison JSON file')

    # List models
    list_models = subparsers.add_parser('list', help='List available models')

    args = parser.parse_args()

    if args.command == 'single':
        mode = 'quality' if args.quality else 'fast'
        api = ExtractionAPI(primary_model=args.model)
        result = api.extract_single(args.image, mode=mode)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            print(f"\n💾 Saved to: {args.output}")
        else:
            print(json.dumps(result, indent=2))

    elif args.command == 'batch':
        mode = 'quality' if args.quality else 'fast'
        api = ExtractionAPI(primary_model=args.model)
        results = api.extract_batch(
            args.images,
            mode=mode,
            save_individual=True,
            output_dir=args.output_dir
        )

        print(f"\n" + "="*70)
        print(f"BATCH COMPLETE: {results['successful']}/{results['total']} successful")
        print("="*70)

        if args.summary:
            with open(args.summary, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            print(f"💾 Summary saved to: {args.summary}")

    elif args.command == 'directory':
        mode = 'quality' if args.quality else 'fast'
        api = ExtractionAPI(primary_model=args.model)
        results = api.extract_directory(
            args.dir,
            mode=mode,
            save_individual=True,
            output_dir=args.output_dir
        )

        print(f"\n" + "="*70)
        print(f"DIRECTORY COMPLETE: {results['successful']}/{results['total']} successful")
        print("="*70)

    elif args.command == 'csv':
        extract_to_csv(args.images, args.output, model=args.model)

    elif args.command == 'compare':
        api = ExtractionAPI()
        results = api.compare_models(args.image, models=args.models)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Comparison saved to: {args.output}")
        else:
            print(json.dumps(results, indent=2))

        if 'best_model' in results:
            print(f"\n🏆 Best Model: {results['best_model'].upper()} "
                  f"(confidence: {results['best_confidence']:.1f})")

    elif args.command == 'list':
        api = ExtractionAPI(cache_models=False)
        models = api.get_available_models()

        print("\n" + "="*70)
        print("AVAILABLE MODELS")
        print("="*70)
        for model in sorted(models, key=lambda x: x['priority']):
            print(f"\n{model['key'].upper()}")
            print(f"  Name: {model['name']}")
            print(f"  Type: {model['type']}")
            print(f"  Description: {model['description']}")
        print()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
