#!/usr/bin/env python3
"""
=============================================================================
Phase 2: Intelligent Analysis Demo
=============================================================================

This script demonstrates the Phase 2 capabilities:
- ML-based pattern clustering
- Anomaly detection for performance regressions
- Historical trend analysis and forecasting
- Code similarity analysis

Run with: python3 scripts/demo_cef_phase2.py
=============================================================================
"""

import sys
import os
from datetime import datetime, timedelta
from random import random, gauss, choice

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.circular_exchange.intelligent_analyzer import (
    INTELLIGENT_ANALYZER,
    PatternClusterer,
    AnomalyDetector,
    TrendAnalyzer,
    CodeEmbeddings,
    AnomalyType,
    TrendDirection,
    ClusterQuality
)


def demo_pattern_clustering():
    """Demonstrate ML-based pattern clustering."""
    print("\n" + "=" * 70)
    print("PHASE 2.1: ML-Based Pattern Clustering")
    print("=" * 70)
    
    clusterer = PatternClusterer(similarity_threshold=0.5)
    
    # Create sample patterns that should cluster together
    patterns = [
        # Connection timeout cluster
        {
            'pattern_id': 'p1',
            'description': 'Connection timeout to database server after 30s',
            'pattern_type': 'error_recurring',
            'occurrences': 15,
            'confidence': 0.85,
            'affected_modules': ['database', 'orm']
        },
        {
            'pattern_id': 'p2', 
            'description': 'Connection timeout to cache server failed',
            'pattern_type': 'error_recurring',
            'occurrences': 12,
            'confidence': 0.80,
            'affected_modules': ['cache', 'redis']
        },
        {
            'pattern_id': 'p3',
            'description': 'Connection timeout error in API gateway',
            'pattern_type': 'error_recurring',
            'occurrences': 8,
            'confidence': 0.75,
            'affected_modules': ['gateway']
        },
        # Memory cluster
        {
            'pattern_id': 'p4',
            'description': 'Memory allocation failed - out of memory',
            'pattern_type': 'error_recurring',
            'occurrences': 7,
            'confidence': 0.90,
            'affected_modules': ['image_processor']
        },
        {
            'pattern_id': 'p5',
            'description': 'Memory overflow error in batch processing',
            'pattern_type': 'error_recurring',
            'occurrences': 5,
            'confidence': 0.88,
            'affected_modules': ['batch']
        },
        # Null pointer cluster
        {
            'pattern_id': 'p6',
            'description': 'Null pointer exception in user handler',
            'pattern_type': 'error_recurring',
            'occurrences': 20,
            'confidence': 0.95,
            'affected_modules': ['user_service']
        },
        {
            'pattern_id': 'p7',
            'description': 'Null reference error - object was None',
            'pattern_type': 'error_recurring',
            'occurrences': 18,
            'confidence': 0.92,
            'affected_modules': ['auth']
        },
    ]
    
    print(f"\nClustering {len(patterns)} patterns...")
    clusters = clusterer.cluster_patterns(patterns)
    
    print(f"\nFound {len(clusters)} clusters:\n")
    
    for i, cluster in enumerate(clusters, 1):
        print(f"  Cluster {i}: {cluster.name}")
        print(f"    - ID: {cluster.cluster_id}")
        print(f"    - Patterns: {len(cluster.pattern_ids)}")
        print(f"    - Total occurrences: {cluster.total_occurrences}")
        print(f"    - Quality: {cluster.quality.value}")
        if cluster.root_cause:
            print(f"    - Root cause: {cluster.root_cause}")
        if cluster.suggested_fix:
            print(f"    - Suggested fix: {cluster.suggested_fix}")
        print()
    
    return len(clusters)


def demo_anomaly_detection():
    """Demonstrate anomaly detection."""
    print("\n" + "=" * 70)
    print("PHASE 2.2: Anomaly Detection for Performance Regressions")
    print("=" * 70)
    
    detector = AnomalyDetector(z_score_threshold=2.0)
    
    # Generate sample latency data with anomalies
    base_time = datetime.now()
    normal_latency = 50.0  # Normal: ~50ms
    
    values = []
    for i in range(48):  # 48 hours of data
        timestamp = base_time - timedelta(hours=48-i)
        
        # Normal operation with some noise
        if i < 40:
            latency = normal_latency + gauss(0, 5)
        # Introduce anomalies in last 8 hours
        elif i == 42:
            latency = 200.0  # Spike
        elif i == 45:
            latency = 180.0  # Another spike
        else:
            latency = normal_latency + gauss(0, 8)
        
        values.append((timestamp, max(10, latency)))
    
    print(f"\nAnalyzing {len(values)} latency measurements...")
    
    anomalies = detector.detect_anomalies('api_latency_ms', values, 'api_gateway')
    
    print(f"\nBaseline calculated:")
    baseline = detector.get_baseline('api_latency_ms')
    if baseline:
        print(f"  - Mean: {baseline['mean']:.2f}ms")
        print(f"  - Std Dev: {baseline['std']:.2f}ms")
        print(f"  - Min: {baseline['min']:.2f}ms")
        print(f"  - Max: {baseline['max']:.2f}ms")
    
    print(f"\nDetected {len(anomalies)} anomalies:\n")
    
    for anomaly in anomalies:
        print(f"  [{anomaly.anomaly_type.value.upper()}]")
        print(f"    - Time: {anomaly.detected_at.strftime('%H:%M:%S')}")
        print(f"    - Expected: {anomaly.expected_value:.2f}ms")
        print(f"    - Actual: {anomaly.actual_value:.2f}ms")
        print(f"    - Deviation: {anomaly.deviation_percent:+.1f}%")
        print(f"    - Severity: {anomaly.severity:.2f}")
        print()
    
    return len(anomalies)


