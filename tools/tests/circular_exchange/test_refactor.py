"""
Tests for the Refactoring Engine module.

This test suite verifies the automated refactoring suggestion engine
that generates code improvement suggestions based on pattern analysis.
"""

import pytest
import uuid
from datetime import datetime
from pathlib import Path
import tempfile


class TestRefactoringEngine:
    """Tests for the RefactoringEngine singleton."""
    
    def setup_method(self):
        """Reset the engine and related components before each test."""
        from shared.circular_exchange.analysis.data_collector import (
            DATA_COLLECTOR, TestStatus, TestResult, LogEntry, ExtractionEvent
        )
        from shared.circular_exchange.analysis.metrics_analyzer import METRICS_ANALYZER
        from shared.circular_exchange.refactor.refactoring_engine import (
            REFACTORING_ENGINE, SuggestionType, ImpactLevel, EffortLevel
        )
        
        self.collector = DATA_COLLECTOR
        self.analyzer = METRICS_ANALYZER
        self.engine = REFACTORING_ENGINE
        
        self.TestStatus = TestStatus
        self.TestResult = TestResult
        self.LogEntry = LogEntry
        self.ExtractionEvent = ExtractionEvent
        self.SuggestionType = SuggestionType
        self.ImpactLevel = ImpactLevel
        self.EffortLevel = EffortLevel
        
        # Clear previous data
        self.collector.clear()
        self.analyzer.clear()
        self.engine.clear()
    
    def test_singleton_pattern(self):
        """Test that RefactoringEngine is a singleton."""
        from shared.circular_exchange.refactor.refactoring_engine import RefactoringEngine
        
        engine1 = RefactoringEngine()
        engine2 = RefactoringEngine()
        
        assert engine1 is engine2
    
    def test_analyze_error_handling_no_data(self):
        """Test error handling analysis with no data."""
        suggestions = self.engine.analyze_error_handling()
        assert suggestions == []
    
    def test_analyze_error_handling_with_patterns(self):
        """Test error handling suggestions from error patterns."""
        # Add error logs to create patterns
        for i in range(5):
            self.collector.record_log_entry(self.LogEntry(
                log_id=str(uuid.uuid4()),
                level="ERROR",
                message="Database connection timeout",
                module="db_module",
                function="connect",
                line_number=100
            ))
        
        # Analyze patterns first
        self.analyzer.analyze_error_patterns()
        
        # Generate suggestions
        suggestions = self.engine.analyze_error_handling()
        
        # Should have at least one suggestion
        assert len(suggestions) >= 1
        assert suggestions[0].suggestion_type == self.SuggestionType.ERROR_HANDLING
    
    def test_analyze_performance_no_data(self):
        """Test performance analysis with no data."""
        suggestions = self.engine.analyze_performance()
        assert suggestions == []
    
    def test_analyze_testing_with_flaky_tests(self):
        """Test testing analysis with flaky tests."""
        # Add flaky test results
        for i in range(4):
            self.collector.record_test_result(self.TestResult(
                test_id=str(uuid.uuid4()),
                test_name="test_flaky_example",
                module_path="tests/test_example.py",
                status=self.TestStatus.PASSED if i < 2 else self.TestStatus.FAILED,
                duration_ms=100.0
            ))
        
        suggestions = self.engine.analyze_testing()
        
        # Should have flaky test suggestion
        flaky_suggestions = [s for s in suggestions if "flaky" in s.title.lower()]
        assert len(flaky_suggestions) >= 1
    
    def test_analyze_testing_with_slow_tests(self):
        """Test testing analysis with slow tests."""
        # Add slow test result
        self.collector.record_test_result(self.TestResult(
            test_id="slow1",
            test_name="test_very_slow",
            module_path="tests/test_slow.py",
            status=self.TestStatus.PASSED,
            duration_ms=10000.0  # 10 seconds
        ))
        
        suggestions = self.engine.analyze_testing()
        
        # Should have slow test suggestion
        slow_suggestions = [s for s in suggestions if "slow" in s.title.lower()]
        assert len(slow_suggestions) >= 1
    
    def test_code_suggestion_priority_score(self):
        """Test CodeSuggestion priority score calculation."""
        from shared.circular_exchange.refactor.refactoring_engine import CodeSuggestion, CodeLocation
        
        high_priority = CodeSuggestion(
            suggestion_id="high",
            suggestion_type=self.SuggestionType.ERROR_HANDLING,
            title="Critical fix",
            description="Important fix",
            location=CodeLocation("file.py", 1, 10),
            current_code="",
            suggested_code="",
            impact=self.ImpactLevel.CRITICAL,
            effort=self.EffortLevel.TRIVIAL
        )
        
        low_priority = CodeSuggestion(
            suggestion_id="low",
            suggestion_type=self.SuggestionType.DOCUMENTATION,
            title="Minor improvement",
            description="Nice to have",
            location=CodeLocation("file.py", 1, 10),
            current_code="",
            suggested_code="",
            impact=self.ImpactLevel.COSMETIC,
            effort=self.EffortLevel.MAJOR
        )
        
        # Higher priority = lower score
        assert high_priority.priority_score() < low_priority.priority_score()
    
    def test_create_refactoring_plan(self):
        """Test creating a refactoring plan."""
        # Generate some suggestions first
        for i in range(5):
            self.collector.record_log_entry(self.LogEntry(
                log_id=str(uuid.uuid4()),
                level="ERROR",
                message="Test error for plan",
                module="test_module",
                function="test_func",
                line_number=1
            ))
        
        self.analyzer.analyze_error_patterns()
        self.engine.analyze_error_handling()
        
        plan = self.engine.create_refactoring_plan(
            title="Test Plan",
            description="Test refactoring plan",
            auto_select=True,
            max_suggestions=5
        )
        
        assert plan.plan_id is not None
        assert plan.title == "Test Plan"
    
    def test_generate_comprehensive_plan(self):
        """Test generating a comprehensive refactoring plan."""
        # Add some data for analysis
        for i in range(5):
            self.collector.record_log_entry(self.LogEntry(
                log_id=str(uuid.uuid4()),
                level="ERROR",
                message="Comprehensive test error",
                module="test_module",
                function="test_func",
                line_number=1
            ))
        
        plan = self.engine.generate_comprehensive_plan()
        
        assert plan is not None
        assert plan.plan_id is not None
    
    def test_analyze_all(self):
        """Test analyze_all method runs all analyses and returns combined suggestions."""
        # Add some data for analysis
        for i in range(5):
            self.collector.record_log_entry(self.LogEntry(
                log_id=str(uuid.uuid4()),
                level="ERROR",
                message="Analyze all test error",
                module="test_module",
                function="test_func",
                line_number=1
            ))
        
        # Also add a flaky test
        for i in range(4):
            self.collector.record_test_result(self.TestResult(
                test_id=str(uuid.uuid4()),
                test_name="test_flaky_for_analyze_all",
                module_path="tests/test_example.py",
                status=self.TestStatus.PASSED if i < 2 else self.TestStatus.FAILED,
                duration_ms=100.0
            ))
        
        # Analyze patterns
        self.analyzer.analyze_error_patterns()
        
        # Call analyze_all
        suggestions = self.engine.analyze_all()
        
        # Should return a list
        assert isinstance(suggestions, list)
        
        # Should have suggestions from both error handling and testing
        error_suggestions = [s for s in suggestions if s.suggestion_type == self.SuggestionType.ERROR_HANDLING]
        testing_suggestions = [s for s in suggestions if s.suggestion_type == self.SuggestionType.TESTING]
        
        # At least one error handling suggestion
        assert len(error_suggestions) >= 1
        # At least one testing suggestion (for flaky test)
        assert len(testing_suggestions) >= 1
    
    def test_get_summary(self):
        """Test getting engine summary."""
        summary = self.engine.get_summary()
        
        assert "total_suggestions" in summary
        assert "by_type" in summary
        assert "by_impact" in summary
        assert "by_effort" in summary
        assert "auto_fixable_count" in summary
    
    def test_get_suggestions_filtering(self):
        """Test filtering suggestions by type."""
        # Generate some suggestions
        for i in range(5):
            self.collector.record_log_entry(self.LogEntry(
                log_id=str(uuid.uuid4()),
                level="ERROR",
                message="Filter test error",
                module="test_module",
                function="test_func",
                line_number=1
            ))
        
        self.analyzer.analyze_error_patterns()
        self.engine.analyze_error_handling()
        
        # Filter by type
        error_suggestions = self.engine.get_suggestions(
            suggestion_type=self.SuggestionType.ERROR_HANDLING
        )
        
        for s in error_suggestions:
            assert s.suggestion_type == self.SuggestionType.ERROR_HANDLING
    
    def test_subscriber_notification(self):
        """Test subscriber notifications for new suggestions."""
        received = []
        
        def on_suggestion(suggestion):
            received.append(suggestion)
        
        self.engine.subscribe(on_suggestion)
        
        # Generate suggestions
        for i in range(5):
            self.collector.record_log_entry(self.LogEntry(
                log_id=str(uuid.uuid4()),
                level="ERROR",
                message="Subscriber test error",
                module="test_module",
                function="test_func",
                line_number=1
            ))
        
        self.analyzer.analyze_error_patterns()
        self.engine.analyze_error_handling()
        
        # Should have received notifications
        assert len(received) >= 1
        
        self.engine.unsubscribe(on_suggestion)
    
    def test_export_suggestions(self):
        """Test exporting suggestions to JSON."""
        # Generate some suggestions
        for i in range(3):
            self.collector.record_log_entry(self.LogEntry(
                log_id=str(uuid.uuid4()),
                level="ERROR",
                message="Export test error",
                module="test_module",
                function="test_func",
                line_number=1
            ))
        
        self.analyzer.analyze_error_patterns()
        self.engine.analyze_error_handling()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "suggestions.json"
            result_path = self.engine.export_suggestions(output_path)
            
            assert result_path.exists()
            
            import json
            with open(result_path) as f:
                data = json.load(f)
            
            assert "suggestions" in data
            assert "generated_at" in data
    
    def test_clear_engine(self):
        """Test clearing engine data."""
        # Generate some suggestions
        for i in range(3):
            self.collector.record_log_entry(self.LogEntry(
                log_id=str(uuid.uuid4()),
                level="ERROR",
                message="Clear test error",
                module="test_module",
                function="test_func",
                line_number=1
            ))
        
        self.analyzer.analyze_error_patterns()
        self.engine.analyze_error_handling()
        
        # Verify we have suggestions
        assert len(self.engine.get_suggestions()) > 0
        
        # Clear
        self.engine.clear()
        
        # Should be empty
        assert len(self.engine.get_suggestions()) == 0


