"""
Tests for api/receipts.py - Receipts CRUD API routes
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import uuid


class TestListReceipts:
    """Tests for GET /api/receipts endpoint"""
    
    def test_list_receipts_no_auth(self, client):
        """Test listing receipts without authentication"""
        response = client.get('/api/receipts')
        assert response.status_code == 401
        data = response.get_json()
        assert 'Missing authorization header' in data['error']
    
    def test_list_receipts_invalid_auth_format(self, client):
        """Test listing receipts with invalid auth format"""
        response = client.get('/api/receipts', headers={
            'Authorization': 'InvalidFormat token'
        })
        assert response.status_code == 401
    
    def test_list_receipts_expired_token(self, client):
        """Test listing receipts with expired token"""
        response = client.get('/api/receipts', headers={
            'Authorization': 'Bearer expired-token-here'
        })
        assert response.status_code == 401


class TestGetReceipt:
    """Tests for GET /api/receipts/<id> endpoint"""
    
    def test_get_receipt_no_auth(self, client):
        """Test getting receipt without authentication"""
        response = client.get('/api/receipts/some-id')
        assert response.status_code == 401
    
    def test_get_receipt_invalid_format(self, client):
        """Test getting receipt with invalid auth format"""
        response = client.get('/api/receipts/some-id', headers={
            'Authorization': 'InvalidFormat'
        })
        assert response.status_code == 401


class TestDeleteReceipt:
    """Tests for DELETE /api/receipts/<id> endpoint"""
    
    def test_delete_receipt_no_auth(self, client):
        """Test deleting receipt without authentication"""
        response = client.delete('/api/receipts/some-id')
        assert response.status_code == 401


class TestUpdateReceipt:
    """Tests for PATCH /api/receipts/<id> endpoint"""
    
    def test_update_receipt_no_auth(self, client):
        """Test updating receipt without authentication"""
        response = client.patch('/api/receipts/some-id', json={
            'store_name': 'Updated Store'
        })
        assert response.status_code == 401


class TestReceiptStats:
    """Tests for GET /api/receipts/stats endpoint"""
    
    def test_stats_no_auth(self, client):
        """Test getting stats without authentication"""
        response = client.get('/api/receipts/stats')
        assert response.status_code == 401
