#!/usr/bin/env python3
"""
=============================================================================
CEFR Image Processing and Analysis Script
=============================================================================

This script:
1. Processes JPG images (0.jpg - 4.jpg) using OCR
2. Analyzes the extraction results
3. Reports findings according to CEFR (CEF Refactoring) standards
4. Shows areas for text detection improvement

Integrates with the Circular Exchange Framework for dynamic parameter tuning.

Usage:
    python scripts/process_images_cefr.py
    python scripts/process_images_cefr.py --verbose
    python scripts/process_images_cefr.py --output-dir data/cefr_results

=============================================================================
"""

import sys
import os
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add parent directories to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(Path(__file__).parent.parent))

# Circular Exchange Framework Integration (MANDATORY)
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_image_files(project_root: Path) -> List[Path]:
    """Get list of JPG image files (0.jpg through 4.jpg) in the project root."""
    image_files = []
    for i in range(5):
        img_path = project_root / f"{i}.jpg"
        if img_path.exists():
            image_files.append(img_path)
        else:
            logger.warning(f"Image not found: {img_path}")
    return image_files

def process_single_image(image_path: Path, processor) -> Dict[str, Any]:
    """
    Process a single image and return extraction results.
    
    Args:
        image_path: Path to the image file
        processor: OCRProcessor instance
        
    Returns:
        Dictionary with extraction results and metadata
    """
    result = {
        'image_path': str(image_path),
        'image_name': image_path.name,
        'success': False,
        'extraction_result': None,
        'error': None,
        'processing_time': 0.0,
        'confidence_score': 0.0,
        'items_count': 0,
        'total_detected': None,
        'store_name': None,
        'transaction_date': None,
        'raw_text_length': 0,
    }
    
    try:
        import time
        start_time = time.time()
        
        extraction = processor.extract(str(image_path))
        
        result['processing_time'] = time.time() - start_time
        result['success'] = extraction.success
        
        if extraction.success and extraction.data:
            data = extraction.data
            result['extraction_result'] = {
                'store_name': data.store_name,
                'transaction_date': data.transaction_date,
                'total': float(data.total) if data.total else None,
                'subtotal': float(data.subtotal) if data.subtotal else None,
                'tax': float(data.tax) if data.tax else None,
                'items_count': len(data.items) if data.items else 0,
                'items': [
                    {'name': item.name, 'price': float(item.total_price) if item.total_price else 0, 'quantity': item.quantity}
                    for item in (data.items or [])
                ],
                'store_address': data.store_address,
                'store_phone': data.store_phone,
                'confidence_score': data.confidence_score,
                'model_used': data.model_used,
                'extraction_notes': data.extraction_notes,
            }
            result['confidence_score'] = data.confidence_score or 0.0
            result['items_count'] = len(data.items) if data.items else 0
            result['total_detected'] = float(data.total) if data.total else None
            result['store_name'] = data.store_name
            result['transaction_date'] = data.transaction_date
        else:
            result['error'] = extraction.error
            
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"Error processing {image_path}: {e}")
    
    return result

def process_images(project_root: Path, verbose: bool = False) -> List[Dict[str, Any]]:
    """
    Process all JPG images and return results.
    
    Args:
        project_root: Path to the project root
        verbose: Enable verbose output
        
    Returns:
        List of extraction results for each image
    """
    from shared.models.config import OCRProcessor
    from shared.models.config import get_ocr_config, reset_ocr_config
    
    # Reset config to defaults for clean testing
    reset_ocr_config()
    ocr_config = get_ocr_config()
    
    # Log configuration
    logger.info("=" * 70)
    logger.info("CEFR IMAGE PROCESSING STARTED")
    logger.info("=" * 70)
    logger.info(f"OCR Configuration:")
    logger.info(f"  - min_confidence: {ocr_config.min_confidence}")
    logger.info(f"  - detection_min_confidence: {ocr_config.detection_min_confidence}")
    logger.info(f"  - auto_tune: {ocr_config.auto_tune}")
    logger.info(f"  - auto_fallback: {ocr_config.auto_fallback}")
    
    # Initialize OCR processor
    model_config = {'name': 'Tesseract OCR', 'type': 'tesseract'}
    processor = OCRProcessor(model_config)
    
    # Get image files
    image_files = get_image_files(project_root)
    logger.info(f"\nFound {len(image_files)} images to process")
    
    results = []
    
    for idx, image_path in enumerate(image_files):
        logger.info(f"\n[{idx+1}/{len(image_files)}] Processing: {image_path.name}")
        
        result = process_single_image(image_path, processor)
        results.append(result)
        
        # Log result summary
        if result['success']:
            logger.info(f"  ✓ Success - Score: {result['confidence_score']:.2f}")
            logger.info(f"    Store: {result['store_name']}")
            logger.info(f"    Total: ${result['total_detected']:.2f}" if result['total_detected'] is not None else "    Total: Not detected")
            logger.info(f"    Items: {result['items_count']}")
            logger.info(f"    Time: {result['processing_time']:.2f}s")
        else:
            logger.info(f"  ✗ Failed - Error: {result['error']}")
    
    return results

