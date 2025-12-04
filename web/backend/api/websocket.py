"""
WebSocket Support for Real-time Progress Updates
Allows clients to receive live extraction progress
"""

import logging
import json
import time
from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect

logger = logging.getLogger(__name__)

# Global SocketIO instance (will be initialized by app)
socketio = None

def init_websocket(app):
    """
    Initialize WebSocket support with Flask-SocketIO

    Installation required:
        pip install flask-socketio python-socketio
    """
    global socketio

    try:
        socketio = SocketIO(
            app,
            cors_allowed_origins="*",
            async_mode='threading',
            logger=False,
            engineio_logger=False
        )

        # Register event handlers
        register_handlers()

        logger.info("WebSocket initialized successfully")
        return socketio

    except ImportError as e:
        logger.warning(f"WebSocket not available (flask-socketio not installed): {e}")
        return None
    except Exception as e:
        logger.error(f"WebSocket initialization error: {e}")
        return None

def register_handlers():
    """Register WebSocket event handlers"""

    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        logger.info(f"Client connected: {request.sid}")
        emit('connection_established', {
            'status': 'connected',
            'session_id': request.sid,
            'timestamp': time.time()
        })

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        logger.info(f"Client disconnected: {request.sid}")

    @socketio.on('join_extraction')
    def handle_join_extraction(data):
        """
        Client joins an extraction room to receive progress updates

        Args:
            data: {'job_id': 'extraction_job_id'}
        """
        job_id = data.get('job_id')
        if not job_id:
            emit('error', {'message': 'job_id required'})
            return

        join_room(job_id)
        logger.info(f"Client {request.sid} joined room {job_id}")
        emit('joined', {
            'job_id': job_id,
            'message': 'Subscribed to extraction updates'
        })

    @socketio.on('leave_extraction')
    def handle_leave_extraction(data):
        """
        Client leaves an extraction room

        Args:
            data: {'job_id': 'extraction_job_id'}
        """
        job_id = data.get('job_id')
        if not job_id:
            return

        leave_room(job_id)
        logger.info(f"Client {request.sid} left room {job_id}")
        emit('left', {'job_id': job_id})

    @socketio.on('ping')
    def handle_ping():
        """Handle ping for keep-alive"""
        emit('pong', {'timestamp': time.time()})

# =============================================================================
# PROGRESS UPDATE FUNCTIONS
# =============================================================================

def send_progress_update(job_id: str, progress: int, status: str, data: dict = None):
    """
    Send progress update to all clients in extraction room

    Args:
        job_id: Extraction job ID
        progress: Progress percentage (0-100)
        status: Status message
        data: Optional additional data
    """
    if not socketio:
        return

    try:
        message = {
            'job_id': job_id,
            'progress': progress,
            'status': status,
            'timestamp': time.time()
        }

        if data:
            message['data'] = data

        socketio.emit('extraction_progress', message, room=job_id)
        logger.debug(f"Progress update sent to room {job_id}: {progress}%")

    except Exception as e:
        logger.error(f"Error sending progress update: {e}")

def send_extraction_complete(job_id: str, results: dict):
    """
    Send completion notification with results

    Args:
        job_id: Extraction job ID
        results: Extraction results
    """
    if not socketio:
        return

    try:
        message = {
            'job_id': job_id,
            'status': 'completed',
            'results': results,
            'timestamp': time.time()
        }

        socketio.emit('extraction_complete', message, room=job_id)
        logger.info(f"Completion notification sent to room {job_id}")

    except Exception as e:
        logger.error(f"Error sending completion notification: {e}")

def send_extraction_error(job_id: str, error: str):
    """
    Send error notification

    Args:
        job_id: Extraction job ID
        error: Error message
    """
    if not socketio:
        return

    try:
        message = {
            'job_id': job_id,
            'status': 'error',
            'error': error,
            'timestamp': time.time()
        }

        socketio.emit('extraction_error', message, room=job_id)
        logger.error(f"Error notification sent to room {job_id}: {error}")

    except Exception as e:
        logger.error(f"Error sending error notification: {e}")

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def is_websocket_available() -> bool:
    """Check if WebSocket support is available"""
    return socketio is not None

def get_socketio_instance():
    """Get SocketIO instance for app.run()"""
    return socketio