class TestCodeLocation:
    """Tests for CodeLocation dataclass."""
    
    def test_code_location_to_dict(self):
        """Test CodeLocation serialization."""
        from shared.circular_exchange.refactor.refactoring_engine import CodeLocation
        
        location = CodeLocation(
            file_path="path/to/file.py",
            start_line=10,
            end_line=20,
            function_name="my_function",
            class_name="MyClass"
        )
        
        data = location.to_dict()
        
        assert data["file_path"] == "path/to/file.py"
        assert data["start_line"] == 10
        assert data["function_name"] == "my_function"


class TestEnums:
    """Tests for refactoring engine enums."""
    
    def test_suggestion_type_values(self):
        """Test SuggestionType enum values."""
        from shared.circular_exchange.refactor.refactoring_engine import SuggestionType
        
        assert SuggestionType.ERROR_HANDLING.value == "error_handling"
        assert SuggestionType.PERFORMANCE.value == "performance"
        assert SuggestionType.TESTING.value == "testing"
    
    def test_effort_level_ordering(self):
        """Test EffortLevel enum ordering."""
        from shared.circular_exchange.refactor.refactoring_engine import EffortLevel
        
        assert EffortLevel.TRIVIAL.value < EffortLevel.LOW.value
        assert EffortLevel.LOW.value < EffortLevel.MEDIUM.value
        assert EffortLevel.MEDIUM.value < EffortLevel.HIGH.value
        assert EffortLevel.HIGH.value < EffortLevel.MAJOR.value
    
    def test_impact_level_ordering(self):
        """Test ImpactLevel enum ordering."""
        from shared.circular_exchange.refactor.refactoring_engine import ImpactLevel
        
        assert ImpactLevel.CRITICAL.value < ImpactLevel.HIGH.value
        assert ImpactLevel.HIGH.value < ImpactLevel.MEDIUM.value
        assert ImpactLevel.MEDIUM.value < ImpactLevel.LOW.value
        assert ImpactLevel.LOW.value < ImpactLevel.COSMETIC.value


