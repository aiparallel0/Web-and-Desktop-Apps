"""
=============================================================================
RECEIPT EXTRACTOR - MAIN FLASK APPLICATION
=============================================================================

Main Flask application entry point with blueprint registration, middleware,
error handlers, and health check endpoints.

This is the primary application file that combines all modules and serves
both the REST API and frontend static files.

Architecture:
    - Blueprint-based modular route system
    - SQLAlchemy database with connection pooling
    - JWT authentication with refresh tokens
    - OpenTelemetry instrumentation
    - Rate limiting and security headers
    - Frontend SPA serving with catch-all routing

Usage:
    Development: python app.py
    Production:  gunicorn web.backend.app:app
=============================================================================
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

# Configure Flask
from flask import Flask, jsonify, request, Response, g, send_from_directory
from flask_cors import CORS

# Import configuration
from web.backend.config import get_config

# Setup logging - Configure before any logging calls
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# FLASK APPLICATION INITIALIZATION
# =============================================================================

# Configure Flask to serve frontend static files
app = Flask(
    __name__,
    static_folder='../frontend',  # Serve from web/frontend/
    static_url_path=''  # Serve at root
)

# Load configuration
config = get_config()
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['DEBUG'] = config.DEBUG
app.config['TESTING'] = config.TESTING

# Enable CORS
CORS(app)

# =============================================================================
# FRONTEND SERVING ROUTES (Must be defined first)
# =============================================================================

# Serve index.html at root
@app.route('/')
def serve_frontend():
    """Serve the frontend index.html at root URL."""
    return app.send_static_file('index.html')

# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

try:
    from web.backend.database import init_db, get_engine
    
    # Check if DATABASE_URL is configured
    import os
    database_url = os.environ.get('DATABASE_URL', '').strip()
    
    if database_url and not database_url.startswith('postgresql://localhost'):
        # Only attempt initialization if we have a proper database URL
        init_db()
        logger.info("Database initialized successfully")
    else:
        logger.warning("DATABASE_URL not configured or using localhost - skipping database initialization")
        logger.warning("Database-dependent features will be unavailable")
except Exception as e:
    logger.warning(f"Database initialization failed: {e}")
    logger.warning("Continuing without database - core API functionality will still work")
    # Continue anyway - OCR routes work without DB

# =============================================================================
# TELEMETRY & MONITORING SETUP
# =============================================================================

try:
    from web.backend.telemetry.otel_config import setup_telemetry
    setup_telemetry(app)
    logger.info("OpenTelemetry instrumentation enabled")
except ImportError:
    logger.info("OpenTelemetry not available - skipping instrumentation")
except Exception as e:
    logger.warning(f"Telemetry setup failed: {e}")

# =============================================================================
# SECURITY MIDDLEWARE
# =============================================================================

try:
    from web.backend.security.headers import setup_security_headers
    setup_security_headers(app)
    logger.info("Security headers configured")
except ImportError:
    logger.warning("Security headers module not available")
except Exception as e:
    logger.warning(f"Security headers setup failed: {e}")

# =============================================================================
# BLUEPRINT REGISTRATION
# =============================================================================

# Authentication blueprints
try:
    from web.backend.routes import auth_bp
    app.register_blueprint(auth_bp)
    logger.info("Registered auth_bp")
except ImportError as e:
    logger.warning(f"Could not import auth_bp: {e}")

try:
    from web.backend.enhanced_auth_routes import enhanced_auth_bp
    app.register_blueprint(enhanced_auth_bp)
    logger.info("Registered enhanced_auth_bp")
except ImportError as e:
    logger.warning(f"Could not import enhanced_auth_bp: {e}")

# Database receipts blueprint
try:
    from web.backend.database import receipts_bp
    app.register_blueprint(receipts_bp)
    logger.info("Registered receipts_bp")
except ImportError as e:
    logger.warning(f"Could not import receipts_bp: {e}")

# Analytics blueprint
try:
    from web.backend.analytics_routes import analytics_bp
    app.register_blueprint(analytics_bp)
    logger.info("Registered analytics_bp")
except ImportError as e:
    logger.warning(f"Could not import analytics_bp: {e}")

# Billing blueprint
try:
    from web.backend.billing.routes import billing_bp
    app.register_blueprint(billing_bp)
    logger.info("Registered billing_bp")
except ImportError as e:
    logger.warning(f"Could not import billing_bp: {e}")

# Marketing blueprint
try:
    from web.backend.marketing.routes import marketing_bp
    app.register_blueprint(marketing_bp)
    logger.info("Registered marketing_bp")
except ImportError as e:
    logger.warning(f"Could not import marketing_bp: {e}")

# Usage tracking blueprint
try:
    from web.backend.usage_routes import usage_bp
    app.register_blueprint(usage_bp)
    logger.info("Registered usage_bp")
except ImportError as e:
    logger.warning(f"Could not import usage_bp: {e}")

# API blueprints
try:
    from web.backend.api.quick_extract import quick_extract_bp
    app.register_blueprint(quick_extract_bp)
    logger.info("Registered quick_extract_bp")
except ImportError as e:
    logger.warning(f"Could not import quick_extract_bp: {e}")

# =============================================================================
# CORE API ROUTES
# =============================================================================

@app.route('/api', methods=['GET'])
def api_root() -> Response:
    """API root endpoint with documentation."""
    return jsonify({
        'service': 'Receipt Extraction API',
        'version': '2.0',
        'status': 'running',
        'endpoints': {
            'health': '/api/health',
            'ready': '/api/ready',
            'version': '/api/version',
            'database_health': '/api/database/health',
            'models': '/api/models',
            'select_model': '/api/models/select (POST)',
            'extract': '/api/extract (POST)',
            'batch_extract': '/api/extract/batch (POST)',
            'model_info': '/api/models/<model_id>/info',
            'unload_models': '/api/models/unload (POST)'
        },
        'documentation': 'Visit /api/health for health check or /api/models to see available models'
    })

@app.route('/api/health', methods=['GET'])
def health_check() -> Response:
    """
    Basic health check endpoint.
    Returns 200 if the application is running.
    """
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'service': 'receipt-extractor',
            'version': '2.0'
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

@app.route('/api/ready', methods=['GET'])
def readiness_check() -> Response:
    """
    Readiness check for Railway/Kubernetes.
    Always returns 200 if app is running - database issues are reported but don't fail the check.
    """
    try:
        from sqlalchemy import text
        
        checks = {
            'app': 'ok',
            'database': 'checking...',
            'config': 'ok'
        }
        
        # Check database connection (non-blocking)
        try:
            engine = get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            checks['database'] = 'ok'
        except Exception as e:
            checks['database'] = f'degraded: {str(e)[:100]}'
            logger.warning(f"Database check failed (non-critical): {e}")
        
        # Always return 200 if app is running
        return jsonify({
            'status': 'ready',
            'checks': checks,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'note': 'App is running. Database issues are non-fatal for this check.'
        }), 200
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 503

@app.route('/api/version', methods=['GET'])
def get_version() -> Response:
    """Get API version information."""
    return jsonify({
        'version': '2.0',
        'service': 'receipt-extractor',
        'environment': config.FLASK_ENV
    })

# =============================================================================
# MODEL MANAGEMENT ROUTES
# =============================================================================

@app.route('/api/models', methods=['GET'])
def list_models() -> Response:
    """List available OCR/AI models."""
    try:
        from shared.models.manager import ModelManager
        
        manager = ModelManager()
        models = manager.get_available_models()
        
        return jsonify({
            'success': True,
            'models': models,
            'count': len(models)
        })
    except Exception as e:
        logger.error(f"Failed to list models: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/models/select', methods=['POST'])
def select_model() -> Response:
    """Select a specific model for extraction."""
    try:
        data = request.get_json()
        model_id = data.get('model_id')
        
        if not model_id:
            return jsonify({
                'success': False,
                'error': 'model_id is required'
            }), 400
        
        from shared.models.manager import ModelManager
        manager = ModelManager()
        
        # Validate model exists
        available_models = manager.get_available_models()
        available_model_ids = [m['id'] for m in available_models]
        if model_id not in available_model_ids:
            return jsonify({
                'success': False,
                'error': f'Model {model_id} not found'
            }), 404
        
        return jsonify({
            'success': True,
            'model_id': model_id,
            'message': f'Model {model_id} selected'
        })
        
    except Exception as e:
        logger.error(f"Model selection failed: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/models/<model_id>/info', methods=['GET'])
def get_model_info(model_id: str) -> Response:
    """Get detailed information about a specific model."""
    try:
        from shared.models.manager import ModelManager
        
        manager = ModelManager()
        info = manager.get_model_info(model_id)
        
        if not info:
            return jsonify({
                'success': False,
                'error': f'Model {model_id} not found'
            }), 404
        
        return jsonify({
            'success': True,
            'model_id': model_id,
            'info': info
        })
        
    except Exception as e:
        logger.error(f"Failed to get model info: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/models/unload', methods=['POST'])
def unload_models() -> Response:
    """Unload models from memory to free resources."""
    try:
        from shared.models.manager import ModelManager
        
        manager = ModelManager()
        manager.unload_all_models()
        
        return jsonify({
            'success': True,
            'message': 'All models unloaded successfully'
        })
        
    except Exception as e:
        logger.error(f"Failed to unload models: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# =============================================================================
# EXTRACTION ROUTES
# =============================================================================

@app.route('/api/extract', methods=['POST'])
def extract_receipt() -> Response:
    """
    Extract text from a receipt image.
    
    Request:
        - file: Image file (multipart/form-data)
        - model_id: Model to use (optional, default: easyocr)
    
    Returns:
        DetectionResult with extracted text and metadata
    """
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Empty filename'
            }), 400
        
        # Get model_id from form data or use default
        model_id = request.form.get('model_id', 'easyocr')
        
        # Save file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            # Process with model
            from shared.models.engine import process_receipt
            result = process_receipt(tmp_path, model_id)
            
            # Clean up temp file
            os.unlink(tmp_path)
            
            return jsonify(result.to_dict())
            
        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/extract/batch', methods=['POST'])
def batch_extract() -> Response:
    """
    Extract text from a receipt using ALL available models.
    Returns results from all models for comparison.
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Empty filename'
            }), 400
        
        # Save file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            # Process with all models
            from shared.models.manager import ModelManager
            manager = ModelManager()
            
            results = {}
            models = manager.get_available_models()
            model_ids = [m['id'] for m in models]
            
            for model_id in model_ids:
                try:
                    from shared.models.engine import process_receipt
                    result = process_receipt(tmp_path, model_id)
                    results[model_id] = result.to_dict()
                except Exception as e:
                    logger.warning(f"Model {model_id} failed: {e}")
                    results[model_id] = {
                        'success': False,
                        'error': str(e)
                    }
            
            # Clean up temp file
            os.unlink(tmp_path)
            
            return jsonify({
                'success': True,
                'results': results,
                'models_tested': len(models)
            })
            
        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
        
    except Exception as e:
        logger.error(f"Batch extraction failed: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# =============================================================================
# DATABASE HEALTH CHECK ENDPOINT
# =============================================================================

@app.route('/api/database/health', methods=['GET'])
def database_health():
    """Check database connection health and pool status."""
    try:
        from web.backend.database import check_database_health
        
        health_info = check_database_health()
        status_code = 200 if health_info.get('status') == 'healthy' else 503
        
        return jsonify(health_info), status_code
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}", exc_info=True)
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'error_type': type(e).__name__
        }), 503

# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors - return JSON for API routes, HTML for frontend."""
    if request.path.startswith('/api'):
        return jsonify({
            'error': 'Not found',
            'path': request.path
        }), 404
    # For non-API routes, let the catch-all handle it (SPA routing)
    return serve_frontend()

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify({
        'error': 'Internal server error',
        'message': str(error)
    }), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {e}", exc_info=True)
    
    # API routes return JSON
    if request.path.startswith('/api'):
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500
    
    # Frontend routes return 500 page
    return jsonify({
        'error': 'Internal server error'
    }), 500

# =============================================================================
# CATCH-ALL ROUTE FOR SPA (MUST BE LAST)
# =============================================================================

@app.route('/<path:path>')
def serve_static_file(path):
    """
    Catch-all route for SPA routing.
    Serves static files if they exist, otherwise returns index.html.
    This MUST be the last route defined to avoid intercepting API routes.
    """
    # Skip API routes (they should already be handled)
    if path.startswith('api/'):
        return jsonify({'error': 'API endpoint not found'}), 404
    
    # Try to serve requested file
    file_path = os.path.join(app.static_folder, path)
    if os.path.exists(file_path):
        return app.send_static_file(path)
    
    # Fall back to index.html for SPA routing
    return app.send_static_file('index.html')

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == '__main__':
    # Startup validation
    logger.info("="*70)
    logger.info("RECEIPT EXTRACTOR API - STARTING UP")
    logger.info("="*70)
    
    # Validate database configuration
    try:
        from web.backend.database import validate_database_config
        validate_database_config()
    except Exception as e:
        logger.error(f"Startup validation failed: {e}")
        logger.error("Fix the errors above and restart the application")
        sys.exit(1)
    
    logger.info("✅ All startup checks passed")
    logger.info(f"🚀 Starting server on port {os.environ.get('PORT', 5000)}")
    logger.info("="*70)
    
    # Development server
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    logger.info(f"Starting Flask development server on {host}:{port}")
    logger.info(f"Environment: {config.FLASK_ENV}")
    logger.info(f"Debug mode: {config.DEBUG}")
    
    app.run(
        host=host,
        port=port,
        debug=config.DEBUG
    )
