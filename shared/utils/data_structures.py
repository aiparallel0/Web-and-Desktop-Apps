"""
=============================================================================
DATA STRUCTURES MODULE - Enterprise Domain Models
=============================================================================

This module defines the core domain models for the Receipt Extraction System,
following Domain-Driven Design (DDD) principles and enterprise architecture patterns.

Design Principles:
- Immutability: Data classes are designed for predictable state management
- Rich Domain Models: Business logic encapsulated within domain objects
- Type Safety: Full type annotations for static analysis
- Serialization: JSON-compatible serialization for API responses

Domain Model Hierarchy:
    LineItem (Value Object)
    ├── Represents individual receipt items
    └── Encapsulates pricing calculations
    
    ReceiptData (Aggregate Root)
    ├── Store information
    ├── Transaction details
    ├── Line items collection
    └── Processing metadata
    
    ExtractionResult (Result Object)
    ├── Operation status
    ├── Extracted data
    └── Error/Warning information

Integration with Circular Exchange:
    These models integrate with the VariablePackage system for reactive updates.
    When receipt data changes, dependent components are automatically notified.

=============================================================================
"""

from __future__ import annotations

from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class ExtractionStatus(Enum):
    """Enumeration of extraction result statuses."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    PENDING = "pending"


@dataclass
class LineItem:
    """
    Value Object representing a single line item on a receipt.
    
    Attributes:
        name: Product or service name
        quantity: Number of units purchased
        unit_price: Price per unit (optional)
        total_price: Total price for this line item
        category: Optional product category for analytics
        sku: Optional stock keeping unit identifier
        
    Example:
        >>> item = LineItem(name="Coffee", quantity=2, unit_price=Decimal("3.50"), total_price=Decimal("7.00"))
        >>> item.to_dict()
        {'name': 'Coffee', 'quantity': 2, 'unit_price': '3.50', 'total_price': '7.00', 'category': None, 'sku': None}
    """
    name: str
    quantity: int = 1
    unit_price: Optional[Decimal] = None
    total_price: Decimal = field(default_factory=lambda: Decimal('0'))
    category: Optional[str] = None
    sku: Optional[str] = None
    
    def __post_init__(self):
        """Validate and normalize line item data."""
        # Ensure total_price is Decimal
        if not isinstance(self.total_price, Decimal):
            try:
                self.total_price = Decimal(str(self.total_price))
            except (InvalidOperation, TypeError):
                self.total_price = Decimal('0')
        
        # Ensure unit_price is Decimal if provided
        if self.unit_price is not None and not isinstance(self.unit_price, Decimal):
            try:
                self.unit_price = Decimal(str(self.unit_price))
            except (InvalidOperation, TypeError):
                self.unit_price = None
    
    def calculate_total(self) -> Decimal:
        """Calculate total from quantity and unit price if available."""
        if self.unit_price is not None and self.quantity > 0:
            return self.unit_price * self.quantity
        return self.total_price
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize line item to dictionary format.
        
        Returns:
            Dictionary representation suitable for JSON serialization.
        """
        return {
            'name': self.name,
            'quantity': self.quantity,
            'unit_price': str(self.unit_price) if self.unit_price else None,
            'total_price': str(self.total_price),
            'category': self.category,
            'sku': self.sku
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LineItem:
        """
        Deserialize line item from dictionary.
        
        Args:
            data: Dictionary containing line item data
            
        Returns:
            LineItem instance
        """
        return cls(
            name=data.get('name', 'Unknown'),
            quantity=data.get('quantity', 1),
            unit_price=Decimal(data['unit_price']) if data.get('unit_price') else None,
            total_price=Decimal(data.get('total_price', '0')),
            category=data.get('category'),
            sku=data.get('sku')
        )


@dataclass
class StoreInfo:
    """Value Object representing store/merchant information."""
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    tax_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize store info to dictionary."""
        return {
            'name': self.name,
            'address': self.address,
            'phone': self.phone,
            'website': self.website,
            'tax_id': self.tax_id
        }


@dataclass
class TransactionTotals:
    """Value Object representing transaction totals."""
    subtotal: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    total: Optional[Decimal] = None
    cash_tendered: Optional[Decimal] = None
    change_given: Optional[Decimal] = None
    discount: Optional[Decimal] = None
    tip: Optional[Decimal] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize totals to dictionary."""
        return {
            'subtotal': str(self.subtotal) if self.subtotal else None,
            'tax': str(self.tax) if self.tax else None,
            'total': str(self.total) if self.total else None,
            'cash': str(self.cash_tendered) if self.cash_tendered else None,
            'change': str(self.change_given) if self.change_given else None,
            'discount': str(self.discount) if self.discount else None,
            'tip': str(self.tip) if self.tip else None
        }


@dataclass
class ReceiptData:
    """
    Aggregate Root representing extracted receipt data.
    
    This is the primary domain model for receipt information, containing
    all extracted data from a receipt image or document.
    
    Attributes:
        store_name: Name of the store/merchant
        store_address: Physical address
        store_phone: Contact phone number
        items: List of purchased items
        subtotal: Pre-tax total
        total: Final total including tax
        tax: Tax amount
        transaction_date: Date of transaction
        transaction_time: Time of transaction
        model_used: AI model used for extraction
        confidence_score: Confidence level (0.0 to 1.0)
        processing_time: Time taken to process (seconds)
        
    Integration:
        This model integrates with the CircularExchange framework.
        Changes to receipt data automatically propagate to dependent modules.
    """
    # Store Information
    store_name: Optional[str] = None
    store_address: Optional[str] = None
    store_phone: Optional[str] = None
    
    # Line Items
    items: List[LineItem] = field(default_factory=list)
    
    # Transaction Totals
    subtotal: Optional[Decimal] = None
    total: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    cash_tendered: Optional[Decimal] = None
    change_given: Optional[Decimal] = None
    
    # Transaction Metadata
    transaction_date: Optional[str] = None
    transaction_time: Optional[str] = None
    payment_method: Optional[str] = None
    receipt_number: Optional[str] = None
    
    # Processing Metadata
    model_used: str = "Unknown"
    extraction_notes: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    processing_time: float = 0.0
    
    # Audit Trail
    extracted_at: Optional[str] = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    raw_text: Optional[str] = None
    
    def add_item(self, item: LineItem) -> None:
        """Add a line item to the receipt."""
        self.items.append(item)
        logger.debug(f"Added item: {item.name}")
    
    def remove_item(self, index: int) -> Optional[LineItem]:
        """Remove and return a line item by index."""
        if 0 <= index < len(self.items):
            return self.items.pop(index)
        return None
    
    def calculate_items_total(self) -> Decimal:
        """Calculate sum of all line item totals."""
        return sum((item.total_price for item in self.items), Decimal('0'))
    
    def _calculate_coverage(self) -> str:
        """
        Calculate coverage percentage of items vs total.
        
        Returns:
            String representation of coverage percentage.
        """
        if not self.total or not self.items:
            return "N/A"
        
        items_sum = self.calculate_items_total()
        coverage = (items_sum / self.total * 100) if self.total > 0 else 0
        return f"{coverage:.1f}%"
    
    def get_store_info(self) -> StoreInfo:
        """Get store information as a value object."""
        return StoreInfo(
            name=self.store_name,
            address=self.store_address,
            phone=self.store_phone
        )
    
    def get_totals(self) -> TransactionTotals:
        """Get transaction totals as a value object."""
        return TransactionTotals(
            subtotal=self.subtotal,
            tax=self.tax,
            total=self.total,
            cash_tendered=self.cash_tendered,
            change_given=self.change_given
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize receipt data to dictionary format.
        
        Returns:
            Complete dictionary representation suitable for JSON/API responses.
        """
        return {
            'store': {
                'name': self.store_name,
                'address': self.store_address,
                'phone': self.store_phone
            },
            'items': [item.to_dict() for item in self.items],
            'totals': {
                'subtotal': str(self.subtotal) if self.subtotal else None,
                'tax': str(self.tax) if self.tax else None,
                'total': str(self.total) if self.total else None,
                'cash': str(self.cash_tendered) if self.cash_tendered else None,
                'change': str(self.change_given) if self.change_given else None
            },
            'date': self.transaction_date,
            'time': self.transaction_time,
            'payment_method': self.payment_method,
            'receipt_number': self.receipt_number,
            'item_count': len(self.items),
            'coverage': self._calculate_coverage(),
            'model': self.model_used,
            'confidence': self.confidence_score,
            'processing_time': self.processing_time,
            'notes': self.extraction_notes,
            'extracted_at': self.extracted_at
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ReceiptData:
        """
        Deserialize receipt data from dictionary.
        
        Args:
            data: Dictionary containing receipt data
            
        Returns:
            ReceiptData instance
        """
        items = [
            LineItem.from_dict(item) if isinstance(item, dict) else item
            for item in data.get('items', [])
        ]
        
        store = data.get('store', {})
        totals = data.get('totals', {})
        
        return cls(
            store_name=store.get('name') or data.get('store_name'),
            store_address=store.get('address') or data.get('store_address'),
            store_phone=store.get('phone') or data.get('store_phone'),
            items=items,
            subtotal=Decimal(totals['subtotal']) if totals.get('subtotal') else None,
            total=Decimal(totals['total']) if totals.get('total') else None,
            tax=Decimal(totals['tax']) if totals.get('tax') else None,
            transaction_date=data.get('date') or data.get('transaction_date'),
            transaction_time=data.get('time') or data.get('transaction_time'),
            model_used=data.get('model', 'Unknown'),
            confidence_score=data.get('confidence', 0.0),
            processing_time=data.get('processing_time', 0.0)
        )


@dataclass
class ExtractionResult:
    """
    Result Object representing the outcome of a receipt extraction operation.
    
    This class follows the Result pattern, encapsulating both success and
    failure cases with appropriate data and error information.
    
    Attributes:
        success: Whether extraction succeeded
        data: Extracted receipt data (if successful)
        error: Error message (if failed)
        warnings: Non-fatal warnings during extraction
        status: Detailed status enum
        metadata: Additional processing metadata
    """
    success: bool
    data: Optional[ReceiptData] = None
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    status: ExtractionStatus = field(default=ExtractionStatus.PENDING)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Set status based on success flag."""
        if self.success and self.data:
            self.status = ExtractionStatus.SUCCESS
        elif self.success and not self.data:
            self.status = ExtractionStatus.PARTIAL
        elif not self.success:
            self.status = ExtractionStatus.FAILED
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
        logger.warning(f"Extraction warning: {warning}")
    
    def is_partial(self) -> bool:
        """Check if extraction was partial."""
        return self.status == ExtractionStatus.PARTIAL
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize extraction result to dictionary.
        
        Returns:
            Dictionary representation including all result data.
        """
        return {
            'success': self.success,
            'status': self.status.value,
            'data': self.data.to_dict() if self.data else None,
            'error': self.error,
            'warnings': self.warnings,
            'metadata': self.metadata
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def success_result(cls, data: ReceiptData, warnings: List[str] = None) -> ExtractionResult:
        """Factory method for successful extraction."""
        return cls(
            success=True,
            data=data,
            warnings=warnings or [],
            status=ExtractionStatus.SUCCESS
        )
    
    @classmethod
    def failure_result(cls, error: str, warnings: List[str] = None) -> ExtractionResult:
        """Factory method for failed extraction."""
        return cls(
            success=False,
            error=error,
            warnings=warnings or [],
            status=ExtractionStatus.FAILED
        )
    
    @classmethod
    def partial_result(cls, data: ReceiptData, warnings: List[str]) -> ExtractionResult:
        """Factory method for partial extraction."""
        return cls(
            success=True,
            data=data,
            warnings=warnings,
            status=ExtractionStatus.PARTIAL
        )