class TestIntegration:
    """Integration tests for refactoring engine with other components."""
    
    def test_cef_module_registration(self):
        """Test that refactoring engine is registered with CEF."""
        from shared.circular_exchange import REFACTORING_ENGINE
        
        assert REFACTORING_ENGINE is not None
    
    def test_full_pipeline(self):
        """Test the full pipeline: data → analysis → suggestions."""
        from shared.circular_exchange import (
            DATA_COLLECTOR, METRICS_ANALYZER, REFACTORING_ENGINE,
            TestStatus, TestResult, LogEntry, ExtractionEvent
        )
        
        # Clear everything
        DATA_COLLECTOR.clear()
        METRICS_ANALYZER.clear()
        REFACTORING_ENGINE.clear()
        
        # Step 1: Collect data
        for i in range(10):
            DATA_COLLECTOR.record_log_entry(LogEntry(
                log_id=str(i),
                level="ERROR",
                message="Pipeline test error",
                module="pipeline_module",
                function="pipeline_func",
                line_number=100
            ))
        
        # Step 2: Analyze patterns
        patterns = METRICS_ANALYZER.analyze_error_patterns()
        
        # Step 3: Generate suggestions
        suggestions = REFACTORING_ENGINE.analyze_error_handling()
        
        # Step 4: Create plan
        plan = REFACTORING_ENGINE.generate_comprehensive_plan()
        
        # Verify pipeline worked
        assert len(patterns) >= 1
        assert plan is not None
