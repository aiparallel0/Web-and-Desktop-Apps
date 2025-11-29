"""
Test suite for data structures
Tests coverage for shared/utils/data_structures.py
"""
import pytest
from decimal import Decimal
from pathlib import Path
import sys

# Add shared to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / 'shared'))

from utils.data_structures import LineItem, ReceiptData, ExtractionResult


class TestLineItem:
    """Test LineItem dataclass"""

    def test_line_item_creation_minimal(self):
        """Test creating line item with minimal fields"""
        item = LineItem(name="Coffee")
        
        assert item.name == "Coffee"
        assert item.quantity == 1
        assert item.unit_price is None
        assert item.total_price == Decimal('0')

    def test_line_item_creation_full(self):
        """Test creating line item with all fields"""
        item = LineItem(
            name="Coffee",
            quantity=2,
            unit_price=Decimal('3.50'),
            total_price=Decimal('7.00')
        )
        
        assert item.name == "Coffee"
        assert item.quantity == 2
        assert item.unit_price == Decimal('3.50')
        assert item.total_price == Decimal('7.00')

    def test_line_item_to_dict(self):
        """Test line item to_dict method"""
        item = LineItem(
            name="Tea",
            quantity=1,
            unit_price=Decimal('2.50'),
            total_price=Decimal('2.50')
        )
        
        result = item.to_dict()
        
        assert result['name'] == "Tea"
        assert result['quantity'] == 1
        assert result['unit_price'] == '2.50'
        assert result['total_price'] == '2.50'

    def test_line_item_to_dict_none_unit_price(self):
        """Test line item to_dict with None unit price"""
        item = LineItem(name="Item", total_price=Decimal('5.00'))
        
        result = item.to_dict()
        
        assert result['unit_price'] is None


class TestReceiptData:
    """Test ReceiptData dataclass"""

    def test_receipt_data_creation_empty(self):
        """Test creating empty receipt data"""
        receipt = ReceiptData()
        
        assert receipt.store_name is None
        assert receipt.store_address is None
        assert receipt.items == []
        assert receipt.total is None
        assert receipt.model_used == "Unknown"

    def test_receipt_data_creation_with_store(self):
        """Test creating receipt data with store info"""
        receipt = ReceiptData(
            store_name="Test Store",
            store_address="123 Main St",
            store_phone="555-1234"
        )
        
        assert receipt.store_name == "Test Store"
        assert receipt.store_address == "123 Main St"
        assert receipt.store_phone == "555-1234"

    def test_receipt_data_with_items(self):
        """Test receipt data with line items"""
        items = [
            LineItem(name="Coffee", total_price=Decimal('3.50')),
            LineItem(name="Muffin", total_price=Decimal('2.00'))
        ]
        
        receipt = ReceiptData(items=items, total=Decimal('5.50'))
        
        assert len(receipt.items) == 2
        assert receipt.total == Decimal('5.50')

    def test_receipt_data_to_dict(self):
        """Test receipt data to_dict method"""
        receipt = ReceiptData(
            store_name="Test Store",
            store_address="123 Main St",
            total=Decimal('10.00'),
            subtotal=Decimal('9.00'),
            tax=Decimal('1.00'),
            model_used="test_model",
            confidence_score=0.95
        )
        
        result = receipt.to_dict()
        
        assert result['store']['name'] == "Test Store"
        assert result['store']['address'] == "123 Main St"
        assert result['totals']['total'] == '10.00'
        assert result['totals']['subtotal'] == '9.00'
        assert result['totals']['tax'] == '1.00'
        assert result['model'] == "test_model"
        assert result['confidence'] == 0.95

    def test_receipt_data_calculate_coverage_no_data(self):
        """Test coverage calculation with no data"""
        receipt = ReceiptData()
        
        result = receipt.to_dict()
        
        assert result['coverage'] == "N/A"

    def test_receipt_data_calculate_coverage_with_items(self):
        """Test coverage calculation with items"""
        items = [
            LineItem(name="Item1", total_price=Decimal('5.00')),
            LineItem(name="Item2", total_price=Decimal('5.00'))
        ]
        
        receipt = ReceiptData(items=items, total=Decimal('10.00'))
        result = receipt.to_dict()
        
        assert result['coverage'] == "100.0%"

    def test_receipt_data_calculate_coverage_partial(self):
        """Test coverage calculation with partial items"""
        items = [
            LineItem(name="Item1", total_price=Decimal('5.00'))
        ]
        
        receipt = ReceiptData(items=items, total=Decimal('10.00'))
        result = receipt.to_dict()
        
        assert result['coverage'] == "50.0%"


class TestExtractionResult:
    """Test ExtractionResult dataclass"""

    def test_extraction_result_success(self):
        """Test successful extraction result"""
        data = ReceiptData(store_name="Test Store")
        result = ExtractionResult(success=True, data=data)
        
        assert result.success is True
        assert result.data is not None
        assert result.error is None
        assert result.warnings == []

    def test_extraction_result_failure(self):
        """Test failed extraction result"""
        result = ExtractionResult(
            success=False,
            error="Failed to extract receipt"
        )
        
        assert result.success is False
        assert result.data is None
        assert result.error == "Failed to extract receipt"

    def test_extraction_result_with_warnings(self):
        """Test extraction result with warnings"""
        data = ReceiptData(store_name="Test Store")
        result = ExtractionResult(
            success=True,
            data=data,
            warnings=["Low confidence", "Missing total"]
        )
        
        assert result.success is True
        assert len(result.warnings) == 2

    def test_extraction_result_to_dict_success(self):
        """Test extraction result to_dict with success"""
        data = ReceiptData(store_name="Test Store")
        result = ExtractionResult(success=True, data=data)
        
        dict_result = result.to_dict()
        
        assert dict_result['success'] is True
        assert dict_result['data'] is not None
        assert dict_result['error'] is None

    def test_extraction_result_to_dict_failure(self):
        """Test extraction result to_dict with failure"""
        result = ExtractionResult(
            success=False,
            error="Test error"
        )
        
        dict_result = result.to_dict()
        
        assert dict_result['success'] is False
        assert dict_result['data'] is None
        assert dict_result['error'] == "Test error"
