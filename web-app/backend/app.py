"""
Flask backend for receipt extraction web application
Provides REST API for uploading images and extracting receipt data
"""
import os
import sys
import logging
import time
import gc
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import tempfile

# Add shared modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from shared.models.model_manager import ModelManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for web frontend

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['REQUEST_TIMEOUT'] = 300  # 5 minutes max per request
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'tif'}

# Initialize model manager with resource limits
# Max 3 models loaded at once to prevent memory exhaustion
model_manager = ModelManager(max_loaded_models=3)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def safe_delete_temp_file(file_path: str, max_retries: int = 3):
    """
    Safely delete temporary file with Windows file locking handling

    Args:
        file_path: Path to temporary file to delete
        max_retries: Maximum number of deletion attempts (default 3)
    """
    if not os.path.exists(file_path):
        return

    for attempt in range(max_retries):
        try:
            # Force garbage collection to release file handles
            gc.collect()

            # Small delay on Windows to allow file handles to close
            if sys.platform == 'win32' and attempt > 0:
                time.sleep(0.1 * (attempt + 1))  # Exponential backoff: 0.1s, 0.2s, 0.3s

            os.unlink(file_path)
            logger.debug(f"Successfully deleted temp file: {file_path}")
            return

        except PermissionError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Temp file deletion attempt {attempt + 1} failed (retrying): {e}")
            else:
                # On final failure, log but don't crash - OS will clean up temp files eventually
                logger.error(f"Failed to delete temp file after {max_retries} attempts: {file_path}. "
                           f"OS will clean up on reboot. Error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error deleting temp file {file_path}: {e}")
            break


def create_error_response(error_message: str, error_type: str = 'UnknownError', status_code: int = 500, details: dict = None):
    """
    Create structured error response

    Args:
        error_message: Human-readable error message
        error_type: Type of error (e.g., 'ValidationError', 'ModelError', 'SystemError')
        status_code: HTTP status code
        details: Optional additional error details

    Returns:
        JSON response with error information
    """
    response = {
        'success': False,
        'error': {
            'type': error_type,
            'message': error_message,
            'timestamp': time.time()
        }
    }

    if details:
        response['error']['details'] = details

    return jsonify(response), status_code