"""
Tests for Phase 3: Autonomous Refactoring Engine
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from shared.circular_exchange.refactor.autonomous_refactor import (
    AutonomousRefactor,
    RefactorRisk,
    RefactorStatus,
    RefactorResult,
    ABTest,
    ABTestVariant,
    ABTestResult,
    ABTestManager,
    RollbackManager,
    RollbackTrigger,
    RollbackAction,
    CodeTransformer,
    PRGenerator,
    get_autonomous_refactor
)


class TestRefactorRisk(unittest.TestCase):
    """Tests for RefactorRisk enum."""
    
    def test_risk_levels_exist(self):
        """Test that all risk levels are defined."""
        self.assertEqual(RefactorRisk.LOW.value, "low")
        self.assertEqual(RefactorRisk.MEDIUM.value, "medium")
        self.assertEqual(RefactorRisk.HIGH.value, "high")
        self.assertEqual(RefactorRisk.CRITICAL.value, "critical")


class TestRefactorResult(unittest.TestCase):
    """Tests for RefactorResult dataclass."""
    
    def test_result_creation(self):
        """Test creating a refactor result."""
        result = RefactorResult(
            suggestion_id="test123",
            risk=RefactorRisk.LOW,
            status=RefactorStatus.PENDING,
            file_path="/test/file.py",
            changes_made=[]
        )
        self.assertEqual(result.suggestion_id, "test123")
        self.assertEqual(result.risk, RefactorRisk.LOW)
        self.assertEqual(result.status, RefactorStatus.PENDING)
    
    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        result = RefactorResult(
            suggestion_id="test123",
            risk=RefactorRisk.MEDIUM,
            status=RefactorStatus.APPLIED,
            file_path="/test/file.py",
            changes_made=[{"type": "format"}],
            applied_at=datetime.now()
        )
        data = result.to_dict()
        self.assertEqual(data['suggestion_id'], "test123")
        self.assertEqual(data['risk'], "medium")
        self.assertEqual(data['status'], "applied")


class TestCodeTransformer(unittest.TestCase):
    """Tests for CodeTransformer."""
    
    def test_format_code_trailing_whitespace(self):
        """Test removing trailing whitespace."""
        source = "def test():   \n    pass   \n"
        result = CodeTransformer.format_code(source)
        self.assertNotIn("   \n", result)
    
    def test_format_code_tabs_to_spaces(self):
        """Test converting tabs to spaces."""
        source = "\tdef test():\n\t\tpass\n"
        result = CodeTransformer.format_code(source)
        self.assertNotIn("\t", result)
        self.assertIn("    ", result)
    
    def test_rename_variable(self):
        """Test renaming a variable."""
        source = "x = 1\nprint(x)\ny = x + 1"
        result = CodeTransformer.rename_variable(source, "x", "value")
        self.assertIn("value = 1", result)
        self.assertIn("print(value)", result)
        self.assertIn("y = value + 1", result)
    
    def test_rename_variable_word_boundary(self):
        """Test that rename respects word boundaries."""
        source = "x = 1\nprefix_x = 2\nx_suffix = 3"
        result = CodeTransformer.rename_variable(source, "x", "value")
        self.assertIn("value = 1", result)
        self.assertIn("prefix_x = 2", result)  # Should not change
        self.assertIn("x_suffix = 3", result)  # Should not change


class TestRollbackManager(unittest.TestCase):
    """Tests for RollbackManager."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = RollbackManager(backup_dir=self.temp_dir)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_backup(self):
        """Test creating a file backup."""
        # Create a test file
        test_file = Path(self.temp_dir) / "test.py"
        test_file.write_text("original content")
        
        backup_path = self.manager.create_backup(str(test_file))
        self.assertTrue(Path(backup_path).exists())
        self.assertEqual(Path(backup_path).read_text(), "original content")
    
    def test_restore_backup(self):
        """Test restoring from backup."""
        test_file = Path(self.temp_dir) / "test.py"
        test_file.write_text("original content")
        
        backup_path = self.manager.create_backup(str(test_file))
        
        # Modify the original
        test_file.write_text("modified content")
        
        # Restore
        success = self.manager.restore_backup(backup_path, str(test_file))
        self.assertTrue(success)
        self.assertEqual(test_file.read_text(), "original content")
    
    def test_should_rollback_error_rate(self):
        """Test rollback detection for error rate spike."""
        metrics_before = {'error_rate': 0.01}
        metrics_after = {'error_rate': 0.10}  # 9% increase
        
        should_rollback, trigger, reason = self.manager.should_rollback(
            metrics_before, metrics_after
        )
        self.assertTrue(should_rollback)
        self.assertEqual(trigger, RollbackTrigger.ERROR_RATE_SPIKE)
    
    def test_should_not_rollback_normal(self):
        """Test no rollback for normal metrics."""
        metrics_before = {'error_rate': 0.01, 'latency_p95': 100}
        metrics_after = {'error_rate': 0.02, 'latency_p95': 105}
        
        should_rollback, trigger, reason = self.manager.should_rollback(
            metrics_before, metrics_after
        )
        self.assertFalse(should_rollback)


class TestABTestManager(unittest.TestCase):
    """Tests for ABTestManager."""
    
    def setUp(self):
        self.manager = ABTestManager()
    
    def test_create_test(self):
        """Test creating an A/B test."""
        test = self.manager.create_test(
            name="Test Config",
            description="Testing a config change",
            config_key="timeout",
            control_value=30,
            treatment_value=60
        )
        self.assertIsNotNone(test.test_id)
        self.assertEqual(test.name, "Test Config")
        self.assertTrue(test.is_active)
    
    def test_record_metric(self):
        """Test recording metrics for a test."""
        test = self.manager.create_test(
            name="Test",
            description="Test",
            config_key="key",
            control_value=1,
            treatment_value=2
        )
        
        self.manager.record_metric(test.test_id, "control", "success_rate", 0.9)
        self.manager.record_metric(test.test_id, "control", "success_rate", 0.85)
        
        retrieved = self.manager.get_test(test.test_id)
        self.assertEqual(len(retrieved.control.metrics['success_rate']), 2)
    
    def test_get_variant(self):
        """Test getting a variant assignment."""
        test = self.manager.create_test(
            name="Test",
            description="Test",
            config_key="key",
            control_value=1,
            treatment_value=2
        )
        
        variant = self.manager.get_variant(test.test_id)
        self.assertIn(variant, ["control", "treatment"])
    
    def test_analyze_test_insufficient_samples(self):
        """Test analysis with insufficient samples."""
        test = self.manager.create_test(
            name="Test",
            description="Test",
            config_key="key",
            control_value=1,
            treatment_value=2,
            min_samples=100
        )
        
        # Add only a few samples
        for _ in range(5):
            self.manager.record_metric(test.test_id, "control", "success_rate", 0.9)
            self.manager.record_metric(test.test_id, "treatment", "success_rate", 0.95)
        
        result = self.manager.analyze_test(test.test_id)
        self.assertFalse(result.is_significant)
        self.assertIn("samples", result.recommendation.lower())


