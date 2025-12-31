"""
Tests for the Phase 1 Enhancement modules from plan.txt

Tests cover:
- Comprehensive error handling system
- Adaptive preprocessing pipeline
- Semantic validation pipeline
"""

import pytest
import numpy as np
from PIL import Image
from decimal import Decimal
from datetime import datetime


# =============================================================================
# SEMANTIC VALIDATION TESTS
# =============================================================================

class TestSemanticValidation:
    """Tests for semantic validation module."""
    
    def test_import_module(self):
        """Test that module imports correctly."""
        from shared.models.semantic_validation import (
            SemanticValidator, 
            validate_receipt, 
            ValidationResult,
            ValidationSeverity,
            ValidationType
        )
        assert SemanticValidator is not None
        assert validate_receipt is not None
    
    def test_validate_complete_receipt(self):
        """Test validation of a complete, valid receipt."""
        from shared.models.semantic_validation import validate_receipt
        
        receipt = {
            'store_name': 'WALMART',
            'total': '25.99',
            'subtotal': '24.00',
            'tax': '1.99',
            'transaction_date': '2024-01-15',
            'items': [
                {'name': 'Item 1', 'price': '12.00'},
                {'name': 'Item 2', 'price': '12.00'}
            ]
        }
        
        result = validate_receipt(receipt)
        
        assert result.is_valid
        assert result.math_validated
        assert result.date_validated
        assert result.store_validated
        assert result.completeness_score == 1.0
    
    def test_math_validation_pass(self):
        """Test that math validation passes when totals match."""
        from shared.models.semantic_validation import SemanticValidator
        
        validator = SemanticValidator()
        receipt = {
            'total': '10.00',
            'subtotal': '9.00',
            'tax': '1.00'
        }
        
        result = validator.validate(receipt)
        assert result.math_validated
    
    def test_math_validation_fail(self):
        """Test that math validation catches errors."""
        from shared.models.semantic_validation import SemanticValidator
        
        validator = SemanticValidator()
        receipt = {
            'total': '15.00',  # Should be 10.00
            'subtotal': '9.00',
            'tax': '1.00'
        }
        
        result = validator.validate(receipt)
        assert not result.math_validated
        assert any('Math validation failed' in str(w) for w in result.warnings)
    
    def test_date_validation_future(self):
        """Test that future dates are caught."""
        from shared.models.semantic_validation import SemanticValidator
        
        validator = SemanticValidator()
        receipt = {
            'total': '10.00',
            'transaction_date': '2099-12-31'
        }
        
        result = validator.validate(receipt)
        assert not result.date_validated
        assert any('future' in str(e).lower() for e in result.errors)
    
    def test_store_validation_known_store(self):
        """Test that known stores are validated."""
        from shared.models.semantic_validation import SemanticValidator
        
        validator = SemanticValidator()
        
        for store in ['WALMART', 'TARGET', 'COSTCO', 'STARBUCKS']:
            result = validator.validate({'store_name': store, 'total': '10.00'})
            assert result.store_validated, f"Store {store} should be validated"
    
    def test_price_normalization(self):
        """Test automatic price format correction."""
        from shared.models.semantic_validation import SemanticValidator
        
        validator = SemanticValidator(auto_correct=True)
        receipt = {
            'total': '$10-99',  # Non-standard format
            'store_name': 'Test Store'
        }
        
        result = validator.validate(receipt)
        
        # Check that correction was applied
        assert len(result.corrections_applied) > 0
        assert any(c['type'] == 'price_format' for c in result.corrections_applied)
    
    def test_completeness_score(self):
        """Test completeness score calculation."""
        from shared.models.semantic_validation import SemanticValidator
        
        validator = SemanticValidator()
        
        # Minimal receipt
        minimal = {'total': '10.00'}
        result = validator.validate(minimal)
        assert result.completeness_score < 0.5
        
        # Complete receipt
        complete = {
            'store_name': 'Test',
            'total': '10.00',
            'subtotal': '9.00',
            'tax': '1.00',
            'transaction_date': '2024-01-15',
            'items': [{'name': 'Item', 'price': '9.00'}]
        }
        result = validator.validate(complete)
        assert result.completeness_score == 1.0


