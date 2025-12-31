"""
Tests for CEFR Developer Tools

Tests the dependency analyzer and import validator tools.
"""

import pytest
import sys
import subprocess
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


class TestDependencyAnalyzer:
    """Tests for dependency_analyzer.py"""
    
    def test_analyzer_exists(self):
        """Test that dependency_analyzer.py exists."""
        analyzer_path = PROJECT_ROOT / 'tools' / 'cefr' / 'dependency_analyzer.py'
        assert analyzer_path.exists(), "dependency_analyzer.py should exist"
    
    def test_analyzer_is_executable(self):
        """Test that dependency_analyzer.py is executable."""
        analyzer_path = PROJECT_ROOT / 'tools' / 'cefr' / 'dependency_analyzer.py'
        result = subprocess.run(
            [sys.executable, str(analyzer_path), '--help'],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        # Should fail with help message or run successfully
        # Exit code 1 means circular deps found, which is OK for test
        assert result.returncode in [0, 1], f"Should be runnable, got: {result.stderr}"
    
    def test_analyzer_output(self):
        """Test that dependency_analyzer.py generates output."""
        analyzer_path = PROJECT_ROOT / 'tools' / 'cefr' / 'dependency_analyzer.py'
        result = subprocess.run(
            [sys.executable, str(analyzer_path)],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=30
        )
        
        # Should produce output
        assert len(result.stdout) > 0, "Should produce output"
        assert "DEPENDENCY ANALYSIS REPORT" in result.stdout, "Should have report header"
        assert "Total Python modules:" in result.stdout, "Should show module count"
    
    def test_analyzer_creates_report(self):
        """Test that dependency_analyzer.py creates report file."""
        analyzer_path = PROJECT_ROOT / 'tools' / 'cefr' / 'dependency_analyzer.py'
        report_path = PROJECT_ROOT / 'docs' / 'DEPENDENCY_ANALYSIS.md'
        
        # Run analyzer
        result = subprocess.run(
            [sys.executable, str(analyzer_path)],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=30
        )
        
        # Check report was created
        assert report_path.exists(), "Report file should be created"
        
        # Check report content
        with open(report_path, 'r') as f:
            content = f.read()
            assert "DEPENDENCY ANALYSIS REPORT" in content
            assert "Total Python modules:" in content


class TestImportValidator:
    """Tests for import_validator.py"""
    
    def test_validator_exists(self):
        """Test that import_validator.py exists."""
        validator_path = PROJECT_ROOT / 'tools' / 'cefr' / 'import_validator.py'
        assert validator_path.exists(), "import_validator.py should exist"
    
    def test_validator_is_executable(self):
        """Test that import_validator.py is executable."""
        validator_path = PROJECT_ROOT / 'tools' / 'cefr' / 'import_validator.py'
        result = subprocess.run(
            [sys.executable, str(validator_path)],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=15
        )
        # Exit code 0 or 1 both acceptable (depends on if deps installed)
        assert result.returncode in [0, 1], f"Should be runnable, got: {result.stderr}"
    
    def test_validator_output(self):
        """Test that import_validator.py generates output."""
        validator_path = PROJECT_ROOT / 'tools' / 'cefr' / 'import_validator.py'
        result = subprocess.run(
            [sys.executable, str(validator_path)],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=15
        )
        
        # Should produce output
        assert len(result.stdout) > 0, "Should produce output"
        assert "IMPORT VALIDATION" in result.stdout, "Should have validation header"
        assert "Validating critical imports" in result.stdout, "Should validate imports"
        assert "SUMMARY" in result.stdout, "Should have summary section"


class TestToolsREADME:
    """Tests for tools/cefr/README.md"""
    
    def test_readme_exists(self):
        """Test that tools/cefr/README.md exists."""
        readme_path = PROJECT_ROOT / 'tools' / 'cefr' / 'README.md'
        assert readme_path.exists(), "README.md should exist"
    
    def test_readme_content(self):
        """Test that README.md has proper content."""
        readme_path = PROJECT_ROOT / 'tools' / 'cefr' / 'README.md'
        
        with open(readme_path, 'r') as f:
            content = f.read()
        
        # Check key sections
        assert "CEFR Developer Tools" in content
        assert "dependency_analyzer.py" in content
        assert "import_validator.py" in content
        assert "Usage" in content or "usage" in content.lower()
        assert "Features" in content
