#!/usr/bin/env python3
"""
=============================================================================
CEFR AUTOMATED PIPELINE - CEF Refactoring Continuous Self-Improvement System
=============================================================================

CEFR (CEF Refactoring) is the automated refactoring component of the
Circular Exchange Framework. This script provides a fully automated 
refactoring cycle that:

1. Runs tests and collects results
2. Analyzes patterns and generates insights using CEFR
3. Applies low-risk automated fixes
4. Generates PRs for medium/high-risk suggestions
5. Reports results to GitHub

This eliminates the manual cycle of:
  commit → git pull → launch.sh → run tests → copy-paste to AI

Usage:
    # Run locally with auto-apply disabled (dry run)
    python scripts/run_automated_cef_pipeline.py --dry-run
    
    # Run locally and auto-apply low-risk fixes
    python scripts/run_automated_cef_pipeline.py --auto-apply
    
    # Run in CI mode (outputs GitHub Actions annotations)
    python scripts/run_automated_cef_pipeline.py --ci
    
    # Watch mode - continuously monitors and refactors
    python scripts/run_automated_cef_pipeline.py --watch --interval 300

Environment Variables:
    CEF_AUTO_APPLY: Set to 'true' to enable auto-applying low-risk fixes
    CEF_GITHUB_TOKEN: GitHub token for PR creation (optional)
    CEF_WEBHOOK_URL: Webhook URL for notifications (optional)

=============================================================================
"""

import sys
import os
import time
import json
import logging
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Add parent directories to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# CEF Component Imports
# =============================================================================

try:
    from shared.circular_exchange.analysis.data_collector import (
        DataCollector, TestResult, LogEntry, ExtractionEvent, TestStatus
    )
    from shared.circular_exchange.analysis.metrics_analyzer import MetricsAnalyzer
    from shared.circular_exchange.refactor.refactoring_engine import (
        RefactoringEngine as CEFRefactoringEngine, SuggestionType, ImpactLevel, EffortLevel
    )
    from shared.circular_exchange.refactor.feedback_loop import FeedbackLoop
    from shared.circular_exchange.analysis.intelligent_analyzer import IntelligentAnalyzer
    from shared.circular_exchange.refactor.autonomous_refactor import (
        AutonomousRefactor, RefactorResult, RefactorRisk as RiskLevel
    )
    CEF_AVAILABLE = True
except ImportError as e:
    logger.warning(f"CEF components not fully available: {e}")
    CEF_AVAILABLE = False


# =============================================================================
# Configuration
# =============================================================================

class PipelineConfig:
    """Configuration for the automated pipeline."""
    
    def __init__(self):
        self.dry_run = True
        self.auto_apply = os.getenv('CEF_AUTO_APPLY', 'false').lower() == 'true'
        self.ci_mode = os.getenv('CI', 'false').lower() == 'true'
        self.github_token = os.getenv('CEF_GITHUB_TOKEN') or os.getenv('GITHUB_TOKEN')
        self.webhook_url = os.getenv('CEF_WEBHOOK_URL')
        self.watch_mode = False
        self.watch_interval = 300  # 5 minutes
        self.max_auto_apply_risk = RiskLevel.LOW if CEF_AVAILABLE else 'low'
        self.test_timeout = 300  # 5 minutes
        self.verbose = False


# =============================================================================
# Test Runner
# =============================================================================

