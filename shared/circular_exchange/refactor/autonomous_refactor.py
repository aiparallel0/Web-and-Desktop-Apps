"""
Phase 3: Autonomous Refactoring Engine

This module implements autonomous code refactoring capabilities:
1. Auto-apply low-risk suggestions (formatting, type hints, docstrings)
2. PR generation for medium-risk changes
3. A/B testing framework for config tuning
4. Automatic rollback on metric degradation
"""

# Circular Exchange Framework Integration (MANDATORY)
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.circular_exchange.autonomous_refactor",
            file_path=__file__,
            description="Autonomous refactoring with auto-apply, PR generation, A/B testing, and rollback",
            dependencies=["shared.circular_exchange.refactoring_engine", "shared.circular_exchange.metrics_analyzer"],
            exports=[
                "AutonomousRefactor", "RefactorRisk", "RefactorResult",
                "ABTest", "ABTestVariant", "ABTestResult",
                "RollbackManager", "RollbackTrigger", "RollbackAction"
            ]
        ))
    except Exception:
        pass

import ast
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union


class RefactorRisk(Enum):
    """Risk level for refactoring suggestions."""
    LOW = "low"           # Formatting, whitespace, docstrings
    MEDIUM = "medium"     # Type hints, variable renames, simple refactors
    HIGH = "high"         # Logic changes, API changes, deletions
    CRITICAL = "critical" # Breaking changes, security fixes


class RefactorStatus(Enum):
    """Status of a refactoring operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPLIED = "applied"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class RefactorResult:
    """Result of a refactoring operation."""
    suggestion_id: str
    risk: RefactorRisk
    status: RefactorStatus
    file_path: str
    changes_made: List[Dict[str, Any]]
    backup_path: Optional[str] = None
    applied_at: Optional[datetime] = None
    rolled_back_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metrics_before: Dict[str, float] = field(default_factory=dict)
    metrics_after: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['risk'] = self.risk.value
        data['status'] = self.status.value
        if self.applied_at:
            data['applied_at'] = self.applied_at.isoformat()
        if self.rolled_back_at:
            data['rolled_back_at'] = self.rolled_back_at.isoformat()
        return data


@dataclass
class ABTestVariant:
    """A variant in an A/B test."""
    name: str
    config: Dict[str, Any]
    weight: float = 0.5  # Traffic allocation weight
    metrics: Dict[str, List[float]] = field(default_factory=dict)
    sample_count: int = 0


@dataclass
class ABTest:
    """An A/B test configuration."""
    test_id: str
    name: str
    description: str
    config_key: str  # The configuration parameter being tested
    control: ABTestVariant
    treatment: ABTestVariant
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    min_samples: int = 100
    confidence_threshold: float = 0.95
    is_active: bool = True
    winner: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'test_id': self.test_id,
            'name': self.name,
            'description': self.description,
            'config_key': self.config_key,
            'control': asdict(self.control),
            'treatment': asdict(self.treatment),
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'min_samples': self.min_samples,
            'confidence_threshold': self.confidence_threshold,
            'is_active': self.is_active,
            'winner': self.winner
        }


@dataclass
class ABTestResult:
    """Result of an A/B test analysis."""
    test_id: str
    is_significant: bool
    winner: Optional[str]
    control_mean: float
    treatment_mean: float
    improvement_percent: float
    confidence: float
    recommendation: str


class RollbackTrigger(Enum):
    """Triggers for automatic rollback."""
    ERROR_RATE_SPIKE = "error_rate_spike"
    LATENCY_DEGRADATION = "latency_degradation"
    TEST_FAILURE = "test_failure"
    MANUAL = "manual"
    METRIC_THRESHOLD = "metric_threshold"


@dataclass
class RollbackAction:
    """A rollback action record."""
    action_id: str
    refactor_result: RefactorResult
    trigger: RollbackTrigger
    triggered_at: datetime
    completed_at: Optional[datetime] = None
    success: bool = False
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'action_id': self.action_id,
            'refactor_id': self.refactor_result.suggestion_id,
            'trigger': self.trigger.value,
            'triggered_at': self.triggered_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'success': self.success,
            'error_message': self.error_message
        }


class CodeTransformer:
    """Transforms code based on refactoring suggestions."""
    
    @staticmethod
    def add_type_hints(source: str, hints: Dict[str, str]) -> str:
        """Add type hints to function parameters and returns."""
        try:
            tree = ast.parse(source)
            lines = source.split('\n')
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_name = node.name
                    if func_name in hints:
                        hint = hints[func_name]
                        # Simple implementation - add return type hint
                        line_idx = node.lineno - 1
                        if lines[line_idx].rstrip().endswith(':'):
                            # Find the colon and insert before it
                            line = lines[line_idx]
                            colon_idx = line.rfind(':')
                            lines[line_idx] = line[:colon_idx] + f' -> {hint}' + line[colon_idx:]
            
            return '\n'.join(lines)
        except SyntaxError:
            return source
    
    @staticmethod
    def add_docstring(source: str, func_name: str, docstring: str) -> str:
        """Add or update a function's docstring."""
        try:
            tree = ast.parse(source)
            lines = source.split('\n')
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == func_name:
                    # Find function body start
                    body_start = node.body[0].lineno - 1
                    indent = len(lines[body_start]) - len(lines[body_start].lstrip())
                    indent_str = ' ' * (indent + 4)  # Function body indent
                    
                    # Check if there's already a docstring
                    if (isinstance(node.body[0], ast.Expr) and 
                        isinstance(node.body[0].value, ast.Constant) and
                        isinstance(node.body[0].value.value, str)):
                        # Replace existing docstring
                        lines[body_start] = f'{indent_str}"""{docstring}"""'
                    else:
                        # Insert new docstring
                        lines.insert(body_start, f'{indent_str}"""{docstring}"""')
                    break
            
            return '\n'.join(lines)
        except SyntaxError:
            return source
    
    @staticmethod
    def format_code(source: str) -> str:
        """Apply basic formatting to code."""
        lines = source.split('\n')
        result = []
        
        for line in lines:
            # Remove trailing whitespace
            line = line.rstrip()
            # Normalize indentation (spaces only)
            if line.startswith('\t'):
                line = line.replace('\t', '    ')
            result.append(line)
        
        # Ensure single newline at end
        while result and result[-1] == '':
            result.pop()
        result.append('')
        
        return '\n'.join(result)
    
    @staticmethod
    def rename_variable(source: str, old_name: str, new_name: str) -> str:
        """Rename a variable throughout the code."""
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(old_name) + r'\b'
        return re.sub(pattern, new_name, source)


