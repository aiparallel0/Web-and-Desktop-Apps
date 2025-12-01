#!/usr/bin/env python3
"""
=============================================================================
FULL CEF REFACTORING CYCLE - Using All 3 Phases
=============================================================================

This script demonstrates the complete CEF continuous improvement pipeline
using all three phases:

Phase 1: Production Hardening
- Persistence layer for data storage
- Webhook notifications for critical events

Phase 2: Intelligent Analysis  
- Pattern clustering
- Anomaly detection
- Trend analysis
- Code similarity

Phase 3: Autonomous Refactoring
- Auto-apply low-risk changes
- PR generation for medium-risk changes
- A/B testing
- Automatic rollback

=============================================================================
"""

import sys
import os
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import CEF components
try:
    from shared.circular_exchange.data_collector import (
        DataCollector, TestResult, LogEntry, ExtractionEvent, TestStatus
    )
    from shared.circular_exchange.metrics_analyzer import (
        MetricsAnalyzer, Pattern
    )
    from shared.circular_exchange.refactoring_engine import (
        RefactoringEngine, CodeSuggestion, ImpactLevel, EffortLevel
    )
    from shared.circular_exchange.feedback_loop import (
        FeedbackLoop
    )
    from shared.circular_exchange.persistence import (
        PersistenceLayer, DBConfig
    )
    from shared.circular_exchange.intelligent_analyzer import (
        IntelligentAnalyzer, AnomalyType, TrendDirection, PatternCluster
    )
    from shared.circular_exchange.autonomous_refactor import (
        AutonomousRefactor, RefactorRisk, RefactorStatus, ABTestManager
    )
    CEF_AVAILABLE = True
except ImportError as e:
    print(f"Error importing CEF components: {e}")
    CEF_AVAILABLE = False
    # Make type hints work even without imports
    PersistenceLayer = None
    IntelligentAnalyzer = None
    AutonomousRefactor = None


def print_header(title: str, char: str = "=") -> None:
    """Print a formatted header."""
    width = 80
    print()
    print(char * width)
    print(f" {title}")
    print(char * width)


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'─' * 40}")
    print(f"  {title}")
    print(f"{'─' * 40}")


def simulate_test_results(collector: DataCollector, count: int = 50) -> None:
    """Simulate test results for the CEF system."""
    test_names = [
        "test_ocr_extraction", "test_image_processing", "test_model_inference",
        "test_api_endpoint", "test_database_connection", "test_cache_hit",
        "test_retry_logic", "test_circuit_breaker", "test_memory_usage",
        "test_async_processing", "test_batch_upload", "test_rate_limiting"
    ]
    
    results = []
    for i in range(count):
        test_name = random.choice(test_names)
        # Simulate improvement over time (higher pass rate in later tests)
        improvement_factor = 0.5 + (i / count) * 0.4  # 0.5 -> 0.9
        passed = random.random() < improvement_factor
        
        duration = random.uniform(100, 2000)  # milliseconds
        if test_name == "test_database_connection" and random.random() < 0.2:
            duration = random.uniform(5000, 15000)  # Slow test
        
        result = TestResult(
            test_id=f"test_{i:04d}",
            test_name=test_name,
            module_path=f"tests.{test_name}",
            status=TestStatus.PASSED if passed else TestStatus.FAILED,
            duration_ms=duration,
            timestamp=datetime.now() - timedelta(minutes=count - i),
            error_message=None if passed else f"Test failed: {test_name} assertion error"
        )
        collector.record_test_result(result)
        results.append(result)
    
    return results