class TestRunner:
    """Runs tests and collects results for CEF analysis."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_results: List[Dict] = []
        self.coverage_data: Optional[Dict] = None
    
    def run_tests(self, timeout: int = 300) -> Tuple[bool, Dict]:
        """
        Run pytest and collect results.
        
        Returns:
            Tuple of (success, results_dict)
        """
        logger.info("Running tests...")
        
        # Ensure output directory exists
        output_dir = self.project_root / "data" / "pipeline"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results_file = output_dir / "test_results.json"
        coverage_file = output_dir / "coverage.json"
        
        try:
            # Run pytest with JSON output
            cmd = [
                sys.executable, "-m", "pytest",
                str(self.project_root / "tests"),
                "--json-report",
                f"--json-report-file={results_file}",
                "--cov=shared",
                f"--cov-report=json:{coverage_file}",
                "-v",
                "--tb=short",
                "-x",  # Stop on first failure for faster feedback
            ]
            
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.project_root)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.project_root),
                env=env
            )
            
            success = result.returncode == 0
            
            # Load results
            results_dict = {'success': success, 'tests': [], 'summary': {}}
            
            if results_file.exists():
                with open(results_file) as f:
                    report = json.load(f)
                    results_dict['tests'] = report.get('tests', [])
                    results_dict['summary'] = report.get('summary', {})
            
            if coverage_file.exists():
                with open(coverage_file) as f:
                    self.coverage_data = json.load(f)
                    results_dict['coverage'] = self.coverage_data
            
            # Store for later use
            self.test_results = results_dict.get('tests', [])
            
            logger.info(f"Tests completed: {'PASSED' if success else 'FAILED'}")
            logger.info(f"  Total: {results_dict['summary'].get('total', 0)}")
            logger.info(f"  Passed: {results_dict['summary'].get('passed', 0)}")
            logger.info(f"  Failed: {results_dict['summary'].get('failed', 0)}")
            
            return success, results_dict
            
        except subprocess.TimeoutExpired:
            logger.error(f"Tests timed out after {timeout} seconds")
            return False, {'success': False, 'error': 'timeout'}
        except Exception as e:
            logger.error(f"Error running tests: {e}")
            return False, {'success': False, 'error': str(e)}
    
    def feed_to_collector(self, collector: DataCollector) -> int:
        """
        Feed test results to the CEF data collector.
        
        Returns:
            Number of test results recorded
        """
        count = 0
        for test in self.test_results:
            status = TestStatus.PASSED if test.get('outcome') == 'passed' else TestStatus.FAILED
            
            result = TestResult(
                test_id=test.get('nodeid', f'test_{count}'),
                test_name=test.get('nodeid', 'unknown').split('::')[-1],
                module_path=test.get('nodeid', 'unknown').split('::')[0],
                status=status,
                duration_ms=test.get('duration', 0) * 1000,
                timestamp=datetime.now(),
                error_message=test.get('call', {}).get('longrepr') if status == TestStatus.FAILED else None
            )
            collector.record_test_result(result)
            count += 1
        
        return count


# =============================================================================
# Automated Refactoring Engine
# =============================================================================

class AutomatedRefactorEngine:
    """Coordinates automated refactoring based on CEF analysis."""
    
    def __init__(self, project_root: Path, config: PipelineConfig):
        self.project_root = project_root
        self.config = config
        self.applied_changes: List[Dict] = []
        self.pending_suggestions: List[Dict] = []
        
        # Initialize CEF components
        if CEF_AVAILABLE:
            self.collector = DataCollector()
            self.analyzer = MetricsAnalyzer()
            self.cefr = CEFRefactoringEngine()
            self.feedback_loop = FeedbackLoop()
            self.intelligent_analyzer = IntelligentAnalyzer()
            try:
                self.autonomous_refactor = AutonomousRefactor()
            except Exception:
                self.autonomous_refactor = None
    
    def analyze_and_suggest(self) -> Dict[str, Any]:
        """
        Run CEF analysis and generate refactoring suggestions.
        
        Returns:
            Dictionary with analysis results and suggestions
        """
        if not CEF_AVAILABLE:
            return {'error': 'CEF components not available'}
        
        results = {
            'patterns': [],
            'insights': [],
            'suggestions': [],
            'bottlenecks': [],
            'tuning_decisions': []
        }
        
        # Analyze error patterns
        try:
            patterns = self.analyzer.analyze_error_patterns()
            results['patterns'] = [p.to_dict() for p in patterns]
            logger.info(f"Detected {len(patterns)} error patterns")
        except Exception as e:
            logger.warning(f"Pattern analysis failed: {e}")
        
        # Analyze test health
        try:
            health_report = self.analyzer.analyze_test_health()
            results['test_health'] = health_report.to_dict() if health_report else None
            logger.info(f"Test health: {health_report.pass_rate:.1%} pass rate" if health_report else "No test data")
        except Exception as e:
            logger.warning(f"Test health analysis failed: {e}")
        
        # Generate refactoring insights
        try:
            insights = self.analyzer.generate_refactoring_insights()
            results['insights'] = [i.to_dict() for i in insights]
            logger.info(f"Generated {len(insights)} refactoring insights")
        except Exception as e:
            logger.warning(f"Insight generation failed: {e}")
        
        # Generate code suggestions
        try:
            # Error handling suggestions
            error_suggestions = self.cefr.analyze_error_handling()
            
            # Performance suggestions
            perf_suggestions = self.cefr.analyze_performance()
            
            # Testing suggestions
            test_suggestions = self.cefr.analyze_testing()
            
            all_suggestions = error_suggestions + perf_suggestions + test_suggestions
            results['suggestions'] = [s.to_dict() for s in all_suggestions]
            
            logger.info(f"Generated {len(all_suggestions)} code suggestions")
            logger.info(f"  - Error handling: {len(error_suggestions)}")
            logger.info(f"  - Performance: {len(perf_suggestions)}")
            logger.info(f"  - Testing: {len(test_suggestions)}")
        except Exception as e:
            logger.warning(f"Suggestion generation failed: {e}")
        
        # Run feedback loop
        try:
            cycle_results = self.feedback_loop.run_cycle()
            results['tuning_decisions'] = cycle_results.get('tuning_decisions', [])
            logger.info(f"Feedback loop generated {len(results['tuning_decisions'])} tuning decisions")
        except Exception as e:
            logger.warning(f"Feedback loop failed: {e}")
        
        return results
    
    def apply_low_risk_fixes(self, suggestions: List[Dict]) -> List[Dict]:
        """
        Apply low-risk automated fixes.
        
        Returns:
            List of applied changes
        """
        if self.config.dry_run:
            logger.info("DRY RUN: Would apply the following fixes:")
            for s in suggestions:
                if s.get('auto_fixable', False):
                    logger.info(f"  - {s.get('title', 'Unknown')}")
            return []
        
        applied = []
        
        if self.autonomous_refactor:
            for suggestion in suggestions:
                # Only apply low-risk, auto-fixable suggestions
                if not suggestion.get('auto_fixable', False):
                    continue
                
                # Check risk level
                risk = suggestion.get('risk_level', 'high')
                if risk not in ['low', RiskLevel.LOW.value if CEF_AVAILABLE else 'low']:
                    continue
                
                try:
                    # Attempt to apply the fix
                    result = self.autonomous_refactor.apply_suggestion(suggestion)
                    if result and result.success:
                        applied.append({
                            'suggestion': suggestion,
                            'result': result.to_dict() if hasattr(result, 'to_dict') else str(result)
                        })
                        logger.info(f"Applied fix: {suggestion.get('title', 'Unknown')}")
                except Exception as e:
                    logger.warning(f"Failed to apply fix: {e}")
        
        self.applied_changes.extend(applied)
        return applied
    
    def generate_report(self, analysis_results: Dict, applied_changes: List[Dict]) -> str:
        """
        Generate a markdown report of the refactoring cycle.
        
        Returns:
            Markdown-formatted report string
        """
        report = []
        report.append("# CEF Automated Refactoring Report")
        report.append(f"\n**Generated:** {datetime.now().isoformat()}")
        report.append(f"**Mode:** {'Dry Run' if self.config.dry_run else 'Live'}")
        report.append("")
        
        # Summary section
        report.append("## Summary")
        report.append("")
        
        patterns_count = len(analysis_results.get('patterns', []))
        insights_count = len(analysis_results.get('insights', []))
        suggestions_count = len(analysis_results.get('suggestions', []))
        applied_count = len(applied_changes)
        
        report.append(f"- **Patterns Detected:** {patterns_count}")
        report.append(f"- **Insights Generated:** {insights_count}")
        report.append(f"- **Suggestions Created:** {suggestions_count}")
        report.append(f"- **Fixes Applied:** {applied_count}")
        report.append("")
        
        # Test Health
        test_health = analysis_results.get('test_health')
        if test_health:
            report.append("## Test Health")
            report.append("")
            report.append(f"- **Pass Rate:** {test_health.get('pass_rate', 0):.1%}")
            report.append(f"- **Total Tests:** {test_health.get('total_tests', 0)}")
            if test_health.get('flaky_tests'):
                report.append(f"- **Flaky Tests:** {len(test_health['flaky_tests'])}")
            if test_health.get('slow_tests'):
                report.append(f"- **Slow Tests:** {len(test_health['slow_tests'])}")
            report.append("")
        
        # Suggestions by category
        suggestions = analysis_results.get('suggestions', [])
        if suggestions:
            report.append("## Refactoring Suggestions")
            report.append("")
            
            # Group by type
            by_type = {}
            for s in suggestions:
                stype = s.get('suggestion_type', 'other')
                if stype not in by_type:
                    by_type[stype] = []
                by_type[stype].append(s)
            
            for stype, items in by_type.items():
                report.append(f"### {stype.replace('_', ' ').title()} ({len(items)})")
                report.append("")
                for item in items[:5]:  # Limit to top 5 per category
                    title = item.get('title', 'Unknown')
                    impact = item.get('impact', 'unknown')
                    auto_fix = "✅ Auto-fixable" if item.get('auto_fixable') else "⚠️ Manual review"
                    report.append(f"- **{title}** - Impact: {impact} - {auto_fix}")
                report.append("")
        
        # Applied changes
        if applied_changes:
            report.append("## Applied Changes")
            report.append("")
            for change in applied_changes:
                s = change.get('suggestion', {})
                report.append(f"- ✅ {s.get('title', 'Unknown change')}")
            report.append("")
        
        # Recommendations
        report.append("## Next Steps")
        report.append("")
        report.append("1. Review the suggestions above and prioritize based on impact")
        report.append("2. For manual changes, create focused PRs for each category")
        report.append("3. Run the pipeline again after changes to verify improvements")
        report.append("4. Consider adding more tests for areas with low coverage")
        report.append("")
        
        return "\n".join(report)


# =============================================================================
# GitHub Integration
# =============================================================================

class GitHubIntegration:
    """Integration with GitHub for PR creation and annotations."""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.github_token = config.github_token
    
    def create_issue(self, title: str, body: str, labels: List[str] = None) -> Optional[str]:
        """Create a GitHub issue with refactoring suggestions."""
        if not self.github_token:
            logger.info("No GitHub token available - skipping issue creation")
            return None
        
        # Would use PyGithub or requests to create issue
        logger.info(f"Would create issue: {title}")
        return None
    
    def add_annotation(self, message: str, level: str = "notice", 
                      file: str = None, line: int = None) -> None:
        """Add GitHub Actions annotation."""
        if not self.config.ci_mode:
            return
        
        prefix = f"::{level} "
        if file:
            prefix += f"file={file}"
            if line:
                prefix += f",line={line}"
            prefix += "::"
        
        print(f"{prefix}{message}")


# =============================================================================
# Main Pipeline
# =============================================================================

class AutomatedCEFPipeline:
    """Main orchestrator for the automated CEF refactoring pipeline."""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.project_root = Path(__file__).parent.parent
        
        self.test_runner = TestRunner(self.project_root)
        self.refactor_engine = AutomatedRefactorEngine(self.project_root, config)
        self.github = GitHubIntegration(config)
    
    def run_cycle(self) -> Dict[str, Any]:
        """
        Run a complete refactoring cycle.
        
        Returns:
            Dictionary with cycle results
        """
        cycle_start = datetime.now()
        
        results = {
            'timestamp': cycle_start.isoformat(),
            'config': {
                'dry_run': self.config.dry_run,
                'auto_apply': self.config.auto_apply,
                'ci_mode': self.config.ci_mode
            },
            'tests': {},
            'analysis': {},
            'applied_changes': [],
            'report': ''
        }
        
        print("=" * 70)
        print("CEF AUTOMATED REFACTORING PIPELINE")
        print("=" * 70)
        print(f"\nTimestamp: {cycle_start.isoformat()}")
        print(f"Mode: {'Dry Run' if self.config.dry_run else 'Live'}")
        print(f"Auto-Apply: {'Enabled' if self.config.auto_apply else 'Disabled'}")
        print("")
        
        # Step 1: Run tests
        print("-" * 40)
        print("Step 1: Running Tests")
        print("-" * 40)
        
        test_success, test_results = self.test_runner.run_tests(self.config.test_timeout)
        results['tests'] = test_results
        
        if not test_success and not self.config.ci_mode:
            logger.warning("Tests failed - continuing with analysis anyway")
        
        # Step 2: Feed data to CEF collector
        print("\n" + "-" * 40)
        print("Step 2: Feeding Data to CEF")
        print("-" * 40)
        
        if CEF_AVAILABLE:
            count = self.test_runner.feed_to_collector(self.refactor_engine.collector)
            print(f"Recorded {count} test results")
        
        # Step 3: Run CEF analysis
        print("\n" + "-" * 40)
        print("Step 3: Running CEF Analysis")
        print("-" * 40)
        
        analysis = self.refactor_engine.analyze_and_suggest()
        results['analysis'] = analysis
        
        # Step 4: Apply low-risk fixes (if enabled)
        print("\n" + "-" * 40)
        print("Step 4: Applying Automated Fixes")
        print("-" * 40)
        
        if self.config.auto_apply and not self.config.dry_run:
            applied = self.refactor_engine.apply_low_risk_fixes(
                analysis.get('suggestions', [])
            )
            results['applied_changes'] = applied
            print(f"Applied {len(applied)} automated fixes")
        else:
            print("Auto-apply disabled or dry run mode")
        
        # Step 5: Generate report
        print("\n" + "-" * 40)
        print("Step 5: Generating Report")
        print("-" * 40)
        
        report = self.refactor_engine.generate_report(analysis, results['applied_changes'])
        results['report'] = report
        
        # Save report
        report_path = self.project_root / "data" / "pipeline" / "refactoring_report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            f.write(report)
        print(f"Report saved to: {report_path}")
        
        # Save full results as JSON
        results_path = self.project_root / "data" / "pipeline" / "pipeline_results.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Full results saved to: {results_path}")
        
        # Print summary
        print("\n" + "=" * 70)
        print("PIPELINE COMPLETE")
        print("=" * 70)
        
        duration = (datetime.now() - cycle_start).total_seconds()
        print(f"\nDuration: {duration:.1f}s")
        print(f"Tests: {test_results.get('summary', {}).get('total', 0)} total, " +
              f"{test_results.get('summary', {}).get('passed', 0)} passed")
        print(f"Patterns: {len(analysis.get('patterns', []))}")
        print(f"Suggestions: {len(analysis.get('suggestions', []))}")
        print(f"Applied: {len(results['applied_changes'])}")
        print("")
        
        # Add GitHub annotations in CI mode
        if self.config.ci_mode:
            for suggestion in analysis.get('suggestions', [])[:10]:
                self.github.add_annotation(
                    f"CEF Suggestion: {suggestion.get('title', 'Unknown')}",
                    level="notice"
                )
        
        return results
    
    def run_watch_mode(self) -> None:
        """
        Run in watch mode, continuously monitoring and refactoring.
        """
        print("Starting watch mode...")
        print(f"Will run every {self.config.watch_interval} seconds")
        print("Press Ctrl+C to stop")
        print("")
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                print(f"\n{'='*70}")
                print(f"WATCH MODE - Cycle #{cycle_count}")
                print(f"{'='*70}")
                
                self.run_cycle()
                
                print(f"\nSleeping for {self.config.watch_interval} seconds...")
                time.sleep(self.config.watch_interval)
                
        except KeyboardInterrupt:
            print("\nWatch mode stopped by user")


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """Main entry point for the automated pipeline."""
    parser = argparse.ArgumentParser(
        description="CEF Automated Refactoring Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run - see what would be done
  python run_automated_cef_pipeline.py --dry-run
  
  # Auto-apply low-risk fixes
  python run_automated_cef_pipeline.py --auto-apply
  
  # Watch mode - continuous monitoring
  python run_automated_cef_pipeline.py --watch --interval 300
  
  # CI mode with verbose output
  python run_automated_cef_pipeline.py --ci --verbose
"""
    )
    
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        default=True,
        help='Run without applying changes (default: True)'
    )
    
    parser.add_argument(
        '--auto-apply',
        action='store_true',
        help='Enable auto-applying low-risk fixes'
    )
    
    parser.add_argument(
        '--ci',
        action='store_true',
        help='Run in CI mode with GitHub Actions annotations'
    )
    
    parser.add_argument(
        '--watch',
        action='store_true',
        help='Run in watch mode for continuous monitoring'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Interval in seconds for watch mode (default: 300)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Configure pipeline
    config = PipelineConfig()
    config.dry_run = not args.auto_apply
    config.auto_apply = args.auto_apply
    config.ci_mode = args.ci
    config.watch_mode = args.watch
    config.watch_interval = args.interval
    config.verbose = args.verbose
    
    if config.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run pipeline
    pipeline = AutomatedCEFPipeline(config)
    
    if config.watch_mode:
        pipeline.run_watch_mode()
    else:
        pipeline.run_cycle()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
