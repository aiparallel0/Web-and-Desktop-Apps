"""
Tests for Feature Flags Functionality

This module tests the feature flag system for CEFR, cloud storage, and cloud training.
"""

import os
import pytest
from unittest.mock import patch


class TestCEFRFeatureFlag:
    """Tests for CEFR feature flag (ENABLE_CEFR)."""
    
    def test_cefr_disabled_by_default(self):
        """Test that CEFR is disabled when ENABLE_CEFR is not set."""
        with patch.dict(os.environ, {}, clear=False):
            # Remove ENABLE_CEFR if present
            os.environ.pop('ENABLE_CEFR', None)
            
            from shared.circular_exchange.core.project_config import _is_cefr_enabled
            assert _is_cefr_enabled() is False
    
    def test_cefr_disabled_explicitly(self):
        """Test that CEFR is disabled when ENABLE_CEFR=false."""
        with patch.dict(os.environ, {'ENABLE_CEFR': 'false'}):
            from shared.circular_exchange.core.project_config import _is_cefr_enabled
            assert _is_cefr_enabled() is False
    
    def test_cefr_enabled(self):
        """Test that CEFR is enabled when ENABLE_CEFR=true."""
        with patch.dict(os.environ, {'ENABLE_CEFR': 'true'}):
            from shared.circular_exchange.core.project_config import _is_cefr_enabled
            assert _is_cefr_enabled() is True
    
    def test_cefr_enabled_case_insensitive(self):
        """Test that ENABLE_CEFR is case-insensitive."""
        test_values = ['True', 'TRUE', 'TrUe', '1', 'yes', 'YES']
        for value in test_values:
            with patch.dict(os.environ, {'ENABLE_CEFR': value}):
                from shared.circular_exchange.core.project_config import _is_cefr_enabled
                assert _is_cefr_enabled() is True, f"Failed for value: {value}"
    
    def test_cefr_project_config_disabled(self):
        """Test that ProjectConfiguration skips initialization when CEFR is disabled."""
        with patch.dict(os.environ, {'ENABLE_CEFR': 'false'}):
            # Force reload to test initialization
            import importlib
            import shared.circular_exchange.core.project_config as pc_module
            importlib.reload(pc_module)
            
            config = pc_module.ProjectConfiguration()
            assert hasattr(config, 'cefr_enabled')
            assert config.cefr_enabled is False
            assert config.module_registry is None


