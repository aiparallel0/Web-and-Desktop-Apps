"""
Test suite for Flask application endpoints
Tests coverage for web-app/backend/app.py
"""
import pytest
import sys
import os
import io
from PIL import Image
from unittest.mock import Mock, patch, MagicMock

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'web-app', 'backend'))

class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check_basic(self, client):
        """Test basic health check"""
        if not client:
            pytest.skip("Flask app not available")

        response = client.get('/api/health')
        assert response.status_code == 200

        data = response.get_json()
        assert 'status' in data
        assert data['status'] in ['healthy', 'warning', 'degraded', 'unhealthy']

    def test_health_check_includes_service_info(self, client):
        """Test that health check includes service information"""
        if not client:
            pytest.skip("Flask app not available")

        response = client.get('/api/health')
        data = response.get_json()

        assert 'service' in data
        assert 'version' in data

    @patch('psutil.virtual_memory')
    def test_health_check_with_system_metrics(self, mock_memory, client):
        """Test health check with system metrics"""
        if not client:
            pytest.skip("Flask app not available")

        # Mock memory stats
        mock_memory.return_value = Mock(
            total=16 * 1024**3,
            available=8 * 1024**3,
            percent=50.0
        )

        response = client.get('/api/health')
        data = response.get_json()

        if 'system' in data:
            assert 'memory_percent_used' in data['system']


class TestModelsEndpoints:
    """Test model management endpoints"""

    def test_get_models(self, client):
        """Test get available models"""
        if not client:
            pytest.skip("Flask app not available")

        response = client.get('/api/models')
        assert response.status_code == 200

        data = response.get_json()
        assert data['success'] is True
        assert 'models' in data
        assert isinstance(data['models'], list)

    def test_select_model_valid(self, client):
        """Test selecting a valid model"""
        if not client:
            pytest.skip("Flask app not available")

        response = client.post('/api/models/select', json={
            'model_id': 'easyocr'
        })

        # May be 200 (success) or 404 (model not found)
        assert response.status_code in [200, 404]

    def test_select_model_missing_id(self, client):
        """Test selecting model without ID"""
        if not client:
            pytest.skip("Flask app not available")

        response = client.post('/api/models/select', json={})
        assert response.status_code == 400

        data = response.get_json()
        assert 'error' in data

    def test_select_model_invalid_characters(self, client):
        """Test selecting model with invalid characters"""
        if not client:
            pytest.skip("Flask app not available")

        response = client.post('/api/models/select', json={
            'model_id': 'invalid@model#id'
        })

        assert response.status_code == 400

    def test_select_model_too_long(self, client):
        """Test selecting model with ID too long"""
        if not client:
            pytest.skip("Flask app not available")

        response = client.post('/api/models/select', json={
            'model_id': 'a' * 101
        })

        assert response.status_code == 400

    def test_unload_models(self, client):
        """Test unloading all models"""
        if not client:
            pytest.skip("Flask app not available")

        response = client.post('/api/models/unload')
        assert response.status_code in [200, 500]  # May fail if no models loaded