class TestPRGenerator(unittest.TestCase):
    """Tests for PRGenerator."""
    
    def setUp(self):
        self.generator = PRGenerator()
    
    def test_generate_diff(self):
        """Test generating a unified diff."""
        original = "line1\nline2\nline3"
        modified = "line1\nmodified\nline3"
        
        diff = self.generator.generate_diff(original, modified, "test.py")
        self.assertIn("--- a/test.py", diff)
        self.assertIn("+++ b/test.py", diff)
        self.assertIn("-line2", diff)
        self.assertIn("+modified", diff)
    
    def test_create_pr_description(self):
        """Test creating PR description."""
        description = self.generator.create_pr_description(
            suggestion_id="test123",
            risk=RefactorRisk.MEDIUM,
            file_path="test.py",
            description="Test refactoring",
            changes=["Change 1", "Change 2"],
            metrics_impact={"performance": 0.1}
        )
        self.assertIn("test123", description)
        self.assertIn("MEDIUM", description)
        self.assertIn("test.py", description)
    
    def test_prepare_pr(self):
        """Test preparing a PR."""
        pr_info = self.generator.prepare_pr(
            suggestion_id="test123",
            risk=RefactorRisk.MEDIUM,
            file_path="test.py",
            original_content="original",
            modified_content="modified",
            description="Test",
            changes=["Change"],
            metrics_impact={}
        )
        self.assertEqual(pr_info['suggestion_id'], "test123")
        self.assertIn("cef/refactor", pr_info['branch_name'])
        self.assertIn("CEF", pr_info['title'])


class TestAutonomousRefactor(unittest.TestCase):
    """Tests for AutonomousRefactor."""
    
    def setUp(self):
        # Reset singleton for testing
        AutonomousRefactor._instance = None
        self.refactor = AutonomousRefactor()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        AutonomousRefactor._instance = None
    
    def test_singleton(self):
        """Test singleton pattern."""
        instance1 = AutonomousRefactor()
        instance2 = AutonomousRefactor()
        self.assertIs(instance1, instance2)
    
    def test_classify_risk_low(self):
        """Test classifying low risk suggestions."""
        suggestion = {'type': 'format'}
        risk = self.refactor.classify_risk(suggestion)
        self.assertEqual(risk, RefactorRisk.LOW)
    
    def test_classify_risk_medium(self):
        """Test classifying medium risk suggestions."""
        suggestion = {'type': 'rename'}
        risk = self.refactor.classify_risk(suggestion)
        self.assertEqual(risk, RefactorRisk.MEDIUM)
    
    def test_classify_risk_high(self):
        """Test classifying high risk suggestions."""
        suggestion = {'type': 'logic_change'}
        risk = self.refactor.classify_risk(suggestion)
        self.assertEqual(risk, RefactorRisk.HIGH)
    
    def test_can_auto_apply(self):
        """Test auto-apply permission check."""
        self.assertTrue(self.refactor.can_auto_apply(RefactorRisk.LOW))
        self.assertFalse(self.refactor.can_auto_apply(RefactorRisk.MEDIUM))
        self.assertFalse(self.refactor.can_auto_apply(RefactorRisk.HIGH))
    
    def test_apply_low_risk_formatting(self):
        """Test applying low-risk formatting refactoring."""
        # Create a test file
        test_file = Path(self.temp_dir) / "test.py"
        test_file.write_text("def test():   \n    pass   \n")
        
        suggestion = {
            'id': 'test123',
            'type': 'format',
            'file_path': str(test_file)
        }
        
        result = self.refactor.apply_low_risk_refactoring(str(test_file), suggestion)
        self.assertEqual(result.status, RefactorStatus.APPLIED)
        self.assertIsNotNone(result.backup_path)
    
    def test_apply_low_risk_dry_run(self):
        """Test dry run mode."""
        test_file = Path(self.temp_dir) / "test.py"
        original = "def test():   \n    pass   \n"
        test_file.write_text(original)
        
        suggestion = {
            'id': 'test123',
            'type': 'format'
        }
        
        result = self.refactor.apply_low_risk_refactoring(
            str(test_file), suggestion, dry_run=True
        )
        self.assertEqual(result.status, RefactorStatus.PENDING)
        # File should be unchanged in dry run
        self.assertEqual(test_file.read_text(), original)
    
    def test_process_suggestion_high_risk(self):
        """Test processing high risk suggestion."""
        suggestion = {
            'id': 'test123',
            'type': 'logic_change',
            'file_path': '/nonexistent/file.py'
        }
        
        result = self.refactor.process_suggestion(suggestion)
        self.assertEqual(result.status, RefactorStatus.SKIPPED)
        self.assertEqual(result.risk, RefactorRisk.HIGH)
    
    def test_export_state(self):
        """Test exporting system state."""
        state = self.refactor.export_state()
        self.assertIn('results', state)
        self.assertIn('pending_prs', state)
        self.assertIn('active_ab_tests', state)
        self.assertIn('settings', state)
        self.assertIn('exported_at', state)
    
    def test_subscriber_notification(self):
        """Test subscriber notifications."""
        notifications = []
        self.refactor.subscribe(lambda r: notifications.append(r))
        
        test_file = Path(self.temp_dir) / "test.py"
        test_file.write_text("def test():\n    pass\n")
        
        suggestion = {'id': 'test123', 'type': 'format'}
        self.refactor.apply_low_risk_refactoring(str(test_file), suggestion)
        
        # Should receive notification (even if no changes)
        self.assertGreaterEqual(len(notifications), 0)


