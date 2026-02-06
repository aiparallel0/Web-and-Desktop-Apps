"""
Test suite for Celery Beat configuration fixes.

Tests:
- Celery worker configuration (beat_schedule_filename vs beat_schedule)
- configure_beat_schedule() function behavior
- Procfile beat command compatibility
- Railway deployment configuration
"""

import sys
import os
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


class TestCeleryBeatConfiguration:
    """Test Celery Beat configuration fixes."""
    
    def test_celery_worker_imports(self):
        """Test that celery_worker module can be imported."""
        try:
            from web.backend.training import celery_worker
            assert celery_worker is not None
        except ImportError as e:
            # Expected if celery is not installed
            pytest.skip(f"Celery not available: {e}")
    
    def test_beat_schedule_filename_configured(self):
        """Test that beat_schedule_filename is configured instead of beat_schedule."""
        try:
            from web.backend.training import celery_worker
            
            if not celery_worker.CELERY_AVAILABLE:
                pytest.skip("Celery not available")
            
            # Check that celery_app has the correct configuration
            celery_app = celery_worker.celery_app
            assert celery_app is not None
            
            # beat_schedule_filename should be set
            config = celery_app.conf
            assert hasattr(config, 'beat_schedule_filename') or 'beat_schedule_filename' in config
            
            # beat_schedule should NOT be a string (should be None or dict)
            beat_schedule = getattr(config, 'beat_schedule', None)
            if beat_schedule is not None:
                assert not isinstance(beat_schedule, str), \
                    "beat_schedule should NOT be a string file path"
        
        except ImportError:
            pytest.skip("Celery not available")
    
    def test_configure_beat_schedule_function_exists(self):
        """Test that configure_beat_schedule function exists."""
        try:
            from web.backend.training.celery_worker import configure_beat_schedule
            assert callable(configure_beat_schedule)
        except ImportError as e:
            pytest.skip(f"Celery or configure_beat_schedule not available: {e}")
    
    def test_configure_beat_schedule_sets_dict(self):
        """Test that configure_beat_schedule sets beat_schedule as a dict."""
        try:
            from web.backend.training import celery_worker
            from web.backend.training.celery_worker import configure_beat_schedule
            
            if not celery_worker.CELERY_AVAILABLE:
                pytest.skip("Celery not available")
            
            celery_app = celery_worker.celery_app
            
            # Clear any existing beat_schedule
            if hasattr(celery_app.conf, 'beat_schedule'):
                delattr(celery_app.conf, 'beat_schedule')
            
            # Call configure_beat_schedule
            configure_beat_schedule()
            
            # Verify beat_schedule is now a dict
            beat_schedule = celery_app.conf.beat_schedule
            assert isinstance(beat_schedule, dict), \
                "beat_schedule should be a dict after calling configure_beat_schedule()"
            
            # Verify it contains the expected task
            assert 'cleanup-old-jobs-daily' in beat_schedule
            task_config = beat_schedule['cleanup-old-jobs-daily']
            assert task_config['task'] == 'training.cleanup_old_jobs'
            assert task_config['schedule'] == 86400.0  # Daily
            assert task_config['args'] == (7,)  # 7 days retention
        
        except ImportError:
            pytest.skip("Celery not available")
    
    def test_configure_beat_schedule_handles_missing_celery(self):
        """Test that configure_beat_schedule handles missing celery gracefully."""
        try:
            from web.backend.training import celery_worker
            
            # Temporarily set celery_app to None
            original_app = celery_worker.celery_app
            celery_worker.celery_app = None
            
            # Import the function
            from web.backend.training.celery_worker import configure_beat_schedule
            
            # Should not raise an error
            configure_beat_schedule()
            
            # Restore original
            celery_worker.celery_app = original_app
        
        except ImportError:
            pytest.skip("Celery not available")
    
    def test_celery_config_has_correct_beat_settings(self):
        """Test that Celery configuration has correct beat-related settings."""
        try:
            from web.backend.training import celery_worker
            
            if not celery_worker.CELERY_AVAILABLE:
                pytest.skip("Celery not available")
            
            celery_app = celery_worker.celery_app
            config = celery_app.conf
            
            # Check beat_schedule_filename is configured
            beat_schedule_filename = config.get('beat_schedule_filename')
            if beat_schedule_filename:
                # Should be a string path
                assert isinstance(beat_schedule_filename, str)
                # Should end with .db
                assert beat_schedule_filename.endswith('.db')
            
            # Check that beat_schedule is NOT set to a string on module import
            beat_schedule = config.get('beat_schedule')
            if beat_schedule is not None:
                assert not isinstance(beat_schedule, str), \
                    "beat_schedule should never be a string (file path)"
        
        except ImportError:
            pytest.skip("Celery not available")