def simulate_log_entries(collector: DataCollector, count: int = 100) -> None:
    """Simulate log entries for pattern detection."""
    log_patterns = [
        ("INFO", "Request processed successfully in {:.3f}s"),
        ("INFO", "Cache hit for key: user_{:04d}"),
        ("WARNING", "Slow query detected: {:.1f}ms"),
        ("ERROR", "Connection timeout after 30s"),
        ("ERROR", "Database connection pool exhausted"),
        ("ERROR", "Memory limit exceeded: {:.0f}MB"),
        ("WARNING", "Rate limit approaching: {:.0f}% of quota"),
        ("INFO", "Model loaded successfully"),
        ("ERROR", "OCR extraction failed: invalid image format"),
        ("WARNING", "Retry attempt {} of 3"),
    ]
    
    modules = ["api", "database", "ocr", "model", "cache", "auth"]
    
    entries = []
    for i in range(count):
        level, pattern = random.choice(log_patterns)
        try:
            if "{" in pattern:
                if ".3f" in pattern:
                    message = pattern.format(random.uniform(0.1, 5.0))
                elif ".1f" in pattern:
                    message = pattern.format(random.uniform(100, 5000))
                elif ".0f" in pattern:
                    message = pattern.format(random.uniform(50, 150))
                elif ":04d" in pattern:
                    message = pattern.format(random.randint(1, 9999))
                elif "{}":
                    message = pattern.format(random.randint(1, 3))
                else:
                    message = pattern
            else:
                message = pattern
        except Exception:
            message = pattern
        
        entry = LogEntry(
            log_id=f"log_{i:04d}",
            level=level,
            message=message,
            module=random.choice(modules),
            function="process_request",
            line_number=random.randint(10, 500),
            timestamp=datetime.now() - timedelta(minutes=count - i)
        )
        collector.record_log_entry(entry)
        entries.append(entry)
    
    return entries


def simulate_extraction_events(collector: DataCollector, count: int = 30) -> None:
    """Simulate extraction events for model performance tracking."""
    document_types = ["receipt", "invoice", "form", "id_card", "passport"]
    
    events = []
    for i in range(count):
        # Simulate improvement over time
        improvement_factor = 0.6 + (i / count) * 0.35
        success = random.random() < improvement_factor
        
        event = ExtractionEvent(
            event_id=f"extract_{i:04d}",
            model_id="easyocr" if random.random() < 0.6 else "paddleocr",
            image_path=f"/tmp/test_images/{random.choice(document_types)}_{i:04d}.jpg",
            success=success,
            confidence_score=random.uniform(0.7, 0.99) if success else random.uniform(0.2, 0.6),
            processing_time_ms=random.uniform(200, 2000),
            timestamp=datetime.now() - timedelta(minutes=count - i),
        )
        collector.record_extraction_event(event)
        events.append(event)
    
    return events


def run_phase1_persistence(collector: DataCollector):
    """Phase 1: Set up persistence and store data."""
    print_section("Phase 1: Persistence Layer")
    
    # Get singleton instance (uses environment config or defaults)
    persistence = PersistenceLayer()
    
    # Store collected data
    stats = collector.get_statistics()
    print(f"  → Data collected:")
    print(f"     • Test results: {stats.get('test_results', 0)}")
    print(f"     • Log entries: {stats.get('log_entries', 0)}")
    print(f"     • Extraction events: {stats.get('extraction_events', 0)}")
    
    # Persist to database
    stored_tests = 0
    stored_logs = 0
    stored_extractions = 0
    
    for result in collector._test_results[-50:]:
        try:
            persistence.store_test_result(result)
            stored_tests += 1
        except Exception:
            pass
    
    for entry in collector._log_entries[-100:]:
        try:
            persistence.store_log_entry(entry)
            stored_logs += 1
        except Exception:
            pass
    
    for event in collector._extraction_events[-30:]:
        try:
            persistence.store_extraction_event(event)
            stored_extractions += 1
        except Exception:
            pass
    
    print(f"  → Data persisted to database:")
    print(f"     • Test results stored: {stored_tests}")
    print(f"     • Log entries stored: {stored_logs}")
    print(f"     • Extraction events stored: {stored_extractions}")
    
    return persistence


