"""
Model Benchmarking Tool - Compare Text Detection Algorithms

This script provides comprehensive benchmarking of all text detection models
in the Receipt Extractor system, measuring accuracy, performance, and reliability.

Features:
- Tests all 7 detection algorithms (Tesseract, EasyOCR, PaddleOCR, Donut, Florence-2, CRAFT, Spatial)
- Calculates precision, recall, F1-score, CER (Character Error Rate)
- Measures processing time and throughput
- Generates JSON and HTML comparison reports
- Supports ground truth annotations

Usage:
    python tools/benchmarks/compare_models.py
    python tools/benchmarks/compare_models.py --dataset tools/benchmarks/data
    python tools/benchmarks/compare_models.py --models tesseract easyocr craft
    python tools/benchmarks/compare_models.py --output results.html
"""

import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import statistics

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.models.manager import ModelManager, ModelType
from shared.utils.image import load_and_validate_image

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkMetrics:
    """Metrics for a single model on a single image."""
    model_id: str
    image_name: str
    processing_time: float
    success: bool
    error: Optional[str] = None
    
    # Text detection metrics
    detected_text_count: int = 0
    extracted_text: str = ""
    confidence_score: float = 0.0
    
    # Accuracy metrics (when ground truth available)
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    character_error_rate: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ModelBenchmarkResults:
    """Aggregate results for a single model across all test images."""
    model_id: str
    model_name: str
    total_images: int
    successful_images: int
    failed_images: int
    
    # Timing statistics
    avg_processing_time: float = 0.0
    min_processing_time: float = 0.0
    max_processing_time: float = 0.0
    total_processing_time: float = 0.0
    
    # Accuracy statistics (when ground truth available)
    avg_precision: Optional[float] = None
    avg_recall: Optional[float] = None
    avg_f1_score: Optional[float] = None
    avg_cer: Optional[float] = None
    
    # Detailed results
    image_results: List[BenchmarkMetrics] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Convert image_results to list of dicts
        data['image_results'] = [r.to_dict() if hasattr(r, 'to_dict') else r 
                                  for r in self.image_results]
        return data


@dataclass
class GroundTruth:
    """Ground truth annotation for a test image."""
    image_name: str
    text_regions: List[Dict[str, Any]]  # List of {text, bbox} dicts
    metadata: Dict[str, Any] = field(default_factory=dict)