class TestStorageFeatureFlags:
    """Tests for cloud storage feature flags."""
    
    def test_s3_storage_disabled_by_default(self):
        """Test that S3 storage is disabled by default."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('ENABLE_S3_STORAGE', None)
            
            from web.backend.storage import StorageFactory
            
            with pytest.raises(ValueError, match="S3 storage is disabled"):
                StorageFactory.get_handler('s3')
    
    def test_s3_storage_disabled_explicitly(self):
        """Test that S3 storage raises error when disabled."""
        with patch.dict(os.environ, {'ENABLE_S3_STORAGE': 'false'}):
            from web.backend.storage import StorageFactory
            
            with pytest.raises(ValueError, match="S3 storage is disabled"):
                StorageFactory.get_handler('s3')
    
    def test_gdrive_storage_disabled(self):
        """Test that Google Drive storage is disabled by default."""
        with patch.dict(os.environ, {'ENABLE_GDRIVE_STORAGE': 'false'}):
            from web.backend.storage import StorageFactory
            
            with pytest.raises(ValueError, match="GDRIVE storage is disabled"):
                StorageFactory.get_handler('gdrive')
    
    def test_dropbox_storage_disabled(self):
        """Test that Dropbox storage is disabled by default."""
        with patch.dict(os.environ, {'ENABLE_DROPBOX_STORAGE': 'false'}):
            from web.backend.storage import StorageFactory
            
            with pytest.raises(ValueError, match="DROPBOX storage is disabled"):
                StorageFactory.get_handler('dropbox')
    
    def test_storage_provider_available_returns_false_when_disabled(self):
        """Test that is_provider_available returns False for disabled providers."""
        with patch.dict(os.environ, {'ENABLE_S3_STORAGE': 'false'}):
            from web.backend.storage import StorageFactory
            
            assert StorageFactory.is_provider_available('s3') is False
    
    def test_storage_error_message_includes_flag_name(self):
        """Test that error message includes the correct flag name."""
        with patch.dict(os.environ, {'ENABLE_S3_STORAGE': 'false'}):
            from web.backend.storage import StorageFactory
            
            try:
                StorageFactory.get_handler('s3')
                pytest.fail("Should have raised ValueError")
            except ValueError as e:
                assert 'ENABLE_S3_STORAGE=true' in str(e)
    
    def test_storage_aliases_use_same_flag(self):
        """Test that storage aliases (s3/aws, gdrive/google_drive) use the same flag."""
        with patch.dict(os.environ, {'ENABLE_S3_STORAGE': 'false'}):
            from web.backend.storage import StorageFactory
            
            # Both 's3' and 'aws' should fail with same flag
            with pytest.raises(ValueError, match="ENABLE_S3_STORAGE"):
                StorageFactory.get_handler('s3')
            
            with pytest.raises(ValueError, match="ENABLE_S3_STORAGE"):
                StorageFactory.get_handler('aws')


class TestTrainingFeatureFlags:
    """Tests for cloud training feature flags."""
    
    def test_hf_training_disabled_by_default(self):
        """Test that HuggingFace training is disabled by default."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('ENABLE_HF_TRAINING', None)
            
            from web.backend.training import TrainingFactory
            
            with pytest.raises(ValueError, match="HUGGINGFACE training is disabled"):
                TrainingFactory.get_trainer('huggingface')
    
    def test_hf_training_disabled_explicitly(self):
        """Test that HuggingFace training raises error when disabled."""
        with patch.dict(os.environ, {'ENABLE_HF_TRAINING': 'false'}):
            from web.backend.training import TrainingFactory
            
            with pytest.raises(ValueError, match="HUGGINGFACE training is disabled"):
                TrainingFactory.get_trainer('huggingface')
    
    def test_replicate_training_disabled(self):
        """Test that Replicate training is disabled by default."""
        with patch.dict(os.environ, {'ENABLE_REPLICATE_TRAINING': 'false'}):
            from web.backend.training import TrainingFactory
            
            with pytest.raises(ValueError, match="REPLICATE training is disabled"):
                TrainingFactory.get_trainer('replicate')
    
    def test_runpod_training_disabled(self):
        """Test that RunPod training is disabled by default."""
        with patch.dict(os.environ, {'ENABLE_RUNPOD_TRAINING': 'false'}):
            from web.backend.training import TrainingFactory
            
            with pytest.raises(ValueError, match="RUNPOD training is disabled"):
                TrainingFactory.get_trainer('runpod')
    
    def test_training_provider_available_returns_false_when_disabled(self):
        """Test that is_provider_available returns False for disabled providers."""
        with patch.dict(os.environ, {'ENABLE_HF_TRAINING': 'false'}):
            from web.backend.training import TrainingFactory
            
            assert TrainingFactory.is_provider_available('huggingface') is False
    
    def test_training_error_message_includes_flag_name(self):
        """Test that error message includes the correct flag name."""
        with patch.dict(os.environ, {'ENABLE_HF_TRAINING': 'false'}):
            from web.backend.training import TrainingFactory
            
            try:
                TrainingFactory.get_trainer('huggingface')
                pytest.fail("Should have raised ValueError")
            except ValueError as e:
                assert 'ENABLE_HF_TRAINING=true' in str(e)
    
    def test_training_aliases_use_same_flag(self):
        """Test that training aliases (huggingface/hf) use the same flag."""
        with patch.dict(os.environ, {'ENABLE_HF_TRAINING': 'false'}):
            from web.backend.training import TrainingFactory
            
            # Both 'huggingface' and 'hf' should fail with same flag
            with pytest.raises(ValueError, match="ENABLE_HF_TRAINING"):
                TrainingFactory.get_trainer('huggingface')
            
            with pytest.raises(ValueError, match="ENABLE_HF_TRAINING"):
                TrainingFactory.get_trainer('hf')