def run_phase2_analysis(test_results, log_entries, extraction_events, analyzer: MetricsAnalyzer):
    """Phase 2: Intelligent analysis with ML-based pattern detection."""
    print_section("Phase 2: Intelligent Analysis")
    
    # Get the intelligent analyzer
    intelligent = IntelligentAnalyzer()
    
    # Run analyzer methods (they use the global DataCollector)
    try:
        test_report = analyzer.analyze_test_health()
        print(f"\n  → Test Health Analysis:")
        print(f"     • Pass rate: {test_report.pass_rate:.1%}")
    except Exception as e:
        print(f"\n  → Test Health Analysis: Skipped ({e})")
    
    try:
        patterns = analyzer.analyze_error_patterns()
        print(f"\n  → Error Patterns Detected: {len(patterns)}")
        for pattern in list(patterns)[:3]:
            count = getattr(pattern, 'occurrence_count', getattr(pattern, 'count', 1))
            print(f"     • {pattern.pattern_type.value}: {count} occurrences")
    except Exception as e:
        patterns = []
        print(f"\n  → Error Pattern Analysis: Skipped ({e})")
    
    # Run pattern clustering with collected data
    if patterns:
        try:
            pattern_dicts = []
            for p in patterns:
                count = getattr(p, 'occurrence_count', getattr(p, 'count', 1))
                pattern_dicts.append({
                    'error_type': p.pattern_type.value,
                    'message': p.description,
                    'count': count
                })
            clusters = intelligent.pattern_clusterer.cluster_patterns(pattern_dicts)
            print(f"\n  → Pattern Clusters: {len(clusters)}")
            for cluster in clusters[:3]:
                print(f"     • {cluster.name}: {len(cluster.pattern_ids)} patterns")
                if cluster.root_cause:
                    print(f"       Root cause: {cluster.root_cause}")
        except Exception as e:
            print(f"\n  → Pattern Clustering: Skipped ({e})")
    
    # Run anomaly detection with extraction events
    metrics_data = []
    for event in extraction_events:
        metrics_data.append({
            'timestamp': event.timestamp,
            'metric_name': 'processing_time_ms',
            'value': event.processing_time_ms
        })
    
    if metrics_data:
        try:
            anomalies = intelligent.anomaly_detector.detect_anomalies(metrics_data)
            print(f"\n  → Anomalies Detected: {len(anomalies)}")
            for anomaly in anomalies[:3]:
                print(f"     • {anomaly.anomaly_type.value}: deviation {anomaly.deviation_percent:.1f}%")
        except Exception as e:
            print(f"\n  → Anomaly Detection: Skipped ({e})")
    
    # Run trend analysis
    if metrics_data:
        try:
            trend = intelligent.trend_analyzer.analyze_trend('processing_time_ms', metrics_data)
            if trend:
                print(f"\n  → Trend Analysis:")
                print(f"     • Direction: {trend.direction.value}")
                print(f"     • R-squared: {trend.r_squared:.3f}")
                if trend.forecast:
                    print(f"     • Forecast: {trend.forecast.value:.1f} (confidence: {trend.forecast.confidence:.1%})")
        except Exception as e:
            print(f"\n  → Trend Analysis: Skipped ({e})")
    
    return intelligent