class BenchmarkRunner:
    """
    Run benchmarks on text detection models.
    
    This class coordinates the benchmarking process, running each model
    on each test image and collecting metrics.
    """
    
    def __init__(
        self,
        dataset_dir: str,
        output_dir: str = "tools/benchmarks/results",
        models: Optional[List[str]] = None
    ):
        """
        Initialize benchmark runner.
        
        Args:
            dataset_dir: Directory containing test images and ground truth
            output_dir: Directory to save results
            models: List of model IDs to test (None = test all)
        """
        self.dataset_dir = Path(dataset_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize model manager
        self.model_manager = ModelManager()
        
        # Determine which models to test
        if models:
            self.models_to_test = models
        else:
            # Test all available models
            available = self.model_manager.get_available_models()
            self.models_to_test = [m['id'] for m in available]
        
        # Load ground truth if available
        self.ground_truth = self._load_ground_truth()
        
        logger.info(f"Initialized benchmark runner")
        logger.info(f"Dataset: {self.dataset_dir}")
        logger.info(f"Models to test: {len(self.models_to_test)}")
        logger.info(f"Ground truth available: {len(self.ground_truth)} images")
    
    def _load_ground_truth(self) -> Dict[str, GroundTruth]:
        """Load ground truth annotations from JSON file."""
        gt_file = self.dataset_dir / "ground_truth.json"
        if not gt_file.exists():
            logger.warning(f"No ground truth file found at {gt_file}")
            return {}
        
        try:
            with open(gt_file, 'r') as f:
                data = json.load(f)
            
            ground_truth = {}
            for item in data:
                gt = GroundTruth(
                    image_name=item['image_name'],
                    text_regions=item.get('text_regions', []),
                    metadata=item.get('metadata', {})
                )
                ground_truth[gt.image_name] = gt
            
            logger.info(f"Loaded ground truth for {len(ground_truth)} images")
            return ground_truth
        
        except Exception as e:
            logger.error(f"Failed to load ground truth: {e}")
            return {}
    
    def _calculate_cer(self, predicted: str, ground_truth: str) -> float:
        """
        Calculate Character Error Rate (CER) using Levenshtein distance.
        
        Args:
            predicted: Predicted text
            ground_truth: Ground truth text
            
        Returns:
            CER as a float (0 = perfect match, 1 = completely wrong)
        """
        # Simple Levenshtein distance implementation
        if not ground_truth:
            return 1.0 if predicted else 0.0
        
        if not predicted:
            return 1.0
        
        # Create distance matrix
        m, n = len(predicted), len(ground_truth)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        # Initialize
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        
        # Fill matrix
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if predicted[i-1] == ground_truth[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(
                        dp[i-1][j],    # deletion
                        dp[i][j-1],    # insertion
                        dp[i-1][j-1]   # substitution
                    )
        
        distance = dp[m][n]
        cer = distance / len(ground_truth)
        return min(1.0, cer)  # Cap at 1.0
    
    def _benchmark_model_on_image(
        self,
        model_id: str,
        image_path: Path
    ) -> BenchmarkMetrics:
        """
        Benchmark a single model on a single image.
        
        Args:
            model_id: Model identifier
            image_path: Path to test image
            
        Returns:
            BenchmarkMetrics object
        """
        start_time = time.time()
        
        try:
            # Get processor
            processor = self.model_manager.get_processor(model_id)
            
            # Run extraction
            result = processor.extract(str(image_path))
            processing_time = time.time() - start_time
            
            # Extract metrics
            metrics = BenchmarkMetrics(
                model_id=model_id,
                image_name=image_path.name,
                processing_time=processing_time,
                success=result.success if hasattr(result, 'success') else True
            )
            
            # Try to extract text and confidence
            if hasattr(result, 'data'):
                # Receipt data format
                data = result.data
                if hasattr(data, 'raw_text'):
                    metrics.extracted_text = data.raw_text or ""
                if hasattr(data, 'confidence_score'):
                    metrics.confidence_score = data.confidence_score or 0.0
            
            # Count detected text regions if available
            if hasattr(result, 'texts'):
                metrics.detected_text_count = len(result.texts)
            
            # Calculate accuracy metrics if ground truth available
            gt = self.ground_truth.get(image_path.name)
            if gt and metrics.extracted_text:
                # Combine ground truth text
                gt_text = " ".join([r.get('text', '') for r in gt.text_regions])
                
                # Calculate CER
                metrics.character_error_rate = self._calculate_cer(
                    metrics.extracted_text,
                    gt_text
                )
                
                # Simple precision/recall based on text overlap
                # (This is simplified - production would use more sophisticated metrics)
                pred_words = set(metrics.extracted_text.lower().split())
                gt_words = set(gt_text.lower().split())
                
                if pred_words:
                    true_positives = len(pred_words & gt_words)
                    metrics.precision = true_positives / len(pred_words)
                    metrics.recall = true_positives / len(gt_words) if gt_words else 0.0
                    
                    if metrics.precision + metrics.recall > 0:
                        metrics.f1_score = (
                            2 * metrics.precision * metrics.recall /
                            (metrics.precision + metrics.recall)
                        )
            
            return metrics
        
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Model {model_id} failed on {image_path.name}: {e}")
            
            return BenchmarkMetrics(
                model_id=model_id,
                image_name=image_path.name,
                processing_time=processing_time,
                success=False,
                error=str(e)
            )
    
    def run_benchmark(self) -> Dict[str, ModelBenchmarkResults]:
        """
        Run benchmark on all models and all test images.
        
        Returns:
            Dictionary mapping model_id to ModelBenchmarkResults
        """
        # Find all test images
        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}
        test_images = [
            f for f in self.dataset_dir.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ]
        
        if not test_images:
            logger.warning(f"No test images found in {self.dataset_dir}")
            return {}
        
        logger.info(f"Found {len(test_images)} test images")
        
        results = {}
        
        for model_id in self.models_to_test:
            logger.info(f"\n{'='*60}")
            logger.info(f"Benchmarking model: {model_id}")
            logger.info(f"{'='*60}")
            
            # Get model info
            model_info = next(
                (m for m in self.model_manager.get_available_models() 
                 if m['id'] == model_id),
                {'id': model_id, 'name': model_id}
            )
            
            image_results = []
            processing_times = []
            
            for i, image_path in enumerate(test_images, 1):
                logger.info(
                    f"Processing image {i}/{len(test_images)}: {image_path.name}"
                )
                
                metrics = self._benchmark_model_on_image(model_id, image_path)
                image_results.append(metrics)
                
                if metrics.success:
                    processing_times.append(metrics.processing_time)
                
                logger.info(
                    f"  Result: {'SUCCESS' if metrics.success else 'FAILED'} "
                    f"({metrics.processing_time:.2f}s)"
                )
            
            # Aggregate results
            successful = [r for r in image_results if r.success]
            failed = [r for r in image_results if not r.success]
            
            model_results = ModelBenchmarkResults(
                model_id=model_id,
                model_name=model_info['name'],
                total_images=len(test_images),
                successful_images=len(successful),
                failed_images=len(failed),
                image_results=image_results
            )
            
            # Calculate timing statistics
            if processing_times:
                model_results.avg_processing_time = statistics.mean(processing_times)
                model_results.min_processing_time = min(processing_times)
                model_results.max_processing_time = max(processing_times)
                model_results.total_processing_time = sum(processing_times)
            
            # Calculate accuracy statistics
            precision_scores = [r.precision for r in successful if r.precision is not None]
            recall_scores = [r.recall for r in successful if r.recall is not None]
            f1_scores = [r.f1_score for r in successful if r.f1_score is not None]
            cer_scores = [r.character_error_rate for r in successful 
                         if r.character_error_rate is not None]
            
            if precision_scores:
                model_results.avg_precision = statistics.mean(precision_scores)
            if recall_scores:
                model_results.avg_recall = statistics.mean(recall_scores)
            if f1_scores:
                model_results.avg_f1_score = statistics.mean(f1_scores)
            if cer_scores:
                model_results.avg_cer = statistics.mean(cer_scores)
            
            results[model_id] = model_results
            
            # Print summary
            logger.info(f"\nModel {model_id} Summary:")
            logger.info(f"  Success rate: {len(successful)}/{len(test_images)}")
            logger.info(f"  Avg processing time: {model_results.avg_processing_time:.2f}s")
            if model_results.avg_f1_score:
                logger.info(f"  Avg F1 score: {model_results.avg_f1_score:.3f}")
            if model_results.avg_cer:
                logger.info(f"  Avg CER: {model_results.avg_cer:.3f}")
        
        return results
    
    def save_results(
        self,
        results: Dict[str, ModelBenchmarkResults],
        format: str = 'json'
    ) -> Path:
        """
        Save benchmark results to file.
        
        Args:
            results: Benchmark results
            format: Output format ('json' or 'html')
            
        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'json':
            output_file = self.output_dir / f"benchmark_{timestamp}.json"
            
            # Convert to serializable format
            data = {
                'timestamp': timestamp,
                'dataset': str(self.dataset_dir),
                'models': {
                    model_id: results_obj.to_dict()
                    for model_id, results_obj in results.items()
                }
            }
            
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved JSON results to {output_file}")
            return output_file
        
        elif format == 'html':
            output_file = self.output_dir / f"benchmark_{timestamp}.html"
            html = self._generate_html_report(results, timestamp)
            
            with open(output_file, 'w') as f:
                f.write(html)
            
            logger.info(f"Saved HTML report to {output_file}")
            return output_file
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_html_report(
        self,
        results: Dict[str, ModelBenchmarkResults],
        timestamp: str
    ) -> str:
        """Generate HTML benchmark report."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Model Benchmark Report - {timestamp}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .metric {{ font-weight: bold; color: #2196F3; }}
        .success {{ color: #4CAF50; }}
        .failure {{ color: #f44336; }}
    </style>
</head>
<body>
    <h1>Text Detection Model Benchmark Report</h1>
    <p>Generated: {timestamp}</p>
    <p>Dataset: {self.dataset_dir}</p>
    
    <h2>Model Comparison Summary</h2>
    <table>
        <tr>
            <th>Model</th>
            <th>Success Rate</th>
            <th>Avg Time (s)</th>
            <th>F1 Score</th>
            <th>CER</th>
        </tr>
"""
        
        for model_id, res in results.items():
            success_rate = (res.successful_images / res.total_images * 100) if res.total_images > 0 else 0
            f1_str = f"{res.avg_f1_score:.3f}" if res.avg_f1_score else "N/A"
            cer_str = f"{res.avg_cer:.3f}" if res.avg_cer else "N/A"
            
            html += f"""
        <tr>
            <td>{res.model_name}</td>
            <td class="{'success' if success_rate > 90 else 'failure'}">{success_rate:.1f}%</td>
            <td>{res.avg_processing_time:.2f}</td>
            <td>{f1_str}</td>
            <td>{cer_str}</td>
        </tr>
"""
        
        html += """
    </table>
    
    <h2>Detailed Results by Model</h2>
"""
        
        for model_id, res in results.items():
            html += f"""
    <h3>{res.model_name} ({model_id})</h3>
    <ul>
        <li><span class="metric">Total Images:</span> {res.total_images}</li>
        <li><span class="metric">Successful:</span> <span class="success">{res.successful_images}</span></li>
        <li><span class="metric">Failed:</span> <span class="failure">{res.failed_images}</span></li>
        <li><span class="metric">Avg Time:</span> {res.avg_processing_time:.2f}s</li>
        <li><span class="metric">Total Time:</span> {res.total_processing_time:.2f}s</li>
"""
            if res.avg_f1_score:
                html += f'        <li><span class="metric">Avg F1 Score:</span> {res.avg_f1_score:.3f}</li>\n'
            if res.avg_cer:
                html += f'        <li><span class="metric">Avg CER:</span> {res.avg_cer:.3f}</li>\n'
            
            html += "    </ul>\n"
        
        html += """
</body>
</html>
"""
        return html


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Benchmark text detection models'
    )
    parser.add_argument(
        '--dataset',
        default='tools/benchmarks/data',
        help='Path to test dataset directory'
    )
    parser.add_argument(
        '--output',
        default='tools/benchmarks/results',
        help='Output directory for results'
    )
    parser.add_argument(
        '--models',
        nargs='*',
        help='Specific models to test (default: all)'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'html', 'both'],
        default='both',
        help='Output format'
    )
    
    args = parser.parse_args()
    
    # Create runner
    runner = BenchmarkRunner(
        dataset_dir=args.dataset,
        output_dir=args.output,
        models=args.models
    )
    
    # Run benchmark
    logger.info("Starting benchmark...")
    results = runner.run_benchmark()
    
    if not results:
        logger.error("No results generated")
        return 1
    
    # Save results
    if args.format in ['json', 'both']:
        runner.save_results(results, format='json')
    
    if args.format in ['html', 'both']:
        runner.save_results(results, format='html')
    
    logger.info("\n" + "="*60)
    logger.info("BENCHMARK COMPLETE")
    logger.info("="*60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