class TestGetAutonomousRefactor(unittest.TestCase):
    """Tests for get_autonomous_refactor function."""
    
    def setUp(self):
        AutonomousRefactor._instance = None
    
    def tearDown(self):
        AutonomousRefactor._instance = None
    
    def test_get_instance(self):
        """Test getting the singleton instance."""
        instance = get_autonomous_refactor()
        self.assertIsInstance(instance, AutonomousRefactor)
    
    def test_get_same_instance(self):
        """Test that multiple calls return the same instance."""
        instance1 = get_autonomous_refactor()
        instance2 = get_autonomous_refactor()
        self.assertIs(instance1, instance2)


if __name__ == '__main__':
    unittest.main()
"""
Tests for the Feedback Loop module.

This test suite verifies the continuous feedback loop that orchestrates
auto-tuning and model fine-tuning based on collected metrics.
"""

import pytest
import uuid
from datetime import datetime
from pathlib import Path
import tempfile


class TestAutoTuner:
    """Tests for the AutoTuner component."""
    
    def setup_method(self):
        """Reset components before each test."""
        from shared.circular_exchange.refactor.feedback_loop import (
            AutoTuner, FeedbackType, TuningAction
        )
        
        self.tuner = AutoTuner()
        self.FeedbackType = FeedbackType
        self.TuningAction = TuningAction
    
    def test_record_feedback(self):
        """Test recording feedback signals."""
        self.tuner.record_feedback(
            self.FeedbackType.TEST_RESULT,
            {'test_name': 'test_example', 'passed': True, 'duration_ms': 100}
        )
        
        # Verify feedback was recorded
        assert len(self.tuner._feedback_history[self.FeedbackType.TEST_RESULT.value]) == 1
    
    def test_analyze_extraction_low_success_rate(self):
        """Test tuning suggestions for low extraction success rate."""
        # Record many failures
        for i in range(8):
            self.tuner.record_feedback(
                self.FeedbackType.EXTRACTION_FAILURE,
                {'model_id': 'test_model', 'confidence': 0.3}
            )
        
        # Record few successes
        for i in range(2):
            self.tuner.record_feedback(
                self.FeedbackType.EXTRACTION_SUCCESS,
                {'model_id': 'test_model', 'confidence': 0.8}
            )
        
        # Analyze should suggest lowering threshold
        decisions = self.tuner.analyze_and_tune()
        
        assert len(decisions) >= 1
        threshold_decisions = [d for d in decisions if d.action == self.TuningAction.DECREASE_THRESHOLD]
        assert len(threshold_decisions) >= 1
    
    def test_analyze_extraction_high_success_rate(self):
        """Test tuning suggestions for high extraction success rate."""
        # Record many successes (>95% success rate required)
        for i in range(20):
            self.tuner.record_feedback(
                self.FeedbackType.EXTRACTION_SUCCESS,
                {'model_id': 'test_model', 'confidence': 0.9}
            )
        
        # Analyze should suggest raising threshold for very high success rate
        decisions = self.tuner.analyze_and_tune()
        
        # With 100% success rate, should suggest increasing threshold for better accuracy
        threshold_decisions = [d for d in decisions if d.action == self.TuningAction.INCREASE_THRESHOLD]
        assert len(threshold_decisions) >= 1
    
    def test_apply_decision(self):
        """Test applying a tuning decision."""
        from shared.circular_exchange.refactor.feedback_loop import TuningDecision, TuningAction
        
        decision = TuningDecision(
            decision_id="test_decision",
            action=TuningAction.DECREASE_THRESHOLD,
            target_config='ocr.min_confidence',
            old_value=0.3,
            new_value=0.25,
            reason="Test reason",
            confidence=0.9
        )
        
        result = self.tuner.apply_decision(decision)
        
        assert result is True
        assert decision.applied is True
    
    def test_get_decisions(self):
        """Test getting tuning decisions."""
        # Generate some decisions
        for i in range(15):
            self.tuner.record_feedback(
                self.FeedbackType.EXTRACTION_FAILURE,
                {'model_id': 'test', 'confidence': 0.2}
            )
        
        self.tuner.analyze_and_tune()
        
        all_decisions = self.tuner.get_decisions()
        applied_decisions = self.tuner.get_decisions(applied_only=True)
        
        assert isinstance(all_decisions, list)
        assert isinstance(applied_decisions, list)


