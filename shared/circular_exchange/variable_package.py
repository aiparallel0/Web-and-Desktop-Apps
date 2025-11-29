"""
Variable Package Module

Provides a container for variable-based data transfer between modules.
Variable packages act as data buses that can notify subscribers when
their values change, enabling the circular information exchange.
"""

import logging
import threading
from typing import Any, Dict, List, Callable, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime
from copy import deepcopy

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class PackageChange:
    """Represents a change in a variable package."""
    variable_name: str
    old_value: Any
    new_value: Any
    timestamp: datetime
    source_module: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert change to dictionary."""
        return {
            'variable_name': self.variable_name,
            'old_value': repr(self.old_value),
            'new_value': repr(self.new_value),
            'timestamp': self.timestamp.isoformat(),
            'source_module': self.source_module
        }


class VariablePackage(Generic[T]):
    """
    A container for variable-based data transfer between modules.
    
    Variable packages act as observable data containers that notify
    subscribers when their values change. This enables the circular
    information exchange pattern where changes in one module automatically
    propagate to dependent modules.
    
    Features:
    - Thread-safe value access and modification
    - Change notification to subscribers
    - Change history tracking
    - Validation hooks
    - Read-only views
    """

    def __init__(
        self,
        name: str,
        initial_value: T = None,
        source_module: Optional[str] = None,
        validator: Optional[Callable[[T], bool]] = None,
        max_history: int = 100
    ):
        """
        Initialize a variable package.
        
        Args:
            name: Name of the variable
            initial_value: Initial value of the variable
            source_module: ID of the module that owns this variable
            validator: Optional function to validate values before setting
            max_history: Maximum number of changes to keep in history
        """
        self._name = name
        self._value: T = initial_value
        self._source_module = source_module
        self._validator = validator
        self._max_history = max_history
        self._lock = threading.RLock()
        self._subscribers: List[Callable[[PackageChange], None]] = []
        self._change_history: List[PackageChange] = []
        self._created_at = datetime.now()
        self._last_modified = datetime.now()
        self._is_frozen = False
        self._metadata: Dict = {}
        logger.debug(f"Created VariablePackage: {name}")

    @property
    def name(self) -> str:
        """Get the variable name."""
        return self._name

    @property
    def value(self) -> T:
        """Get the current value."""
        with self._lock:
            return self._value

    @value.setter
    def value(self, new_value: T) -> None:
        """Set the value and notify subscribers."""
        self.set(new_value)

    @property
    def source_module(self) -> Optional[str]:
        """Get the source module ID."""
        return self._source_module

    @property
    def last_modified(self) -> datetime:
        """Get the last modification timestamp."""
        with self._lock:
            return self._last_modified

    @property
    def is_frozen(self) -> bool:
        """Check if the package is frozen (read-only)."""
        with self._lock:
            return self._is_frozen

    def get(self) -> T:
        """Get the current value (thread-safe)."""
        with self._lock:
            return self._value

    def get_copy(self) -> T:
        """Get a deep copy of the current value."""
        with self._lock:
            return deepcopy(self._value)

    def set(self, new_value: T, source_module: Optional[str] = None) -> bool:
        """
        Set the value and notify subscribers.
        
        Args:
            new_value: The new value to set
            source_module: Optional source module that triggered the change
            
        Returns:
            True if value was set, False if validation failed or frozen
        """
        with self._lock:
            if self._is_frozen:
                logger.warning(f"Cannot modify frozen package: {self._name}")
                return False

            # Validate if validator is set
            if self._validator and not self._validator(new_value):
                logger.warning(f"Validation failed for {self._name}: {new_value}")
                return False

            old_value = self._value
            self._value = new_value
            self._last_modified = datetime.now()

            # Create change record
            change = PackageChange(
                variable_name=self._name,
                old_value=old_value,
                new_value=new_value,
                timestamp=self._last_modified,
                source_module=source_module or self._source_module
            )

            # Add to history
            self._change_history.append(change)
            if len(self._change_history) > self._max_history:
                self._change_history.pop(0)

            logger.debug(f"Updated {self._name}: {repr(old_value)} -> {repr(new_value)}")

            # Notify subscribers
            self._notify_subscribers(change)
            return True

    def update(self, updater: Callable[[T], T], source_module: Optional[str] = None) -> bool:
        """
        Update the value using an updater function.
        
        Args:
            updater: Function that takes the current value and returns the new value
            source_module: Optional source module that triggered the change
            
        Returns:
            True if value was updated, False otherwise
        """
        with self._lock:
            new_value = updater(self._value)
            return self.set(new_value, source_module)

    def subscribe(self, callback: Callable[[PackageChange], None]) -> Callable[[], None]:
        """
        Subscribe to changes in this package.
        
        Args:
            callback: Function to call when the value changes
            
        Returns:
            Unsubscribe function
        """
        with self._lock:
            self._subscribers.append(callback)
            logger.debug(f"Added subscriber to {self._name}")

            def unsubscribe():
                with self._lock:
                    if callback in self._subscribers:
                        self._subscribers.remove(callback)
                        logger.debug(f"Removed subscriber from {self._name}")

            return unsubscribe

    def _notify_subscribers(self, change: PackageChange) -> None:
        """Notify all subscribers of a change."""
        for subscriber in self._subscribers:
            try:
                subscriber(change)
            except Exception as e:
                logger.error(f"Error notifying subscriber for {self._name}: {e}")

    def freeze(self) -> None:
        """Freeze the package, making it read-only."""
        with self._lock:
            self._is_frozen = True
            logger.info(f"Froze package: {self._name}")

    def unfreeze(self) -> None:
        """Unfreeze the package, allowing modifications."""
        with self._lock:
            self._is_frozen = False
            logger.info(f"Unfroze package: {self._name}")

    def get_history(self, limit: Optional[int] = None) -> List[PackageChange]:
        """
        Get the change history.
        
        Args:
            limit: Maximum number of changes to return (None for all)
            
        Returns:
            List of PackageChange objects
        """
        with self._lock:
            if limit:
                return self._change_history[-limit:]
            return self._change_history.copy()

    def clear_history(self) -> None:
        """Clear the change history."""
        with self._lock:
            self._change_history.clear()
            logger.debug(f"Cleared history for {self._name}")

    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata for this package."""
        with self._lock:
            self._metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata for this package."""
        with self._lock:
            return self._metadata.get(key, default)

    def to_dict(self) -> Dict:
        """Convert package to dictionary."""
        with self._lock:
            return {
                'name': self._name,
                'value': repr(self._value),
                'source_module': self._source_module,
                'last_modified': self._last_modified.isoformat(),
                'is_frozen': self._is_frozen,
                'subscriber_count': len(self._subscribers),
                'history_length': len(self._change_history),
                'metadata': self._metadata
            }


class PackageRegistry:
    """
    Registry for managing variable packages across modules.
    
    Provides a central location for creating, accessing, and managing
    variable packages used in the circular information exchange.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern for global package registry."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._packages: Dict[str, VariablePackage] = {}
        self._package_lock = threading.RLock()
        self._initialized = True
        logger.info("PackageRegistry initialized")

    def create_package(
        self,
        name: str,
        initial_value: Any = None,
        source_module: Optional[str] = None,
        validator: Optional[Callable] = None
    ) -> VariablePackage:
        """
        Create or get a variable package.
        
        Args:
            name: Unique name for the package
            initial_value: Initial value
            source_module: Source module ID
            validator: Optional validator function
            
        Returns:
            The created or existing VariablePackage
        """
        with self._package_lock:
            if name in self._packages:
                logger.debug(f"Returning existing package: {name}")
                return self._packages[name]

            package = VariablePackage(
                name=name,
                initial_value=initial_value,
                source_module=source_module,
                validator=validator
            )
            self._packages[name] = package
            logger.info(f"Created package: {name}")
            return package

    def get_package(self, name: str) -> Optional[VariablePackage]:
        """Get a package by name."""
        with self._package_lock:
            return self._packages.get(name)

    def remove_package(self, name: str) -> bool:
        """Remove a package from the registry."""
        with self._package_lock:
            if name in self._packages:
                del self._packages[name]
                logger.info(f"Removed package: {name}")
                return True
            return False

    def get_all_packages(self) -> Dict[str, VariablePackage]:
        """Get all packages in the registry."""
        with self._package_lock:
            return self._packages.copy()

    def get_packages_by_module(self, module_id: str) -> List[VariablePackage]:
        """Get all packages owned by a module."""
        with self._package_lock:
            return [p for p in self._packages.values() if p.source_module == module_id]

    def clear(self) -> None:
        """Clear all packages from the registry."""
        with self._package_lock:
            self._packages.clear()
            logger.info("Cleared all packages from registry")

    def get_stats(self) -> Dict:
        """Get statistics about the package registry."""
        with self._package_lock:
            total_subscribers = sum(len(p._subscribers) for p in self._packages.values())
            frozen_count = sum(1 for p in self._packages.values() if p.is_frozen)

            return {
                'total_packages': len(self._packages),
                'total_subscribers': total_subscribers,
                'frozen_packages': frozen_count,
                'packages_by_module': {
                    module: len(list(p for p in self._packages.values() if p.source_module == module))
                    for module in set(p.source_module for p in self._packages.values() if p.source_module)
                }
            }
