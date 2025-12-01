"""
Tests for the enhanced Florence-2 processor text detection capabilities.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from decimal import Decimal


class TestFlorenceProcessorEnhancements:
    """Tests for Florence-2 processor enhancements."""

    @pytest.fixture
    def mock_florence_processor(self):
        """Create a mock Florence processor for testing extraction methods."""
        # Import at test time to avoid dependencies
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared', 'models'))
        
        # Mock the transformers and torch imports
        with patch.dict('sys.modules', {
            'torch': MagicMock(),
            'transformers': MagicMock()
        }):
            # Create a mock processor with the enhanced methods
            mock_processor = Mock()
            mock_processor.normalize_price = lambda x: Decimal(str(x).replace(',', '.').replace('$', '')) if x else None
            
            # Add the enhanced extraction methods
            from ai_models import FlorenceProcessor
            
            # Create instance without loading model
            with patch.object(FlorenceProcessor, '_load_model', return_value=None):
                processor = FlorenceProcessor.__new__(FlorenceProcessor)
                processor.model_config = {'huggingface_id': 'test', 'task_prompt': '<OCR_WITH_REGION>', 'name': 'test'}
                processor.model_id = 'test'
                processor.task_prompt = '<OCR_WITH_REGION>'
                processor.model_name = 'test'
                processor.device = 'cpu'
                processor.model = None
                processor.processor = None
                
            return processor

    def test_extract_store_name_from_regions_top_text(self, mock_florence_processor):
        """Test store name extraction from top regions."""
        regions = [
            {'text': 'WALMART', 'bbox': [0, 0, 100, 20], 'y_pos': 0, 'index': 0},
            {'text': '123 Main St', 'bbox': [0, 20, 100, 40], 'y_pos': 20, 'index': 1},
            {'text': '555-1234', 'bbox': [0, 40, 100, 60], 'y_pos': 40, 'index': 2},
        ]
        result = mock_florence_processor._extract_store_name_from_regions(regions)
        assert result == 'WALMART'

    def test_extract_store_name_skips_short_text(self, mock_florence_processor):
        """Test that short text is skipped for store name."""
        regions = [
            {'text': 'AB', 'bbox': [0, 0, 100, 20], 'y_pos': 0, 'index': 0},
            {'text': 'COSTCO', 'bbox': [0, 20, 100, 40], 'y_pos': 20, 'index': 1},
        ]
        result = mock_florence_processor._extract_store_name_from_regions(regions)
        assert result == 'COSTCO'

    def test_extract_store_name_skips_digits(self, mock_florence_processor):
        """Test that digit-only text is skipped."""
        regions = [
            {'text': '12345', 'bbox': [0, 0, 100, 20], 'y_pos': 0, 'index': 0},
            {'text': 'TARGET', 'bbox': [0, 20, 100, 40], 'y_pos': 20, 'index': 1},
        ]
        result = mock_florence_processor._extract_store_name_from_regions(regions)
        assert result == 'TARGET'

    def test_extract_store_name_skips_prices(self, mock_florence_processor):
        """Test that prices are skipped for store name."""
        regions = [
            {'text': '$12.99', 'bbox': [0, 0, 100, 20], 'y_pos': 0, 'index': 0},
            {'text': 'KROGER', 'bbox': [0, 20, 100, 40], 'y_pos': 20, 'index': 1},
        ]
        result = mock_florence_processor._extract_store_name_from_regions(regions)
        assert result == 'KROGER'

    def test_extract_address_with_street(self, mock_florence_processor):
        """Test address extraction with street keyword."""
        regions = [
            {'text': 'WALMART SUPERCENTER', 'bbox': [0, 0, 100, 20], 'y_pos': 0, 'index': 0},
            {'text': '123 Main Street Suite 100', 'bbox': [0, 20, 100, 40], 'y_pos': 20, 'index': 1},
            {'text': 'City, ST 12345', 'bbox': [0, 40, 100, 60], 'y_pos': 40, 'index': 2},
        ]
        result = mock_florence_processor._extract_address_from_regions(regions)
        assert result == '123 Main Street Suite 100'

    def test_extract_address_with_state_zip(self, mock_florence_processor):
        """Test address extraction with state + ZIP pattern."""
        regions = [
            {'text': 'WALMART', 'bbox': [0, 0, 100, 20], 'y_pos': 0, 'index': 0},
            {'text': 'Some City, CA 90210', 'bbox': [0, 20, 100, 40], 'y_pos': 20, 'index': 1},
        ]
        result = mock_florence_processor._extract_address_from_regions(regions)
        assert result == 'Some City, CA 90210'

    def test_extract_phone_standard_format(self, mock_florence_processor):
        """Test phone extraction with standard format."""
        text = "Call us at (555) 123-4567 for questions"
        result = mock_florence_processor._extract_phone_from_text(text)
        assert result == '(555) 123-4567'

    def test_extract_phone_no_parentheses(self, mock_florence_processor):
        """Test phone extraction without parentheses."""
        text = "Phone: 555-123-4567"
        result = mock_florence_processor._extract_phone_from_text(text)
        assert result == '555-123-4567'

    def test_extract_date_slash_format(self, mock_florence_processor):
        """Test date extraction with slash format."""
        text = "Transaction date: 12/25/2024"
        result = mock_florence_processor._extract_date_from_text(text)
        assert result == '12/25/2024'

    def test_extract_date_dash_format(self, mock_florence_processor):
        """Test date extraction with dash format."""
        text = "Date: 01-15-2024"
        result = mock_florence_processor._extract_date_from_text(text)
        assert result == '01-15-2024'

    def test_extract_date_month_name_format(self, mock_florence_processor):
        """Test date extraction with month name."""
        text = "January 15, 2024"
        result = mock_florence_processor._extract_date_from_text(text)
        assert result == 'January 15, 2024'


class TestFlorenceItemExtraction:
    """Tests for Florence-2 line item extraction."""

    @pytest.fixture
    def mock_florence_processor(self):
        """Create a mock Florence processor."""
        with patch.dict('sys.modules', {
            'torch': MagicMock(),
            'transformers': MagicMock()
        }):
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared', 'models'))
            from ai_models import FlorenceProcessor
            
            with patch.object(FlorenceProcessor, '_load_model', return_value=None):
                processor = FlorenceProcessor.__new__(FlorenceProcessor)
                processor.model_config = {'huggingface_id': 'test', 'task_prompt': '<OCR>', 'name': 'test'}
                processor.model_id = 'test'
                processor.task_prompt = '<OCR>'
                processor.model_name = 'test'
                processor.device = 'cpu'
                processor.model = None
                processor.processor = None
                
            return processor

    def test_extract_items_basic(self, mock_florence_processor):
        """Test basic item extraction."""
        regions = [
            {'text': 'MILK 2.99', 'bbox': [0, 0, 100, 20], 'y_pos': 0, 'index': 0},
            {'text': 'BREAD 1.50', 'bbox': [0, 20, 100, 40], 'y_pos': 20, 'index': 1},
            {'text': 'TOTAL 4.49', 'bbox': [0, 40, 100, 60], 'y_pos': 40, 'index': 2},
        ]
        result = mock_florence_processor._extract_items_from_regions(regions)
        assert len(result) == 2
        assert result[0].name == 'MILK'
        assert result[1].name == 'BREAD'

    def test_extract_items_skips_total(self, mock_florence_processor):
        """Test that total lines are skipped."""
        regions = [
            {'text': 'EGGS 3.99', 'bbox': [0, 0, 100, 20], 'y_pos': 0, 'index': 0},
            {'text': 'SUBTOTAL 3.99', 'bbox': [0, 20, 100, 40], 'y_pos': 20, 'index': 1},
            {'text': 'TAX 0.32', 'bbox': [0, 40, 100, 60], 'y_pos': 40, 'index': 2},
            {'text': 'TOTAL 4.31', 'bbox': [0, 60, 100, 80], 'y_pos': 60, 'index': 3},
        ]
        result = mock_florence_processor._extract_items_from_regions(regions)
        assert len(result) == 1
        assert result[0].name == 'EGGS'

    def test_extract_items_with_dollar_sign(self, mock_florence_processor):
        """Test item extraction with dollar signs."""
        regions = [
            {'text': 'COFFEE $4.99', 'bbox': [0, 0, 100, 20], 'y_pos': 0, 'index': 0},
        ]
        result = mock_florence_processor._extract_items_from_regions(regions)
        assert len(result) == 1
        assert result[0].name == 'COFFEE'


class TestFlorenceTotalExtraction:
    """Tests for Florence-2 total extraction."""

    @pytest.fixture
    def mock_florence_processor(self):
        """Create a mock Florence processor."""
        with patch.dict('sys.modules', {
            'torch': MagicMock(),
            'transformers': MagicMock()
        }):
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared', 'models'))
            from ai_models import FlorenceProcessor
            
            with patch.object(FlorenceProcessor, '_load_model', return_value=None):
                processor = FlorenceProcessor.__new__(FlorenceProcessor)
                processor.model_config = {'huggingface_id': 'test', 'task_prompt': '<OCR>', 'name': 'test'}
                processor.model_id = 'test'
                processor.task_prompt = '<OCR>'
                processor.model_name = 'test'
                processor.device = 'cpu'
                processor.model = None
                processor.processor = None
                
            return processor

    def test_extract_total_from_bottom_regions(self, mock_florence_processor):
        """Test total extraction from bottom regions."""
        regions = [
            {'text': 'ITEM 5.00', 'bbox': [0, 0, 100, 20], 'y_pos': 0, 'index': 0},
            {'text': 'ITEM 3.00', 'bbox': [0, 20, 100, 40], 'y_pos': 20, 'index': 1},
            {'text': 'SUBTOTAL 8.00', 'bbox': [0, 40, 100, 60], 'y_pos': 40, 'index': 2},
            {'text': 'TAX 0.64', 'bbox': [0, 60, 100, 80], 'y_pos': 60, 'index': 3},
            {'text': 'TOTAL 8.64', 'bbox': [0, 80, 100, 100], 'y_pos': 80, 'index': 4},
        ]
        total, subtotal = mock_florence_processor._extract_totals_from_regions(regions, '')
        assert total is not None
        assert float(total) == 8.64

    def test_extract_total_grand_total(self, mock_florence_processor):
        """Test grand total extraction."""
        regions = [
            {'text': 'GRAND TOTAL: $25.99', 'bbox': [0, 0, 100, 20], 'y_pos': 0, 'index': 0},
        ]
        total, subtotal = mock_florence_processor._extract_totals_from_regions(regions, '')
        assert total is not None
        assert float(total) == 25.99


class TestFlorenceConfidenceCalculation:
    """Tests for Florence-2 confidence calculation."""

    @pytest.fixture
    def mock_florence_processor(self):
        """Create a mock Florence processor."""
        with patch.dict('sys.modules', {
            'torch': MagicMock(),
            'transformers': MagicMock()
        }):
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared', 'models'))
            from ai_models import FlorenceProcessor
            from utils.data_structures import ReceiptData, LineItem
            
            with patch.object(FlorenceProcessor, '_load_model', return_value=None):
                processor = FlorenceProcessor.__new__(FlorenceProcessor)
                processor.model_config = {'huggingface_id': 'test', 'task_prompt': '<OCR>', 'name': 'test'}
                processor.model_id = 'test'
                processor.task_prompt = '<OCR>'
                processor.model_name = 'test'
                processor.device = 'cpu'
                processor.model = None
                processor.processor = None
                
            return processor

    def test_confidence_with_all_fields(self, mock_florence_processor):
        """Test confidence with all fields populated."""
        from shared.utils.data_structures import ReceiptData, LineItem
        
        receipt = ReceiptData()
        receipt.store_name = "Test Store"
        receipt.total = Decimal("25.99")
        receipt.transaction_date = "2024-01-15"
        receipt.store_address = "123 Main St"
        receipt.items = [
            LineItem(name="Item 1", total_price=Decimal("10.00")),
            LineItem(name="Item 2", total_price=Decimal("15.00")),
        ]
        
        regions = [{'text': 'text', 'bbox': [0,0,0,0], 'y_pos': 0, 'index': i} for i in range(10)]
        
        confidence = mock_florence_processor._calculate_extraction_confidence(receipt, regions)
        assert confidence > 50.0  # Should have high confidence with all fields

    def test_confidence_with_minimal_fields(self, mock_florence_processor):
        """Test confidence with minimal fields."""
        from shared.utils.data_structures import ReceiptData
        
        receipt = ReceiptData()
        # No fields populated
        
        regions = []
        
        confidence = mock_florence_processor._calculate_extraction_confidence(receipt, regions)
        assert confidence == 0.0


class TestFlorenceTaskPrompts:
    """Tests for Florence-2 task prompt constants."""

    def test_task_prompts_defined(self):
        """Test that task prompts are properly defined."""
        with patch.dict('sys.modules', {
            'torch': MagicMock(),
            'transformers': MagicMock()
        }):
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared', 'models'))
            from ai_models import FlorenceProcessor
            
            assert hasattr(FlorenceProcessor, 'TASK_OCR')
            assert hasattr(FlorenceProcessor, 'TASK_OCR_WITH_REGION')
            assert hasattr(FlorenceProcessor, 'TASK_DENSE_CAPTION')
            
            assert FlorenceProcessor.TASK_OCR == "<OCR>"
            assert FlorenceProcessor.TASK_OCR_WITH_REGION == "<OCR_WITH_REGION>"
            assert FlorenceProcessor.TASK_DENSE_CAPTION == "<DENSE_REGION_CAPTION>"


class TestFlorenceNullChecks:
    """Tests for Florence-2 null safety checks."""

    @pytest.fixture
    def mock_florence_processor_no_model(self):
        """Create a mock Florence processor without model loaded."""
        with patch.dict('sys.modules', {
            'torch': MagicMock(),
            'transformers': MagicMock()
        }):
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared', 'models'))
            from ai_models import FlorenceProcessor
            
            with patch.object(FlorenceProcessor, '_load_model', return_value=None):
                processor = FlorenceProcessor.__new__(FlorenceProcessor)
                processor.model_config = {'huggingface_id': 'test', 'task_prompt': '<OCR>', 'name': 'test'}
                processor.model_id = 'test'
                processor.task_prompt = '<OCR>'
                processor.model_name = 'test'
                processor.device = 'cpu'
                processor.model = None  # Simulate failed model load
                processor.processor = None  # Simulate failed processor load
                
            return processor

    def test_extract_returns_error_when_model_none(self, mock_florence_processor_no_model):
        """Test that extract returns error result when model is None."""
        result = mock_florence_processor_no_model.extract('/path/to/image.jpg')
        assert result.success is False
        assert 'not loaded' in result.error.lower()

    def test_run_florence_task_raises_when_processor_none(self, mock_florence_processor_no_model):
        """Test that _run_florence_task raises error when processor is None."""
        with pytest.raises(RuntimeError) as exc_info:
            mock_florence_processor_no_model._run_florence_task(Mock(), '<OCR>')
        assert 'processor not loaded' in str(exc_info.value).lower()

    def test_run_florence_task_raises_when_model_none(self):
        """Test that _run_florence_task raises error when model is None."""
        with patch.dict('sys.modules', {
            'torch': MagicMock(),
            'transformers': MagicMock()
        }):
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared', 'models'))
            from ai_models import FlorenceProcessor
            
            with patch.object(FlorenceProcessor, '_load_model', return_value=None):
                processor = FlorenceProcessor.__new__(FlorenceProcessor)
                processor.model_config = {'huggingface_id': 'test', 'task_prompt': '<OCR>', 'name': 'test'}
                processor.model_id = 'test'
                processor.task_prompt = '<OCR>'
                processor.model_name = 'test'
                processor.device = 'cpu'
                processor.processor = Mock()  # Processor is set
                processor.model = None  # Model is None
            
            with pytest.raises(RuntimeError) as exc_info:
                processor._run_florence_task(Mock(), '<OCR>')
            assert 'model not loaded' in str(exc_info.value).lower()

    def test_run_florence_task_raises_when_image_none(self):
        """Test that _run_florence_task raises error when image is None."""
        with patch.dict('sys.modules', {
            'torch': MagicMock(),
            'transformers': MagicMock()
        }):
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared', 'models'))
            from ai_models import FlorenceProcessor
            
            with patch.object(FlorenceProcessor, '_load_model', return_value=None):
                processor = FlorenceProcessor.__new__(FlorenceProcessor)
                processor.model_config = {'huggingface_id': 'test', 'task_prompt': '<OCR>', 'name': 'test'}
                processor.model_id = 'test'
                processor.task_prompt = '<OCR>'
                processor.model_name = 'test'
                processor.device = 'cpu'
                processor.processor = Mock()  # Processor is set
                processor.model = Mock()  # Model is set
            
            with pytest.raises(ValueError) as exc_info:
                processor._run_florence_task(None, '<OCR>')
            assert 'image cannot be none' in str(exc_info.value).lower()
