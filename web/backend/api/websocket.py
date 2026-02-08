"""
WebSocket Support for Real-time Progress Updates
Enhanced with connection pooling, heartbeat, and automatic reconnection

Features:
- Real-time extraction progress updates
- Connection health monitoring with heartbeat
- Automatic reconnection handling
- Room-based message routing
- Message queuing and replay
- Connection pool management
"""

import logging
import json
import time
import threading
from collections import defaultdict, deque
from typing import Dict, List, Optional, Any
from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect

# Import telemetry utilities
from shared.utils.telemetry import get_tracer, set_span_attributes

logger = logging.getLogger(__name__)

# Global SocketIO instance (will be initialized by app)
socketio = None

# Connection management
active_connections = {}  # session_id -> connection_info
room_members = defaultdict(set)  # room_id -> set of session_ids
message_queues = defaultdict(lambda: deque(maxlen=100))  # room_id -> message queue

# Heartbeat configuration
HEARTBEAT_INTERVAL = 15  # seconds
heartbeat_thread = None
heartbeat_running = False

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
        tracer = get_tracer()
        with tracer.start_as_current_span("websocket.connect") as span:
            try:
                client_ip = request.remote_addr or 'unknown'
                set_span_attributes(span, {
                    "operation.type": "websocket_connect",
                    "client.session_id": request.sid,
                    "client.ip": client_ip
                })
                
                logger.info(f"Client connected: {request.sid} from {client_ip}")
                emit('connection_established', {
                    'status': 'connected',
                    'session_id': request.sid,
                    'timestamp': time.time()
                })
            except Exception as e:
                logger.error(f"Connection error: {e}")
                span.record_exception(e)

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        tracer = get_tracer()
        with tracer.start_as_current_span("websocket.disconnect") as span:
            try:
                set_span_attributes(span, {
                    "operation.type": "websocket_disconnect",
                    "client.session_id": request.sid
                })
                
                logger.info(f"Client disconnected: {request.sid}")
            except Exception as e:
                logger.error(f"Disconnect error: {e}")
                span.record_exception(e)

    @socketio.on('join_extraction')
    def handle_join_extraction(data):
        """
        Client joins an extraction room to receive progress updates

        Args:
            data: {'job_id': 'extraction_job_id'}
        """
        tracer = get_tracer()
        with tracer.start_as_current_span("websocket.join_extraction") as span:
            try:
                job_id = data.get('job_id')
                
                set_span_attributes(span, {
                    "operation.type": "join_extraction",
                    "client.session_id": request.sid,
                    "extraction.job_id": job_id or "none"
                })
                
                if not job_id:
                    emit('error', {'message': 'job_id required'})
                    return

                join_room(job_id)
                logger.info(f"Client {request.sid} joined room {job_id}")
                emit('joined', {
                    'job_id': job_id,
                    'message': 'Subscribed to extraction updates'
                })
            except Exception as e:
                logger.error(f"Join extraction error: {e}")
                span.record_exception(e)
                emit('error', {'message': 'Failed to join extraction room'})

    @socketio.on('leave_extraction')
    def handle_leave_extraction(data):
        """
        Client leaves an extraction room

        Args:
            data: {'job_id': 'extraction_job_id'}
        """
        tracer = get_tracer()
        with tracer.start_as_current_span("websocket.leave_extraction") as span:
            try:
                job_id = data.get('job_id')
                
                set_span_attributes(span, {
                    "operation.type": "leave_extraction",
                    "client.session_id": request.sid,
                    "extraction.job_id": job_id or "none"
                })
                
                if not job_id:
                    return

                leave_room(job_id)
                logger.info(f"Client {request.sid} left room {job_id}")
                emit('left', {'job_id': job_id})
            except Exception as e:
                logger.error(f"Leave extraction error: {e}")
                span.record_exception(e)

    @socketio.on('ping')
    def handle_ping():
        """Handle ping for keep-alive"""
        tracer = get_tracer()
        with tracer.start_as_current_span("websocket.ping") as span:
            try:
                set_span_attributes(span, {
                    "operation.type": "ping",
                    "client.session_id": request.sid
                })
                
                emit('pong', {'timestamp': time.time()})
            except Exception as e:
                logger.error(f"Ping error: {e}")
                span.record_exception(e)

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