def analyze_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze extraction results and generate CEFR-style insights.
    
    Args:
        results: List of extraction results
        
    Returns:
        Dictionary with analysis insights
    """
    analysis = {
        'total_images': len(results),
        'successful_extractions': sum(1 for r in results if r['success']),
        'failed_extractions': sum(1 for r in results if not r['success']),
        'success_rate': 0.0,
        'avg_confidence': 0.0,
        'avg_processing_time': 0.0,
        'total_items_extracted': 0,
        'images_with_total': 0,
        'images_with_store': 0,
        'images_with_date': 0,
        'issues': [],
        'improvement_suggestions': [],
        'detection_stats': {},
    }
    
    if not results:
        return analysis
    
    # Calculate metrics
    successful = [r for r in results if r['success']]
    analysis['success_rate'] = len(successful) / len(results) if results else 0
    
    if successful:
        analysis['avg_confidence'] = sum(r['confidence_score'] for r in successful) / len(successful)
        analysis['avg_processing_time'] = sum(r['processing_time'] for r in successful) / len(successful)
        analysis['total_items_extracted'] = sum(r['items_count'] for r in successful)
        analysis['images_with_total'] = sum(1 for r in successful if r['total_detected'])
        analysis['images_with_store'] = sum(1 for r in successful if r['store_name'])
        analysis['images_with_date'] = sum(1 for r in successful if r['transaction_date'])
    
    # Identify issues
    for result in results:
        if not result['success']:
            analysis['issues'].append({
                'image': result['image_name'],
                'type': 'extraction_failed',
                'details': result['error']
            })
        elif result['confidence_score'] < 0.5:
            analysis['issues'].append({
                'image': result['image_name'],
                'type': 'low_confidence',
                'details': f"Confidence score: {result['confidence_score']:.2f}"
            })
        if result['success'] and result['items_count'] == 0:
            analysis['issues'].append({
                'image': result['image_name'],
                'type': 'no_items_detected',
                'details': 'No line items were extracted'
            })
        if result['success'] and not result['total_detected']:
            analysis['issues'].append({
                'image': result['image_name'],
                'type': 'no_total_detected',
                'details': 'No total amount was extracted'
            })
    
    # Generate improvement suggestions based on issues
    if analysis['success_rate'] < 0.8:
        analysis['improvement_suggestions'].append({
            'category': 'detection_threshold',
            'suggestion': 'Lower detection_min_confidence threshold to detect more text regions',
            'current_issue': f"Only {analysis['success_rate']*100:.1f}% success rate",
            'auto_tunable': True
        })
    
    if analysis['avg_confidence'] < 0.6:
        analysis['improvement_suggestions'].append({
            'category': 'preprocessing',
            'suggestion': 'Enable enhanced contrast and denoising for better OCR accuracy',
            'current_issue': f"Average confidence: {analysis['avg_confidence']:.2f}",
            'auto_tunable': True
        })
    
    low_item_count = sum(1 for r in successful if r['items_count'] == 0) if successful else 0
    if low_item_count > 0:
        analysis['improvement_suggestions'].append({
            'category': 'item_extraction',
            'suggestion': 'Enable relaxed_mode for more aggressive line item matching',
            'current_issue': f"{low_item_count} images with no items extracted",
            'auto_tunable': True
        })
    
    if analysis['images_with_total'] < len(successful) if successful else 0:
        analysis['improvement_suggestions'].append({
            'category': 'total_detection',
            'suggestion': 'Add more total pattern variants for edge cases',
            'current_issue': f"Only {analysis['images_with_total']}/{len(successful)} images have total detected",
            'auto_tunable': False
        })
    
    # Get detection stats from OCR config
    try:
        from shared.models.config import get_ocr_config
        config = get_ocr_config()
        analysis['detection_stats'] = config.get_detection_stats()
    except Exception:
        pass
    
    return analysis

def generate_report(results: List[Dict[str, Any]], analysis: Dict[str, Any], output_dir: Path) -> str:
    """
    Generate a CEFR-style analysis report.
    
    Args:
        results: List of extraction results
        analysis: Analysis insights
        output_dir: Directory to save report
        
    Returns:
        Path to generated report
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report_lines = []
    report_lines.append("=" * 70)
    report_lines.append("CEFR IMAGE PROCESSING ANALYSIS REPORT")
    report_lines.append("=" * 70)
    report_lines.append(f"\nGenerated: {datetime.now().isoformat()}")
    report_lines.append("")
    
    # Summary
    report_lines.append("## SUMMARY")
    report_lines.append("-" * 40)
    report_lines.append(f"Total Images Processed: {analysis['total_images']}")
    report_lines.append(f"Successful Extractions: {analysis['successful_extractions']}")
    report_lines.append(f"Failed Extractions: {analysis['failed_extractions']}")
    report_lines.append(f"Success Rate: {analysis['success_rate']*100:.1f}%")
    report_lines.append(f"Average Confidence: {analysis['avg_confidence']:.2f}")
    report_lines.append(f"Average Processing Time: {analysis['avg_processing_time']:.2f}s")
    report_lines.append(f"Total Items Extracted: {analysis['total_items_extracted']}")
    report_lines.append("")
    
    # Per-image results
    report_lines.append("## IMAGE RESULTS")
    report_lines.append("-" * 40)
    for result in results:
        status = "✓ SUCCESS" if result['success'] else "✗ FAILED"
        report_lines.append(f"\n### {result['image_name']} [{status}]")
        if result['success']:
            report_lines.append(f"  - Confidence: {result['confidence_score']:.2f}")
            report_lines.append(f"  - Store: {result['store_name'] or 'Not detected'}")
            report_lines.append(f"  - Date: {result['transaction_date'] or 'Not detected'}")
            report_lines.append(f"  - Total: ${result['total_detected']:.2f}" if result['total_detected'] else "  - Total: Not detected")
            report_lines.append(f"  - Items: {result['items_count']}")
            report_lines.append(f"  - Processing Time: {result['processing_time']:.2f}s")
            
            # Show extracted items if any
            if result.get('extraction_result', {}).get('items'):
                report_lines.append("  - Extracted Items:")
                for item in result['extraction_result']['items'][:10]:  # Limit to 10 items
                    report_lines.append(f"      • {item['name']}: ${item['price']:.2f}")
                if len(result['extraction_result']['items']) > 10:
                    report_lines.append(f"      ... and {len(result['extraction_result']['items']) - 10} more")
        else:
            report_lines.append(f"  - Error: {result['error']}")
    report_lines.append("")
    
    # Issues
    if analysis['issues']:
        report_lines.append("## ISSUES DETECTED")
        report_lines.append("-" * 40)
        for issue in analysis['issues']:
            report_lines.append(f"  - [{issue['type']}] {issue['image']}: {issue['details']}")
        report_lines.append("")
    
    # Improvement suggestions
    if analysis['improvement_suggestions']:
        report_lines.append("## IMPROVEMENT SUGGESTIONS (CEFR)")
        report_lines.append("-" * 40)
        for idx, suggestion in enumerate(analysis['improvement_suggestions'], 1):
            report_lines.append(f"\n{idx}. [{suggestion['category']}] {suggestion['suggestion']}")
            report_lines.append(f"   Current Issue: {suggestion['current_issue']}")
            report_lines.append(f"   Auto-tunable: {'Yes' if suggestion['auto_tunable'] else 'No'}")
    report_lines.append("")
    
    # Detection stats
    if analysis.get('detection_stats'):
        report_lines.append("## DETECTION STATISTICS")
        report_lines.append("-" * 40)
        stats = analysis['detection_stats']
        for key, value in stats.items():
            if isinstance(value, float):
                report_lines.append(f"  - {key}: {value:.4f}")
            else:
                report_lines.append(f"  - {key}: {value}")
    report_lines.append("")
    
    report_lines.append("=" * 70)
    report_lines.append("END OF REPORT")
    report_lines.append("=" * 70)
    
    # Save report
    report_text = "\n".join(report_lines)
    report_path = output_dir / "cefr_image_analysis_report.txt"
    with open(report_path, 'w') as f:
        f.write(report_text)
    
    # Also save as JSON for programmatic access
    json_path = output_dir / "cefr_image_analysis.json"
    with open(json_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'analysis': analysis
        }, f, indent=2, default=str)
    
    return str(report_path)

