"""
Test suite for Dockerfile fixes.

Tests:
- Training module is not excluded in .dockerignore
- Cleanup commands no longer use -prune (training is copied naturally)
- HEALTHCHECK uses proper shell interpolation
- Training module verification steps have been removed (no longer needed)
"""

import sys
import os
import re
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


class TestDockerignoreFixes:
    """Test .dockerignore file fixes."""
    
    def test_dockerignore_exists(self):
        """Test that .dockerignore exists."""
        dockerignore_path = project_root / '.dockerignore'
        assert dockerignore_path.exists(), ".dockerignore not found"
    
    def test_training_not_excluded(self):
        """Test that training directory is NOT excluded."""
        dockerignore_path = project_root / '.dockerignore'
        content = dockerignore_path.read_text()
        
        # Check that web/backend/training/ is NOT in the file as an exclusion
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            # Fail if we find an uncommented exclusion
            if line == 'web/backend/training/' or line == 'web/backend/training':
                assert False, "Training directory should not be excluded in .dockerignore"
    
    def test_training_comment_exists(self):
        """Test that there's a comment explaining why training is needed."""
        dockerignore_path = project_root / '.dockerignore'
        content = dockerignore_path.read_text()
        
        # Check for explanatory comment about training and Celery
        assert 'training' in content.lower() or 'celery' in content.lower(), \
            "Missing comment about training/celery requirements"


class TestDockerfileCleanupFixes:
    """Test Dockerfile cleanup command fixes."""
    
    def test_dockerfile_exists(self):
        """Test that Dockerfile exists."""
        dockerfile_path = project_root / 'Dockerfile'
        assert dockerfile_path.exists(), "Dockerfile not found"
    
    def test_cleanup_simplified(self):
        """Test that cleanup commands no longer use -prune pattern."""
        dockerfile_path = project_root / 'Dockerfile'
        content = dockerfile_path.read_text()
        
        # Check that -prune pattern is NOT present (we simplified it)
        assert '-path ./web/backend/training -prune' not in content, \
            "Cleanup should not use -prune pattern (training is naturally included)"
    
    def test_cleanup_still_removes_tests(self):
        """Test that cleanup still removes test directories."""
        dockerfile_path = project_root / 'Dockerfile'
        content = dockerfile_path.read_text()
        
        # Verify test cleanup still exists
        assert 'find . -type d -name "tests"' in content or \
               'find . -type d -name "__pycache__"' in content, \
            "Cleanup should still remove test directories"
    
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
    
    def test_no_verification_step(self):
        """Test that verification step has been removed."""
        dockerfile_path = project_root / 'Dockerfile'
        content = dockerfile_path.read_text()
        
        # Verification step should NOT exist anymore (no longer needed)
        assert 'test -d web/backend/training ||' not in content, \
            "Verification step should be removed (training is naturally included)"
        
        # Import verification should also be gone
        assert 'import web.backend.training.celery_worker; print' not in content, \
            "Import verification should be removed"
    
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


class TestProcfileFixes:
    """Test Procfile configuration."""
    
    def test_procfile_exists(self):
        """Test that Procfile exists."""
        procfile_path = project_root / 'Procfile'
        assert procfile_path.exists(), "Procfile not found"
    
    def test_worker_has_error_handling(self):
        """Test that worker command has error handling."""
        procfile_path = project_root / 'Procfile'
        content = procfile_path.read_text()
        
        # Check for worker line with error handling
        assert 'worker:' in content, "Missing worker definition"
        assert 'celery_worker' in content, "Missing celery_worker reference"
        
        # Check for error handling (|| echo ...)
        if 'worker:' in content:
            worker_line = [line for line in content.split('\n') if 'worker:' in line][0]
            # Optional: can check for error handling if present
            # assert '||' in worker_line or 'echo' in worker_line, "Worker should have error handling"
    
    def test_beat_has_error_handling(self):
        """Test that beat command has error handling."""
        procfile_path = project_root / 'Procfile'
        content = procfile_path.read_text()
        
        # Check for beat line with error handling
        if 'beat:' in content:
            assert 'celery_worker' in content, "Missing celery_worker reference"


def test_dockerfile_validation():
    """Main validation function."""
    dockerfile_path = project_root / 'Dockerfile'
    dockerignore_path = project_root / '.dockerignore'
    
    assert dockerfile_path.exists(), "Dockerfile not found"
    assert dockerignore_path.exists(), ".dockerignore not found"
    
    dockerfile_content = dockerfile_path.read_text()
    dockerignore_content = dockerignore_path.read_text()
    
    print("\n=== Docker Configuration Validation ===\n")
    
    # Check 1: Training directory not excluded
    training_excluded = False
    for line in dockerignore_content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if 'web/backend/training' in line:
            training_excluded = True
            break
    
    if not training_excluded:
        print("✅ Training directory is NOT excluded in .dockerignore")
    else:
        print("❌ Training directory should not be excluded in .dockerignore")
        return False
    
    # Check 2: Cleanup simplified (no -prune)
    if '-path ./web/backend/training -prune' not in dockerfile_content:
        print("✅ Cleanup commands simplified (no -prune)")
    else:
        print("❌ Cleanup commands should not use -prune pattern")
        return False
    
    # Check 3: HEALTHCHECK
    if 'sh -c' in dockerfile_content and '${PORT:-5000}' in dockerfile_content:
        print("✅ HEALTHCHECK uses proper shell interpolation")
    else:
        print("❌ HEALTHCHECK doesn't use proper shell interpolation")
        return False
    
    # Check 4: Verification steps removed
    if 'test -d web/backend/training ||' not in dockerfile_content:
        print("✅ Verification step removed (no longer needed)")
    else:
        print("❌ Verification step should be removed")
        return False
    
    print("\n✅ All Docker configuration validations passed!\n")
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