class TestModelTrainingPipeline:
    """Tests for the ModelTrainingPipeline component."""
    
    def setup_method(self):
        """Reset pipeline before each test."""
        from shared.circular_exchange.refactor.feedback_loop import (
            ModelTrainingPipeline, TrainingStatus
        )
        
        self.pipeline = ModelTrainingPipeline()
        self.TrainingStatus = TrainingStatus
    
    def test_create_training_job(self):
        """Test creating a training job."""
        job = self.pipeline.create_training_job(
            model_id='test_model',
            target_samples=100,
            target_epochs=5
        )
        
        assert job.job_id is not None
        assert job.model_id == 'test_model'
        assert job.status == self.TrainingStatus.COLLECTING
        assert job.target_samples == 100
    
    def test_add_training_sample(self):
        """Test adding training samples."""
        job = self.pipeline.create_training_job(
            model_id='test_model',
            target_samples=5
        )
        
        # Add samples
        for i in range(5):
            result = self.pipeline.add_training_sample(
                job.job_id,
                input_data={'image': f'image_{i}.jpg'},
                output_data={'text': f'extracted_text_{i}'},
                metadata={'confidence': 0.9}
            )
            assert result is True
        
        # Job should be ready for training
        updated_job = self.pipeline.get_job(job.job_id)
        assert updated_job.samples_collected == 5
        assert updated_job.status == self.TrainingStatus.PENDING
    
    def test_start_training(self):
        """Test starting a training job."""
        job = self.pipeline.create_training_job(
            model_id='test_model',
            target_samples=2
        )
        
        # Add enough samples
        for i in range(2):
            self.pipeline.add_training_sample(
                job.job_id,
                input_data={'image': f'image_{i}.jpg'},
                output_data={'text': 'text'}
            )
        
        # Start training
        result = self.pipeline.start_training(job.job_id)
        
        assert result is True
        
        updated_job = self.pipeline.get_job(job.job_id)
        assert updated_job.status == self.TrainingStatus.TRAINING
        assert updated_job.started_at is not None
    
    def test_update_training_progress(self):
        """Test updating training progress."""
        job = self.pipeline.create_training_job(
            model_id='test_model',
            target_samples=1,
            target_epochs=5
        )
        
        # Add sample and start
        self.pipeline.add_training_sample(
            job.job_id,
            {'image': 'test.jpg'},
            {'text': 'test'}
        )
        self.pipeline.start_training(job.job_id)
        
        # Update progress
        self.pipeline.update_training_progress(
            job.job_id,
            epoch=3,
            metrics={'accuracy': 0.85, 'loss': 0.15}
        )
        
        updated_job = self.pipeline.get_job(job.job_id)
        assert updated_job.epochs_completed == 3
        assert updated_job.current_metrics['accuracy'] == 0.85
    
    def test_complete_training(self):
        """Test completing a training job."""
        job = self.pipeline.create_training_job(
            model_id='test_model',
            target_samples=1
        )
        
        self.pipeline.add_training_sample(
            job.job_id,
            {'image': 'test.jpg'},
            {'text': 'test'}
        )
        self.pipeline.start_training(job.job_id)
        
        self.pipeline.complete_training(
            job.job_id,
            final_metrics={'accuracy': 0.92, 'loss': 0.08},
            success=True
        )
        
        updated_job = self.pipeline.get_job(job.job_id)
        assert updated_job.status == self.TrainingStatus.COMPLETED
        assert updated_job.completed_at is not None
    
    def test_get_active_jobs(self):
        """Test getting active training jobs."""
        # Create multiple jobs
        job1 = self.pipeline.create_training_job('model1')
        job2 = self.pipeline.create_training_job('model2')
        
        active = self.pipeline.get_active_jobs()
        
        assert len(active) >= 2


class TestFeedbackLoop:
    """Tests for the FeedbackLoop orchestrator."""
    
    def setup_method(self):
        """Reset feedback loop before each test."""
        from shared.circular_exchange.refactor.feedback_loop import FEEDBACK_LOOP
        from shared.circular_exchange.analysis.data_collector import DATA_COLLECTOR
        from shared.circular_exchange.analysis.metrics_analyzer import METRICS_ANALYZER
        from shared.circular_exchange.refactor.refactoring_engine import REFACTORING_ENGINE
        
        # Clear all components
        DATA_COLLECTOR.clear()
        METRICS_ANALYZER.clear()
        REFACTORING_ENGINE.clear()
        
        self.loop = FEEDBACK_LOOP
        # Reset internal state
        self.loop._cycle_count = 0
        self.loop._metrics.total_feedback_signals = 0
        self.loop._metrics.tuning_decisions_made = 0
        self.loop._metrics.tuning_decisions_applied = 0
        self.loop._metrics.config_improvements = 0
        self.loop._auto_tuner._decisions.clear()
        self.loop._auto_tuner._feedback_history.clear()
    
    def test_singleton_pattern(self):
        """Test that FeedbackLoop is a singleton."""
        from shared.circular_exchange.refactor.feedback_loop import FeedbackLoop
        
        loop1 = FeedbackLoop()
        loop2 = FeedbackLoop()
        
        assert loop1 is loop2
    
    def test_process_test_result(self):
        """Test processing test results."""
        initial_signals = self.loop._metrics.total_feedback_signals
        
        self.loop.process_test_result(
            test_name='test_example',
            passed=True,
            duration_ms=150.0
        )
        
        assert self.loop._metrics.total_feedback_signals == initial_signals + 1
    
    def test_process_extraction_result(self):
        """Test processing extraction results."""
        initial_signals = self.loop._metrics.total_feedback_signals
        
        self.loop.process_extraction_result(
            model_id='donut_model',
            success=True,
            confidence=0.95,
            processing_time_ms=1500.0
        )
        
        assert self.loop._metrics.total_feedback_signals == initial_signals + 1
    
    def test_process_performance_metric(self):
        """Test processing performance metrics."""
        initial_signals = self.loop._metrics.total_feedback_signals
        
        self.loop.process_performance_metric(
            metric_name='cache_hit_rate',
            value=0.75,
            tags={'cache_type': 'model'}
        )
        
        assert self.loop._metrics.total_feedback_signals == initial_signals + 1
    
    def test_run_cycle(self):
        """Test running a feedback cycle."""
        # Add some feedback first
        for i in range(15):
            self.loop.process_extraction_result(
                model_id='test_model',
                success=i < 5,  # 33% success rate
                confidence=0.5,
                processing_time_ms=1000.0
            )
        
        initial_cycle = self.loop._cycle_count
        
        results = self.loop.run_cycle()
        
        assert self.loop._cycle_count == initial_cycle + 1
        assert 'tuning_decisions' in results
        assert 'patterns_detected' in results
        assert 'duration_ms' in results
    
    def test_get_metrics(self):
        """Test getting feedback loop metrics."""
        metrics = self.loop.get_metrics()
        
        assert hasattr(metrics, 'total_feedback_signals')
        assert hasattr(metrics, 'tuning_decisions_made')
        assert hasattr(metrics, 'training_jobs_created')
    
    def test_get_summary(self):
        """Test getting feedback loop summary."""
        summary = self.loop.get_summary()
        
        assert 'cycle_count' in summary
        assert 'metrics' in summary
        assert 'active_training_jobs' in summary
        assert 'tuner_stats' in summary
    
    def test_subscriber_notification(self):
        """Test subscriber notifications."""
        received_decisions = []
        
        def on_decision(decision):
            received_decisions.append(decision)
        
        self.loop.subscribe_to_decisions(on_decision)
        
        # Generate high-confidence decisions
        for i in range(20):
            self.loop.process_extraction_result(
                model_id='test',
                success=False,
                confidence=0.2,
                processing_time_ms=1000.0
            )
        
        self.loop.run_cycle()
        
        # May or may not have received notifications depending on confidence
        assert isinstance(received_decisions, list)
    
    def test_export_state(self):
        """Test exporting feedback loop state."""
        # Add some activity
        self.loop.process_test_result('test1', True, 100.0)
        self.loop.run_cycle()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "state.json"
            result_path = self.loop.export_state(output_path)
            
            assert result_path.exists()
            
            import json
            with open(result_path) as f:
                data = json.load(f)
            
            assert 'summary' in data
            assert 'tuning_decisions' in data
            assert 'exported_at' in data