# =============================================================================
# ADAPTIVE PREPROCESSING TESTS
# =============================================================================

class TestAdaptivePreprocessing:
    """Tests for adaptive preprocessing module."""
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample grayscale image for testing."""
        # Create a 500x400 image with some variation
        img_array = np.random.randint(50, 200, (500, 400), dtype=np.uint8)
        return Image.fromarray(img_array)
    
    def test_import_module(self):
        """Test that module imports correctly."""
        from shared.models.adaptive_preprocessing import (
            AdaptivePreprocessor,
            assess_image_quality,
            QualityMetrics,
            PreprocessingStrategy,
            PreprocessingEnsemble
        )
        assert AdaptivePreprocessor is not None
        assert assess_image_quality is not None
    
    def test_quality_assessment(self, sample_image):
        """Test image quality assessment."""
        from shared.models.adaptive_preprocessing import assess_image_quality
        
        metrics = assess_image_quality(sample_image)
        
        # Check all metrics are populated
        assert metrics.blur_score >= 0
        assert metrics.noise_level >= 0
        assert metrics.contrast >= 0
        assert metrics.brightness >= 0
        assert 0 <= metrics.overall_score <= 100
        
        # Check quality level
        assert metrics.get_quality_level() in ['excellent', 'good', 'fair', 'poor']
    
    def test_quality_metrics_to_dict(self, sample_image):
        """Test QualityMetrics serialization."""
        from shared.models.adaptive_preprocessing import assess_image_quality
        
        metrics = assess_image_quality(sample_image)
        d = metrics.to_dict()
        
        assert 'blur_score' in d
        assert 'noise_level' in d
        assert 'contrast' in d
        assert 'overall_score' in d
        assert 'quality_level' in d
    
    def test_strategy_selection(self, sample_image):
        """Test preprocessing strategy selection."""
        from shared.models.adaptive_preprocessing import AdaptivePreprocessor
        
        preprocessor = AdaptivePreprocessor()
        strategies = preprocessor.select_strategy(sample_image)
        
        assert len(strategies) > 0
        assert all(hasattr(s, 'value') for s in strategies)
    
    def test_process_generates_versions(self, sample_image):
        """Test that process generates multiple versions."""
        from shared.models.adaptive_preprocessing import AdaptivePreprocessor
        
        preprocessor = AdaptivePreprocessor()
        versions = preprocessor.process(sample_image)
        
        assert len(versions) >= 1
        
        # Check format of versions
        for name, img in versions:
            assert isinstance(name, str)
            assert isinstance(img, Image.Image)
    
    def test_preprocessing_ensemble(self, sample_image):
        """Test preprocessing ensemble."""
        from shared.models.adaptive_preprocessing import PreprocessingEnsemble
        
        ensemble = PreprocessingEnsemble(num_versions=3)
        versions = ensemble.generate_versions(sample_image)
        
        assert len(versions) <= 3
        assert all(isinstance(name, str) for name, _ in versions)


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

class TestErrorHandling:
    """Tests for comprehensive error handling module."""
    
    def test_import_module(self):
        """Test that module imports correctly."""
        from web.backend.errors import (
            ErrorCode,
            ErrorCategory,
            ErrorResponse,
            create_error_response,
            ErrorRecoveryHandler
        )
        assert ErrorCode is not None
        assert ErrorCategory is not None
    
    def test_error_codes_defined(self):
        """Test that error codes are properly defined."""
        from web.backend.errors import ErrorCode, ERROR_METADATA
        
        # Check we have a good number of error codes
        assert len(ErrorCode) > 20
        
        # Check all error codes have metadata
        for code in ErrorCode:
            assert code in ERROR_METADATA, f"Missing metadata for {code}"
    
    def test_error_response_creation(self):
        """Test ErrorResponse dataclass."""
        from web.backend.errors import ErrorResponse, ErrorCode, ErrorCategory
        
        error = ErrorResponse(
            error_code=ErrorCode.OCR_EXTRACTION_FAILED.value,
            error_type=ErrorCategory.PROCESSING.value,
            message="Test error",
            suggested_action="Try again"
        )
        
        assert error.error_code == "ERR_OCR_100"
        assert error.error_type == "ProcessingError"
        assert error.message == "Test error"
        assert error.request_id is not None
        assert error.timestamp > 0
    
    def test_error_response_to_dict(self):
        """Test error response serialization."""
        from web.backend.errors import ErrorResponse, ErrorCode, ErrorCategory
        
        error = ErrorResponse(
            error_code=ErrorCode.VALIDATION_FILE_TYPE.value,
            error_type=ErrorCategory.VALIDATION.value,
            message="File type not allowed",
            suggested_action="Upload an image file",
            details={'allowed': ['png', 'jpg']}
        )
        
        d = error.to_dict()
        
        assert d['success'] == False
        assert 'error' in d
        assert d['error']['code'] == "ERR_VALIDATION_003"
        assert d['error']['message'] == "File type not allowed"
        assert d['error']['details'] == {'allowed': ['png', 'jpg']}
    
    def test_error_recovery_handler(self):
        """Test error recovery with retry."""
        from web.backend.errors import ErrorRecoveryHandler
        
        handler = ErrorRecoveryHandler(max_retries=3, base_delay=0.01)
        
        # Test successful retry
        call_count = 0
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"
        
        result = handler.with_retry(flaky_function)
        assert result == "success"
        assert call_count == 3
    
    def test_partial_success_response(self):
        """Test partial success response creation."""
        from web.backend.errors import create_partial_success_response, ErrorCode
        
        response = create_partial_success_response(
            data={'total': '25.99'},
            warnings=[ErrorCode.PARSE_NO_STORE_NAME, ErrorCode.PARSE_NO_ITEMS],
            confidence=0.75
        )
        
        assert response['success'] == True
        assert response['partial'] == True
        assert response['confidence'] == 0.75
        assert len(response['warnings']) == 2


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for Phase 1 enhancements."""
    
    def test_preprocessing_and_validation_workflow(self):
        """Test combined preprocessing and validation workflow."""
        from shared.models.adaptive_preprocessing import AdaptivePreprocessor, assess_image_quality
        from shared.models.semantic_validation import validate_receipt
        
        # Create test image
        img_array = np.random.randint(100, 200, (400, 300), dtype=np.uint8)
        image = Image.fromarray(img_array)
        
        # Assess quality
        quality = assess_image_quality(image)
        assert quality.overall_score > 0
        
        # Simulate OCR result
        receipt_data = {
            'store_name': 'TEST STORE',
            'total': '15.99',
            'subtotal': '14.50',
            'tax': '1.49',
            'items': [{'name': 'Test Item', 'price': '14.50'}]
        }
        
        # Validate result
        validation = validate_receipt(receipt_data)
        assert validation.math_validated
    
    def test_error_handling_with_validation(self):
        """Test error handling integration with validation."""
        from web.backend.errors import ErrorCode, create_partial_success_response
        from shared.models.semantic_validation import validate_receipt
        
        # Incomplete receipt
        receipt_data = {
            'total': '10.00'
            # Missing store, items, subtotal, tax
        }
        
        validation = validate_receipt(receipt_data)
        
        if not validation.is_valid or validation.completeness_score < 0.5:
            # Create partial success response with warnings
            warning_codes = []
            if not validation.store_validated:
                warning_codes.append(ErrorCode.PARSE_NO_STORE_NAME)
            if validation.completeness_score < 0.5:
                warning_codes.append(ErrorCode.PARSE_NO_ITEMS)
            
            response = create_partial_success_response(
                data=receipt_data,
                warnings=warning_codes,
                confidence=validation.completeness_score
            )
            
            assert response['partial'] == True
            assert response['confidence'] < 1.0
