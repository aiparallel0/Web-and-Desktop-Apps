"""
Tests for OCRConfig module with circular exchange integration.
"""
import pytest
from decimal import Decimal
from unittest.mock import Mock, patch

from shared.models.ocr_config import OCRConfig, OCRPipelineStage, get_ocr_config


class TestOCRConfig:
    """Test OCRConfig class."""
    
    def setup_method(self):
        """Reset singleton for each test."""
        OCRConfig._instance = None
    
    def test_singleton_pattern(self):
        """Test that OCRConfig is a singleton."""
        config1 = OCRConfig()
        config2 = OCRConfig()
        assert config1 is config2
    
    def test_default_parameters(self):
        """Test default parameter values."""
        config = OCRConfig()
        
        assert config.min_confidence == 0.3
        assert config.relaxed_confidence == 0.2
        assert config.relaxed_mode == False
        assert config.auto_fallback == True
        assert config.min_name_length == 2
        assert config.max_price == 1000.0
        assert config.max_digit_ratio == 2.0
        assert config.auto_tune == True
    
    def test_set_min_confidence(self):
        """Test setting min_confidence."""
        config = OCRConfig()
        
        assert config.set_min_confidence(0.5) == True
        assert config.min_confidence == 0.5
        
        # Invalid value should be rejected
        assert config.set_min_confidence(1.5) == False
        assert config.min_confidence == 0.5  # Still previous value
    
    def test_set_relaxed_mode(self):
        """Test setting relaxed_mode."""
        config = OCRConfig()
        
        assert config.set_relaxed_mode(True) == True
        assert config.relaxed_mode == True
    
    def test_get_package(self):
        """Test getting parameter packages."""
        config = OCRConfig()
        
        pkg = config.get_package('ocr.min_confidence')
        assert pkg is not None
        # Value may have been modified by previous tests due to singleton
        assert isinstance(pkg.get(), float)
        
        # Non-existent package
        assert config.get_package('non.existent') is None


class TestOCRConfigPipeline:
    """Test OCRConfig pipeline functionality."""
    
    def setup_method(self):
        """Reset singleton for each test."""
        OCRConfig._instance = None
    
    def test_pipeline_stages_initialized(self):
        """Test that pipeline stages are initialized."""
        config = OCRConfig()
        
        stages = config.get_enabled_stages()
        assert 'preprocessing' in stages
        assert 'text_detection' in stages
        assert 'line_extraction' in stages
        assert 'item_parsing' in stages
        assert 'validation' in stages
    
    def test_disable_enable_stage(self):
        """Test disabling and enabling pipeline stages."""
        config = OCRConfig()
        
        assert config.disable_stage('preprocessing') == True
        assert 'preprocessing' not in config.get_enabled_stages()
        
        assert config.enable_stage('preprocessing') == True
        assert 'preprocessing' in config.get_enabled_stages()
    
    def test_set_stage_parameter(self):
        """Test setting stage parameters."""
        config = OCRConfig()
        
        assert config.set_stage_parameter('preprocessing', 'deskew', False) == True
        stage = config.get_pipeline_stage('preprocessing')
        assert stage.parameters['deskew'] == False


class TestOCRConfigAutoTuning:
    """Test OCRConfig auto-tuning functionality."""
    
    def setup_method(self):
        """Reset singleton for each test."""
        OCRConfig._instance = None
    
    def test_record_extraction_result(self):
        """Test recording extraction results."""
        config = OCRConfig()
        
        config.record_extraction_result(
            items_count=5,
            total_detected=Decimal('25.99'),
            confidence_avg=0.85,
            success=True,
            used_relaxed=False
        )
        
        stats = config.get_extraction_stats()
        assert stats['total'] == 1
        assert stats['successful'] == 1
        assert stats['success_rate'] == 1.0
    
    def test_auto_tune_on_low_success_rate(self):
        """Test that auto-tuning relaxes constraints on low success rate."""
        config = OCRConfig()
        config.set_min_confidence(0.4)
        
        # Record many failed extractions
        for _ in range(15):
            config.record_extraction_result(
                items_count=0,
                total_detected=None,
                confidence_avg=0.3,
                success=False,
                used_relaxed=False
            )
        
        # Min confidence should be lowered
        assert config.min_confidence < 0.4


class TestOCRConfigExportImport:
    """Test OCRConfig export/import functionality."""
    
    def setup_method(self):
        """Reset singleton for each test."""
        OCRConfig._instance = None
    
    def test_export_config(self):
        """Test exporting configuration."""
        config = OCRConfig()
        config.set_min_confidence(0.35)
        
        exported = config.export_config()
        
        assert 'parameters' in exported
        assert 'pipeline' in exported
        assert 'stats' in exported
        assert exported['parameters']['min_confidence'] == 0.35
    
    def test_import_config(self):
        """Test importing configuration."""
        config = OCRConfig()
        
        new_config = {
            'parameters': {
                'min_confidence': 0.25,
                'relaxed_mode': True
            },
            'pipeline': {
                'preprocessing': {
                    'enabled': False
                }
            }
        }
        
        assert config.import_config(new_config) == True
        assert config.min_confidence == 0.25
        assert config.relaxed_mode == True
    
    def test_reset_to_defaults(self):
        """Test resetting to default values."""
        config = OCRConfig()
        config.set_min_confidence(0.1)
        config.set_relaxed_mode(True)
        
        config.reset_to_defaults()
        
        assert config.min_confidence == 0.3
        assert config.relaxed_mode == False


class TestOCRPipelineStage:
    """Test OCRPipelineStage dataclass."""
    
    def test_record_result(self):
        """Test recording stage results."""
        stage = OCRPipelineStage(name='test')
        
        stage.record_result(True)
        stage.record_result(True)
        stage.record_result(False)
        
        assert stage.total_runs == 3
        assert stage.successful_runs == 2
        assert abs(stage.success_rate - 0.667) < 0.01


class TestGetOcrConfig:
    """Test get_ocr_config function."""
    
    def setup_method(self):
        """Reset singleton for each test."""
        OCRConfig._instance = None
    
    def test_get_ocr_config(self):
        """Test that get_ocr_config returns singleton."""
        config1 = get_ocr_config()
        config2 = get_ocr_config()
        
        assert config1 is config2
        assert isinstance(config1, OCRConfig)