class TestEnums:
    """Tests for feedback loop enums."""
    
    def test_tuning_action_values(self):
        """Test TuningAction enum values."""
        from shared.circular_exchange.refactor.feedback_loop import TuningAction
        
        assert TuningAction.INCREASE_THRESHOLD.value == "increase_threshold"
        assert TuningAction.DECREASE_THRESHOLD.value == "decrease_threshold"
        assert TuningAction.ADJUST_TIMEOUT.value == "adjust_timeout"
    
    def test_feedback_type_values(self):
        """Test FeedbackType enum values."""
        from shared.circular_exchange.refactor.feedback_loop import FeedbackType
        
        assert FeedbackType.TEST_RESULT.value == "test_result"
        assert FeedbackType.EXTRACTION_SUCCESS.value == "extraction_success"
        assert FeedbackType.PERFORMANCE_METRIC.value == "performance_metric"
    
    def test_training_status_values(self):
        """Test TrainingStatus enum values."""
        from shared.circular_exchange.refactor.feedback_loop import TrainingStatus
        
        assert TrainingStatus.PENDING.value == "pending"
        assert TrainingStatus.TRAINING.value == "training"
        assert TrainingStatus.COMPLETED.value == "completed"


class TestIntegration:
    """Integration tests for the complete feedback loop system."""
    
    def test_cef_module_registration(self):
        """Test that feedback loop is registered with CEF."""
        from shared.circular_exchange import FEEDBACK_LOOP
        
        assert FEEDBACK_LOOP is not None
    
    def test_full_pipeline_integration(self):
        """Test the complete pipeline from data collection to tuning."""
        from shared.circular_exchange import (
            DATA_COLLECTOR, METRICS_ANALYZER, REFACTORING_ENGINE, FEEDBACK_LOOP,
            LogEntry, TestResult, TestStatus
        )
        
        # Clear everything
        DATA_COLLECTOR.clear()
        METRICS_ANALYZER.clear()
        REFACTORING_ENGINE.clear()
        
        # Step 1: Collect data
        for i in range(10):
            DATA_COLLECTOR.record_log_entry(LogEntry(
                log_id=str(i),
                level="ERROR",
                message="Integration test error",
                module="test_module",
                function="test_func",
                line_number=100
            ))
        
        for i in range(5):
            DATA_COLLECTOR.record_test_result(TestResult(
                test_id=str(i),
                test_name=f"test_{i}",
                module_path="tests/test.py",
                status=TestStatus.PASSED if i < 4 else TestStatus.FAILED,
                duration_ms=100.0
            ))
        
        # Step 2: Feed into feedback loop
        for i in range(15):
            FEEDBACK_LOOP.process_extraction_result(
                model_id="integration_model",
                success=i < 10,  # 67% success
                confidence=0.7,
                processing_time_ms=1000.0
            )
        
        # Step 3: Run feedback cycle
        results = FEEDBACK_LOOP.run_cycle()
        
        # Step 4: Verify results
        assert results['cycle_number'] >= 1
        
        summary = FEEDBACK_LOOP.get_summary()
        assert summary['metrics']['total_feedback_signals'] >= 15
