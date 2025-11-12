"""
Flask backend for receipt extraction web application
Provides REST API for uploading images and extracting receipt data
"""
import os
import sys
import logging
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
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'tif'}

# Initialize model manager
model_manager = ModelManager()


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET'])
def index():
    """Root endpoint - API information"""
    return jsonify({
        'service': 'Receipt Extraction API',
        'version': '1.0',
        'status': 'running',
        'endpoints': {
            'health': '/api/health',
            'models': '/api/models',
            'select_model': '/api/models/select (POST)',
            'extract': '/api/extract (POST)',
            'model_info': '/api/models/<model_id>/info',
            'unload_models': '/api/models/unload (POST)'
        },
        'documentation': 'Access /api/health for health check or /api/models to see available models'
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'receipt-extraction-api'
    })


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
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        logger.error(f"Extraction error: {e}", exc_info=True)
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
