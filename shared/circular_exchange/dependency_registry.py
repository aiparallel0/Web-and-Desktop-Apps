"""
Dependency Registry Module

Tracks dependencies between modules in the project. Provides the foundation
for the circular information exchange by maintaining a graph of which modules
depend on which other modules.
"""

import logging
import threading
from typing import Dict, Set, List, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ModuleInfo:
    """Information about a registered module."""
    module_id: str
    file_path: str
    exports: Set[str] = field(default_factory=set)
    imports: Set[str] = field(default_factory=set)
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    last_modified: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert module info to dictionary."""
        return {
            'module_id': self.module_id,
            'file_path': self.file_path,
            'exports': list(self.exports),
            'imports': list(self.imports),
            'dependencies': list(self.dependencies),
            'dependents': list(self.dependents),
            'last_modified': self.last_modified.isoformat() if self.last_modified else None,
            'metadata': self.metadata
        }


class DependencyRegistry:
    """
    Registry that tracks dependencies between modules in the project.
    
    This class maintains a bidirectional graph of module dependencies,
    allowing the system to understand which modules depend on which
    other modules, and propagate changes accordingly.
    
    Thread-safe implementation using locks for concurrent access.
    """

    def __init__(self):
        self._modules: Dict[str, ModuleInfo] = {}
        self._dependency_graph: Dict[str, Set[str]] = {}  # module -> its dependencies
        self._dependent_graph: Dict[str, Set[str]] = {}   # module -> modules that depend on it
        self._lock = threading.RLock()
        self._change_callbacks: List[Callable] = []
        logger.info("DependencyRegistry initialized")

    def register_module(
        self,
        module_id: str,
        file_path: str,
        exports: Optional[Set[str]] = None,
        imports: Optional[Set[str]] = None,
        metadata: Optional[Dict] = None
    ) -> ModuleInfo:
        """
        Register a module in the dependency registry.
        
        Args:
            module_id: Unique identifier for the module
            file_path: Path to the module file
            exports: Set of variable/function names exported by this module
            imports: Set of variable/function names imported by this module
            metadata: Additional metadata about the module
            
        Returns:
            ModuleInfo object for the registered module
        """
        with self._lock:
            if module_id in self._modules:
                logger.warning(f"Module '{module_id}' already registered, updating")
                existing = self._modules[module_id]
                existing.file_path = file_path
                existing.exports = exports or existing.exports
                existing.imports = imports or existing.imports
                existing.metadata.update(metadata or {})
                existing.last_modified = datetime.now()
                return existing

            module_info = ModuleInfo(
                module_id=module_id,
                file_path=file_path,
                exports=exports or set(),
                imports=imports or set(),
                last_modified=datetime.now(),
                metadata=metadata or {}
            )
            self._modules[module_id] = module_info
            self._dependency_graph[module_id] = set()
            self._dependent_graph[module_id] = set()

            logger.info(f"Registered module: {module_id} (exports: {len(module_info.exports)}, imports: {len(module_info.imports)})")
            return module_info

    def unregister_module(self, module_id: str) -> bool:
        """
        Unregister a module from the registry.
        
        Args:
            module_id: Unique identifier for the module
            
        Returns:
            True if module was unregistered, False if not found
        """
        with self._lock:
            if module_id not in self._modules:
                logger.warning(f"Module '{module_id}' not found in registry")
                return False

            # Remove all dependency relationships
            for dep_id in list(self._dependency_graph.get(module_id, [])):
                self._dependent_graph[dep_id].discard(module_id)

            for dependent_id in list(self._dependent_graph.get(module_id, [])):
                self._dependency_graph[dependent_id].discard(module_id)

            # Remove from graphs
            self._dependency_graph.pop(module_id, None)
            self._dependent_graph.pop(module_id, None)
            del self._modules[module_id]

            logger.info(f"Unregistered module: {module_id}")
            return True

    def add_dependency(self, module_id: str, dependency_id: str) -> bool:
        """
        Add a dependency relationship between two modules.
        
        Args:
            module_id: The module that depends on another
            dependency_id: The module being depended upon
            
        Returns:
            True if dependency was added, False otherwise
        """
        with self._lock:
            if module_id not in self._modules:
                logger.warning(f"Module '{module_id}' not registered")
                return False
            if dependency_id not in self._modules:
                logger.warning(f"Dependency module '{dependency_id}' not registered")
                return False

            # Check for circular dependency
            if self._would_create_cycle(module_id, dependency_id):
                logger.warning(f"Circular dependency detected: {module_id} -> {dependency_id}")
                # In circular exchange, we allow circular dependencies but track them
                self._modules[module_id].metadata['has_circular'] = True
                self._modules[dependency_id].metadata['has_circular'] = True

            self._dependency_graph[module_id].add(dependency_id)
            self._dependent_graph[dependency_id].add(module_id)
            self._modules[module_id].dependencies.add(dependency_id)
            self._modules[dependency_id].dependents.add(module_id)

            logger.debug(f"Added dependency: {module_id} -> {dependency_id}")
            return True

    def remove_dependency(self, module_id: str, dependency_id: str) -> bool:
        """
        Remove a dependency relationship between two modules.
        
        Args:
            module_id: The module that depends on another
            dependency_id: The module being depended upon
            
        Returns:
            True if dependency was removed, False otherwise
        """
        with self._lock:
            if module_id not in self._dependency_graph:
                return False

            self._dependency_graph[module_id].discard(dependency_id)
            self._dependent_graph.get(dependency_id, set()).discard(module_id)

            if module_id in self._modules:
                self._modules[module_id].dependencies.discard(dependency_id)
            if dependency_id in self._modules:
                self._modules[dependency_id].dependents.discard(module_id)

            logger.debug(f"Removed dependency: {module_id} -> {dependency_id}")
            return True

    def get_dependencies(self, module_id: str) -> Set[str]:
        """Get all modules that this module depends on."""
        with self._lock:
            return self._dependency_graph.get(module_id, set()).copy()

    def get_dependents(self, module_id: str) -> Set[str]:
        """Get all modules that depend on this module."""
        with self._lock:
            return self._dependent_graph.get(module_id, set()).copy()

    def get_all_dependents(self, module_id: str, visited: Optional[Set[str]] = None) -> Set[str]:
        """
        Get all modules that depend on this module (recursively).
        
        This traverses the dependent graph to find all modules that would
        be affected by a change in the given module.
        """
        with self._lock:
            if visited is None:
                visited = set()

            if module_id in visited:
                return set()

            visited.add(module_id)
            all_dependents = set()

            direct_dependents = self._dependent_graph.get(module_id, set())
            for dependent in direct_dependents:
                if dependent not in visited:
                    all_dependents.add(dependent)
                    all_dependents.update(self.get_all_dependents(dependent, visited))

            return all_dependents

    def get_module_info(self, module_id: str) -> Optional[ModuleInfo]:
        """Get information about a registered module."""
        with self._lock:
            return self._modules.get(module_id)

    def get_all_modules(self) -> List[ModuleInfo]:
        """Get information about all registered modules."""
        with self._lock:
            return list(self._modules.values())

    def _would_create_cycle(self, module_id: str, dependency_id: str) -> bool:
        """Check if adding a dependency would create a cycle."""
        visited = set()
        queue = [dependency_id]

        while queue:
            current = queue.pop(0)
            if current == module_id:
                return True
            if current in visited:
                continue
            visited.add(current)
            queue.extend(self._dependency_graph.get(current, []))

        return False

    def get_topological_order(self) -> List[str]:
        """
        Get modules in topological order (dependencies before dependents).
        
        Returns:
            List of module IDs in topological order
        """
        with self._lock:
            in_degree = {m: len(self._dependency_graph.get(m, set())) for m in self._modules}
            queue = [m for m, d in in_degree.items() if d == 0]
            result = []

            while queue:
                current = queue.pop(0)
                result.append(current)

                for dependent in self._dependent_graph.get(current, []):
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

            # Handle circular dependencies - add remaining modules
            remaining = [m for m in self._modules if m not in result]
            result.extend(remaining)

            return result

    def get_update_order(self, changed_module: str) -> List[str]:
        """
        Get the order in which modules should be updated after a change.
        
        Args:
            changed_module: The module that was changed
            
        Returns:
            List of module IDs in the order they should be updated
        """
        with self._lock:
            if changed_module not in self._modules:
                return []

            all_affected = self.get_all_dependents(changed_module)
            all_affected.add(changed_module)

            # Sort by dependency level
            levels: Dict[str, int] = {changed_module: 0}
            queue = [(changed_module, 0)]

            while queue:
                current, level = queue.pop(0)
                for dependent in self._dependent_graph.get(current, []):
                    if dependent in all_affected:
                        if dependent not in levels or levels[dependent] < level + 1:
                            levels[dependent] = level + 1
                            queue.append((dependent, level + 1))

            # Sort by level, then alphabetically for consistency
            sorted_modules = sorted(all_affected, key=lambda m: (levels.get(m, 0), m))
            return sorted_modules

    def on_change(self, callback: Callable) -> None:
        """Register a callback to be called when dependencies change."""
        with self._lock:
            self._change_callbacks.append(callback)

    def notify_change(self, module_id: str) -> None:
        """Notify that a module has changed."""
        with self._lock:
            if module_id in self._modules:
                self._modules[module_id].last_modified = datetime.now()

            for callback in self._change_callbacks:
                try:
                    callback(module_id)
                except Exception as e:
                    logger.error(f"Error in change callback: {e}")

    def get_stats(self) -> Dict:
        """Get statistics about the dependency registry."""
        with self._lock:
            total_deps = sum(len(deps) for deps in self._dependency_graph.values())
            circular_modules = [m for m in self._modules.values() if m.metadata.get('has_circular')]

            return {
                'total_modules': len(self._modules),
                'total_dependencies': total_deps,
                'circular_dependencies': len(circular_modules),
                'modules_with_exports': sum(1 for m in self._modules.values() if m.exports),
                'modules_with_imports': sum(1 for m in self._modules.values() if m.imports)
            }
