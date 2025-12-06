"""
Progress Tracker for Real-Time Updates

This module provides a progress tracking system for long-running OCR and text
detection operations, enabling real-time feedback to users through Server-Sent
Events (SSE) or callbacks.

Integration with Circular Exchange Framework (CEFR) for reactive updates.
"""

import logging
import time
import threading
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from queue import Queue, Empty

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    try:
        from ..circular_exchange import PROJECT_CONFIG, ModuleRegistration
        CIRCULAR_EXCHANGE_AVAILABLE = True
    except ImportError:
        CIRCULAR_EXCHANGE_AVAILABLE = False

logger = logging.getLogger(__name__)

# Register module with Circular Exchange
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.utils.progress",
            file_path=__file__,
            description="Progress tracking for long-running operations with SSE support",
            dependencies=["shared.circular_exchange"],
            exports=["ProgressTracker", "ProgressEvent", "ProcessingStage"]
        ))
    except Exception as e:
        logger.debug(f"Module registration skipped: {e}")


class ProcessingStage(Enum):
    """Enumeration of processing stages for progress tracking."""
    INITIALIZING = "initializing"
    LOADING_IMAGE = "loading_image"
    PREPROCESSING = "preprocessing"
    LOADING_MODEL = "loading_model"
    DETECTING = "detecting"
    EXTRACTING = "extracting"
    POST_PROCESSING = "post_processing"
    VALIDATING = "validating"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProgressEvent:
    """Represents a progress update event."""
    progress: float  # 0-100
    stage: ProcessingStage
    message: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for JSON serialization."""
        return {
            'progress': round(self.progress, 2),
            'stage': self.stage.value,
            'message': self.message,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }
    
    def to_sse(self) -> str:
        """Convert to Server-Sent Events format."""
        import json
        data = self.to_dict()
        return f"data: {json.dumps(data)}\n\n"


class ProgressTracker:
    """
    Thread-safe progress tracker for long-running operations.
    
    This class enables real-time progress updates during text detection and
    extraction operations, which can take 10-60 seconds for AI models.
    
    Features:
    - Thread-safe progress updates
    - Stage-based progress tracking
    - Automatic time estimation
    - SSE (Server-Sent Events) support
    - Callback system for custom handlers
    
    Example:
        >>> tracker = ProgressTracker(operation_id="detect_123")
        >>> tracker.start()
        >>> tracker.update(10, ProcessingStage.LOADING_IMAGE, "Loading image...")
        >>> tracker.update(50, ProcessingStage.DETECTING, "Running detection...")
        >>> tracker.complete("Detection complete")
        >>> events = tracker.get_events()
    """
    
    def __init__(
        self,
        operation_id: str,
        callback: Optional[Callable[[ProgressEvent], None]] = None,
        enable_history: bool = True,
        max_history_size: int = 100
    ):
        """
        Initialize progress tracker.
        
        Args:
            operation_id: Unique identifier for this operation
            callback: Optional callback function called on each progress update
            enable_history: Whether to keep history of all events (default: True)
            max_history_size: Maximum number of events to keep in history
        """
        self.operation_id = operation_id
        self.callback = callback
        self.enable_history = enable_history
        self.max_history_size = max_history_size
        
        # State management
        self._lock = threading.Lock()
        self._started = False
        self._completed = False
        self._failed = False
        self._current_progress = 0.0
        self._current_stage = ProcessingStage.INITIALIZING
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        
        # Event storage
        self._events: List[ProgressEvent] = []
        self._event_queue: Queue = Queue()
        
        logger.debug(f"ProgressTracker initialized for operation: {operation_id}")
    
    def start(self, message: str = "Starting operation...") -> None:
        """
        Mark operation as started.
        
        Args:
            message: Initial status message
        """
        with self._lock:
            if self._started:
                logger.warning(f"Operation {self.operation_id} already started")
                return
            
            self._started = True
            self._start_time = time.time()
            
            event = ProgressEvent(
                progress=0.0,
                stage=ProcessingStage.INITIALIZING,
                message=message,
                metadata={'operation_id': self.operation_id}
            )
            self._add_event(event)
            
            logger.info(f"Operation {self.operation_id} started")
    
    def update(
        self,
        progress: float,
        stage: ProcessingStage,
        message: str,
        **metadata
    ) -> None:
        """
        Update progress.
        
        Args:
            progress: Progress percentage (0-100)
            stage: Current processing stage
            message: Status message
            **metadata: Additional metadata to include in event
        """
        with self._lock:
            if not self._started:
                logger.warning(f"Operation {self.operation_id} not started yet")
                return
            
            if self._completed or self._failed:
                logger.debug(f"Operation {self.operation_id} already finished")
                return
            
            # Clamp progress to 0-100
            progress = max(0.0, min(100.0, progress))
            
            self._current_progress = progress
            self._current_stage = stage
            
            # Calculate estimated time remaining
            if self._start_time and progress > 0:
                elapsed = time.time() - self._start_time
                estimated_total = elapsed / (progress / 100.0)
                eta_seconds = max(0, estimated_total - elapsed)
                metadata['eta_seconds'] = round(eta_seconds, 1)
            
            event = ProgressEvent(
                progress=progress,
                stage=stage,
                message=message,
                metadata={
                    'operation_id': self.operation_id,
                    **metadata
                }
            )
            self._add_event(event)
            
            logger.debug(
                f"Operation {self.operation_id}: {progress:.1f}% - {stage.value} - {message}"
            )
    
    def complete(self, message: str = "Operation completed successfully") -> None:
        """
        Mark operation as completed.
        
        Args:
            message: Completion message
        """
        with self._lock:
            if not self._started:
                logger.warning(f"Operation {self.operation_id} not started")
                return
            
            if self._completed or self._failed:
                logger.debug(f"Operation {self.operation_id} already finished")
                return
            
            self._completed = True
            self._end_time = time.time()
            
            elapsed = self._end_time - (self._start_time or self._end_time)
            
            event = ProgressEvent(
                progress=100.0,
                stage=ProcessingStage.COMPLETED,
                message=message,
                metadata={
                    'operation_id': self.operation_id,
                    'duration_seconds': round(elapsed, 2)
                }
            )
            self._add_event(event)
            
            logger.info(
                f"Operation {self.operation_id} completed in {elapsed:.2f}s"
            )
    
    def fail(self, message: str, error: Optional[Exception] = None) -> None:
        """
        Mark operation as failed.
        
        Args:
            message: Error message
            error: Optional exception that caused the failure
        """
        with self._lock:
            if not self._started:
                logger.warning(f"Operation {self.operation_id} not started")
                return
            
            if self._completed or self._failed:
                logger.debug(f"Operation {self.operation_id} already finished")
                return
            
            self._failed = True
            self._end_time = time.time()
            
            metadata = {'operation_id': self.operation_id}
            if error:
                metadata['error'] = str(error)
                metadata['error_type'] = type(error).__name__
            
            event = ProgressEvent(
                progress=self._current_progress,
                stage=ProcessingStage.FAILED,
                message=message,
                metadata=metadata
            )
            self._add_event(event)
            
            logger.error(f"Operation {self.operation_id} failed: {message}")
    
    def _add_event(self, event: ProgressEvent) -> None:
        """
        Add event to history and queue (internal method).
        
        Args:
            event: ProgressEvent to add
        """
        # Add to history
        if self.enable_history:
            self._events.append(event)
            # Trim history if needed
            if len(self._events) > self.max_history_size:
                self._events = self._events[-self.max_history_size:]
        
        # Add to queue for consumers
        self._event_queue.put(event)
        
        # Call callback if registered
        if self.callback:
            try:
                self.callback(event)
            except Exception as e:
                logger.error(f"Progress callback error: {e}", exc_info=True)
    
    def get_events(self, since: Optional[float] = None) -> List[ProgressEvent]:
        """
        Get progress events.
        
        Args:
            since: Optional timestamp to get events after (Unix timestamp)
            
        Returns:
            List of ProgressEvent objects
        """
        with self._lock:
            if since is None:
                return self._events.copy()
            return [e for e in self._events if e.timestamp > since]
    
    def get_next_event(self, timeout: float = 30.0) -> Optional[ProgressEvent]:
        """
        Get next event from queue (blocking).
        
        This method is useful for SSE endpoints that need to stream events.
        
        Args:
            timeout: Maximum time to wait for an event (seconds)
            
        Returns:
            ProgressEvent or None if timeout
        """
        try:
            return self._event_queue.get(timeout=timeout)
        except Empty:
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status summary.
        
        Returns:
            Dictionary with current progress status
        """
        with self._lock:
            status = {
                'operation_id': self.operation_id,
                'started': self._started,
                'completed': self._completed,
                'failed': self._failed,
                'progress': self._current_progress,
                'stage': self._current_stage.value if self._current_stage else None
            }
            
            if self._start_time:
                status['start_time'] = self._start_time
                if self._end_time:
                    status['duration'] = self._end_time - self._start_time
                else:
                    status['elapsed'] = time.time() - self._start_time
            
            return status
    
    def is_active(self) -> bool:
        """Check if operation is still active."""
        with self._lock:
            return self._started and not (self._completed or self._failed)
    
    def is_complete(self) -> bool:
        """Check if operation completed successfully."""
        with self._lock:
            return self._completed
    
    def is_failed(self) -> bool:
        """Check if operation failed."""
        with self._lock:
            return self._failed


