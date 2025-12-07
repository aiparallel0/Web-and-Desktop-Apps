"""
Quick Extract API - No Authentication Required
Allows instant trial extractions for new users
"""

import os
import logging
import tempfile
from flask import Blueprint, request, jsonify
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.models.manager import ModelManager
from shared.utils.telemetry import get_tracer, set_span_attributes
from shared.utils.validation import validate_file_upload, sanitize_filename
from web.backend.security.rate_limiting import rate_limit

logger = logging.getLogger(__name__)

# Create blueprint
quick_extract_bp = Blueprint('quick_extract', __name__)


@quick_extract_bp.route('/api/quick-extract', methods=['POST'])
@rate_limit(requests=10, window=3600, error_message="Free tier rate limit exceeded. Upgrade to Pro for unlimited access.")
@validate_file_upload(param_name='image', max_size=10*1024*1024)  # 10MB limit for free tier
def quick_extract():
    """
    Quick extraction endpoint - No authentication required
    Allows free trial with rate limiting and input validation
    """
    tracer = get_tracer()
    with tracer.start_as_current_span("api.quick_extract") as span:
        temp_path = None
        try:
            # Get client IP
            ip_address = request.remote_addr or 'unknown'
            
            # Set span attributes
            set_span_attributes(span, {
                "operation.type": "quick_extract",
                "client.ip": ip_address,
                "request.authenticated": False
            })

            file = request.files['image']
            
            # Get optional model preference
            model_id = request.form.get('model_id')
            
            # Sanitize filename
            filename = sanitize_filename(file.filename)
            
            # Set file attributes
            set_span_attributes(span, {
                "file.name": filename,
                "file.size": len(file.read())
            })
            file.seek(0)  # Reset file pointer

            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
                temp_path = temp_file.name
                file.save(temp_path)

            # Initialize model manager (use default model for free tier)
            model_manager = ModelManager(max_loaded_models=2)

            # If no model specified, use fastest model (tesseract) for free tier
            if not model_id:
                # Get available models and select Tesseract (fastest)
                available_models = model_manager.get_available_models()
                tesseract_model = next(
                    (m for m in available_models if 'tesseract' in m['id'].lower()),
                    available_models[0] if available_models else None
                )
                if tesseract_model:
                    model_id = tesseract_model['id']
            
            # Set model in span
            set_span_attributes(span, {
                "model.id": model_id or "default"
            })

            # Process image
            logger.info(f"Quick extract: {filename} from {ip_address}")

            processor = model_manager.get_processor(model_id)
            result = processor.extract(temp_path)
            
            # Set result attributes
            set_span_attributes(span, {
                "extraction.success": result.success,
                "extraction.confidence": getattr(result.data, 'confidence_score', 0) if result.data else 0,
                "extraction.items_count": len(getattr(result.data, 'items', [])) if result.data else 0
            })

            # Add metadata
            response = result.to_dict()
            response['metadata'] = {
                'model_used': model_manager.get_current_model(),
                'processing_time': result.to_dict().get('processing_time', 0),
                'free_tier': True
            }

            return jsonify(response)

        except Exception as e:
            logger.error(f"Quick extract error: {e}", exc_info=True)
            span.record_exception(e)
            try:
                from opentelemetry.trace import Status, StatusCode
                span.set_status(Status(StatusCode.ERROR, str(e)))
            except ImportError:
                pass
            return jsonify({
                'success': False,
                'error': 'Extraction failed. Please try again with a different image.'
            }), 500
        
        finally:
            # Clean up temp file
            if temp_path:
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {e}")


@quick_extract_bp.route('/api/quick-extract/status', methods=['GET'])
def quick_extract_status():
    """
    Get current rate limit status for client
    """
    tracer = get_tracer()
    with tracer.start_as_current_span("api.quick_extract_status") as span:
        try:
            ip_address = request.remote_addr or 'unknown'
            
            set_span_attributes(span, {
                "operation.type": "rate_limit_status",
                "client.ip": ip_address
            })

            return jsonify({
                'success': True,
                'message': 'Rate limiting managed by backend middleware'
            })
        except Exception as e:
            logger.error(f"Status check error: {e}")
            span.record_exception(e)
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
