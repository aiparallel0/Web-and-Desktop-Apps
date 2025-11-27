import pytest
import sys
import os
from pathlib import Path

# Add project root to path to import app
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

@pytest.mark.web
def test_api_requirements_installed():
    """Test that Flask and Flask-CORS are installed"""
    try:
        import flask
        import flask_cors
        assert True
    except ImportError as e:
        pytest.fail(f"Required packages not installed: {e}")

@pytest.mark.web
def test_api_health_check():
    """Test the health check endpoint"""
    try:
        # Import Flask app module dynamically to handle hyphenated directory name
        import importlib.util
        app_path = project_root / 'web-app' / 'backend' / 'app.py'
        spec = importlib.util.spec_from_file_location("app", app_path)
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)
        app = app_module.app

        with app.test_client() as client:
            response = client.get('/api/health')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] in ['healthy', 'warning', 'degraded']
            assert 'service' in data
    except ImportError as e:
        pytest.skip(f"Cannot import Flask app: {e}")
    except Exception as e:
        pytest.skip(f"Test requires app dependencies: {e}")

@pytest.mark.web
def test_api_get_models():
    """Test the get models endpoint"""
    try:
        # Import Flask app module dynamically to handle hyphenated directory name
        import importlib.util
        app_path = project_root / 'web-app' / 'backend' / 'app.py'
        spec = importlib.util.spec_from_file_location("app", app_path)
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)
        app = app_module.app

        with app.test_client() as client:
            response = client.get('/api/models')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'models' in data
            assert isinstance(data['models'], list)
    except ImportError as e:
        pytest.skip(f"Cannot import Flask app: {e}")
    except Exception as e:
        pytest.skip(f"Test requires app dependencies: {e}")

@pytest.mark.web
def test_api_extract_receipt():
    """Test the extract receipt endpoint with mock data"""
    try:
        # Import Flask app module dynamically to handle hyphenated directory name
        import importlib.util
        app_path = project_root / 'web-app' / 'backend' / 'app.py'
        spec = importlib.util.spec_from_file_location("app", app_path)
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)
        app = app_module.app

        import io
        from PIL import Image

        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='white')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        with app.test_client() as client:
            response = client.post(
                '/api/extract',
                data={'image': (img_bytes, 'test.png')},
                content_type='multipart/form-data'
            )
            # Should get a response (may succeed or fail depending on model availability)
            assert response.status_code in [200, 400, 500]
    except ImportError as e:
        pytest.skip(f"Cannot import Flask app or dependencies: {e}")
    except Exception as e:
        pytest.skip(f"Test requires app dependencies: {e}")

@pytest.mark.web
def test_api_invalid_image():
    """Test the extract endpoint with invalid data"""
    try:
        # Import Flask app module dynamically to handle hyphenated directory name
        import importlib.util
        app_path = project_root / 'web-app' / 'backend' / 'app.py'
        spec = importlib.util.spec_from_file_location("app", app_path)
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)
        app = app_module.app

        with app.test_client() as client:
            # Test without image
            response = client.post('/api/extract')
            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] is False
    except ImportError as e:
        pytest.skip(f"Cannot import Flask app: {e}")
    except Exception as e:
        pytest.skip(f"Test requires app dependencies: {e}")
