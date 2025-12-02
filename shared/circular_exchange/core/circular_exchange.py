"""
Circular Exchange Module

The main orchestrator for the circular information exchange framework.
Combines DependencyRegistry, VariablePackage, and ChangeNotifier to
provide a unified interface for tracking dependencies and propagating
changes through the system.
"""

import logging
import threading
import ast
import os
from typing import Dict, Set, List, Optional, Any, Callable
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

from .dependency_registry import DependencyRegistry, ModuleInfo
from .variable_package import VariablePackage, PackageRegistry, PackageChange
from .change_notifier import ChangeNotifier, ChangeType, ChangeEvent

logger = logging.getLogger(__name__)


@dataclass
class ModuleExport:
    """Represents an export from a module."""
    name: str
    export_type: str  # 'class', 'function', 'variable'
    module_id: str
    line_number: Optional[int] = None


@dataclass
class ModuleImport:
    """Represents an import in a module."""
    name: str
    from_module: str
    alias: Optional[str] = None
    line_number: Optional[int] = None


class CircularExchange:
    """
    Main orchestrator for the circular information exchange framework.
    
    This class provides a unified interface for:
    - Registering modules and their dependencies
    - Tracking file changes and propagating updates
    - Managing variable packages for data transfer
    - Analyzing Python files for imports and exports
    
    The circular exchange pattern allows modules to be interconnected
    and automatically updated when their dependencies change.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Singleton pattern for global exchange instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, project_root: Optional[str] = None, auto_analyze: bool = False):
        """
        Initialize the circular exchange.
        
        Args:
            project_root: Root directory of the project
            auto_analyze: Whether to automatically analyze Python files
        """
        if self._initialized:
            return

        self._project_root = Path(project_root) if project_root else Path.cwd()
        self._dependency_registry = DependencyRegistry()
        self._package_registry = PackageRegistry()
        self._change_notifier = ChangeNotifier(self._dependency_registry)
        self._lock = threading.RLock()

        # File tracking
        self._file_hashes: Dict[str, str] = {}
        self._file_modules: Dict[str, str] = {}  # file_path -> module_id

        # Module info cache
        self._module_exports: Dict[str, List[ModuleExport]] = {}
        self._module_imports: Dict[str, List[ModuleImport]] = {}

        # Watch callbacks
        self._watch_callbacks: List[Callable] = []

        self._initialized = True

        if auto_analyze:
            self.analyze_project()

        logger.info(f"CircularExchange initialized (root: {self._project_root})")

    @property
    def dependency_registry(self) -> DependencyRegistry:
        """Get the dependency registry."""
        return self._dependency_registry

    @property
    def package_registry(self) -> PackageRegistry:
        """Get the package registry."""
        return self._package_registry

    @property
    def change_notifier(self) -> ChangeNotifier:
        """Get the change notifier."""
        return self._change_notifier

    def register_module(
        self,
        module_id: str,
        file_path: str,
        analyze: bool = True
    ) -> ModuleInfo:
        """
        Register a module in the exchange.
        
        Args:
            module_id: Unique identifier for the module
            file_path: Path to the module file
            analyze: Whether to analyze the file for imports/exports
            
        Returns:
            ModuleInfo object for the registered module
        """
        with self._lock:
            exports = set()
            imports = set()

            if analyze and file_path.endswith('.py'):
                full_path = self._resolve_path(file_path)
                if full_path.exists():
                    analysis = self.analyze_file(str(full_path))
                    exports = set(e.name for e in analysis.get('exports', []))
                    imports = set(i.name for i in analysis.get('imports', []))

            module_info = self._dependency_registry.register_module(
                module_id=module_id,
                file_path=file_path,
                exports=exports,
                imports=imports
            )

            self._file_modules[file_path] = module_id

            # Notify of registration
            self._change_notifier.notify_change(
                source_module=module_id,
                event_type=ChangeType.MODULE_REGISTERED,
                data={'file_path': file_path}
            )

            return module_info

    def unregister_module(self, module_id: str) -> bool:
        """
        Unregister a module from the exchange.
        
        Args:
            module_id: The module to unregister
            
        Returns:
            True if unregistered, False if not found
        """
        with self._lock:
            result = self._dependency_registry.unregister_module(module_id)

            if result:
                # Clean up file tracking
                to_remove = [fp for fp, mid in self._file_modules.items() if mid == module_id]
                for fp in to_remove:
                    del self._file_modules[fp]

                # Remove packages
                packages = self._package_registry.get_packages_by_module(module_id)
                for pkg in packages:
                    self._package_registry.remove_package(pkg.name)

                # Notify
                self._change_notifier.notify_change(
                    source_module=module_id,
                    event_type=ChangeType.MODULE_UNREGISTERED
                )

            return result

    def add_dependency(self, module_id: str, depends_on: str) -> bool:
        """
        Add a dependency between two modules.
        
        Args:
            module_id: The module that depends on another
            depends_on: The module being depended upon
            
        Returns:
            True if dependency was added
        """
        with self._lock:
            result = self._dependency_registry.add_dependency(module_id, depends_on)

            if result:
                self._change_notifier.notify_change(
                    source_module=module_id,
                    event_type=ChangeType.DEPENDENCY_ADDED,
                    data={'dependency': depends_on}
                )

            return result

    def create_package(
        self,
        name: str,
        initial_value: Any = None,
        module_id: Optional[str] = None,
        validator: Optional[Callable] = None
    ) -> VariablePackage:
        """
        Create a variable package for data transfer.
        
        Args:
            name: Name of the package
            initial_value: Initial value
            module_id: Owner module
            validator: Optional value validator
            
        Returns:
            The created VariablePackage
        """
        package = self._package_registry.create_package(
            name=name,
            initial_value=initial_value,
            source_module=module_id,
            validator=validator
        )

        # Subscribe to changes for notification
        def on_change(change: PackageChange):
            self._change_notifier.notify_variable_updated(
                module_id=change.source_module or 'unknown',
                variable_name=change.variable_name,
                old_value=change.old_value,
                new_value=change.new_value
            )

        package.subscribe(on_change)
        return package

    def get_package(self, name: str) -> Optional[VariablePackage]:
        """Get a package by name."""
        return self._package_registry.get_package(name)

    def notify_file_changed(self, file_path: str) -> None:
        """
        Notify that a file has been changed.
        
        Args:
            file_path: Path to the changed file
        """
        with self._lock:
            module_id = self._file_modules.get(file_path)

            if module_id:
                # Re-analyze the file
                if file_path.endswith('.py'):
                    full_path = self._resolve_path(file_path)
                    if full_path.exists():
                        analysis = self.analyze_file(str(full_path))
                        exports = set(e.name for e in analysis.get('exports', []))
                        imports = set(i.name for i in analysis.get('imports', []))

                        # Update module info
                        self._dependency_registry.register_module(
                            module_id=module_id,
                            file_path=file_path,
                            exports=exports,
                            imports=imports
                        )

                # Notify of change
                self._change_notifier.notify_file_modified(module_id, file_path)

                # Call watch callbacks
                for callback in self._watch_callbacks:
                    try:
                        callback(file_path, module_id)
                    except Exception as e:
                        logger.error(f"Watch callback error: {e}")
            else:
                logger.debug(f"File not registered: {file_path}")

    def on_file_change(self, callback: Callable[[str, str], None]) -> Callable[[], None]:
        """
        Register a callback for file changes.
        
        Args:
            callback: Function(file_path, module_id) to call on change
            
        Returns:
            Unsubscribe function
        """
        with self._lock:
            self._watch_callbacks.append(callback)

            def unsubscribe():
                with self._lock:
                    if callback in self._watch_callbacks:
                        self._watch_callbacks.remove(callback)

            return unsubscribe

    def analyze_file(self, file_path: str) -> Dict:
        """
        Analyze a Python file for imports and exports.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            Dictionary with 'imports' and 'exports' lists
        """
        result = {'imports': [], 'exports': []}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source)
            module_id = self._get_module_id_from_path(file_path)

            for node in ast.walk(tree):
                # Find imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        result['imports'].append(ModuleImport(
                            name=alias.name,
                            from_module=alias.name,
                            alias=alias.asname,
                            line_number=node.lineno
                        ))
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for alias in node.names:
                            result['imports'].append(ModuleImport(
                                name=alias.name,
                                from_module=node.module,
                                alias=alias.asname,
                                line_number=node.lineno
                            ))

                # Find exports (top-level definitions)
                if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                    result['exports'].append(ModuleExport(
                        name=node.name,
                        export_type='function',
                        module_id=module_id,
                        line_number=node.lineno
                    ))
                elif isinstance(node, ast.ClassDef) and not node.name.startswith('_'):
                    result['exports'].append(ModuleExport(
                        name=node.name,
                        export_type='class',
                        module_id=module_id,
                        line_number=node.lineno
                    ))
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and not target.id.startswith('_'):
                            result['exports'].append(ModuleExport(
                                name=target.id,
                                export_type='variable',
                                module_id=module_id,
                                line_number=node.lineno
                            ))

            # Store in cache
            self._module_exports[module_id] = result['exports']
            self._module_imports[module_id] = result['imports']

        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")

        return result

    def analyze_project(self, patterns: Optional[List[str]] = None) -> Dict:
        """
        Analyze all Python files in the project.
        
        Args:
            patterns: Optional list of glob patterns to match
            
        Returns:
            Statistics about the analysis
        """
        patterns = patterns or ['**/*.py']
        stats = {
            'files_analyzed': 0,
            'modules_registered': 0,
            'dependencies_found': 0,
            'exports_found': 0,
            'imports_found': 0
        }

        with self._lock:
            python_files = []
            for pattern in patterns:
                python_files.extend(self._project_root.glob(pattern))

            # First pass: register all modules
            for file_path in python_files:
                if '__pycache__' in str(file_path):
                    continue

                module_id = self._get_module_id_from_path(str(file_path))
                relative_path = str(file_path.relative_to(self._project_root))

                self.register_module(module_id, relative_path, analyze=True)
                stats['files_analyzed'] += 1
                stats['modules_registered'] += 1

            # Second pass: resolve dependencies based on imports
            for module_id, imports in self._module_imports.items():
                for imp in imports:
                    dep_module_id = self._resolve_import_to_module(imp.from_module)
                    if dep_module_id and dep_module_id in self._dependency_registry._modules:
                        self._dependency_registry.add_dependency(module_id, dep_module_id)
                        stats['dependencies_found'] += 1

            # Calculate totals
            for exports in self._module_exports.values():
                stats['exports_found'] += len(exports)
            for imports in self._module_imports.values():
                stats['imports_found'] += len(imports)

        logger.info(f"Project analysis complete: {stats}")
        return stats

    def _resolve_path(self, file_path: str) -> Path:
        """Resolve a relative path to absolute."""
        path = Path(file_path)
        if not path.is_absolute():
            path = self._project_root / path
        return path

    def _get_module_id_from_path(self, file_path: str) -> str:
        """Convert a file path to a module ID."""
        path = Path(file_path)

        # Make relative to project root if possible
        try:
            path = path.relative_to(self._project_root)
        except ValueError:
            pass

        # Convert path to module notation
        parts = list(path.parts)
        if parts[-1].endswith('.py'):
            parts[-1] = parts[-1][:-3]  # Remove .py extension

        return '.'.join(parts)

    def _resolve_import_to_module(self, import_name: str) -> Optional[str]:
        """Try to resolve an import name to a registered module ID."""
        # Direct match
        if import_name in self._dependency_registry._modules:
            return import_name

        # Try with common prefixes
        for prefix in ['shared.', 'web-app.', 'desktop-app.']:
            full_name = prefix + import_name
            if full_name in self._dependency_registry._modules:
                return full_name

        return None

    def get_affected_modules(self, module_id: str) -> Set[str]:
        """Get all modules affected by a change in the given module."""
        return self._dependency_registry.get_all_dependents(module_id)

    def get_update_order(self, module_id: str) -> List[str]:
        """Get the order in which modules should be updated."""
        return self._dependency_registry.get_update_order(module_id)

    def get_stats(self) -> Dict:
        """Get statistics about the exchange."""
        return {
            'registry': self._dependency_registry.get_stats(),
            'packages': self._package_registry.get_stats(),
            'notifier': self._change_notifier.get_stats(),
            'files_tracked': len(self._file_modules),
            'project_root': str(self._project_root)
        }

    def reset(self) -> None:
        """Reset the exchange to initial state."""
        with self._lock:
            self._file_hashes.clear()
            self._file_modules.clear()
            self._module_exports.clear()
            self._module_imports.clear()
            self._watch_callbacks.clear()
            self._package_registry.clear()
            self._change_notifier.clear_history()

            # Note: DependencyRegistry doesn't have a clear method,
            # so we create a new one
            self._dependency_registry = DependencyRegistry()
            self._change_notifier.set_dependency_registry(self._dependency_registry)

            logger.info("CircularExchange reset")