def demo_trend_analysis():
    """Demonstrate trend analysis and forecasting."""
    print("\n" + "=" * 70)
    print("PHASE 2.3: Historical Trend Analysis and Forecasting")
    print("=" * 70)
    
    analyzer = TrendAnalyzer()
    
    # Generate sample data with different trends
    base_time = datetime.now()
    
    # 1. Improving trend (success rate increasing)
    success_rate_values = []
    for i in range(14):
        timestamp = base_time - timedelta(days=14-i)
        rate = 75.0 + i * 1.5 + gauss(0, 2)  # Increasing from 75% to 95%
        success_rate_values.append((timestamp, min(100, max(0, rate))))
    
    # 2. Degrading trend (latency increasing)
    latency_values = []
    for i in range(14):
        timestamp = base_time - timedelta(days=14-i)
        latency = 30.0 + i * 3 + gauss(0, 5)  # Increasing from 30ms to 75ms
        latency_values.append((timestamp, max(10, latency)))
    
    # 3. Stable trend
    stable_values = []
    for i in range(14):
        timestamp = base_time - timedelta(days=14-i)
        value = 50.0 + gauss(0, 2)
        stable_values.append((timestamp, value))
    
    print("\nAnalyzing trends over 14-day window...\n")
    
    # Analyze success rate
    trend1 = analyzer.analyze_trend('success_rate', success_rate_values, '14d')
    if trend1:
        print("  SUCCESS RATE Trend:")
        print(f"    - Direction: {trend1.direction.value}")
        print(f"    - Slope: {trend1.slope:.4f}")
        print(f"    - R-squared: {trend1.r_squared:.3f}")
        print(f"    - Forecast: {trend1.forecast_next_period:.1f}%")
        print(f"    - Confidence: {trend1.forecast_confidence:.2f}")
        if trend1.recommendations:
            print(f"    - Recommendations: {'; '.join(trend1.recommendations[:2])}")
        print()
    
    # Analyze latency
    trend2 = analyzer.analyze_trend('latency_ms', latency_values, '14d')
    if trend2:
        print("  LATENCY Trend:")
        print(f"    - Direction: {trend2.direction.value}")
        print(f"    - Slope: {trend2.slope:.4f}")
        print(f"    - R-squared: {trend2.r_squared:.3f}")
        print(f"    - Forecast: {trend2.forecast_next_period:.1f}ms")
        print(f"    - Confidence: {trend2.forecast_confidence:.2f}")
        if trend2.recommendations:
            print(f"    - Recommendations: {'; '.join(trend2.recommendations[:2])}")
        print()
    
    # Analyze stable metric
    trend3 = analyzer.analyze_trend('memory_usage', stable_values, '14d')
    if trend3:
        print("  MEMORY USAGE Trend:")
        print(f"    - Direction: {trend3.direction.value}")
        print(f"    - Slope: {trend3.slope:.4f}")
        print(f"    - R-squared: {trend3.r_squared:.3f}")
        print()
    
    return 3  # Number of trends analyzed