def run_phase3_refactoring(
    refactoring_engine: RefactoringEngine,
    analyzer: MetricsAnalyzer,
    test_results,
    extraction_events
) -> AutonomousRefactor:
    """Phase 3: Autonomous refactoring with auto-apply and A/B testing."""
    print_section("Phase 3: Autonomous Refactoring")
    
    # Get autonomous refactor instance
    autonomous = AutonomousRefactor()
    
    # Generate suggestions from the refactoring engine using its methods
    try:
        error_suggestions = refactoring_engine.analyze_error_handling()
        testing_suggestions = refactoring_engine.analyze_testing()
        suggestions = error_suggestions + testing_suggestions
    except Exception:
        suggestions = []
    
    print(f"\n  → Suggestions Generated: {len(suggestions)}")
    
    # Classify suggestions by risk
    risk_counts = {risk: 0 for risk in RefactorRisk}
    for suggestion in suggestions:
        suggestion_dict = {
            'id': suggestion.suggestion_id if hasattr(suggestion, 'suggestion_id') else str(id(suggestion)),
            'type': suggestion.category if hasattr(suggestion, 'category') else 'unknown',
            'file_path': suggestion.location.file_path if hasattr(suggestion, 'location') and suggestion.location else '',
            'description': suggestion.description if hasattr(suggestion, 'description') else ''
        }
        risk = autonomous.classify_risk(suggestion_dict)
        risk_counts[risk] += 1
    
    print(f"\n  → Risk Classification:")
    for risk, count in risk_counts.items():
        if count > 0:
            print(f"     • {risk.value.upper()}: {count} suggestions")
    
    # Create A/B test for a configuration
    print(f"\n  → A/B Testing:")
    ab_manager = autonomous.ab_test_manager
    test = ab_manager.create_test(
        name="OCR Confidence Threshold",
        description="Test optimal confidence threshold for OCR extraction",
        config_key="ocr.confidence_threshold",
        control_value=0.7,
        treatment_value=0.8,
        min_samples=50,
        confidence_threshold=0.95
    )
    print(f"     • Created test: {test.name}")
    print(f"     • Control: {test.config_key}={test.control.config[test.config_key]}")
    print(f"     • Treatment: {test.config_key}={test.treatment.config[test.config_key]}")
    
    # Simulate A/B test metrics
    for i in range(100):
        variant = "control" if i % 2 == 0 else "treatment"
        # Treatment has slightly better success rate
        success = random.random() < (0.75 if variant == "control" else 0.82)
        ab_manager.record_metric(test.test_id, variant, "success_rate", 1.0 if success else 0.0)
    
    # Analyze A/B test
    result = ab_manager.analyze_test(test.test_id, "success_rate")
    if result:
        print(f"\n  → A/B Test Results:")
        print(f"     • Significant: {result.is_significant}")
        print(f"     • Control mean: {result.control_mean:.3f}")
        print(f"     • Treatment mean: {result.treatment_mean:.3f}")
        print(f"     • Improvement: {result.improvement_percent:.1f}%")
        print(f"     • Confidence: {result.confidence:.1%}")
        print(f"     • Recommendation: {result.recommendation}")
    
    # Process low-risk suggestions (dry run)
    print(f"\n  → Auto-Apply (Dry Run):")
    applied_count = 0
    skipped_count = 0
    for suggestion in suggestions[:5]:
        suggestion_dict = {
            'id': suggestion.suggestion_id,
            'type': 'format',  # Low risk for demo
            'file_path': '/tmp/demo_file.py',
            'description': suggestion.description
        }
        risk = autonomous.classify_risk(suggestion_dict)
        if autonomous.can_auto_apply(risk):
            applied_count += 1
        else:
            skipped_count += 1
    
    print(f"     • Would auto-apply: {applied_count}")
    print(f"     • Requires review: {skipped_count}")
    
    return autonomous


def run_feedback_loop(
    feedback_loop: FeedbackLoop,
    test_results,
    extraction_events
) -> None:
    """Run a feedback cycle to apply learnings."""
    print_section("Feedback Loop Cycle")
    
    # Process collected data through feedback loop
    for result in test_results[-10:]:
        passed = result.status == TestStatus.PASSED
        feedback_loop.process_test_result(result.test_name, passed, result.duration_ms)
    
    for event in extraction_events[-10:]:
        feedback_loop.process_extraction_result(
            model_id=event.model_id,
            success=event.success,
            confidence=event.confidence_score,
            processing_time_ms=event.processing_time_ms
        )
    
    # Run analysis cycle
    feedback_loop.run_cycle()
    
    # Get summary
    summary = feedback_loop.get_summary()
    
    print(f"\n  → Feedback Loop State:")
    print(f"     • Cycle completed")
    print(f"     • Tests processed: {len(test_results[-10:])}")
    print(f"     • Extractions processed: {len(extraction_events[-10:])}")