class TestFeatureFlagIntegration:
    """Integration tests for feature flags across modules."""
    
    def test_mvp_mode_all_disabled(self):
        """Test MVP mode with all feature flags disabled."""
        mvp_env = {
            'ENABLE_CEFR': 'false',
            'ENABLE_S3_STORAGE': 'false',
            'ENABLE_GDRIVE_STORAGE': 'false',
            'ENABLE_DROPBOX_STORAGE': 'false',
            'ENABLE_HF_TRAINING': 'false',
            'ENABLE_REPLICATE_TRAINING': 'false',
            'ENABLE_RUNPOD_TRAINING': 'false',
        }
        
        with patch.dict(os.environ, mvp_env):
            from shared.circular_exchange.core.project_config import _is_cefr_enabled
            from web.backend.storage import StorageFactory
            from web.backend.training import TrainingFactory
            
            # CEFR should be disabled
            assert _is_cefr_enabled() is False
            
            # All storage providers should be disabled
            assert StorageFactory.is_provider_available('s3') is False
            assert StorageFactory.is_provider_available('gdrive') is False
            assert StorageFactory.is_provider_available('dropbox') is False
            
            # All training providers should be disabled
            assert TrainingFactory.is_provider_available('huggingface') is False
            assert TrainingFactory.is_provider_available('replicate') is False
            assert TrainingFactory.is_provider_available('runpod') is False
    
    def test_full_mode_all_enabled(self):
        """Test full mode with all feature flags enabled."""
        full_env = {
            'ENABLE_CEFR': 'true',
            'ENABLE_S3_STORAGE': 'true',
            'ENABLE_GDRIVE_STORAGE': 'true',
            'ENABLE_DROPBOX_STORAGE': 'true',
            'ENABLE_HF_TRAINING': 'true',
            'ENABLE_REPLICATE_TRAINING': 'true',
            'ENABLE_RUNPOD_TRAINING': 'true',
        }
        
        with patch.dict(os.environ, full_env):
            from shared.circular_exchange.core.project_config import _is_cefr_enabled
            
            # CEFR should be enabled
            assert _is_cefr_enabled() is True
            
            # Note: Storage and training providers will still fail without credentials,
            # but they should not fail due to feature flags
            # We just test that the flag check passes
    
    def test_hybrid_mode_selective_features(self):
        """Test hybrid mode with some features enabled, others disabled."""
        hybrid_env = {
            'ENABLE_CEFR': 'true',
            'ENABLE_S3_STORAGE': 'true',
            'ENABLE_GDRIVE_STORAGE': 'false',
            'ENABLE_DROPBOX_STORAGE': 'false',
            'ENABLE_HF_TRAINING': 'true',
            'ENABLE_REPLICATE_TRAINING': 'false',
            'ENABLE_RUNPOD_TRAINING': 'false',
        }
        
        with patch.dict(os.environ, hybrid_env):
            from shared.circular_exchange.core.project_config import _is_cefr_enabled
            from web.backend.storage import StorageFactory
            from web.backend.training import TrainingFactory
            
            # CEFR should be enabled
            assert _is_cefr_enabled() is True
            
            # S3 enabled (but may fail on credentials)
            # GDrive and Dropbox should be disabled
            assert StorageFactory.is_provider_available('gdrive') is False
            assert StorageFactory.is_provider_available('dropbox') is False
            
            # HF enabled (but may fail on credentials)
            # Replicate and RunPod should be disabled
            assert TrainingFactory.is_provider_available('replicate') is False
            assert TrainingFactory.is_provider_available('runpod') is False


class TestBackwardCompatibility:
    """Tests for backward compatibility with existing deployments."""
    
    def test_missing_flags_default_to_disabled(self):
        """Test that missing feature flags default to disabled (MVP mode)."""
        # Clear all feature flag environment variables
        clear_env = {}
        for key in list(os.environ.keys()):
            if key.startswith('ENABLE_'):
                clear_env[key] = None
        
        with patch.dict(os.environ, clear_env, clear=False):
            # Remove flags
            for key in ['ENABLE_CEFR', 'ENABLE_S3_STORAGE', 'ENABLE_GDRIVE_STORAGE',
                       'ENABLE_DROPBOX_STORAGE', 'ENABLE_HF_TRAINING',
                       'ENABLE_REPLICATE_TRAINING', 'ENABLE_RUNPOD_TRAINING']:
                os.environ.pop(key, None)
            
            from shared.circular_exchange.core.project_config import _is_cefr_enabled
            from web.backend.storage import StorageFactory
            from web.backend.training import TrainingFactory
            
            # All should default to disabled
            assert _is_cefr_enabled() is False
            assert StorageFactory.is_provider_available('s3') is False
            assert TrainingFactory.is_provider_available('huggingface') is False
