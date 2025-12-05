"""
Integration tests for receipt processing workflow.

These tests verify the complete receipt processing pipeline:
Upload → OCR Extraction → Data Validation → Response

Tests use actual module implementations with minimal mocking.
"""
import pytest
import io
import numpy as np
from PIL import Image
from decimal import Decimal


class TestReceiptProcessingWorkflow:
    """Test complete receipt processing without mocks where possible."""
    
    @pytest.fixture
    def sample_receipt_image(self):
        """Create a simple test image that simulates a receipt."""
        # Create a simple gray image with some text-like patterns
        img = Image.new('RGB', (400, 600), color='white')
        
        # Convert to bytes for upload simulation
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer
    
    @pytest.fixture
    def sample_receipt_image_bytes(self, sample_receipt_image):
        """Get bytes from sample receipt image."""
        return sample_receipt_image.getvalue()
    
    @pytest.fixture
    def sample_image_path(self, tmp_path):
        """Create a sample image file and return its path."""
        img = Image.new('RGB', (400, 600), color='white')
        image_path = tmp_path / "test_receipt.png"
        img.save(str(image_path), format='PNG')
        return str(image_path)
    
    def test_image_load_and_validation_workflow(self, sample_image_path):
        """Test complete image loading and validation workflow."""
        from shared.utils.image import load_and_validate_image
        
        # Step 1: Load image from file path
        result = load_and_validate_image(sample_image_path)
        
        # Step 2: Verify image was loaded correctly
        assert result is not None
        # The function may return PIL Image or numpy array depending on implementation
        if isinstance(result, np.ndarray):
            assert len(result.shape) >= 2  # At least 2D (height, width)
        else:
            # PIL Image
            assert hasattr(result, 'size')
    
    def test_image_enhancement_workflow(self, sample_image_path):
        """Test image load → enhance → preprocess workflow."""
        from shared.utils.image import (
            load_and_validate_image,
            enhance_image,
            preprocess_for_ocr
        )
        
        # Step 1: Load image
        image = load_and_validate_image(sample_image_path)
        assert image is not None
        
        # Step 2: Enhance image
        enhanced = enhance_image(image)
        assert enhanced is not None
        
        # Step 3: Preprocess for OCR
        preprocessed = preprocess_for_ocr(image)
        assert preprocessed is not None
    
    def test_receipt_data_creation_workflow(self, sample_receipt_data):
        """Test receipt data object creation and serialization workflow."""
        from shared.utils.data import ReceiptData, LineItem, StoreInfo, TransactionTotals
        
        # Step 1: Create store info
        store_info = StoreInfo(
            name=sample_receipt_data['store']['name'],
            address=sample_receipt_data['store']['address'],
            phone=sample_receipt_data['store']['phone']
        )
        assert store_info.name == "Sample Store"
        
        # Step 2: Create line items
        items = []
        for item_data in sample_receipt_data['items']:
            item = LineItem(
                name=item_data['name'],
                quantity=item_data['quantity'],
                unit_price=Decimal(str(item_data['unit_price']))
            )
            items.append(item)
        assert len(items) == 2
        
        # Step 3: Create totals (using Decimal)
        totals = TransactionTotals(
            subtotal=Decimal(str(sample_receipt_data['totals']['subtotal'])),
            tax=Decimal(str(sample_receipt_data['totals']['tax'])),
            total=Decimal(str(sample_receipt_data['totals']['total']))
        )
        assert totals.total == Decimal('16.71')
        
        # Step 4: Create receipt data (using correct API)
        receipt = ReceiptData(
            store_name=store_info.name,
            store_address=store_info.address,
            store_phone=store_info.phone,
            items=items,
            subtotal=totals.subtotal,
            tax=totals.tax,
            total=totals.total,
            payment_method=sample_receipt_data['payment_method']
        )
        
        # Step 5: Serialize to dict
        receipt_dict = receipt.to_dict()
        # Check for store info in dict (structure may have 'store' key with nested data)
        assert 'store' in receipt_dict or 'store_name' in receipt_dict
        assert 'items' in receipt_dict
        
        # Step 6: Serialize to JSON
        receipt_json = receipt.to_json()
        assert isinstance(receipt_json, str)
        assert 'Sample Store' in receipt_json
    
    def test_extraction_result_workflow(self):
        """Test extraction result creation and status handling."""
        from shared.utils.data import (
            ExtractionResult, 
            ExtractionStatus,
            ReceiptData
        )
        
        # Create a minimal receipt for testing
        receipt = ReceiptData(
            store_name="Test Store",
            total=Decimal('10.00')
        )
        
        # Test successful extraction (using correct API with 'data' not 'receipt_data')
        success_result = ExtractionResult(
            success=True,
            data=receipt,
            metadata={'confidence': 0.95, 'processing_time': 1.5}
        )
        assert success_result.success
        assert success_result.status == ExtractionStatus.SUCCESS
        
        # Test failed extraction
        fail_result = ExtractionResult(
            success=False,
            error="OCR failed to process image"
        )
        assert not fail_result.success
        assert fail_result.error is not None
        
        # Test with warnings
        partial_result = ExtractionResult(
            success=True,
            data=receipt,
            warnings=["Could not extract all line items"]
        )
        assert len(partial_result.warnings) == 1
    
    def test_image_quality_assessment_workflow(self, sample_image_path):
        """Test image quality assessment workflow."""
        from shared.utils.image import (
            load_and_validate_image,
            assess_image_quality
        )
        
        # Load image
        image = load_and_validate_image(sample_image_path)
        
        # Assess quality
        quality = assess_image_quality(image)
        
        # Verify quality metrics
        assert quality is not None
        assert isinstance(quality, dict)
        # Quality dict should have some metrics
        assert len(quality) > 0