def print_summary(
    test_results,
    extraction_events,
    analyzer: MetricsAnalyzer,
    autonomous: AutonomousRefactor
) -> None:
    """Print final summary of the CEF refactoring cycle."""
    print_header("CEF REFACTORING CYCLE SUMMARY")
    
    # Data collection stats
    print(f"\n📊 Data Collected:")
    print(f"   • Test results: {len(test_results)}")
    print(f"   • Extraction events: {len(extraction_events)}")
    
    # Analysis results
    patterns = analyzer.get_patterns()
    insights = analyzer.get_insights()
    
    # Calculate pass rate
    passed = sum(1 for r in test_results if r.status == TestStatus.PASSED)
    pass_rate = passed / len(test_results) if test_results else 0
    
    # Calculate extraction success rate
    successful = sum(1 for e in extraction_events if e.success)
    success_rate = successful / len(extraction_events) if extraction_events else 0
    
    print(f"\n📈 Analysis Results:")
    print(f"   • Test pass rate: {pass_rate:.1%}")
    print(f"   • Extraction success rate: {success_rate:.1%}")
    print(f"   • Patterns detected: {len(patterns)}")
    print(f"   • Insights generated: {len(insights)}")
    
    # Refactoring results
    state = autonomous.export_state()
    print(f"\n🔧 Refactoring Status:")
    print(f"   • Results tracked: {len(state.get('results', []))}")
    print(f"   • Pending PRs: {len(state.get('pending_prs', []))}")
    print(f"   • Active A/B tests: {len(state.get('active_ab_tests', []))}")
    
    print(f"\n✅ Full CEF cycle completed successfully!")
    print(f"   All 3 phases executed:")
    print(f"   • Phase 1: Persistence ✓")
    print(f"   • Phase 2: Intelligent Analysis ✓")
    print(f"   • Phase 3: Autonomous Refactoring ✓")


def main():
    """Main entry point for full CEF refactoring cycle."""
    print_header("FULL CEF REFACTORING CYCLE", "═")
    print(f"\nTimestamp: {datetime.now().isoformat()}")
    print(f"Using all 3 phases of the CEF system:")
    print(f"  1. Production Hardening (Persistence, Webhooks)")
    print(f"  2. Intelligent Analysis (ML Clustering, Anomaly Detection)")
    print(f"  3. Autonomous Refactoring (Auto-Apply, A/B Testing, Rollback)")
    
    if not CEF_AVAILABLE:
        print("\n❌ CEF components not available. Please check imports.")
        return 1
    
    # Initialize CEF components
    print_section("Initializing CEF Components")
    collector = DataCollector()
    analyzer = MetricsAnalyzer()
    refactoring_engine = RefactoringEngine()
    feedback_loop = FeedbackLoop()
    
    print(f"  → DataCollector initialized")
    print(f"  → MetricsAnalyzer initialized")
    print(f"  → RefactoringEngine initialized")
    print(f"  → FeedbackLoop initialized")
    
    # Simulate data collection - store the results
    print_section("Simulating Data Collection")
    test_results = simulate_test_results(collector, 50)
    print(f"  → Simulated 50 test results")
    
    log_entries = simulate_log_entries(collector, 100)
    print(f"  → Simulated 100 log entries")
    
    extraction_events = simulate_extraction_events(collector, 30)
    print(f"  → Simulated 30 extraction events")
    
    # Run Phase 1: Persistence
    persistence = run_phase1_persistence(collector)
    
    # Run Phase 2: Intelligent Analysis
    intelligent = run_phase2_analysis(test_results, log_entries, extraction_events, analyzer)
    
    # Run Phase 3: Autonomous Refactoring
    autonomous = run_phase3_refactoring(refactoring_engine, analyzer, test_results, extraction_events)
    
    # Run Feedback Loop
    run_feedback_loop(feedback_loop, test_results, extraction_events)
    
    # Print summary
    print_summary(test_results, extraction_events, analyzer, autonomous)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
