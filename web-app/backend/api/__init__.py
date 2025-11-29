"""
API module for Receipt Extractor.

This module contains all API route blueprints for the application.
"""
from .receipts import receipts_bp, register_receipts_routes

__all__ = ['receipts_bp', 'register_receipts_routes']