def main():
    """Main entry point for CEFR image processing."""
    parser = argparse.ArgumentParser(
        description="CEFR Image Processing and Analysis Script"
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/cefr_results',
        help='Directory to save results (default: data/cefr_results)'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    project_root = Path(__file__).parent.parent
    output_dir = project_root / args.output_dir
    
    # Process images
    results = process_images(project_root, args.verbose)
    
    # Analyze results
    analysis = analyze_results(results)
    
    # Generate report
    report_path = generate_report(results, analysis, output_dir)
    
    # Print summary
    print("\n" + "=" * 70)
    print("CEFR ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"\nSuccess Rate: {analysis['success_rate']*100:.1f}%")
    print(f"Average Confidence: {analysis['avg_confidence']:.2f}")
    print(f"Total Items Extracted: {analysis['total_items_extracted']}")
    print(f"\nReport saved to: {report_path}")
    print(f"JSON data saved to: {output_dir / 'cefr_image_analysis.json'}")
    
    # Print improvement suggestions
    if analysis['improvement_suggestions']:
        print("\n" + "-" * 40)
        print("CEFR IMPROVEMENT SUGGESTIONS:")
        print("-" * 40)
        for suggestion in analysis['improvement_suggestions']:
            print(f"  • [{suggestion['category']}] {suggestion['suggestion']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
