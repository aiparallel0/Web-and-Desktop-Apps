"""
Quick Extract API - No Authentication Required
Allows instant trial extractions for new users
"""

import os
import logging
import time
import tempfile
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.models.manager import ModelManager

logger = logging.getLogger(__name__)

# Create blueprint
quick_extract_bp = Blueprint('quick_extract', __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'tif'}

# Rate limiting storage (in-memory, simple implementation)
# In production, use Redis or similar
rate_limit_storage = {}
RATE_LIMIT_WINDOW = 3600  # 1 hour
FREE_TIER_LIMIT = 10  # 10 extractions per hour

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_rate_limit(ip_address: str) -> tuple:
    """
    Check if IP address has exceeded rate limit.
    Returns (allowed: bool, remaining: int)
    """
    now = time.time()

    # Clean old entries
    expired_ips = [ip for ip, data in rate_limit_storage.items()
                   if now - data['timestamp'] > RATE_LIMIT_WINDOW]
    for ip in expired_ips:
        del rate_limit_storage[ip]

    # Check current IP
    if ip_address not in rate_limit_storage:
        rate_limit_storage[ip_address] = {
            'count': 0,
            'timestamp': now
        }

    data = rate_limit_storage[ip_address]

    # Reset if window expired
    if now - data['timestamp'] > RATE_LIMIT_WINDOW:
        data['count'] = 0
        data['timestamp'] = now

    # Check limit
    if data['count'] >= FREE_TIER_LIMIT:
        return False, 0

    return True, FREE_TIER_LIMIT - data['count']

def increment_rate_limit(ip_address: str):
    """Increment extraction count for IP address."""
    if ip_address in rate_limit_storage:
        rate_limit_storage[ip_address]['count'] += 1

@quick_extract_bp.route('/api/quick-extract', methods=['POST'])
def quick_extract():
    """
    Quick extraction endpoint - No authentication required
    Allows free trial with rate limiting
    """
    try:
        # Get client IP
        ip_address = request.remote_addr or 'unknown'

        # Check rate limit
        allowed, remaining = check_rate_limit(ip_address)
        if not allowed:
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded',
                'message': f'Free tier allows {FREE_TIER_LIMIT} extractions per hour. Please wait or upgrade to Pro.',
                'upgrade_url': '/pricing.html'
            }), 429

        # Validate request
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image file provided'
            }), 400

        file = request.files['image']

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'File type not allowed. Supported: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # Get optional model preference
        model_id = request.form.get('model_id')

        # Save file temporarily
        filename = secure_filename(file.filename)
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
            temp_path = temp_file.name
            file.save(temp_path)

        try:
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

            # Process image
            logger.info(f"Quick extract: {filename} from {ip_address} (remaining: {remaining - 1})")

            processor = model_manager.get_processor(model_id)
            result = processor.extract(temp_path)

            # Increment rate limit
            increment_rate_limit(ip_address)

            # Add metadata
            response = result.to_dict()
            response['metadata'] = {
                'model_used': model_manager.get_current_model(),
                'processing_time': result.to_dict().get('processing_time', 0),
                'extractions_remaining': remaining - 1,
                'free_tier': True,
                'upgrade_message': f'You have {remaining - 1} free extractions remaining this hour.'
            }

            return jsonify(response)

        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")

    except Exception as e:
        logger.error(f"Quick extract error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@quick_extract_bp.route('/api/quick-extract/status', methods=['GET'])
def quick_extract_status():
    """
    Get current rate limit status for client
    """
    try:
        ip_address = request.remote_addr or 'unknown'
        allowed, remaining = check_rate_limit(ip_address)

        return jsonify({
            'success': True,
            'rate_limit': {
                'allowed': allowed,
                'remaining': remaining,
                'limit': FREE_TIER_LIMIT,
                'window_seconds': RATE_LIMIT_WINDOW
            }
        })
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
