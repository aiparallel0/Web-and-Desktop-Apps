"""
Shared data structures for receipt extraction
Used by both web and desktop applications
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class LineItem:
    """Represents a single line item on a receipt"""
    name: str
    quantity: int = 1
    unit_price: Optional[Decimal] = None
    total_price: Decimal = Decimal('0')

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'quantity': self.quantity,
            'unit_price': str(self.unit_price) if self.unit_price else None,
            'total_price': str(self.total_price)
        }


@dataclass
class ReceiptData:
    """Complete receipt data structure"""
    store_name: Optional[str] = None
    store_address: Optional[str] = None
    store_phone: Optional[str] = None
    items: List[LineItem] = field(default_factory=list)
    subtotal: Optional[Decimal] = None
    total: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    cash_tendered: Optional[Decimal] = None
    change_given: Optional[Decimal] = None
    transaction_date: Optional[str] = None
    transaction_time: Optional[str] = None
    model_used: str = "Unknown"
    extraction_notes: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    processing_time: float = 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
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
            'item_count': len(self.items),
            'coverage': self._calculate_coverage(),
            'model': self.model_used,
            'confidence': self.confidence_score,
            'processing_time': self.processing_time,
            'notes': self.extraction_notes
        }

    def _calculate_coverage(self) -> str:
        """Calculate how much of the total is covered by itemized prices"""
        if not self.total or not self.items:
            return "N/A"
        items_sum = sum(item.total_price for item in self.items)
        coverage = (items_sum / self.total * 100) if self.total > 0 else 0
        return f"{coverage:.1f}%"


@dataclass
class ExtractionResult:
    """Result of extraction process"""
    success: bool
    data: Optional[ReceiptData] = None
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'success': self.success,
            'data': self.data.to_dict() if self.data else None,
            'error': self.error,
            'warnings': self.warnings
        }
