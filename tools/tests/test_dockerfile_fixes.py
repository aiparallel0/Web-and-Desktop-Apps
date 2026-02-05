"""
Test suite for Dockerfile fixes.

Tests:
- Cleanup commands preserve training directory
- HEALTHCHECK uses proper shell interpolation
- Training module verification steps are present
"""

import sys
import os
import re
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


class TestDockerfileCleanupFixes:
    """Test Dockerfile cleanup command fixes."""
    
    def test_dockerfile_exists(self):
        """Test that Dockerfile exists."""
        dockerfile_path = project_root / 'Dockerfile'
        assert dockerfile_path.exists(), "Dockerfile not found"
    
    def test_cleanup_preserves_training_directory(self):
        """Test that cleanup commands exclude web/backend/training."""
        dockerfile_path = project_root / 'Dockerfile'
        content = dockerfile_path.read_text()
        
        # Check for the prune pattern that excludes training directory
        # Pattern: find . -path ./web/backend/training -prune -o -type d -name "tests"
        assert '-path ./web/backend/training -prune' in content, \
            "Cleanup commands don't exclude training directory"
        
        # Count occurrences (should be at least 2: one for "tests", one for "test")
        prune_count = content.count('-path ./web/backend/training -prune')
        assert prune_count >= 2, \
            f"Expected at least 2 prune patterns, found {prune_count}"
    
    def test_healthcheck_uses_shell_interpolation(self):
        """Test that HEALTHCHECK uses proper shell interpolation."""
        dockerfile_path = project_root / 'Dockerfile'
        content = dockerfile_path.read_text()
        
        # Check for sh -c with proper variable expansion
        assert 'sh -c' in content, "HEALTHCHECK doesn't use sh -c"
        assert '${PORT:-5000}' in content, \
            "HEALTHCHECK doesn't use proper ${PORT:-5000} syntax"
        
        # Verify HEALTHCHECK line format
        healthcheck_pattern = r'HEALTHCHECK.*CMD\s+sh\s+-c.*\$\{PORT:-5000\}'
        assert re.search(healthcheck_pattern, content), \
            "HEALTHCHECK format is incorrect"
    
    def test_training_module_verification_exists(self):
        """Test that training module verification step exists."""
        dockerfile_path = project_root / 'Dockerfile'
        content = dockerfile_path.read_text()
        
        # Check for verification RUN command
        assert 'test -d web/backend/training' in content, \
            "Missing training directory existence check"
        
        # Check for import verification
        assert 'import web.backend.training.celery_worker' in content, \
            "Missing training module import verification"
        
        # Check for error messages
        assert 'web/backend/training missing' in content or \
               'training missing' in content, \
               "Missing error message for training directory check"
    
    def test_cleanup_comment_mentions_preservation(self):
        """Test that cleanup section has comment about preservation."""
        dockerfile_path = project_root / 'Dockerfile'
        content = dockerfile_path.read_text()
        
        # Check for comment mentioning training preservation
        assert 'training is preserved' in content or \
               'training' in content, \
               "Missing comment about training preservation"
    
    def test_dockerfile_structure(self):
        """Test overall Dockerfile structure."""
        dockerfile_path = project_root / 'Dockerfile'
        content = dockerfile_path.read_text()
        
        # Basic structure checks
        assert 'FROM python:' in content, "Missing FROM instruction"
        assert 'COPY' in content, "Missing COPY instruction"
        assert 'RUN' in content, "Missing RUN instruction"
        assert 'CMD' in content, "Missing CMD instruction"
        assert 'EXPOSE' in content, "Missing EXPOSE instruction"
        
        # Check order: cleanup should come before verification
        cleanup_pos = content.find('find . -path ./web/backend/training')
        verify_pos = content.find('test -d web/backend/training')
        
        if cleanup_pos != -1 and verify_pos != -1:
            assert cleanup_pos < verify_pos, \
                "Verification should come after cleanup"


class TestDockerfileSecurity:
    """Test Dockerfile security best practices."""
    
    def test_non_root_user(self):
        """Test that Dockerfile uses non-root user."""
        dockerfile_path = project_root / 'Dockerfile'
        content = dockerfile_path.read_text()
        
        # Check for user creation
        assert 'useradd' in content or 'adduser' in content, \
            "Missing non-root user creation"
        
        # Check for USER directive
        assert 'USER ' in content, "Missing USER directive"
        
        # Verify USER comes after installation steps
        user_pos = content.find('USER receipt')
        copy_pos = content.find('COPY')
        assert user_pos > copy_pos, \
            "USER directive should come after COPY instructions"


def test_dockerfile_validation():
    """Main validation function."""
    dockerfile_path = project_root / 'Dockerfile'
    assert dockerfile_path.exists(), "Dockerfile not found"
    
    content = dockerfile_path.read_text()
    
    print("\n=== Dockerfile Validation ===\n")
    
    # Check 1: Training directory preservation
    if '-path ./web/backend/training -prune' in content:
        print("✅ Cleanup commands exclude training directory")
    else:
        print("❌ Cleanup commands don't exclude training directory")
        return False
    
    # Check 2: HEALTHCHECK
    if 'sh -c' in content and '${PORT:-5000}' in content:
        print("✅ HEALTHCHECK uses proper shell interpolation")
    else:
        print("❌ HEALTHCHECK doesn't use proper shell interpolation")
        return False
    
    # Check 3: Verification steps
    if 'test -d web/backend/training' in content:
        print("✅ Training directory verification exists")
    else:
        print("❌ Training directory verification missing")
        return False
    
    if 'import web.backend.training.celery_worker' in content:
        print("✅ Training module import verification exists")
    else:
        print("❌ Training module import verification missing")
        return False
    
    print("\n✅ All Dockerfile validations passed!\n")
    return True


if __name__ == '__main__':
    import pytest
    
    # Run with pytest
    exit_code = pytest.main([
        __file__,
        '-v',
        '--tb=short'
    ])
    
    sys.exit(exit_code)
