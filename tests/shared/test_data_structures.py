"""
Tests for the shared data structures module.
"""
import pytest
from decimal import Decimal


class TestLineItem:
    """Tests for LineItem class."""

    def test_create_basic_line_item(self):
        from shared.utils.data_structures import LineItem
        item = LineItem(name="Coffee", total_price=Decimal("3.50"))
        assert item.name == "Coffee"
        assert item.total_price == Decimal("3.50")
        assert item.quantity == 1

    def test_line_item_with_quantity(self):
        from shared.utils.data_structures import LineItem
        item = LineItem(name="Apple", quantity=3, unit_price=Decimal("0.50"), total_price=Decimal("1.50"))
        assert item.quantity == 3
        assert item.unit_price == Decimal("0.50")

    def test_line_item_calculate_total(self):
        from shared.utils.data_structures import LineItem
        item = LineItem(name="Banana", quantity=5, unit_price=Decimal("0.30"), total_price=Decimal("0"))
        calculated = item.calculate_total()
        assert calculated == Decimal("1.50")

    def test_line_item_to_dict(self):
        from shared.utils.data_structures import LineItem
        item = LineItem(name="Milk", total_price=Decimal("2.99"), category="Dairy")
        result = item.to_dict()
        assert result['name'] == "Milk"
        assert result['total_price'] == "2.99"
        assert result['category'] == "Dairy"

    def test_line_item_from_dict(self):
        from shared.utils.data_structures import LineItem
        data = {
            'name': 'Bread',
            'quantity': 2,
            'total_price': '4.50',
            'category': 'Bakery'
        }
        item = LineItem.from_dict(data)
        assert item.name == 'Bread'
        assert item.quantity == 2
        assert item.total_price == Decimal('4.50')

    def test_line_item_normalizes_string_price(self):
        from shared.utils.data_structures import LineItem
        item = LineItem(name="Test", total_price="5.99")
        assert item.total_price == Decimal("5.99")

    def test_line_item_handles_invalid_price(self):
        from shared.utils.data_structures import LineItem
        item = LineItem(name="Test", total_price="invalid")
        assert item.total_price == Decimal("0")


class TestReceiptData:
    """Tests for ReceiptData class."""

    def test_create_empty_receipt(self):
        from shared.utils.data_structures import ReceiptData
        receipt = ReceiptData()
        assert receipt.store_name is None
        assert receipt.items == []
        assert receipt.total is None

    def test_receipt_with_store_info(self):
        from shared.utils.data_structures import ReceiptData
        receipt = ReceiptData(
            store_name="Test Store",
            store_address="123 Main St",
            store_phone="555-1234"
        )
        assert receipt.store_name == "Test Store"
        assert receipt.store_address == "123 Main St"
        assert receipt.store_phone == "555-1234"

    def test_receipt_with_totals(self):
        from shared.utils.data_structures import ReceiptData
        receipt = ReceiptData(
            subtotal=Decimal("10.00"),
            tax=Decimal("0.80"),
            total=Decimal("10.80")
        )
        assert receipt.subtotal == Decimal("10.00")
        assert receipt.tax == Decimal("0.80")
        assert receipt.total == Decimal("10.80")

    def test_receipt_with_items(self):
        from shared.utils.data_structures import ReceiptData, LineItem
        items = [
            LineItem(name="Item 1", total_price=Decimal("5.00")),
            LineItem(name="Item 2", total_price=Decimal("3.00"))
        ]
        receipt = ReceiptData(items=items)
        assert len(receipt.items) == 2

    def test_receipt_to_dict(self):
        from shared.utils.data_structures import ReceiptData
        receipt = ReceiptData(
            store_name="Test Store",
            total=Decimal("25.00")
        )
        result = receipt.to_dict()
        assert result['store']['name'] == "Test Store"

    def test_receipt_add_item(self):
        from shared.utils.data_structures import ReceiptData, LineItem
        receipt = ReceiptData()
        item = LineItem(name="Coffee", total_price=Decimal("4.50"))
        receipt.add_item(item)
        assert len(receipt.items) == 1
        assert receipt.items[0].name == "Coffee"


class TestExtractionResult:
    """Tests for ExtractionResult class."""

    def test_successful_result(self):
        from shared.utils.data_structures import ExtractionResult, ReceiptData
        receipt = ReceiptData(store_name="Test")
        result = ExtractionResult(success=True, data=receipt)
        assert result.success is True
        assert result.data.store_name == "Test"
        assert result.error is None

    def test_failed_result(self):
        from shared.utils.data_structures import ExtractionResult
        result = ExtractionResult(success=False, error="Image processing failed")
        assert result.success is False
        assert result.error == "Image processing failed"
        assert result.data is None

    def test_result_with_warnings(self):
        from shared.utils.data_structures import ExtractionResult, ReceiptData
        receipt = ReceiptData()
        result = ExtractionResult(
            success=True,
            data=receipt,
            warnings=["Low image quality", "Some text unclear"]
        )
        assert len(result.warnings) == 2


class TestStoreInfo:
    """Tests for StoreInfo class."""

    def test_create_store_info(self):
        from shared.utils.data_structures import StoreInfo
        store = StoreInfo(
            name="Walmart",
            address="123 Main St",
            phone="555-1234"
        )
        assert store.name == "Walmart"
        assert store.address == "123 Main St"

    def test_store_info_to_dict(self):
        from shared.utils.data_structures import StoreInfo
        store = StoreInfo(name="Target", phone="555-5678")
        result = store.to_dict()
        assert result['name'] == "Target"
        assert result['phone'] == "555-5678"
        assert result['address'] is None


class TestTransactionTotals:
    """Tests for TransactionTotals class."""

    def test_create_totals(self):
        from shared.utils.data_structures import TransactionTotals
        totals = TransactionTotals(
            subtotal=Decimal("50.00"),
            tax=Decimal("4.00"),
            total=Decimal("54.00")
        )
        assert totals.subtotal == Decimal("50.00")
        assert totals.tax == Decimal("4.00")
        assert totals.total == Decimal("54.00")

    def test_totals_with_payment(self):
        from shared.utils.data_structures import TransactionTotals
        totals = TransactionTotals(
            total=Decimal("54.00"),
            cash_tendered=Decimal("60.00"),
            change_given=Decimal("6.00")
        )
        assert totals.cash_tendered == Decimal("60.00")
        assert totals.change_given == Decimal("6.00")

    def test_totals_to_dict(self):
        from shared.utils.data_structures import TransactionTotals
        totals = TransactionTotals(
            subtotal=Decimal("100.00"),
            discount=Decimal("10.00"),
            total=Decimal("90.00")
        )
        result = totals.to_dict()
        assert result['subtotal'] == "100.00"
        assert result['discount'] == "10.00"


class TestExtractionStatus:
    """Tests for ExtractionStatus enum."""

    def test_status_values(self):
        from shared.utils.data_structures import ExtractionStatus
        assert ExtractionStatus.SUCCESS.value == "success"
        assert ExtractionStatus.PARTIAL.value == "partial"
        assert ExtractionStatus.FAILED.value == "failed"
        assert ExtractionStatus.PENDING.value == "pending"