def demo_code_similarity():
    """Demonstrate code similarity analysis."""
    print("\n" + "=" * 70)
    print("PHASE 2.4: Code Embeddings and Semantic Similarity")
    print("=" * 70)
    
    embeddings = CodeEmbeddings()
    
    # Sample code snippets
    code1 = '''
def process_user_data(user_id):
    try:
        data = fetch_from_database(user_id)
        if data is None:
            return None
        for record in data:
            validate_record(record)
            transform_record(record)
        return save_results(data)
    except DatabaseError as e:
        log_error(e)
        return None
'''
    
    code2 = '''
def handle_customer_info(customer_id):
    try:
        info = get_from_db(customer_id)
        if info is None:
            return None
        for item in info:
            check_item(item)
            convert_item(item)
        return store_output(info)
    except DBException as e:
        log_exception(e)
        return None
'''
    
    code3 = '''
class ImageProcessor:
    def __init__(self, config):
        self.config = config
        self.cache = LRUCache(100)
    
    def process(self, image):
        if image in self.cache:
            return self.cache[image]
        result = self._apply_filters(image)
        self.cache[image] = result
        return result
'''
    
    print("\nComputing code signatures...\n")
    
    sig1 = embeddings.compute_signature('user_data_processor', code1)
    sig2 = embeddings.compute_signature('customer_info_handler', code2)
    sig3 = embeddings.compute_signature('image_processor', code3)
    
    print("  Code Snippet 1: user_data_processor")
    print(f"    - Tokens: {sig1['token_count']}, Unique: {sig1['unique_tokens']}")
    print(f"    - Has function: {sig1['has_function']}")
    print(f"    - Has exception handling: {sig1['has_try_except']}")
    print()
    
    print("  Code Snippet 2: customer_info_handler")
    print(f"    - Tokens: {sig2['token_count']}, Unique: {sig2['unique_tokens']}")
    print(f"    - Has function: {sig2['has_function']}")
    print(f"    - Has exception handling: {sig2['has_try_except']}")
    print()
    
    print("  Code Snippet 3: image_processor")
    print(f"    - Tokens: {sig3['token_count']}, Unique: {sig3['unique_tokens']}")
    print(f"    - Has class: {sig3['has_class']}")
    print(f"    - Has exception handling: {sig3['has_try_except']}")
    print()
    
    print("Computing similarities...\n")
    
    sim1_2 = embeddings.compute_similarity('user_data_processor', 'customer_info_handler')
    sim1_3 = embeddings.compute_similarity('user_data_processor', 'image_processor')
    sim2_3 = embeddings.compute_similarity('customer_info_handler', 'image_processor')
    
    print(f"  user_data_processor <-> customer_info_handler")
    print(f"    - Similarity: {sim1_2.similarity_score:.2%}")
    print(f"    - Type: {sim1_2.similarity_type}")
    print(f"    - Common patterns: {', '.join(sim1_2.common_patterns)}")
    if sim1_2.suggested_refactoring:
        print(f"    - Suggestion: {sim1_2.suggested_refactoring}")
    print()
    
    print(f"  user_data_processor <-> image_processor")
    print(f"    - Similarity: {sim1_3.similarity_score:.2%}")
    print(f"    - Type: {sim1_3.similarity_type}")
    print()
    
    print(f"  customer_info_handler <-> image_processor")
    print(f"    - Similarity: {sim2_3.similarity_score:.2%}")
    print(f"    - Type: {sim2_3.similarity_type}")
    print()
    
    return 3  # Number of comparisons


def demo_full_analysis():
    """Demonstrate full intelligent analysis cycle."""
    print("\n" + "=" * 70)
    print("PHASE 2.5: Full Intelligent Analysis Cycle")
    print("=" * 70)
    
    analyzer = INTELLIGENT_ANALYZER
    
    print("\nRunning full intelligent analysis...")
    print("(This integrates with DataCollector and MetricsAnalyzer if data available)")
    
    results = analyzer.run_full_analysis()
    
    print("\nAnalysis Summary:")
    print(f"  - Clusters found: {results['summary'].get('clusters_found', 0)}")
    print(f"  - Anomalies detected: {results['summary'].get('anomalies_detected', 0)}")
    print(f"  - Trends analyzed: {results['summary'].get('trends_analyzed', 0)}")
    print(f"  - High severity anomalies: {results['summary'].get('high_severity_anomalies', 0)}")
    
    print("\nIntelligent Analyzer State:")
    summary = analyzer.get_summary()
    print(f"  - Total clusters: {summary['total_clusters']}")
    print(f"  - Total anomalies: {summary['total_anomalies']}")
    print(f"  - Metrics with baselines: {len(summary['metrics_with_baselines'])}")
    print(f"  - Analysis runs: {summary['analysis_runs']}")
    
    return 1


def main():
    """Run all Phase 2 demos."""
    print("=" * 70)
    print("CEF PHASE 2: INTELLIGENT ANALYSIS")
    print("ML-Based Pattern Analysis and Anomaly Detection")
    print("=" * 70)
    print(f"\nTimestamp: {datetime.now().isoformat()}")
    
    # Track results
    results = {}
    
    # Run demos
    results['clusters'] = demo_pattern_clustering()
    results['anomalies'] = demo_anomaly_detection()
    results['trends'] = demo_trend_analysis()
    results['similarities'] = demo_code_similarity()
    results['full_analysis'] = demo_full_analysis()
    
    # Print summary
    print("\n" + "=" * 70)
    print("PHASE 2 SUMMARY")
    print("=" * 70)
    print(f"""
    ✅ Pattern Clustering: {results['clusters']} clusters identified
    ✅ Anomaly Detection: {results['anomalies']} anomalies detected
    ✅ Trend Analysis: {results['trends']} metrics analyzed
    ✅ Code Similarity: {results['similarities']} comparisons made
    ✅ Full Analysis: {results['full_analysis']} cycle completed
    
    Phase 2 Capabilities:
    ---------------------
    • ML-based pattern clustering without external dependencies
    • Z-score based anomaly detection with baseline learning
    • Linear regression trend analysis with forecasting
    • Lightweight code similarity using token features
    • Integrated analysis orchestration
    
    Next: Phase 3 (Autonomous Refactoring)
    - Auto-apply low-risk suggestions
    - PR generation for medium-risk changes
    - A/B testing for config tuning
    - Automatic rollback on metric degradation
    """)
    
    print("=" * 70)
    print("Phase 2 demo complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