class TestRailwayConfiguration:
    """Test Railway deployment configuration."""
    
    def test_railway_json_exists(self):
        """Test that railway.json exists."""
        railway_json = project_root / 'railway.json'
        assert railway_json.exists(), "railway.json should exist"
    
    def test_railway_json_no_start_command(self):
        """Test that railway.json does NOT have startCommand (uses Dockerfile CMD instead)."""
        import json
        railway_json = project_root / 'railway.json'
        
        with open(railway_json, 'r') as f:
            config = json.load(f)
        
        # startCommand should NOT be present - Railway should use Dockerfile CMD
        # This allows proper PORT variable expansion via shell
        assert 'deploy' in config
        assert 'startCommand' not in config['deploy'], \
            "startCommand should be removed to allow Dockerfile CMD with shell expansion"
    
    def test_railway_json_valid_format(self):
        """Test that railway.json is valid JSON with required fields."""
        import json
        railway_json = project_root / 'railway.json'
        
        with open(railway_json, 'r') as f:
            config = json.load(f)
        
        # Check required fields
        assert 'build' in config
        assert 'deploy' in config
        
        # Check build configuration
        assert config['build']['builder'] == 'DOCKERFILE'
        assert 'dockerfilePath' in config['build']
        
        # Check deploy configuration
        deploy = config['deploy']
        assert 'healthcheckPath' in deploy
        assert deploy['healthcheckPath'] == '/api/health'
    
    def test_procfile_beat_command_correct(self):
        """Test that Procfile beat command calls configure_beat_schedule."""
        procfile_path = project_root / 'Procfile'
        
        with open(procfile_path, 'r') as f:
            content = f.read()
        
        # Check that beat line exists
        assert 'beat:' in content
        
        # Check that configure_beat_schedule is called
        beat_line = [line for line in content.split('\n') if line.startswith('beat:')][0]
        assert 'configure_beat_schedule' in beat_line
        assert 'celery -A web.backend.training.celery_worker beat' in beat_line
    
    def test_dockerfile_has_celerybeat_directory(self):
        """Test that Dockerfile creates celerybeat directory."""
        dockerfile_path = project_root / 'Dockerfile'
        
        with open(dockerfile_path, 'r') as f:
            content = f.read()
        
        # Check that celerybeat directory is created
        assert 'celerybeat' in content
        assert 'mkdir -p' in content or 'mkdir' in content


class TestCeleryBeatErrorConditions:
    """Test error conditions related to Celery Beat configuration."""
    
    def test_beat_schedule_not_string_on_import(self):
        """
        CRITICAL: Test that beat_schedule is NOT set to a string on module import.
        
        This was the root cause of the Railway deployment failure:
        TypeError: string indices must be integers, not 'str'
        """
        try:
            # Fresh import of celery_worker
            import importlib
            import sys
            
            # Remove from cache if present
            if 'web.backend.training.celery_worker' in sys.modules:
                del sys.modules['web.backend.training.celery_worker']
            
            from web.backend.training import celery_worker
            
            if not celery_worker.CELERY_AVAILABLE:
                pytest.skip("Celery not available")
            
            celery_app = celery_worker.celery_app
            config = celery_app.conf
            
            # Get beat_schedule from config
            beat_schedule = getattr(config, 'beat_schedule', None)
            
            # CRITICAL CHECK: beat_schedule should NEVER be a string
            if beat_schedule is not None:
                assert not isinstance(beat_schedule, str), \
                    f"CRITICAL ERROR: beat_schedule is a string '{beat_schedule}'. " \
                    f"This causes 'TypeError: string indices must be integers' in Celery Beat. " \
                    f"Use 'beat_schedule_filename' for file paths."
        
        except ImportError:
            pytest.skip("Celery not available")
    
    def test_beat_schedule_filename_is_string(self):
        """Test that beat_schedule_filename (if set) is a string."""
        try:
            from web.backend.training import celery_worker
            
            if not celery_worker.CELERY_AVAILABLE:
                pytest.skip("Celery not available")
            
            celery_app = celery_worker.celery_app
            config = celery_app.conf
            
            # Get beat_schedule_filename
            beat_schedule_filename = getattr(config, 'beat_schedule_filename', None)
            
            # If set, should be a string
            if beat_schedule_filename is not None:
                assert isinstance(beat_schedule_filename, str), \
                    "beat_schedule_filename should be a string file path"
        
        except ImportError:
            pytest.skip("Celery not available")


class TestDeploymentReadiness:
    """Test overall deployment readiness."""
    
    def test_deployment_files_exist(self):
        """Test that all required deployment files exist."""
        required_files = [
            'Dockerfile',
            'Procfile',
            'railway.json',
            '.dockerignore',
            'requirements-prod.txt',
            'RAILWAY_DEPLOY.md'
        ]
        
        for filename in required_files:
            filepath = project_root / filename
            assert filepath.exists(), f"{filename} should exist for deployment"
    
    def test_railway_deploy_md_exists(self):
        """Test that RAILWAY_DEPLOY.md documentation exists."""
        deploy_md = project_root / 'RAILWAY_DEPLOY.md'
        assert deploy_md.exists(), "RAILWAY_DEPLOY.md should exist"
        
        # Check that it contains key information
        with open(deploy_md, 'r') as f:
            content = f.read()
        
        assert 'Railway Deployment Guide' in content
        assert 'Celery Beat Configuration Fix' in content
        assert 'beat_schedule_filename' in content
        assert 'configure_beat_schedule' in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