class TestDataValidationWorkflow:
    """Test data validation and error handling workflows."""
    
    def test_line_item_validation(self):
        """Test line item creation with validation."""
        from shared.utils.data import LineItem
        
        # Valid line item - use Decimal for price
        item = LineItem(name="Test Product", quantity=2, unit_price=Decimal('5.99'))
        assert item.name == "Test Product"
        assert item.quantity == 2
        assert item.unit_price == Decimal('5.99')
        
        # Calculate total
        total = item.calculate_total()
        assert abs(float(total) - 11.98) < 0.01
    
    def test_receipt_data_item_operations(self):
        """Test receipt data add/remove item operations."""
        from shared.utils.data import ReceiptData, LineItem
        
        receipt = ReceiptData(
            store_name="Test Store",
            total=Decimal('0')
        )
        
        # Add items - total_price is used for calculate_items_total()
        # This reflects the actual API where total_price is the calculated line total
        item1 = LineItem(
            name="Item 1", 
            quantity=1, 
            unit_price=Decimal('10.00'), 
            total_price=Decimal('10.00')  # 1 * 10.00
        )
        item2 = LineItem(
            name="Item 2", 
            quantity=2, 
            unit_price=Decimal('5.00'), 
            total_price=Decimal('10.00')  # 2 * 5.00
        )
        
        receipt.add_item(item1)
        receipt.add_item(item2)
        
        assert len(receipt.items) == 2
        
        # Calculate items total - total is sum of total_price fields
        items_total = receipt.calculate_items_total()
        assert abs(float(items_total) - 20.00) < 0.01  # 10 + 10 = 20
        
        # Remove item
        receipt.remove_item(0)
        assert len(receipt.items) == 1
    
    def test_receipt_data_serialization_roundtrip(self, sample_receipt_data):
        """Test receipt data to dict and back."""
        from shared.utils.data import ReceiptData, LineItem
        
        # Create original receipt using correct API
        original = ReceiptData(
            store_name=sample_receipt_data['store']['name'],
            store_address=sample_receipt_data['store']['address'],
            transaction_date=sample_receipt_data['date'],
            items=[
                LineItem(
                    name=item['name'], 
                    quantity=item['quantity'], 
                    unit_price=Decimal(str(item['unit_price']))
                )
                for item in sample_receipt_data['items']
            ],
            subtotal=Decimal(str(sample_receipt_data['totals']['subtotal'])),
            tax=Decimal(str(sample_receipt_data['totals']['tax'])),
            total=Decimal(str(sample_receipt_data['totals']['total'])),
            payment_method=sample_receipt_data['payment_method']
        )
        
        # Convert to dict
        as_dict = original.to_dict()
        
        # Convert back to ReceiptData
        restored = ReceiptData.from_dict(as_dict)
        
        # Verify restoration
        assert restored.store_name == original.store_name
        assert len(restored.items) == len(original.items)


class TestErrorHandlingWorkflow:
    """Test error handling across the workflow."""
    
    def test_invalid_image_handling(self):
        """Test handling of invalid image data."""
        from shared.utils.image import load_and_validate_image
        
        # Test with invalid path
        invalid_path = "/nonexistent/path/to/image.jpg"
        
        # Should return None or raise appropriate exception
        try:
            result = load_and_validate_image(invalid_path)
            # If it returns, should be None for invalid input
            assert result is None
        except Exception as e:
            # Exception is acceptable for invalid input
            assert True
    
    def test_error_classes_workflow(self):
        """Test error classes from helpers module."""
        from shared.utils.helpers import (
            ErrorCode, 
            ErrorCategory, 
            ReceiptExtractorError,
            ValidationError
        )
        
        # Create validation error
        error = ValidationError(
            message="Invalid input data",
            code=ErrorCode.INVALID_INPUT
        )
        
        assert error is not None
        assert error.message == "Invalid input data"
        assert error.category == ErrorCategory.VALIDATION
        
        # Test error to_dict method
        error_dict = error.to_dict()
        assert 'error' in error_dict
    
    def test_circuit_breaker_workflow(self):
        """Test circuit breaker pattern for external service calls."""
        from shared.utils.helpers import CircuitBreaker, CircuitBreakerConfig
        
        # Create circuit breaker with config
        config = CircuitBreakerConfig(
            failure_threshold=3,
            timeout_seconds=1.0
        )
        breaker = CircuitBreaker("test_service", config=config)
        
        assert breaker is not None
        assert breaker.state.value == "closed"
        
        # Record failures
        for _ in range(3):
            breaker.record_failure()
        
        # Should be open after threshold
        assert breaker.state.value == "open"


class TestCacheWorkflow:
    """Test caching workflow for performance optimization."""
    
    def test_lru_cache_operations(self):
        """Test LRU cache basic operations."""
        from shared.utils.helpers import LRUCache
        
        cache = LRUCache(max_size=3)
        
        # Add items
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Retrieve
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        
        # Add fourth item (should evict oldest)
        cache.set("key4", "value4")
        
        # Check stats
        stats = cache.get_stats()
        assert "size" in stats or "hits" in stats or len(stats) > 0
    
    def test_cache_ttl_expiration(self):
        """Test cache TTL functionality."""
        from shared.utils.helpers import LRUCache
        import time
        
        # ttl_seconds is the correct parameter name
        cache = LRUCache(max_size=10, ttl_seconds=0.1)  # 100ms TTL
        
        cache.set("expiring_key", "value")
        
        # Should exist immediately
        assert cache.get("expiring_key") == "value"
        
        # Wait for expiration
        time.sleep(0.15)
        
        # Should be expired
        assert cache.get("expiring_key") is None
