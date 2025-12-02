"""
Change Notifier Module

Propagates updates when files change. Works with the DependencyRegistry
and VariablePackage to notify dependent modules of changes and trigger
updates through the circular information exchange.
"""

import logging
import threading
from typing import Dict, Set, List, Callable, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """Types of changes that can occur."""
    FILE_MODIFIED = "file_modified"
    VARIABLE_UPDATED = "variable_updated"
    DEPENDENCY_ADDED = "dependency_added"
    DEPENDENCY_REMOVED = "dependency_removed"
    MODULE_REGISTERED = "module_registered"
    MODULE_UNREGISTERED = "module_unregistered"


@dataclass
class ChangeEvent:
    """Represents a change event in the system."""
    event_type: ChangeType
    source_module: str
    timestamp: datetime
    data: Dict = field(default_factory=dict)
    affected_modules: Set[str] = field(default_factory=set)
    propagated: bool = False

    def to_dict(self) -> Dict:
        """Convert event to dictionary."""
        return {
            'event_type': self.event_type.value,
            'source_module': self.source_module,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'affected_modules': list(self.affected_modules),
            'propagated': self.propagated
        }


@dataclass
class NotificationResult:
    """Result of a notification attempt."""
    module_id: str
    success: bool
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convert result to dictionary."""
        return {
            'module_id': self.module_id,
            'success': self.success,
            'error': self.error,
            'timestamp': self.timestamp.isoformat()
        }


class ChangeNotifier:
    """
    Propagates changes through the dependency graph.
    
    When a file or module is updated, the ChangeNotifier determines
    which other modules are affected and propagates the change
    notification to them in the correct order.
    
    Features:
    - Async and sync notification modes
    - Change batching for efficiency
    - Notification history
    - Retry logic for failed notifications
    - Circular dependency handling
    """

    def __init__(self, dependency_registry=None, max_history: int = 1000):
        """
        Initialize the change notifier.
        
        Args:
            dependency_registry: DependencyRegistry to use for dependency info
            max_history: Maximum number of events to keep in history
        """
        self._dependency_registry = dependency_registry
        self._max_history = max_history
        self._lock = threading.RLock()

        # Event handlers for different change types
        self._handlers: Dict[ChangeType, List[Callable]] = {
            change_type: [] for change_type in ChangeType
        }

        # Module-specific handlers
        self._module_handlers: Dict[str, List[Callable]] = {}

        # Event history
        self._event_history: List[ChangeEvent] = []

        # Pending notifications (for batching)
        self._pending_events: List[ChangeEvent] = []
        self._batch_mode = False

        # Statistics
        self._stats = {
            'total_events': 0,
            'successful_notifications': 0,
            'failed_notifications': 0
        }

        logger.info("ChangeNotifier initialized")

    def set_dependency_registry(self, registry) -> None:
        """Set the dependency registry to use."""
        with self._lock:
            self._dependency_registry = registry
            logger.info("Dependency registry set")

    def on(self, event_type: ChangeType, handler: Callable[[ChangeEvent], None]) -> Callable[[], None]:
        """
        Register a handler for a specific event type.
        
        Args:
            event_type: The type of event to handle
            handler: Function to call when event occurs
            
        Returns:
            Unsubscribe function
        """
        with self._lock:
            self._handlers[event_type].append(handler)
            logger.debug(f"Registered handler for {event_type.value}")

            def unsubscribe():
                with self._lock:
                    if handler in self._handlers[event_type]:
                        self._handlers[event_type].remove(handler)

            return unsubscribe

    def on_module_change(self, module_id: str, handler: Callable[[ChangeEvent], None]) -> Callable[[], None]:
        """
        Register a handler for changes affecting a specific module.
        
        Args:
            module_id: The module to watch for changes
            handler: Function to call when module is affected
            
        Returns:
            Unsubscribe function
        """
        with self._lock:
            if module_id not in self._module_handlers:
                self._module_handlers[module_id] = []
            self._module_handlers[module_id].append(handler)
            logger.debug(f"Registered module handler for {module_id}")

            def unsubscribe():
                with self._lock:
                    if module_id in self._module_handlers and handler in self._module_handlers[module_id]:
                        self._module_handlers[module_id].remove(handler)

            return unsubscribe

    def notify_change(
        self,
        source_module: str,
        event_type: ChangeType,
        data: Optional[Dict] = None
    ) -> List[NotificationResult]:
        """
        Notify that a change has occurred.
        
        Args:
            source_module: The module that changed
            event_type: Type of change
            data: Additional data about the change
            
        Returns:
            List of notification results
        """
        with self._lock:
            event = ChangeEvent(
                event_type=event_type,
                source_module=source_module,
                timestamp=datetime.now(),
                data=data or {}
            )

            # Determine affected modules
            if self._dependency_registry:
                event.affected_modules = self._dependency_registry.get_all_dependents(source_module)
            event.affected_modules.add(source_module)

            # If in batch mode, queue the event
            if self._batch_mode:
                self._pending_events.append(event)
                logger.debug(f"Batched event: {event_type.value} from {source_module}")
                return []

            # Otherwise, process immediately
            return self._process_event(event)

    def _process_event(self, event: ChangeEvent) -> List[NotificationResult]:
        """Process a single change event."""
        results = []
        self._stats['total_events'] += 1

        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        # Call type-specific handlers
        for handler in self._handlers[event.event_type]:
            try:
                handler(event)
                results.append(NotificationResult(
                    module_id='_type_handler',
                    success=True
                ))
                self._stats['successful_notifications'] += 1
            except Exception as e:
                logger.error(f"Handler error for {event.event_type.value}: {e}")
                results.append(NotificationResult(
                    module_id='_type_handler',
                    success=False,
                    error=str(e)
                ))
                self._stats['failed_notifications'] += 1

        # Get update order from registry
        if self._dependency_registry:
            update_order = self._dependency_registry.get_update_order(event.source_module)
        else:
            update_order = list(event.affected_modules)

        # Notify affected modules in order
        for module_id in update_order:
            if module_id in self._module_handlers:
                for handler in self._module_handlers[module_id]:
                    try:
                        handler(event)
                        results.append(NotificationResult(
                            module_id=module_id,
                            success=True
                        ))
                        self._stats['successful_notifications'] += 1
                    except Exception as e:
                        logger.error(f"Module handler error for {module_id}: {e}")
                        results.append(NotificationResult(
                            module_id=module_id,
                            success=False,
                            error=str(e)
                        ))
                        self._stats['failed_notifications'] += 1

        event.propagated = True
        logger.info(f"Processed {event.event_type.value} from {event.source_module}, affected {len(event.affected_modules)} modules")

        return results

    def begin_batch(self) -> None:
        """Begin batching notifications for efficiency."""
        with self._lock:
            self._batch_mode = True
            logger.debug("Batch mode enabled")

    def end_batch(self) -> List[NotificationResult]:
        """End batching and process all pending events."""
        with self._lock:
            self._batch_mode = False
            results = []

            # Merge events by source module
            merged_events: Dict[str, ChangeEvent] = {}
            for event in self._pending_events:
                key = f"{event.source_module}:{event.event_type.value}"
                if key in merged_events:
                    # Merge affected modules and data
                    merged_events[key].affected_modules.update(event.affected_modules)
                    merged_events[key].data.update(event.data)
                else:
                    merged_events[key] = event

            # Process merged events
            for event in merged_events.values():
                results.extend(self._process_event(event))

            self._pending_events.clear()
            logger.debug(f"Batch mode ended, processed {len(merged_events)} events")

            return results

    def notify_file_modified(self, module_id: str, file_path: str) -> List[NotificationResult]:
        """Convenience method to notify that a file was modified."""
        return self.notify_change(
            source_module=module_id,
            event_type=ChangeType.FILE_MODIFIED,
            data={'file_path': file_path, 'modified_at': datetime.now().isoformat()}
        )

    def notify_variable_updated(
        self,
        module_id: str,
        variable_name: str,
        old_value: Any,
        new_value: Any
    ) -> List[NotificationResult]:
        """Convenience method to notify that a variable was updated."""
        return self.notify_change(
            source_module=module_id,
            event_type=ChangeType.VARIABLE_UPDATED,
            data={
                'variable_name': variable_name,
                'old_value': repr(old_value),
                'new_value': repr(new_value)
            }
        )

    def get_history(self, limit: Optional[int] = None, event_type: Optional[ChangeType] = None) -> List[ChangeEvent]:
        """
        Get the event history.
        
        Args:
            limit: Maximum number of events to return
            event_type: Filter by event type
            
        Returns:
            List of ChangeEvent objects
        """
        with self._lock:
            events = self._event_history
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            if limit:
                events = events[-limit:]
            return events.copy()

    def clear_history(self) -> None:
        """Clear the event history."""
        with self._lock:
            self._event_history.clear()
            logger.info("Event history cleared")

    def get_stats(self) -> Dict:
        """Get statistics about the notifier."""
        with self._lock:
            return {
                **self._stats,
                'pending_events': len(self._pending_events),
                'history_length': len(self._event_history),
                'batch_mode': self._batch_mode,
                'handler_counts': {
                    change_type.value: len(handlers)
                    for change_type, handlers in self._handlers.items()
                },
                'module_handler_count': sum(len(h) for h in self._module_handlers.values())
            }
