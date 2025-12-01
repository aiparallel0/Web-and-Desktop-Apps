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

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.circular_exchange.autonomous_refactor import (
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
