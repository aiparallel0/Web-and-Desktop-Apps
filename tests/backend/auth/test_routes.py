"""
Tests for auth/routes.py - Authentication API routes
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import hashlib


class TestRegisterRoute:
    """Tests for /api/auth/register endpoint"""
    
    def test_register_missing_email(self, client):
        """Test register without email"""
        response = client.post('/api/auth/register', json={
            'password': 'SecurePass123!'
        })
        assert response.status_code == 400
    
    def test_register_invalid_email(self, client):
        """Test register with invalid email format"""
        response = client.post('/api/auth/register', json={
            'email': 'invalid-email',
            'password': 'SecurePass123!'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'Invalid email format' in data['error']
    
    def test_register_weak_password(self, client):
        """Test register with weak password"""
        response = client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'weak'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'does not meet requirements' in data['error']


class TestLoginRoute:
    """Tests for /api/auth/login endpoint"""
    
    def test_login_missing_credentials(self, client):
        """Test login without email or password"""
        response = client.post('/api/auth/login', json={})
        assert response.status_code == 400


class TestRefreshRoute:
    """Tests for /api/auth/refresh endpoint"""
    
    def test_refresh_missing_token(self, client):
        """Test refresh without token"""
        response = client.post('/api/auth/refresh', json={})
        assert response.status_code == 400


class TestLogoutRoute:
    """Tests for /api/auth/logout endpoint"""
    
    def test_logout_no_token(self, client):
        """Test logout without token still succeeds"""
        response = client.post('/api/auth/logout', json={})
        assert response.status_code == 200


class TestMeRoute:
    """Tests for /api/auth/me endpoint"""
    
    def test_me_missing_auth_header(self, client):
        """Test /me without authorization header"""
        response = client.get('/api/auth/me')
        assert response.status_code == 401
        data = response.get_json()
        assert 'Missing authorization header' in data['error']
    
    def test_me_invalid_auth_format(self, client):
        """Test /me with invalid auth format"""
        response = client.get('/api/auth/me', headers={
            'Authorization': 'InvalidFormat token'
        })
        assert response.status_code == 401
    
    def test_me_expired_token(self, client):
        """Test /me with expired token"""
        response = client.get('/api/auth/me', headers={
            'Authorization': 'Bearer expired-token-here'
        })
        assert response.status_code == 401


class TestChangePasswordRoute:
    """Tests for /api/auth/change-password endpoint"""
    
    def test_change_password_missing_auth(self, client):
        """Test change password without auth"""
        response = client.post('/api/auth/change-password', json={
            'current_password': 'old',
            'new_password': 'new'
        })
        assert response.status_code == 401

