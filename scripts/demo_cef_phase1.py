#!/usr/bin/env python3
"""
CEF Development Path Implementation Demo
=========================================

This script demonstrates the newly implemented features from the CEF development path:

Phase 1: Production Hardening (IMPLEMENTED)
1. Webhook Notifier - Real-time notifications for critical insights
2. SQLite Persistence - Persistent storage for collected data  
3. CI/CD Integration - GitHub Actions workflow for automated CEF cycles

Run with: python3 scripts/demo_cef_phase1.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import json


def demo_webhook_notifier():
    """Demonstrate the webhook notification system."""
    print("\n" + "=" * 60)
    print("WEBHOOK NOTIFIER DEMO")
    print("=" * 60)
    
    from shared.circular_exchange.webhook_notifier import (
        WEBHOOK_NOTIFIER, NotificationConfig, NotificationChannel, NotificationLevel
    )
    
    # Add a test endpoint (will fail but demonstrates the API)
    print("\n📧 Adding test notification endpoint...")
    WEBHOOK_NOTIFIER.add_endpoint(NotificationConfig(
        channel=NotificationChannel.WEBHOOK,
        url="https://httpbin.org/post",  # Test endpoint
        name="test_endpoint",
        min_level=NotificationLevel.INFO,
        enabled=True
    ))
    
    # Show configured endpoints
    print("\n📋 Configured endpoints:")
    for endpoint in WEBHOOK_NOTIFIER.get_endpoints():
        print(f"   - {endpoint['name']} ({endpoint['channel']}): {endpoint['url']}")
    
    # Send a test notification
    print("\n📤 Sending test notification...")
    result = WEBHOOK_NOTIFIER.notify(
        title="CEF Test Notification",
        message="This is a test notification from the CEF Phase 1 demo.",
        level=NotificationLevel.INFO,
        source="demo_script",
        data={"demo": True, "timestamp": datetime.now().isoformat()},
        tags=["test", "demo"]
    )
    print(f"   Notification sent: {result}")
    
    # Show stats
    print("\n📊 Notification stats:")
    stats = WEBHOOK_NOTIFIER.get_stats()
    for key, value in stats.items():
        print(f"   - {key}: {value}")
    
    # Show history
    print("\n📜 Notification history:")
    for notif in WEBHOOK_NOTIFIER.get_history(limit=5):
        print(f"   [{notif.level.value}] {notif.title} ({notif.timestamp.strftime('%H:%M:%S')})")


def demo_persistence_layer():
    """Demonstrate the SQLite persistence layer."""
    print("\n" + "=" * 60)
    print("PERSISTENCE LAYER DEMO")
    print("=" * 60)
    
    from shared.circular_exchange.persistence import PERSISTENCE_LAYER
    from shared.circular_exchange.data_collector import TestResult, TestStatus, LogEntry, ExtractionEvent
    
    print("\n💾 SQLite Persistence Layer")
    print(f"   Database: {PERSISTENCE_LAYER.config.db_path}")
    
    # Save some test results
    print("\n📝 Saving test results...")
    for i in range(5):
        result = TestResult(
            test_id=f"test_{i}",
            test_name=f"test_function_{i}",
            module_path="tests/demo_test.py",
            status=TestStatus.PASSED if i % 2 == 0 else TestStatus.FAILED,
            duration_ms=100 + i * 50,
            error_message="Demo error" if i % 2 != 0 else None
        )
        PERSISTENCE_LAYER.save_test_result(result)
    print("   Saved 5 test results")
    
    # Save some log entries
    print("\n📝 Saving log entries...")
    for i in range(3):
        entry = LogEntry(
            log_id=f"log_{i}",
            level="ERROR" if i == 0 else "INFO",
            message=f"Demo log message {i}",
            module="demo_module",
            function="demo_function",
            line_number=100 + i
        )
        PERSISTENCE_LAYER.save_log_entry(entry)
    print("   Saved 3 log entries")
    
    # Save extraction events
    print("\n📝 Saving extraction events...")
    for i in range(3):
        event = ExtractionEvent(
            event_id=f"extract_{i}",
            model_id="donut_v1",
            image_path=f"/images/test_{i}.jpg",
            success=i != 1,
            processing_time_ms=500 + i * 100,
            confidence_score=0.85 - i * 0.1
        )
        PERSISTENCE_LAYER.save_extraction_event(event)
    print("   Saved 3 extraction events")
    
    # Query data
    print("\n🔍 Querying data...")
    
    test_results = PERSISTENCE_LAYER.query_test_results(limit=3)
    print(f"   Test results: {len(test_results)} records")
    
    log_entries = PERSISTENCE_LAYER.query_log_entries(level="ERROR", limit=5)
    print(f"   Error logs: {len(log_entries)} records")
    
    extractions = PERSISTENCE_LAYER.query_extraction_events(success=True, limit=5)
    print(f"   Successful extractions: {len(extractions)} records")
    
    # Show stats
    print("\n📊 Database statistics:")
    stats = PERSISTENCE_LAYER.get_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   - {key}: {value:.2%}")
        else:
            print(f"   - {key}: {value}")


def demo_ci_integration():
    """Demonstrate the CI/CD integration."""
    print("\n" + "=" * 60)
    print("CI/CD INTEGRATION")
    print("=" * 60)
    
    workflow_path = ".github/workflows/cef-pipeline.yml"
    
    print(f"\n📁 GitHub Actions workflow: {workflow_path}")
    print("\n🔧 Features:")
    print("   1. Automated test collection on push/PR")
    print("   2. Full CEF analysis cycle")
    print("   3. Pattern detection and insight generation")
    print("   4. Webhook notifications for critical events")
    print("   5. Scheduled daily analysis (cron)")
    print("   6. Manual trigger support")
    print("   7. Automatic data cleanup")
    
    print("\n📋 Workflow Jobs:")
    print("   1. test-and-collect: Run tests and collect CEF data")
    print("   2. cef-analysis: Analyze patterns and generate insights")
    print("   3. notify: Send webhook notifications")
    print("   4. cleanup: Remove data older than 30 days")
    
    print("\n🔐 Required Secrets:")
    print("   - WEBHOOK_ENDPOINT_CEF: URL for CEF notifications")


def demo_cef_subscriptions():
    """Demonstrate CEF auto-notifications."""
    print("\n" + "=" * 60)
    print("CEF AUTO-NOTIFICATIONS DEMO")
    print("=" * 60)
    
    from shared.circular_exchange.webhook_notifier import WEBHOOK_NOTIFIER
    from shared.circular_exchange.data_collector import DATA_COLLECTOR, TestResult, TestStatus, DataCategory
    from shared.circular_exchange.metrics_analyzer import METRICS_ANALYZER, InsightPriority
    
    # Set up CEF subscriptions
    print("\n🔗 Setting up CEF subscriptions...")
    WEBHOOK_NOTIFIER.setup_cef_subscriptions()
    print("   ✅ Subscribed to patterns")
    print("   ✅ Subscribed to insights")
    print("   ✅ Subscribed to test failures")
    
    # Simulate a critical insight
    print("\n🚨 Simulating critical insight generation...")
    from shared.circular_exchange.metrics_analyzer import Insight, RefactorCategory
    
    insight = Insight(
        insight_id="demo_insight_001",
        title="Critical Performance Issue Detected",
        description="Average API response time exceeds 5 seconds",
        priority=InsightPriority.CRITICAL,
        category=RefactorCategory.PERFORMANCE,
        recommended_actions=["Add caching", "Optimize database queries"],
        estimated_impact="50% reduction in response time"
    )
    
    # Notify subscribers
    METRICS_ANALYZER._notify_insight_subscribers(insight)
    print("   ✅ Critical insight notification triggered")
    
    # Show notification history
    print("\n📜 Recent notifications:")
    for notif in WEBHOOK_NOTIFIER.get_history(limit=5):
        print(f"   [{notif.level.value.upper():8}] {notif.title}")


def main():
    """Run all Phase 1 demos."""
    print("\n" + "=" * 60)
    print("CEF DEVELOPMENT PATH - PHASE 1 IMPLEMENTATION")
    print("=" * 60)
    print("\nPhase 1: Production Hardening")
    print("   ✅ Webhook Notifications")
    print("   ✅ SQLite Persistence Layer")
    print("   ✅ GitHub Actions CI/CD Integration")
    
    demo_webhook_notifier()
    demo_persistence_layer()
    demo_ci_integration()
    demo_cef_subscriptions()
    
    print("\n" + "=" * 60)
    print("PHASE 1 DEMO COMPLETE")
    print("=" * 60)
    print("\n📌 Next Steps (Phase 2: Intelligent Analysis):")
    print("   - ML-based pattern clustering")
    print("   - Anomaly detection for performance regressions")
    print("   - Code embedding models for semantic similarity")
    print("   - Historical trend analysis and forecasting")


if __name__ == "__main__":
    main()
