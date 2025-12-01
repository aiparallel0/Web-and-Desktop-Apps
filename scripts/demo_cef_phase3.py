#!/usr/bin/env python3
"""
Demo script for CEF Phase 3: Autonomous Refactoring

This script demonstrates the capabilities of the autonomous refactoring system:
1. Auto-apply low-risk suggestions (formatting, type hints)
2. PR generation for medium-risk changes
3. A/B testing framework for config tuning
4. Automatic rollback on metric degradation
"""

import sys
import os
import tempfile
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.circular_exchange.autonomous_refactor import (
    AutonomousRefactor,
    RefactorRisk,
    RefactorStatus,
    ABTestManager,
    RollbackManager,
    RollbackTrigger,
    get_autonomous_refactor
)


def print_header(title: str) -> None:
    """Print a section header."""
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)
    print()


def print_result(label: str, value: str, indent: int = 0) -> None:
    """Print a labeled result."""
    prefix = "  " * indent
    print(f"{prefix}• {label}: {value}")


def demo_auto_apply_low_risk():
    """Demonstrate auto-applying low-risk refactorings."""
    print_header("1. Auto-Apply Low-Risk Refactorings")
    
    # Create a temporary file with messy code
    temp_dir = tempfile.mkdtemp()
    test_file = Path(temp_dir) / "messy_code.py"
    
    messy_code = '''def   calculate_total(items ):   
    total=0   
    for item in items:   
	total += item.price   
    return total   

def process_data( data):
    result = []
    for d in data:
        result.append(d * 2)   
    return result
'''
    test_file.write_text(messy_code)
    
    print("Original Code (with issues):")
    print("-" * 40)
    print(messy_code[:200] + "...")
    print("-" * 40)
    
    # Get the autonomous refactor instance
    refactor = get_autonomous_refactor()
    
    # Apply formatting (low risk)
    suggestion = {
        'id': 'format_001',
        'type': 'format',
        'file_path': str(test_file),
        'description': 'Apply code formatting'
    }
    
    result = refactor.apply_low_risk_refactoring(str(test_file), suggestion)
    
    print()
    print("Refactoring Result:")
    print_result("Suggestion ID", result.suggestion_id)
    print_result("Risk Level", result.risk.value)
    print_result("Status", result.status.value)
    print_result("Backup Created", "Yes" if result.backup_path else "No")
    
    if result.status == RefactorStatus.APPLIED:
        print()
        print("Formatted Code:")
        print("-" * 40)
        print(test_file.read_text()[:200] + "...")
        print("-" * 40)
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    return result


def demo_pr_generation():
    """Demonstrate PR generation for medium-risk changes."""
    print_header("2. PR Generation for Medium-Risk Changes")
    
    refactor = get_autonomous_refactor()
    
    # Create a medium-risk suggestion
    suggestion = {
        'id': 'rename_001',
        'type': 'rename',
        'file_path': 'shared/models/processors.py',
        'description': 'Rename variable for clarity',
        'suggested_code': '''def process_image(img):
    """Process an image for OCR."""
    processed_image = preprocess(img)
    return processed_image
''',
        'expected_impact': {
            'readability': 0.15,
            'maintainability': 0.10
        }
    }
    
    # Process the suggestion
    result = refactor.process_suggestion(suggestion)
    
    print("Medium-Risk Suggestion:")
    print_result("Suggestion ID", suggestion['id'])
    print_result("Type", suggestion['type'])
    print_result("Risk", result.risk.value)
    print_result("Status", result.status.value)
    
    # Check pending PRs
    pending_prs = refactor.get_pending_prs()
    print()
    print(f"Pending PRs Generated: {len(pending_prs)}")
    
    if pending_prs:
        pr = pending_prs[-1]
        print()
        print("Latest PR Preview:")
        print_result("Branch", pr['branch_name'], indent=1)
        print_result("Title", pr['title'], indent=1)
        print()
        print("PR Description (excerpt):")
        print("-" * 40)
        print(pr['description'][:500] + "...")
        print("-" * 40)
    
    return result


def demo_ab_testing():
    """Demonstrate A/B testing framework."""
    print_header("3. A/B Testing Framework")
    
    refactor = get_autonomous_refactor()
    ab_manager = refactor.ab_test_manager
    
    # Create an A/B test
    test = ab_manager.create_test(
        name="Timeout Configuration",
        description="Testing if longer timeout improves success rate",
        config_key="OCR_TIMEOUT",
        control_value=30,
        treatment_value=60,
        min_samples=10,  # Low for demo
        confidence_threshold=0.90
    )
    
    print("A/B Test Created:")
    print_result("Test ID", test.test_id)
    print_result("Name", test.name)
    print_result("Config Key", test.config_key)
    print_result("Control Value", str(test.control.config[test.config_key]))
    print_result("Treatment Value", str(test.treatment.config[test.config_key]))
    print_result("Min Samples", str(test.min_samples))
    
    # Simulate some data
    import random
    print()
    print("Simulating traffic allocation and metrics...")
    
    for i in range(20):
        variant = ab_manager.get_variant(test.test_id)
        # Simulate that treatment performs slightly better
        if variant == "control":
            success = 0.80 + random.uniform(-0.1, 0.1)
        else:
            success = 0.85 + random.uniform(-0.1, 0.1)
        ab_manager.record_metric(test.test_id, variant, "success_rate", success)
    
    # Analyze results
    result = ab_manager.analyze_test(test.test_id, "success_rate")
    
    print()
    print("A/B Test Analysis:")
    print_result("Control Mean", f"{result.control_mean:.3f}")
    print_result("Treatment Mean", f"{result.treatment_mean:.3f}")
    print_result("Improvement", f"{result.improvement_percent:+.1f}%")
    print_result("Confidence", f"{result.confidence:.1%}")
    print_result("Significant", "Yes" if result.is_significant else "No")
    print_result("Recommendation", result.recommendation)
    
    return result


