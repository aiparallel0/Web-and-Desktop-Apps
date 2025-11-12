"""
Pytest configuration and shared fixtures for Receipt Extractor tests.
"""

import sys
from pathlib import Path
import pytest

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'shared'))
sys.path.insert(0, str(project_root / 'web-app' / 'backend'))


@pytest.fixture
def sample_receipt_data():
    """Sample receipt data for testing."""
    return {
        "store": {
            "name": "Sample Store",
            "address": "123 Main St, City, State 12345",
            "phone": "(555) 123-4567"
        },
        "date": "2024-01-15",
        "items": [
            {
                "name": "Product A",
                "quantity": 2,
                "unit_price": 5.99,
                "total_price": 11.98
            },
            {
                "name": "Product B",
                "quantity": 1,
                "unit_price": 3.49,
                "total_price": 3.49
            }
        ],
        "totals": {
            "subtotal": 15.47,
            "tax": 1.24,
            "total": 16.71
        },
        "payment_method": "Credit Card",
        "category": "grocery"
    }


@pytest.fixture
def test_data_dir():
    """Path to test data directory."""
    return project_root / 'test_data'


@pytest.fixture
def sample_receipts_dir(test_data_dir):
    """Path to sample receipts directory."""
    return test_data_dir / 'receipts'


@pytest.fixture
def expected_outputs_dir(test_data_dir):
    """Path to expected outputs directory."""
    return test_data_dir / 'expected_outputs'