# Global error handlers
@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large errors"""
    return create_error_response(
        f"File too large. Maximum file size is {app.config['MAX_CONTENT_LENGTH'] / (1024*1024):.0f}MB",
        error_type='FileTooLarge',
        status_code=413
    )


@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {error}")
    return create_error_response(
        'Internal server error occurred',
        error_type='InternalServerError',
        status_code=500
    )


@app.route('/', methods=['GET'])
def index():
    """Root endpoint - API information"""
    return jsonify({
        'service': 'Receipt Extraction API',
        'version': '1.1',
        'status': 'running',
        'endpoints': {
            'health': '/api/health',
            'models': '/api/models',
            'select_model': '/api/models/select (POST)',
            'extract': '/api/extract (POST)',
            'batch_extract': '/api/extract/batch (POST) - Extract with ALL models',
            'model_info': '/api/models/<model_id>/info',
            'unload_models': '/api/models/unload (POST)'
        },
        'documentation': 'Access /api/health for health check or /api/models to see available models'
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Enhanced health check endpoint with system diagnostics"""
    try:
        import psutil
        import platform

        # Get system resources
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Get model manager stats
        resource_stats = model_manager.get_resource_stats()

        health_data = {
            'status': 'healthy',
            'service': 'receipt-extraction-api',
            'version': '2.0',
            'timestamp': time.time(),

            # System info
            'system': {
                'platform': platform.system(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': round(memory.total / (1024**3), 2),
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'memory_percent_used': memory.percent,
                'disk_total_gb': round(disk.total / (1024**3), 2),
                'disk_free_gb': round(disk.free / (1024**3), 2),
                'disk_percent_used': disk.percent
            },

            # Model manager state
            'models': resource_stats
        }

        # Determine overall health status
        if memory.percent > 90:
            health_data['status'] = 'degraded'
            health_data['warnings'] = ['Memory usage critical (>90%)']
        elif memory.percent > 80:
            health_data['status'] = 'warning'
            health_data['warnings'] = ['Memory usage high (>80%)']

        return jsonify(health_data)

    except ImportError:
        # psutil not available, return basic health check
        return jsonify({
            'status': 'healthy',
            'service': 'receipt-extraction-api',
            'version': '2.0',
            'note': 'Install psutil for detailed system metrics'
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'service': 'receipt-extraction-api',
            'error': str(e)
        }), 500


@app.route('/api/models', methods=['GET'])
def get_models():
    """Get list of available models"""
    try:
        models = model_manager.get_available_models()
        current_model = model_manager.get_current_model()
        default_model = model_manager.get_default_model()

        return jsonify({
            'success': True,
            'models': models,
            'current_model': current_model,
            'default_model': default_model
        })
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/models/select', methods=['POST'])
def select_model():
    """Select a model for extraction"""
    try:
        data = request.get_json()
        model_id = data.get('model_id')

        if not model_id:
            return jsonify({
                'success': False,
                'error': 'model_id is required'
            }), 400

        success = model_manager.select_model(model_id)

        if success:
            return jsonify({
                'success': True,
                'model_id': model_id,
                'message': f'Model {model_id} selected successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Model {model_id} not found'
            }), 404

    except Exception as e:
        logger.error(f"Error selecting model: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/extract', methods=['POST'])
def extract_receipt():
    """Extract receipt data from uploaded image"""
    try:
        # Check if file is present
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image file provided'
            }), 400

        file = request.files['image']

        # Check if filename is empty
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        # Check if file type is allowed
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # Get optional model_id parameter
        model_id = request.form.get('model_id')

        # Save file to temporary location
        filename = secure_filename(file.filename)
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
            temp_path = temp_file.name
            file.save(temp_path)

        try:
            # Get processor for selected model
            processor = model_manager.get_processor(model_id)

            # Extract receipt data
            logger.info(f"Processing image with model: {model_manager.get_current_model()}")
            result = processor.extract(temp_path)

            # Return result
            return jsonify(result.to_dict())

        finally:
            # Clean up temporary file
            safe_delete_temp_file(temp_path)

    except Exception as e:
        logger.error(f"Extraction error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/extract/batch', methods=['POST'])
def extract_batch():
    """Extract receipt data using ALL models and return combined results"""
    try:
        # Check if file is present
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image file provided'
            }), 400

        file = request.files['image']

        # Check if filename is empty
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        # Check if file type is allowed
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # Save file to temporary location
        filename = secure_filename(file.filename)
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
            temp_path = temp_file.name
            file.save(temp_path)

        try:
            # Get all available models
            available_models = model_manager.get_available_models()
            logger.info(f"Running batch extraction with {len(available_models)} models")

            # Store results from all models
            batch_results = {
                'success': True,
                'image_filename': filename,
                'models_count': len(available_models),
                'results': {}
            }

            # Process image with each model
            for model_info in available_models:
                model_id = model_info['id']
                model_name = model_info['name']

                logger.info(f"Processing with model: {model_name} ({model_id})")

                try:
                    # Get processor for this model
                    processor = model_manager.get_processor(model_id)

                    # Extract receipt data
                    result = processor.extract(temp_path)

                    # Store result
                    batch_results['results'][model_id] = {
                        'model_name': model_name,
                        'model_id': model_id,
                        'extraction': result.to_dict()
                    }

                    logger.info(f"✓ {model_name}: {'Success' if result.success else 'Failed'}")

                except Exception as e:
                    # If one model fails, continue with others
                    logger.error(f"Model {model_name} failed: {e}")
                    batch_results['results'][model_id] = {
                        'model_name': model_name,
                        'model_id': model_id,
                        'extraction': {
                            'success': False,
                            'error': str(e)
                        }
                    }

            logger.info(f"Batch extraction complete: {len(batch_results['results'])} models processed")

            # Return combined results
            return jsonify(batch_results)

        finally:
            # Clean up temporary file
            safe_delete_temp_file(temp_path)

    except Exception as e:
        logger.error(f"Batch extraction error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/models/<model_id>/info', methods=['GET'])
def get_model_info(model_id):
    """Get detailed information about a specific model"""
    try:
        model_info = model_manager.get_model_info(model_id)

        if model_info:
            return jsonify({
                'success': True,
                'model': model_info
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Model {model_id} not found'
            }), 404

    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/models/unload', methods=['POST'])
def unload_models():
    """Unload all models from memory"""
    try:
        model_manager.unload_all_models()
        return jsonify({
            'success': True,
            'message': 'All models unloaded successfully'
        })
    except Exception as e:
        logger.error(f"Error unloading models: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    # Run development server
    logger.info("Starting Receipt Extraction API...")
    logger.info(f"Available models: {len(model_manager.get_available_models())}")
    app.run(host='0.0.0.0', port=5000, debug=True)