class RollbackManager:
    """Manages rollback of applied refactorings."""
    
    def __init__(self, backup_dir: str = "/tmp/cef_backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._rollback_history: List[RollbackAction] = []
        self._lock = threading.Lock()
        
        # Metric thresholds for automatic rollback
        self.thresholds = {
            'error_rate': 0.05,      # 5% error rate increase triggers rollback
            'latency_p95': 0.20,     # 20% latency increase triggers rollback
            'test_pass_rate': 0.10   # 10% test pass rate decrease triggers rollback
        }
    
    def create_backup(self, file_path: str) -> str:
        """Create a backup of a file before modification."""
        source_path = Path(file_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Cannot backup non-existent file: {file_path}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(source_path.read_bytes()).hexdigest()[:8]
        backup_name = f"{source_path.name}.{timestamp}.{file_hash}.bak"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(source_path, backup_path)
        return str(backup_path)
    
    def restore_backup(self, backup_path: str, original_path: str) -> bool:
        """Restore a file from backup."""
        try:
            backup = Path(backup_path)
            original = Path(original_path)
            
            if not backup.exists():
                return False
            
            shutil.copy2(backup, original)
            return True
        except Exception:
            return False
    
    def should_rollback(
        self,
        metrics_before: Dict[str, float],
        metrics_after: Dict[str, float]
    ) -> Tuple[bool, Optional[RollbackTrigger], str]:
        """Determine if a rollback should be triggered based on metrics."""
        reasons = []
        trigger = None
        
        # Check error rate
        if 'error_rate' in metrics_before and 'error_rate' in metrics_after:
            increase = metrics_after['error_rate'] - metrics_before['error_rate']
            if increase > self.thresholds['error_rate']:
                reasons.append(f"Error rate increased by {increase:.1%}")
                trigger = RollbackTrigger.ERROR_RATE_SPIKE
        
        # Check latency
        if 'latency_p95' in metrics_before and 'latency_p95' in metrics_after:
            if metrics_before['latency_p95'] > 0:
                increase = (metrics_after['latency_p95'] - metrics_before['latency_p95']) / metrics_before['latency_p95']
                if increase > self.thresholds['latency_p95']:
                    reasons.append(f"P95 latency increased by {increase:.1%}")
                    trigger = RollbackTrigger.LATENCY_DEGRADATION
        
        # Check test pass rate
        if 'test_pass_rate' in metrics_before and 'test_pass_rate' in metrics_after:
            decrease = metrics_before['test_pass_rate'] - metrics_after['test_pass_rate']
            if decrease > self.thresholds['test_pass_rate']:
                reasons.append(f"Test pass rate decreased by {decrease:.1%}")
                trigger = RollbackTrigger.TEST_FAILURE
        
        should_rollback = len(reasons) > 0
        reason_str = "; ".join(reasons) if reasons else ""
        
        return should_rollback, trigger, reason_str
    
    def execute_rollback(
        self,
        refactor_result: RefactorResult,
        trigger: RollbackTrigger
    ) -> RollbackAction:
        """Execute a rollback operation."""
        action_id = f"rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{refactor_result.suggestion_id[:8]}"
        action = RollbackAction(
            action_id=action_id,
            refactor_result=refactor_result,
            trigger=trigger,
            triggered_at=datetime.now()
        )
        
        with self._lock:
            try:
                if refactor_result.backup_path:
                    success = self.restore_backup(
                        refactor_result.backup_path,
                        refactor_result.file_path
                    )
                    action.success = success
                    if not success:
                        action.error_message = "Failed to restore from backup"
                else:
                    action.error_message = "No backup path available"
                    action.success = False
                
                action.completed_at = datetime.now()
                refactor_result.status = RefactorStatus.ROLLED_BACK
                refactor_result.rolled_back_at = datetime.now()
                
                self._rollback_history.append(action)
                
            except Exception as e:
                action.success = False
                action.error_message = str(e)
                action.completed_at = datetime.now()
                self._rollback_history.append(action)
        
        return action
    
    def get_rollback_history(self) -> List[RollbackAction]:
        """Get the rollback history."""
        with self._lock:
            return list(self._rollback_history)


class ABTestManager:
    """Manages A/B tests for configuration tuning."""
    
    def __init__(self):
        self._tests: Dict[str, ABTest] = {}
        self._lock = threading.Lock()
        self._subscribers: List[Callable[[ABTestResult], None]] = []
    
    def create_test(
        self,
        name: str,
        description: str,
        config_key: str,
        control_value: Any,
        treatment_value: Any,
        min_samples: int = 100,
        confidence_threshold: float = 0.95
    ) -> ABTest:
        """Create a new A/B test."""
        test_id = f"ab_{hashlib.md5(f'{name}_{datetime.now()}'.encode()).hexdigest()[:8]}"
        
        control = ABTestVariant(
            name="control",
            config={config_key: control_value}
        )
        treatment = ABTestVariant(
            name="treatment",
            config={config_key: treatment_value}
        )
        
        test = ABTest(
            test_id=test_id,
            name=name,
            description=description,
            config_key=config_key,
            control=control,
            treatment=treatment,
            min_samples=min_samples,
            confidence_threshold=confidence_threshold
        )
        
        with self._lock:
            self._tests[test_id] = test
        
        return test
    
    def record_metric(
        self,
        test_id: str,
        variant: str,
        metric_name: str,
        value: float
    ) -> None:
        """Record a metric observation for a test variant."""
        with self._lock:
            if test_id not in self._tests:
                return
            
            test = self._tests[test_id]
            target = test.control if variant == "control" else test.treatment
            
            if metric_name not in target.metrics:
                target.metrics[metric_name] = []
            target.metrics[metric_name].append(value)
            target.sample_count += 1
    
    def get_variant(self, test_id: str) -> str:
        """Get a variant assignment for a request."""
        with self._lock:
            if test_id not in self._tests or not self._tests[test_id].is_active:
                return "control"
            
            test = self._tests[test_id]
            # Simple random assignment based on weights
            import random
            return "treatment" if random.random() < test.treatment.weight else "control"
    
    def analyze_test(self, test_id: str, metric_name: str = "success_rate") -> Optional[ABTestResult]:
        """Analyze an A/B test and determine if there's a winner."""
        with self._lock:
            if test_id not in self._tests:
                return None
            
            test = self._tests[test_id]
            control = test.control
            treatment = test.treatment
            
            # Check if we have enough samples
            if control.sample_count < test.min_samples or treatment.sample_count < test.min_samples:
                return ABTestResult(
                    test_id=test_id,
                    is_significant=False,
                    winner=None,
                    control_mean=0,
                    treatment_mean=0,
                    improvement_percent=0,
                    confidence=0,
                    recommendation="Need more samples"
                )
            
            # Get metric values
            control_values = control.metrics.get(metric_name, [])
            treatment_values = treatment.metrics.get(metric_name, [])
            
            if not control_values or not treatment_values:
                return ABTestResult(
                    test_id=test_id,
                    is_significant=False,
                    winner=None,
                    control_mean=0,
                    treatment_mean=0,
                    improvement_percent=0,
                    confidence=0,
                    recommendation=f"No data for metric: {metric_name}"
                )
            
            # Calculate statistics
            control_mean = sum(control_values) / len(control_values)
            treatment_mean = sum(treatment_values) / len(treatment_values)
            
            # Simple t-test approximation
            control_var = sum((x - control_mean) ** 2 for x in control_values) / len(control_values)
            treatment_var = sum((x - treatment_mean) ** 2 for x in treatment_values) / len(treatment_values)
            
            pooled_se = ((control_var / len(control_values)) + (treatment_var / len(treatment_values))) ** 0.5
            
            if pooled_se > 0:
                t_stat = abs(treatment_mean - control_mean) / pooled_se
                # Approximate confidence from t-stat (simplified)
                confidence = min(0.99, 1 - 2 * (1 / (1 + t_stat ** 2)))
            else:
                confidence = 0.5 if control_mean == treatment_mean else 0.99
            
            improvement = ((treatment_mean - control_mean) / control_mean * 100) if control_mean != 0 else 0
            is_significant = confidence >= test.confidence_threshold
            
            # Determine winner
            winner = None
            recommendation = "Continue test"
            if is_significant:
                if treatment_mean > control_mean:
                    winner = "treatment"
                    recommendation = f"Adopt treatment: {improvement:.1f}% improvement"
                else:
                    winner = "control"
                    recommendation = f"Keep control: treatment {-improvement:.1f}% worse"
            
            result = ABTestResult(
                test_id=test_id,
                is_significant=is_significant,
                winner=winner,
                control_mean=control_mean,
                treatment_mean=treatment_mean,
                improvement_percent=improvement,
                confidence=confidence,
                recommendation=recommendation
            )
            
            # Notify subscribers
            for subscriber in self._subscribers:
                try:
                    subscriber(result)
                except Exception:
                    pass
            
            return result
    
    def conclude_test(self, test_id: str) -> Optional[ABTestResult]:
        """Conclude an A/B test and apply the winner."""
        result = self.analyze_test(test_id)
        
        with self._lock:
            if test_id in self._tests:
                test = self._tests[test_id]
                test.is_active = False
                test.end_time = datetime.now()
                if result and result.winner:
                    test.winner = result.winner
        
        return result
    
    def subscribe(self, callback: Callable[[ABTestResult], None]) -> None:
        """Subscribe to A/B test result notifications."""
        self._subscribers.append(callback)
    
    def get_active_tests(self) -> List[ABTest]:
        """Get all active A/B tests."""
        with self._lock:
            return [t for t in self._tests.values() if t.is_active]
    
    def get_test(self, test_id: str) -> Optional[ABTest]:
        """Get a specific test."""
        with self._lock:
            return self._tests.get(test_id)


class PRGenerator:
    """Generates pull requests for medium-risk refactorings."""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self._generated_prs: List[Dict[str, Any]] = []
    
    def generate_diff(self, original: str, modified: str, file_path: str) -> str:
        """Generate a unified diff between original and modified content."""
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}"
        )
        
        return ''.join(diff)
    
    def create_pr_description(
        self,
        suggestion_id: str,
        risk: RefactorRisk,
        file_path: str,
        description: str,
        changes: List[str],
        metrics_impact: Dict[str, float]
    ) -> str:
        """Create a PR description for a refactoring."""
        template = f"""## CEF Automated Refactoring

**Suggestion ID:** `{suggestion_id}`
**Risk Level:** {risk.value.upper()}
**File:** `{file_path}`

### Description
{description}

### Changes Made
{chr(10).join(f'- {c}' for c in changes)}

### Expected Impact
{chr(10).join(f'- **{k}:** {v:+.1%}' for k, v in metrics_impact.items())}

### Validation
- [ ] Code review completed
- [ ] Tests pass
- [ ] No regressions detected

---
*Generated by CEF Autonomous Refactoring Engine*
"""
        return template
    
    def prepare_pr(
        self,
        suggestion_id: str,
        risk: RefactorRisk,
        file_path: str,
        original_content: str,
        modified_content: str,
        description: str,
        changes: List[str],
        metrics_impact: Dict[str, float]
    ) -> Dict[str, Any]:
        """Prepare a PR for review (doesn't actually create it)."""
        diff = self.generate_diff(original_content, modified_content, file_path)
        pr_description = self.create_pr_description(
            suggestion_id, risk, file_path, description, changes, metrics_impact
        )
        
        branch_name = f"cef/refactor-{suggestion_id[:8]}"
        pr_title = f"[CEF] {risk.value.capitalize()} Risk Refactoring: {Path(file_path).name}"
        
        pr_info = {
            'suggestion_id': suggestion_id,
            'branch_name': branch_name,
            'title': pr_title,
            'description': pr_description,
            'diff': diff,
            'file_path': file_path,
            'risk': risk.value,
            'created_at': datetime.now().isoformat()
        }
        
        self._generated_prs.append(pr_info)
        return pr_info
    
    def get_pending_prs(self) -> List[Dict[str, Any]]:
        """Get all prepared PRs that haven't been submitted."""
        return list(self._generated_prs)
    
    def export_pr(self, pr_info: Dict[str, Any], output_dir: str = "/tmp/cef_prs") -> str:
        """Export a PR to files for review."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        pr_dir = output_path / pr_info['suggestion_id'][:8]
        pr_dir.mkdir(exist_ok=True)
        
        # Write PR description
        (pr_dir / "PR_DESCRIPTION.md").write_text(pr_info['description'])
        
        # Write diff
        (pr_dir / "changes.diff").write_text(pr_info['diff'])
        
        # Write metadata
        (pr_dir / "metadata.json").write_text(json.dumps({
            k: v for k, v in pr_info.items() if k != 'diff'
        }, indent=2))
        
        return str(pr_dir)


class AutonomousRefactor:
    """Main orchestrator for autonomous refactoring operations."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.transformer = CodeTransformer()
        self.rollback_manager = RollbackManager()
        self.ab_test_manager = ABTestManager()
        self.pr_generator = PRGenerator()
        
        self._results: List[RefactorResult] = []
        self._subscribers: List[Callable[[RefactorResult], None]] = []
        self._auto_apply_enabled = True
        self._auto_rollback_enabled = True
        
        # Risk thresholds for auto-application
        self.auto_apply_risks = {RefactorRisk.LOW}  # Only auto-apply low risk by default
    
    def subscribe(self, callback: Callable[[RefactorResult], None]) -> None:
        """Subscribe to refactoring result notifications."""
        self._subscribers.append(callback)
    
    def _notify_subscribers(self, result: RefactorResult) -> None:
        """Notify all subscribers of a refactoring result."""
        for subscriber in self._subscribers:
            try:
                subscriber(result)
            except Exception:
                pass
    
    def classify_risk(self, suggestion: Dict[str, Any]) -> RefactorRisk:
        """Classify the risk level of a refactoring suggestion."""
        suggestion_type = suggestion.get('type', '').lower()
        
        # Low risk: formatting, whitespace, docstrings
        if suggestion_type in ['format', 'formatting', 'whitespace', 'docstring', 'comment']:
            return RefactorRisk.LOW
        
        # Low-Medium: type hints
        if suggestion_type in ['type_hint', 'type_annotation']:
            return RefactorRisk.LOW
        
        # Medium risk: variable renames, simple refactors
        if suggestion_type in ['rename', 'extract_method', 'extract_variable']:
            return RefactorRisk.MEDIUM
        
        # High risk: logic changes, API changes
        if suggestion_type in ['logic_change', 'api_change', 'function_signature']:
            return RefactorRisk.HIGH
        
        # Critical: deletions, security fixes
        if suggestion_type in ['delete', 'security_fix', 'breaking_change']:
            return RefactorRisk.CRITICAL
        
        # Default to medium
        return RefactorRisk.MEDIUM
    
    def can_auto_apply(self, risk: RefactorRisk) -> bool:
        """Check if a risk level can be auto-applied."""
        return self._auto_apply_enabled and risk in self.auto_apply_risks
    
    def apply_low_risk_refactoring(
        self,
        file_path: str,
        suggestion: Dict[str, Any],
        dry_run: bool = False
    ) -> RefactorResult:
        """Apply a low-risk refactoring (formatting, type hints, docstrings)."""
        suggestion_id = suggestion.get('id', hashlib.md5(str(suggestion).encode()).hexdigest()[:12])
        risk = self.classify_risk(suggestion)
        
        result = RefactorResult(
            suggestion_id=suggestion_id,
            risk=risk,
            status=RefactorStatus.PENDING,
            file_path=file_path,
            changes_made=[]
        )
        
        try:
            path = Path(file_path)
            if not path.exists():
                result.status = RefactorStatus.FAILED
                result.error_message = f"File not found: {file_path}"
                return result
            
            original_content = path.read_text()
            modified_content = original_content
            changes = []
            
            suggestion_type = suggestion.get('type', '').lower()
            
            # Apply formatting
            if suggestion_type in ['format', 'formatting', 'whitespace']:
                modified_content = self.transformer.format_code(modified_content)
                changes.append("Applied code formatting")
            
            # Add type hints
            elif suggestion_type in ['type_hint', 'type_annotation']:
                hints = suggestion.get('hints', {})
                modified_content = self.transformer.add_type_hints(modified_content, hints)
                changes.append(f"Added type hints: {list(hints.keys())}")
            
            # Add docstrings
            elif suggestion_type == 'docstring':
                func_name = suggestion.get('function')
                docstring = suggestion.get('docstring', '')
                if func_name and docstring:
                    modified_content = self.transformer.add_docstring(modified_content, func_name, docstring)
                    changes.append(f"Added docstring to {func_name}")
            
            # Check if any changes were made
            if modified_content == original_content:
                result.status = RefactorStatus.SKIPPED
                result.error_message = "No changes needed"
                return result
            
            result.changes_made = [{'type': suggestion_type, 'description': c} for c in changes]
            
            if not dry_run:
                # Create backup
                result.backup_path = self.rollback_manager.create_backup(file_path)
                
                # Write changes
                path.write_text(modified_content)
                result.status = RefactorStatus.APPLIED
                result.applied_at = datetime.now()
            else:
                result.status = RefactorStatus.PENDING
            
            self._results.append(result)
            self._notify_subscribers(result)
            
        except Exception as e:
            result.status = RefactorStatus.FAILED
            result.error_message = str(e)
        
        return result
    
    def process_suggestion(
        self,
        suggestion: Dict[str, Any],
        metrics_collector: Optional[Callable[[], Dict[str, float]]] = None
    ) -> RefactorResult:
        """Process a refactoring suggestion based on its risk level."""
        file_path = suggestion.get('file_path', '')
        risk = self.classify_risk(suggestion)
        
        # Collect metrics before (if collector provided)
        metrics_before = metrics_collector() if metrics_collector else {}
        
        if self.can_auto_apply(risk):
            # Auto-apply low risk
            result = self.apply_low_risk_refactoring(file_path, suggestion)
            result.metrics_before = metrics_before
            
            # Collect metrics after
            if metrics_collector and result.status == RefactorStatus.APPLIED:
                result.metrics_after = metrics_collector()
                
                # Check if rollback is needed
                if self._auto_rollback_enabled:
                    should_rollback, trigger, reason = self.rollback_manager.should_rollback(
                        result.metrics_before,
                        result.metrics_after
                    )
                    if should_rollback and trigger:
                        self.rollback_manager.execute_rollback(result, trigger)
        
        elif risk == RefactorRisk.MEDIUM:
            # Generate PR for medium risk
            path = Path(file_path)
            if path.exists():
                original_content = path.read_text()
                # For medium risk, we just prepare the PR
                pr_info = self.pr_generator.prepare_pr(
                    suggestion_id=suggestion.get('id', 'unknown'),
                    risk=risk,
                    file_path=file_path,
                    original_content=original_content,
                    modified_content=suggestion.get('suggested_code', original_content),
                    description=suggestion.get('description', 'Medium risk refactoring'),
                    changes=[suggestion.get('description', 'Code improvement')],
                    metrics_impact=suggestion.get('expected_impact', {})
                )
                
                result = RefactorResult(
                    suggestion_id=suggestion.get('id', 'unknown'),
                    risk=risk,
                    status=RefactorStatus.PENDING,
                    file_path=file_path,
                    changes_made=[{'type': 'pr_generated', 'pr_info': pr_info}]
                )
            else:
                result = RefactorResult(
                    suggestion_id=suggestion.get('id', 'unknown'),
                    risk=risk,
                    status=RefactorStatus.FAILED,
                    file_path=file_path,
                    changes_made=[],
                    error_message=f"File not found: {file_path}"
                )
        
        else:
            # High/Critical risk - skip auto-processing
            result = RefactorResult(
                suggestion_id=suggestion.get('id', 'unknown'),
                risk=risk,
                status=RefactorStatus.SKIPPED,
                file_path=file_path,
                changes_made=[],
                error_message=f"Risk level {risk.value} requires manual review"
            )
        
        self._results.append(result)
        return result
    
    def process_suggestions_batch(
        self,
        suggestions: List[Dict[str, Any]],
        metrics_collector: Optional[Callable[[], Dict[str, float]]] = None
    ) -> List[RefactorResult]:
        """Process multiple suggestions in batch."""
        results = []
        for suggestion in suggestions:
            result = self.process_suggestion(suggestion, metrics_collector)
            results.append(result)
        return results
    
    def get_results(self) -> List[RefactorResult]:
        """Get all refactoring results."""
        return list(self._results)
    
    def get_results_by_status(self, status: RefactorStatus) -> List[RefactorResult]:
        """Get results filtered by status."""
        return [r for r in self._results if r.status == status]
    
    def get_pending_prs(self) -> List[Dict[str, Any]]:
        """Get all pending PRs for medium-risk refactorings."""
        return self.pr_generator.get_pending_prs()
    
    def export_state(self) -> Dict[str, Any]:
        """Export the current state of the autonomous refactor system."""
        return {
            'results': [r.to_dict() for r in self._results],
            'pending_prs': self.pr_generator.get_pending_prs(),
            'active_ab_tests': [t.to_dict() for t in self.ab_test_manager.get_active_tests()],
            'rollback_history': [a.to_dict() for a in self.rollback_manager.get_rollback_history()],
            'settings': {
                'auto_apply_enabled': self._auto_apply_enabled,
                'auto_rollback_enabled': self._auto_rollback_enabled,
                'auto_apply_risks': [r.value for r in self.auto_apply_risks]
            },
            'exported_at': datetime.now().isoformat()
        }


# Convenience function to get singleton instance
def get_autonomous_refactor() -> AutonomousRefactor:
    """Get the singleton AutonomousRefactor instance."""
    return AutonomousRefactor()
