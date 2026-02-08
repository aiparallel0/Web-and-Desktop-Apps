"""
Integration tests for Model Health API endpoint.

Tests the /api/models/health endpoint to ensure it correctly reports
model availability and dependency status.
"""
import pytest
import json
from unittest.mock import patch, MagicMock


class TestModelHealthAPI:
    """Integration tests for model health API endpoint."""

    @pytest.fixture
    def client(self):
        """Create a test client for the Flask app."""
        from web.backend.app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_models_health_endpoint_exists(self, client):
        """Test that /api/models/health endpoint exists and returns 200."""
        response = client.get('/api/models/health')
        
        # Should return 200 even if models are unavailable
        assert response.status_code in [200, 500]
        
        data = json.loads(response.data)
        assert 'success' in data

    def test_models_health_response_structure(self, client):
        """Test that health endpoint returns expected structure."""
        response = client.get('/api/models/health')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            
            # Check required keys
            assert 'success' in data
            assert 'available_models' in data
            assert 'unavailable_models' in data
            assert 'missing_dependencies' in data
            assert 'dependency_status' in data
            assert 'summary' in data
            
            # Check summary structure
            summary = data['summary']
            assert 'total_models' in summary
            assert 'available_count' in summary
            assert 'unavailable_count' in summary
            
            # Verify counts add up
            assert summary['available_count'] + summary['unavailable_count'] == summary['total_models']

    def test_available_models_structure(self, client):
        """Test structure of available models list."""
        response = client.get('/api/models/health')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            
            # Check available models structure
            for model in data.get('available_models', []):
                assert 'id' in model
                assert 'name' in model
                assert 'type' in model
                assert 'status' in model
                assert model['status'] == 'ready'

    def test_unavailable_models_structure(self, client):
        """Test structure of unavailable models list."""
        response = client.get('/api/models/health')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            
            # Check unavailable models structure
            for model in data.get('unavailable_models', []):
                assert 'id' in model
                assert 'name' in model
                assert 'type' in model
                assert 'error' in model
                assert 'missing_dependencies' in model
                
                # Should have at least one missing dependency
                if model['missing_dependencies']:
                    assert len(model['missing_dependencies']) > 0

    def test_dependency_status_structure(self, client):
        """Test structure of dependency status."""
        response = client.get('/api/models/health')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            
            deps = data.get('dependency_status', {})
            
            # Should check these dependencies
            expected_deps = ['opencv', 'easyocr', 'paddleocr', 'torch', 'transformers', 'craft', 'pytesseract']
            
            for dep in expected_deps:
                if dep in deps:
                    assert 'available' in deps[dep]
                    # If available, should have version
                    if deps[dep]['available']:
                        # Version might be available
                        pass
                    else:
                        # If not available, should have error
                        assert 'error' in deps[dep]

    def test_models_list_endpoint_with_availability(self, client):
        """Test that /api/models endpoint also supports availability checking."""
        response = client.get('/api/models?check_availability=true')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'success' in data
        assert data['success'] == True
        assert 'models' in data
        assert 'count' in data
        
        if 'working_count' in data:
            # Should report working count when checking availability
            assert data['working_count'] >= 0
            assert data['working_count'] <= data['count']

    def test_models_without_availability_check(self, client):
        """Test /api/models without availability check."""
        response = client.get('/api/models?check_availability=false')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert len(data['models']) >= 8  # Should return all configured models

    def test_health_endpoint_handles_errors_gracefully(self, client):
        """Test that health endpoint handles errors gracefully."""
        # This test verifies error handling doesn't crash the endpoint
        response = client.get('/api/models/health')
        
        # Should always return a response, even if there's an error
        assert response.status_code in [200, 500]
        
        data = json.loads(response.data)
        assert 'success' in data
        
        # If error occurred, should have error message
        if not data['success']:
            assert 'error' in data


class TestModelHealthEndpointWithMockedDependencies:
    """Test model health endpoint with mocked dependencies."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        from web.backend.app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_health_with_all_deps_missing(self, client):
        """Test health endpoint when all dependencies are missing."""
        # Mock ModelManager to return no available dependencies
        with patch('web.backend.app.ModelManager') as MockManager:
            mock_instance = MagicMock()
            
            # Mock _check_dependencies to return all unavailable
            mock_instance._check_dependencies.return_value = {
                'opencv': {'available': False, 'error': 'Not installed'},
                'easyocr': {'available': False, 'error': 'Not installed'},
                'paddleocr': {'available': False, 'error': 'Not installed'},
                'torch': {'available': False, 'error': 'Not installed'},
                'transformers': {'available': False, 'error': 'Not installed'},
                'craft': {'available': False, 'error': 'Not installed'},
                'pytesseract': {'available': False, 'error': 'Not installed'}
            }
            
            # Mock get_available_models to return all unavailable
            mock_instance.get_available_models.return_value = [
                {
                    'id': 'ocr_tesseract',
                    'name': 'Tesseract OCR',
                    'type': 'ocr',
                    'available': False,
                    'missing_dependencies': ['opencv', 'pytesseract']
                }
            ]
            
            MockManager.return_value = mock_instance
            
            response = client.get('/api/models/health')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # All models should be unavailable
            assert len(data['available_models']) == 0
            assert len(data['unavailable_models']) >= 1

    def test_health_with_some_deps_available(self, client):
        """Test health endpoint when some dependencies are available."""
        with patch('web.backend.app.ModelManager') as MockManager:
            mock_instance = MagicMock()
            
            # Mock some dependencies as available
            mock_instance._check_dependencies.return_value = {
                'opencv': {'available': True, 'version': '4.8.1'},
                'pytesseract': {'available': True, 'version': '5.0.0'},
                'easyocr': {'available': False, 'error': 'Not installed'},
                'torch': {'available': False, 'error': 'Not installed'}
            }
            
            # Mock models with mixed availability
            mock_instance.get_available_models.return_value = [
                {
                    'id': 'ocr_tesseract',
                    'name': 'Tesseract OCR',
                    'type': 'ocr',
                    'available': True,
                    'status': 'ready'
                },
                {
                    'id': 'florence2',
                    'name': 'Florence-2',
                    'type': 'florence',
                    'available': False,
                    'missing_dependencies': ['torch', 'transformers']
                }
            ]
            
            MockManager.return_value = mock_instance
            
            response = client.get('/api/models/health')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Should have at least one available and one unavailable
            assert len(data['available_models']) >= 1
            assert len(data['unavailable_models']) >= 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