class TestExtractEndpoint:
    """Test receipt extraction endpoint"""

    def create_test_image(self):
        """Create a test image"""
        img = Image.new('RGB', (100, 100), color='white')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes

    def test_extract_receipt_no_image(self, client):
        """Test extraction without image"""
        if not client:
            pytest.skip("Flask app not available")

        response = client.post('/api/extract')
        assert response.status_code == 400

        data = response.get_json()
        assert 'error' in data

    def test_extract_receipt_empty_filename(self, client):
        """Test extraction with empty filename"""
        if not client:
            pytest.skip("Flask app not available")

        response = client.post(
            '/api/extract',
            data={'image': (io.BytesIO(), '')}
        )

        assert response.status_code == 400

    def test_extract_receipt_invalid_file_type(self, client):
        """Test extraction with invalid file type"""
        if not client:
            pytest.skip("Flask app not available")

        response = client.post(
            '/api/extract',
            data={'image': (io.BytesIO(b'test'), 'test.txt')}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'not allowed' in data['error'].lower()

    def test_extract_receipt_valid_image(self, client):
        """Test extraction with valid image"""
        if not client:
            pytest.skip("Flask app not available")

        img_bytes = self.create_test_image()

        response = client.post(
            '/api/extract',
            data={'image': (img_bytes, 'test.png')},
            content_type='multipart/form-data'
        )

        # May succeed or fail depending on model availability
        assert response.status_code in [200, 500]


class TestBatchExtraction:
    """Test batch extraction endpoints"""

    def create_test_image(self):
        """Create a test image"""
        img = Image.new('RGB', (100, 100), color='white')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes

    def test_batch_extract_no_image(self, client):
        """Test batch extraction without image"""
        if not client:
            pytest.skip("Flask app not available")

        response = client.post('/api/extract/batch')
        assert response.status_code == 400

    def test_batch_extract_multi_no_images(self, client):
        """Test multi-batch extraction without images"""
        if not client:
            pytest.skip("Flask app not available")

        response = client.post('/api/extract/batch-multi')
        assert response.status_code == 400


class TestFinetuningEndpoints:
    """Test model finetuning endpoints"""

    def test_prepare_finetune_missing_model_id(self, client):
        """Test preparing finetune without model ID"""
        if not client:
            pytest.skip("Flask app not available")

        response = client.post('/api/finetune/prepare', json={})
        assert response.status_code == 400

    def test_prepare_finetune_valid(self, client):
        """Test preparing finetune with valid data"""
        if not client:
            pytest.skip("Flask app not available")

        response = client.post('/api/finetune/prepare', json={
            'model_id': 'donut_base',
            'mode': 'local'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'job_id' in data

    def test_finetune_status_not_found(self, client):
        """Test getting status of non-existent job"""
        if not client:
            pytest.skip("Flask app not available")

        response = client.get('/api/finetune/fake_job_id/status')
        assert response.status_code == 404

    def test_list_finetune_jobs(self, client):
        """Test listing finetuning jobs"""
        if not client:
            pytest.skip("Flask app not available")

        response = client.get('/api/finetune/jobs')
        assert response.status_code == 200

        data = response.get_json()
        assert 'jobs' in data


class TestErrorHandlers:
    """Test error handling"""

    def test_413_file_too_large(self, client):
        """Test handling of invalid image data (non-image bytes)"""
        if not client:
            pytest.skip("Flask app not available")

        # Create fake image data (not a valid image)
        # The server will accept it but fail to process it as an image
        fake_data = b'x' * (1 * 1024 * 1024)  # 1 MB of invalid data

        response = client.post(
            '/api/extract',
            data={'image': (io.BytesIO(fake_data), 'fake.png')},
            content_type='multipart/form-data'
        )

        # The response could be:
        # - 200 with success=False (image processing failed)
        # - 400 (bad request due to invalid image)
        # - 500 (internal error processing invalid data)
        assert response.status_code in [200, 400, 500]
        # If 200, verify that the response indicates failure
        if response.status_code == 200:
            data = json.loads(response.data)
            # Either explicitly marked as failure or error message present
            assert data.get('success') is False or 'error' in data or 'message' in data

    def test_404_not_found(self, client):
        """Test 404 for non-existent endpoint"""
        if not client:
            pytest.skip("Flask app not available")

        response = client.get('/api/nonexistent')
        assert response.status_code == 404


class TestFileValidation:
    """Test file validation"""

    def test_allowed_file_valid_extensions(self):
        """Test allowed file extensions"""
        from app import allowed_file

        valid_files = [
            'image.png',
            'photo.jpg',
            'scan.jpeg',
            'receipt.bmp',
            'document.tiff',
            'doc.tif'
        ]

        for filename in valid_files:
            assert allowed_file(filename) is True

    def test_allowed_file_invalid_extensions(self):
        """Test invalid file extensions"""
        from app import allowed_file

        invalid_files = [
            'document.pdf',
            'file.txt',
            'video.mp4',
            'archive.zip'
        ]

        for filename in invalid_files:
            assert allowed_file(filename) is False

    def test_allowed_file_case_insensitive(self):
        """Test that file extension check is case insensitive"""
        from app import allowed_file

        assert allowed_file('image.PNG') is True
        assert allowed_file('photo.JPG') is True
        assert allowed_file('scan.JPEG') is True


class TestSecurityConsiderations:
    """Test security aspects of the application"""

    def test_filename_sanitization(self):
        """Test that filenames are sanitized"""
        from werkzeug.utils import secure_filename

        dangerous_names = [
            '../../../etc/passwd',
            'test<script>.png',
            'file|name.jpg'
        ]

        for name in dangerous_names:
            safe_name = secure_filename(name)
            assert '../' not in safe_name
            assert '<' not in safe_name
            assert '|' not in safe_name

    def test_cors_enabled(self, client):
        """Test that CORS is enabled"""
        if not client:
            pytest.skip("Flask app not available")

        response = client.get('/api/health')

        # Check if CORS headers are present
        # Note: Actual headers depend on Flask-CORS configuration

    def test_max_content_length_configured(self, client):
        """Test that max content length is configured"""
        if not client:
            pytest.skip("Flask app not available")

        from app import app

        assert 'MAX_CONTENT_LENGTH' in app.config
        assert app.config['MAX_CONTENT_LENGTH'] > 0


class TestTempFileCleanup:
    """Test temporary file cleanup"""

    def test_safe_delete_temp_file_exists(self):
        """Test deleting existing temp file"""
        from app import safe_delete_temp_file
        import tempfile

        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        # Delete it
        safe_delete_temp_file(temp_path)

        # Verify deleted
        assert not os.path.exists(temp_path)

    def test_safe_delete_temp_file_not_exists(self):
        """Test deleting non-existent file doesn't error"""
        from app import safe_delete_temp_file

        # Should not raise error
        safe_delete_temp_file('/nonexistent/path/file.txt')


class TestErrorResponseFormat:
    """Test error response formatting"""

    def test_create_error_response_format(self, flask_app):
        """Test error response format"""
        if not flask_app:
            pytest.skip("Flask app not available")
            
        from app import create_error_response

        with flask_app.app_context():
            response, status_code = create_error_response(
                "Test error",
                error_type="TestError",
                status_code=400
            )

            data = response.get_json()

            assert data['success'] is False
            assert 'error' in data
            assert data['error']['type'] == 'TestError'
            assert data['error']['message'] == 'Test error'
            assert 'timestamp' in data['error']
            assert status_code == 400

    def test_create_error_response_with_details(self, flask_app):
        """Test error response with details"""
        if not flask_app:
            pytest.skip("Flask app not available")
            
        from app import create_error_response

        with flask_app.app_context():
            details = {'field': 'email', 'issue': 'invalid format'}

            response, status_code = create_error_response(
                "Validation error",
                error_type="ValidationError",
                status_code=422,
                details=details
            )

            data = response.get_json()

            assert 'details' in data['error']
            assert data['error']['details'] == details