def demo_automatic_rollback():
    """Demonstrate automatic rollback on metric degradation."""
    print_header("4. Automatic Rollback")
    
    refactor = get_autonomous_refactor()
    rollback_manager = refactor.rollback_manager
    
    # Simulate metrics before and after a change
    metrics_scenarios = [
        {
            'name': 'Error Rate Spike',
            'before': {'error_rate': 0.01, 'latency_p95': 100, 'test_pass_rate': 0.95},
            'after': {'error_rate': 0.15, 'latency_p95': 105, 'test_pass_rate': 0.93}
        },
        {
            'name': 'Latency Degradation',
            'before': {'error_rate': 0.02, 'latency_p95': 100, 'test_pass_rate': 0.95},
            'after': {'error_rate': 0.02, 'latency_p95': 150, 'test_pass_rate': 0.95}
        },
        {
            'name': 'Test Failures',
            'before': {'error_rate': 0.01, 'latency_p95': 100, 'test_pass_rate': 0.95},
            'after': {'error_rate': 0.02, 'latency_p95': 100, 'test_pass_rate': 0.80}
        },
        {
            'name': 'All Good',
            'before': {'error_rate': 0.01, 'latency_p95': 100, 'test_pass_rate': 0.95},
            'after': {'error_rate': 0.015, 'latency_p95': 105, 'test_pass_rate': 0.94}
        }
    ]
    
    print("Rollback Detection Scenarios:")
    print()
    
    for scenario in metrics_scenarios:
        should_rollback, trigger, reason = rollback_manager.should_rollback(
            scenario['before'],
            scenario['after']
        )
        
        status = "🔴 ROLLBACK" if should_rollback else "🟢 OK"
        trigger_str = trigger.value if trigger else "N/A"
        
        print(f"  {scenario['name']}:")
        print(f"    Status: {status}")
        print(f"    Trigger: {trigger_str}")
        if reason:
            print(f"    Reason: {reason}")
        print()
    
    print("Rollback Thresholds:")
    print_result("Error Rate", f"{rollback_manager.thresholds['error_rate']:.0%} increase", indent=1)
    print_result("Latency P95", f"{rollback_manager.thresholds['latency_p95']:.0%} increase", indent=1)
    print_result("Test Pass Rate", f"{rollback_manager.thresholds['test_pass_rate']:.0%} decrease", indent=1)


def demo_batch_processing():
    """Demonstrate batch processing of suggestions."""
    print_header("5. Batch Processing")
    
    refactor = get_autonomous_refactor()
    
    # Create multiple suggestions with different risk levels
    suggestions = [
        {'id': 'batch_001', 'type': 'format', 'file_path': 'test1.py'},
        {'id': 'batch_002', 'type': 'docstring', 'file_path': 'test2.py', 'function': 'main', 'docstring': 'Main entry point'},
        {'id': 'batch_003', 'type': 'rename', 'file_path': 'test3.py'},
        {'id': 'batch_004', 'type': 'logic_change', 'file_path': 'test4.py'},
        {'id': 'batch_005', 'type': 'security_fix', 'file_path': 'test5.py'}
    ]
    
    print("Processing 5 suggestions with different risk levels:")
    print()
    
    for suggestion in suggestions:
        risk = refactor.classify_risk(suggestion)
        can_auto = refactor.can_auto_apply(risk)
        
        print(f"  {suggestion['id']}:")
        print_result("Type", suggestion['type'], indent=2)
        print_result("Risk", risk.value, indent=2)
        print_result("Auto-Apply", "Yes" if can_auto else "No (requires review)", indent=2)
        print()


def demo_system_state():
    """Demonstrate system state export."""
    print_header("6. System State Export")
    
    refactor = get_autonomous_refactor()
    state = refactor.export_state()
    
    print("Current System State:")
    print_result("Total Results", str(len(state['results'])))
    print_result("Pending PRs", str(len(state['pending_prs'])))
    print_result("Active A/B Tests", str(len(state['active_ab_tests'])))
    print_result("Rollback History", str(len(state['rollback_history'])))
    print()
    
    print("Settings:")
    for key, value in state['settings'].items():
        print_result(key, str(value), indent=1)


def main():
    """Run the Phase 3 demo."""
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║       CEF Phase 3: Autonomous Refactoring Demo          ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    # Reset singleton for clean demo
    AutonomousRefactor._instance = None
    
    # Run all demos
    demo_auto_apply_low_risk()
    demo_pr_generation()
    demo_ab_testing()
    demo_automatic_rollback()
    demo_batch_processing()
    demo_system_state()
    
    print_header("Demo Complete!")
    print("Phase 3 Autonomous Refactoring capabilities demonstrated:")
    print()
    print("  ✅ Auto-apply low-risk suggestions (formatting, type hints)")
    print("  ✅ PR generation for medium-risk changes")
    print("  ✅ A/B testing framework for config tuning")
    print("  ✅ Automatic rollback on metric degradation")
    print("  ✅ Batch processing of suggestions")
    print("  ✅ System state export and monitoring")
    print()
    print("Run this script: python3 scripts/demo_cef_phase3.py")
    print()


if __name__ == '__main__':
    main()