# Global registry for active trackers (for SSE endpoints to access)
_active_trackers: Dict[str, ProgressTracker] = {}
_trackers_lock = threading.Lock()


def get_tracker(operation_id: str) -> Optional[ProgressTracker]:
    """
    Get active progress tracker by operation ID.
    
    Args:
        operation_id: Operation identifier
        
    Returns:
        ProgressTracker or None if not found
    """
    with _trackers_lock:
        return _active_trackers.get(operation_id)


def register_tracker(tracker: ProgressTracker) -> None:
    """
    Register a tracker in global registry.
    
    Args:
        tracker: ProgressTracker instance
    """
    with _trackers_lock:
        _active_trackers[tracker.operation_id] = tracker
        logger.debug(f"Registered tracker: {tracker.operation_id}")


def unregister_tracker(operation_id: str) -> None:
    """
    Unregister a tracker from global registry.
    
    Args:
        operation_id: Operation identifier
    """
    with _trackers_lock:
        if operation_id in _active_trackers:
            del _active_trackers[operation_id]
            logger.debug(f"Unregistered tracker: {operation_id}")


def cleanup_old_trackers(max_age_seconds: float = 3600) -> int:
    """
    Remove old completed/failed trackers from registry.
    
    Args:
        max_age_seconds: Maximum age for inactive trackers (default: 1 hour)
        
    Returns:
        Number of trackers removed
    """
    with _trackers_lock:
        now = time.time()
        to_remove = []
        
        for op_id, tracker in _active_trackers.items():
            if not tracker.is_active():
                status = tracker.get_status()
                if 'start_time' in status:
                    age = now - status['start_time']
                    if age > max_age_seconds:
                        to_remove.append(op_id)
        
        for op_id in to_remove:
            del _active_trackers[op_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old trackers")
        
        return len(to_remove)


__all__ = [
    'ProgressTracker',
    'ProgressEvent',
    'ProcessingStage',
    'get_tracker',
    'register_tracker',
    'unregister_tracker',
    'cleanup_old_trackers'
]
