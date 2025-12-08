"""
=============================================================================
CIRCULAR EXCHANGE - Project Configuration Hub (Central Node)
=============================================================================

This module serves as the CENTRAL NODE in the bidirectional weighted graph
of the Circular Exchange framework. It has ACCESS TO ALL FILES in the project.

GRAPH ARCHITECTURE:
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WEIGHTED BIDIRECTIONAL DEPENDENCY GRAPH                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                         ┌─────────────────────┐                              │
│                         │   PROJECT_CONFIG    │ ◄── CENTRAL HUB              │
│                         │   (Degree: ∞)       │     Access to ALL files      │
│                         │   Weight: 1.0       │     Changes affect ALL       │
│                         └──────────┬──────────┘                              │
│                                    │                                          │
│            ┌───────────────────────┼───────────────────────┐                 │
│            │                       │                       │                  │
│            ▼                       ▼                       ▼                  │
│   ┌────────────────┐    ┌────────────────┐    ┌────────────────┐            │
│   │ shared/models  │◄──►│ shared/utils   │◄──►│ shared/config  │            │
│   │ (Degree: 2.5)  │    │ (Degree: 3.0)  │    │ (Degree: 2.0)  │            │
│   │ Weight: 0.8    │    │ Weight: 0.9    │    │ Weight: 0.7    │            │
│   └────────┬───────┘    └────────┬───────┘    └────────┬───────┘            │
│            │                     │                     │                      │
│            ▼                     ▼                     ▼                      │
│   ┌────────────────┐    ┌────────────────┐    ┌────────────────┐            │
│   │ model_manager  │    │ data_structures│    │   settings     │            │
│   │ (Degree: 1.5)  │    │ (Degree: 1.0)  │    │ (Degree: 1.0)  │            │
│   └────────────────┘    └────────────────┘    └────────────────┘            │
│                                                                              │
│   DEGREE MEANINGS:                                                           │
│   - 1.0: First-degree (direct imports only)                                  │
│   - 1.5-2.5: Hybrid access (some indirect dependencies)                      │
│   - 3.0+: High connectivity (affects many modules)                           │
│   - ∞: Central hub (affects ALL modules)                                     │
│                                                                              │
│   WEIGHT MEANINGS:                                                           │
│   - 1.0: Maximum impact (changes always propagate)                           │
│   - 0.5-0.9: Partial impact (conditional propagation)                        │
│   - 0.0: No impact (isolated module)                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

DESIGN PRINCIPLES:
- Variable-Based Coding: All configuration is stored in VariablePackages
- Single Source of Truth: One location controls project-wide behavior
- Reactive Updates: Changes propagate automatically based on weights
- Degree-Based Access: Modules access others based on connection degree
- AI Agent Compatible: Structured for autonomous code development

USAGE BY AI AGENTS:
When developing code in this repository, AI agents should:
1. Import PROJECT_CONFIG from this module
2. Subscribe to relevant configuration packages
3. Use configuration values rather than hardcoded values
4. Propagate changes through the circular exchange system
5. Check module degree before accessing other modules
6. Respect weight-based propagation rules

Example:
    from shared.circular_exchange.project_config import PROJECT_CONFIG
    
    # Get current configuration
    debug_mode = PROJECT_CONFIG.debug.value
    
    # Subscribe to changes
    PROJECT_CONFIG.debug.subscribe(lambda change: handle_debug_change(change))
    
    # Check if a module can access another
    can_access = PROJECT_CONFIG.can_access_module("shared.models", "shared.utils")
    
    # Get propagation weight
    weight = PROJECT_CONFIG.get_propagation_weight("shared.models")

=============================================================================
"""

import logging
import threading
import os
from typing import Dict, Any, Optional, Callable, List, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum
import math

from .variable_package import VariablePackage, PackageChange

logger = logging.getLogger(__name__)


# =============================================================================
# FEATURE FLAG - ENABLE CEFR
# =============================================================================
def _is_cefr_enabled() -> bool:
    """
    Check if CEFR framework is enabled via environment variable.
    
    Returns:
        True if ENABLE_CEFR is set to 'true' (case-insensitive), False otherwise.
        Defaults to False for MVP mode.
    """
    return os.getenv('ENABLE_CEFR', 'false').lower() in ('true', '1', 'yes')


# =============================================================================
# GRAPH-BASED DEPENDENCY SYSTEM
# =============================================================================

class PropagationMode(Enum):
    """Modes for change propagation through the graph."""
    IMMEDIATE = "immediate"      # Changes propagate instantly
    BATCHED = "batched"          # Changes are batched and propagated together
    CONDITIONAL = "conditional"  # Changes propagate based on conditions
    WEIGHTED = "weighted"        # Changes propagate based on weight thresholds


@dataclass
class GraphNode:
    """
    Represents a node (module) in the bidirectional dependency graph.
    
    Each node has:
    - degree: Connectivity level (1.0 = direct only, ∞ = central hub)
    - weight: Impact factor for change propagation (0.0-1.0)
    - connections: Set of directly connected module IDs
    """
    module_id: str
    degree: float  # 1.0, 1.5, 2.0, 2.5, 3.0, ... or math.inf for central
    weight: float  # 0.0 to 1.0
    connections: Set[str] = field(default_factory=set)
    is_central_hub: bool = False
    
    def can_access(self, target_degree: float) -> bool:
        """Check if this node can access a target based on degrees."""
        if self.is_central_hub:
            return True  # Central hub can access everything
        return self.degree >= target_degree
    
    def get_propagation_weight(self, target_weight: float) -> float:
        """Calculate the effective propagation weight to a target."""
        return self.weight * target_weight


@dataclass
class GraphEdge:
    """
    Represents a weighted bidirectional edge between two modules.
    """
    source_id: str
    target_id: str
    weight: float = 1.0  # Edge weight for propagation
    bidirectional: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# PROJECT-WIDE VARIABLE DEFINITIONS
# =============================================================================

@dataclass
class ModuleRegistration:
    """Registration information for a module in the circular exchange."""
    module_id: str
    file_path: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    is_circular_exchange_compliant: bool = True
    compliance_version: str = "2.0.0"


@dataclass 
class SecurityPolicy:
    """Security policy configuration for the project."""
    require_authentication: bool = True
    enable_rate_limiting: bool = True
    max_requests_per_minute: int = 100
    enable_input_validation: bool = True
    enable_output_sanitization: bool = True
    log_security_events: bool = True


@dataclass
class CodingStandards:
    """Coding standards that AI agents should follow."""
    use_type_hints: bool = True
    require_docstrings: bool = True
    max_function_length: int = 50
    max_file_length: int = 500
    require_error_handling: bool = True
    use_logging: bool = True
    follow_pep8: bool = True


class ProjectConfiguration:
    """
    Central configuration hub for the entire project.
    
    All configuration is stored in VariablePackages, enabling:
    - Automatic propagation of changes
    - Subscription-based updates
    - Thread-safe access
    - Change history tracking
    
    AI AGENT INSTRUCTIONS:
    When modifying project behavior:
    1. Update the relevant VariablePackage here
    2. All subscribed modules will automatically update
    3. Do NOT hardcode values in individual files
    4. Always use PROJECT_CONFIG for configuration access
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for global configuration."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the project configuration."""
        if self._initialized:
            return
        
        # Check if CEFR is enabled via environment variable
        self.cefr_enabled = _is_cefr_enabled()
        
        if not self.cefr_enabled:
            logger.info("CEFR Framework is disabled (ENABLE_CEFR=false). Skipping initialization.")
            self._initialized = True
            # Set minimal attributes for compatibility
            self.module_registry = None
            self._graph_nodes = {}
            self._graph_edges = []
            return
            
        logger.info("CEFR Framework is enabled. Initializing...")
        self._lock = threading.RLock()
        
        # =================================================================
        # CORE CONFIGURATION PACKAGES
        # Modify these to change project-wide behavior
        # =================================================================
        
        # Debug mode - controls logging verbosity across all modules
        self.debug = VariablePackage[bool](
            name="project.debug",
            initial_value=False,
            source_module="project_config",
            max_history=50
        )
        
        # Project metadata
        self.project_name = VariablePackage[str](
            name="project.name",
            initial_value="Receipt Extractor",
            source_module="project_config"
        )
        
        self.project_version = VariablePackage[str](
            name="project.version",
            initial_value="3.0.0",
            source_module="project_config"
        )
        
        # =================================================================
        # SECURITY CONFIGURATION
        # =================================================================
        
        self.security_policy = VariablePackage[SecurityPolicy](
            name="project.security",
            initial_value=SecurityPolicy(),
            source_module="project_config"
        )
        
        # =================================================================
        # CODING STANDARDS
        # AI agents must follow these standards
        # =================================================================
        
        self.coding_standards = VariablePackage[CodingStandards](
            name="project.coding_standards",
            initial_value=CodingStandards(),
            source_module="project_config"
        )
        
        # =================================================================
        # MODULE REGISTRY
        # All modules registered with circular exchange
        # =================================================================
        
        self.module_registry = VariablePackage[Dict[str, ModuleRegistration]](
            name="project.modules",
            initial_value={},
            source_module="project_config"
        )
        
        # =================================================================
        # PATHS CONFIGURATION
        # =================================================================
        
        self.paths = VariablePackage[Dict[str, str]](
            name="project.paths",
            initial_value={
                "root": str(Path(__file__).parent.parent.parent.parent),
                "shared": "shared",
                "models": "shared/models",
                "utils": "shared/utils",
                "config": "shared/config",
                "circular_exchange": "shared/circular_exchange",
                "web_backend": "web/backend",
                "tests": "tests"
            },
            source_module="project_config"
        )
        
        # =================================================================
        # LOGGING CONFIGURATION
        # =================================================================
        
        self.logging_config = VariablePackage[Dict[str, Any]](
            name="project.logging",
            initial_value={
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "enable_file_logging": True,
                "log_file": "logs/application.log",
                "max_file_size_mb": 10,
                "backup_count": 5
            },
            source_module="project_config"
        )
        
        # =================================================================
        # AI AGENT CONFIGURATION
        # Instructions for AI agents working on this codebase
        # =================================================================
        
        self.ai_agent_config = VariablePackage[Dict[str, Any]](
            name="project.ai_agents",
            initial_value={
                "must_use_circular_exchange": True,
                "must_register_modules": True,
                "must_use_variable_packages": True,
                "must_add_compliance_headers": True,
                "compliance_header_template": self._get_compliance_header_template(),
                "import_structure": {
                    "always_import": [
                        "from shared.circular_exchange.project_config import PROJECT_CONFIG"
                    ],
                    "conditional_imports": {
                        "models": "from shared.circular_exchange import CircularExchange",
                        "utils": "from shared.circular_exchange import VariablePackage",
                        "backend": "from shared.circular_exchange import ChangeNotifier"
                    }
                }
            },
            source_module="project_config"
        )
        
        # =================================================================
        # DEPENDENCY GRAPH CONFIGURATION
        # Weighted bidirectional graph for module connections
        # =================================================================
        
        self._graph_nodes: Dict[str, GraphNode] = {}
        self._graph_edges: List[GraphEdge] = []
        
        # Initialize central hub (this module)
        self._graph_nodes["project_config"] = GraphNode(
            module_id="project_config",
            degree=math.inf,  # Infinite degree - can access everything
            weight=1.0,  # Maximum weight - changes always propagate
            is_central_hub=True
        )
        
        # Initialize default module degrees and weights
        self._default_degrees = VariablePackage[Dict[str, float]](
            name="project.graph.degrees",
            initial_value={
                # Central modules (high connectivity)
                "shared": 4.0,
                "shared.circular_exchange": math.inf,
                "shared.circular_exchange.project_config": math.inf,
                # Utility modules (medium-high connectivity)
                "shared.utils": 3.0,
                "shared.utils.data_structures": 2.5,
                "shared.utils.logger": 2.5,
                "shared.utils.errors": 2.0,
                "shared.utils.image_processing": 1.5,
                # Model modules (medium connectivity)
                "shared.models": 2.5,
                "shared.models.model_manager": 2.0,
                "shared.models.processors": 1.5,
                "shared.models.ai_models": 1.5,
                # Config modules (low-medium connectivity)
                "shared.config": 2.0,
                "shared.config.settings": 1.5,
                # Backend modules (medium connectivity)
                "web.backend": 2.5,
                "web.backend.app": 2.0,
                "web.backend.auth": 1.5,
                "web.backend.database": 1.5,
                # Test modules (low connectivity)
                "tests": 1.0,
            },
            source_module="project_config"
        )
        
        self._default_weights = VariablePackage[Dict[str, float]](
            name="project.graph.weights",
            initial_value={
                # Central modules (high impact)
                "shared": 0.95,
                "shared.circular_exchange": 1.0,
                "shared.circular_exchange.project_config": 1.0,
                # Utility modules
                "shared.utils": 0.9,
                "shared.utils.data_structures": 0.85,
                "shared.utils.logger": 0.8,
                "shared.utils.errors": 0.75,
                "shared.utils.image_processing": 0.7,
                # Model modules
                "shared.models": 0.85,
                "shared.models.model_manager": 0.8,
                "shared.models.processors": 0.75,
                "shared.models.ai_models": 0.75,
                # Config modules
                "shared.config": 0.8,
                "shared.config.settings": 0.7,
                # Backend modules
                "web.backend": 0.85,
                "web.backend.app": 0.8,
                "web.backend.auth": 0.7,
                "web.backend.database": 0.7,
                # Test modules (low impact on production)
                "tests": 0.3,
            },
            source_module="project_config"
        )
        
        self._initialized = True
        logger.info("ProjectConfiguration initialized - Central hub ready")
    
    def _get_compliance_header_template(self) -> str:
        """Get the compliance header template for all files."""
        return '''"""
=============================================================================
CIRCULAR EXCHANGE COMPLIANT MODULE
=============================================================================

Module: {module_name}
Path: {file_path}
Description: {description}
Compliance Version: 2.0.0

CIRCULAR EXCHANGE INTEGRATION:
This module is integrated with the Circular Information Exchange Framework.
All changes are tracked and propagated through the reactive system.

Dependencies: {dependencies}
Exports: {exports}

AI AGENT INSTRUCTIONS:
- Use PROJECT_CONFIG for all configuration values
- Register this module with CircularExchange on import
- Use VariablePackages for shared data
- Subscribe to relevant change notifications

=============================================================================
"""
'''
    
    def register_module(self, registration: ModuleRegistration) -> None:
        """
        Register a module with the circular exchange.
        
        Args:
            registration: Module registration information
        """
        # Skip registration if CEFR is disabled
        if not self.cefr_enabled:
            logger.debug(f"Skipping module registration (CEFR disabled): {registration.module_id}")
            return
            
        with self._lock:
            current = self.module_registry.value.copy()
            current[registration.module_id] = registration
            self.module_registry.set(current)
            logger.info(f"Registered module: {registration.module_id}")
    
    def get_module(self, module_id: str) -> Optional[ModuleRegistration]:
        """Get a registered module by ID."""
        if not self.cefr_enabled or self.module_registry is None:
            return None
        return self.module_registry.value.get(module_id)
    
    def get_all_modules(self) -> Dict[str, ModuleRegistration]:
        """Get all registered modules."""
        if not self.cefr_enabled or self.module_registry is None:
            return {}
        return self.module_registry.value.copy()
    
    def validate_module_imports(self) -> Dict[str, List[str]]:
        """
        Validate that all registered module imports are resolvable.
        
        This method checks that:
        1. All registered module IDs correspond to actual importable modules
        2. All declared dependencies are resolvable
        3. All exports are actually present in the modules
        
        Returns:
            Dictionary with 'errors' and 'warnings' lists
            
        Example:
            >>> from shared.circular_exchange import PROJECT_CONFIG
            >>> results = PROJECT_CONFIG.validate_module_imports()
            >>> if results['errors']:
            ...     print("Import validation failed:", results['errors'])
        """
        import importlib
        import importlib.util
        
        errors = []
        warnings = []
        
        for module_id, registration in self.module_registry.value.items():
            # Check if the module is importable
            try:
                spec = importlib.util.find_spec(module_id)
                if spec is None:
                    errors.append(f"Module '{module_id}' is registered but file does not exist")
            except (ModuleNotFoundError, ImportError) as e:
                errors.append(f"Module '{module_id}' cannot be imported: {e}")
            
            # Check dependencies
            for dep in registration.dependencies:
                try:
                    spec = importlib.util.find_spec(dep)
                    if spec is None:
                        warnings.append(f"Module '{module_id}' depends on '{dep}' which may not exist")
                except (ModuleNotFoundError, ImportError):
                    warnings.append(f"Module '{module_id}' has unresolvable dependency: '{dep}'")
        
        return {'errors': errors, 'warnings': warnings}
    
    def check_for_empty_imports(self, module_path: str) -> List[str]:
        """
        Check a module for imports that would fail at runtime.
        
        This helps prevent issues where a module file exists but imports
        from non-existent modules (the original issue this fix addresses).
        
        Args:
            module_path: Path to the Python module file to check
            
        Returns:
            List of problematic import statements found
        """
        import ast
        
        issues = []
        
        try:
            with open(module_path, 'r') as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith('shared.models.'):
                            # Check if the module file exists
                            parts = alias.name.split('.')
                            if len(parts) >= 3:
                                module_name = parts[2]
                                expected_path = Path(__file__).parent.parent.parent / 'models' / f'{module_name}.py'
                                if not expected_path.exists():
                                    issues.append(f"Import '{alias.name}' - file {expected_path} does not exist")
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith('shared.models.'):
                        parts = node.module.split('.')
                        if len(parts) >= 3:
                            module_name = parts[2]
                            expected_path = Path(__file__).parent.parent.parent / 'models' / f'{module_name}.py'
                            if not expected_path.exists():
                                issues.append(f"Import from '{node.module}' - file {expected_path} does not exist")
        
        except Exception as e:
            issues.append(f"Could not parse {module_path}: {e}")
        
        return issues

    def update_config(self, package_name: str, new_value: Any) -> bool:
        """
        Update a configuration package by name.
        
        This is the primary method for changing project-wide configuration.
        Changes will automatically propagate to all subscribers.
        
        Args:
            package_name: Name of the package to update (e.g., "debug", "logging_config")
            new_value: New value to set
            
        Returns:
            True if update was successful
        """
        try:
            package = getattr(self, package_name, None)
            if package and isinstance(package, VariablePackage):
                package.set(new_value)
                logger.info(f"Updated configuration: {package_name}")
                return True
            else:
                logger.warning(f"Unknown configuration package: {package_name}")
                return False
        except Exception as e:
            logger.error(f"Failed to update configuration {package_name}: {e}")
            return False
    
    def subscribe_to_all(self, callback: Callable[[str, PackageChange], None]) -> List[Callable]:
        """
        Subscribe to changes in all configuration packages.
        
        Args:
            callback: Function(package_name, change) to call on any change
            
        Returns:
            List of unsubscribe functions
        """
        unsubscribers = []
        packages = [
            ("debug", self.debug),
            ("project_name", self.project_name),
            ("project_version", self.project_version),
            ("security_policy", self.security_policy),
            ("coding_standards", self.coding_standards),
            ("module_registry", self.module_registry),
            ("paths", self.paths),
            ("logging_config", self.logging_config),
            ("ai_agent_config", self.ai_agent_config)
        ]
        
        for name, package in packages:
            unsub = package.subscribe(lambda c, n=name: callback(n, c))
            unsubscribers.append(unsub)
        
        return unsubscribers
    
    def get_compliance_header(
        self,
        module_name: str,
        file_path: str,
        description: str,
        dependencies: List[str] = None,
        exports: List[str] = None
    ) -> str:
        """
        Generate a compliance header for a module.
        
        AI agents should use this to add proper headers to all files.
        """
        template = self.ai_agent_config.value.get("compliance_header_template", "")
        return template.format(
            module_name=module_name,
            file_path=file_path,
            description=description,
            dependencies=", ".join(dependencies or []),
            exports=", ".join(exports or [])
        )

    # =========================================================================
    # GRAPH-BASED DEPENDENCY MANAGEMENT
    # =========================================================================
    
    def add_graph_node(
        self,
        module_id: str,
        degree: Optional[float] = None,
        weight: Optional[float] = None,
        connections: Optional[Set[str]] = None
    ) -> GraphNode:
        """
        Add or update a node in the dependency graph.
        
        Args:
            module_id: Unique identifier for the module
            degree: Connectivity level (default from _default_degrees)
            weight: Impact factor (default from _default_weights)
            connections: Set of directly connected module IDs
            
        Returns:
            The created or updated GraphNode
        """
        with self._lock:
            if degree is None:
                degree = self._default_degrees.value.get(module_id, 1.0)
            if weight is None:
                weight = self._default_weights.value.get(module_id, 0.5)
            
            node = GraphNode(
                module_id=module_id,
                degree=degree,
                weight=weight,
                connections=connections or set(),
                is_central_hub=(degree == math.inf)
            )
            self._graph_nodes[module_id] = node
            logger.debug(f"Added graph node: {module_id} (degree={degree}, weight={weight})")
            return node
    
    def add_graph_edge(
        self,
        source_id: str,
        target_id: str,
        weight: float = 1.0,
        bidirectional: bool = True
    ) -> GraphEdge:
        """
        Add an edge between two modules in the dependency graph.
        
        Args:
            source_id: Source module ID
            target_id: Target module ID
            weight: Edge weight for propagation strength
            bidirectional: Whether edge works both ways
            
        Returns:
            The created GraphEdge
        """
        with self._lock:
            edge = GraphEdge(
                source_id=source_id,
                target_id=target_id,
                weight=weight,
                bidirectional=bidirectional
            )
            self._graph_edges.append(edge)
            
            # Update node connections
            if source_id in self._graph_nodes:
                self._graph_nodes[source_id].connections.add(target_id)
            if bidirectional and target_id in self._graph_nodes:
                self._graph_nodes[target_id].connections.add(source_id)
            
            logger.debug(f"Added graph edge: {source_id} <-> {target_id} (weight={weight})")
            return edge
    
    def get_module_degree(self, module_id: str) -> float:
        """
        Get the degree (connectivity level) of a module.
        
        Args:
            module_id: Module identifier
            
        Returns:
            Degree value (1.0 for first-degree, higher for more connected)
        """
        if module_id in self._graph_nodes:
            return self._graph_nodes[module_id].degree
        return self._default_degrees.value.get(module_id, 1.0)
    
    def get_propagation_weight(self, module_id: str) -> float:
        """
        Get the propagation weight of a module.
        
        Args:
            module_id: Module identifier
            
        Returns:
            Weight value (0.0-1.0)
        """
        if module_id in self._graph_nodes:
            return self._graph_nodes[module_id].weight
        return self._default_weights.value.get(module_id, 0.5)
    
    def can_access_module(self, source_id: str, target_id: str) -> bool:
        """
        Check if a source module can access a target module based on degrees.
        
        Args:
            source_id: Source module ID
            target_id: Target module ID
            
        Returns:
            True if source can access target
        """
        source_degree = self.get_module_degree(source_id)
        target_degree = self.get_module_degree(target_id)
        
        # Central hub can access everything
        if source_degree == math.inf:
            return True
        
        # Check if source has sufficient degree
        return source_degree >= target_degree
    
    def get_affected_modules(
        self,
        source_id: str,
        max_depth: Optional[int] = None
    ) -> List[Tuple[str, float, int]]:
        """
        Get all modules that would be affected by a change in the source module.
        
        Uses breadth-first traversal with weight decay based on distance.
        
        Args:
            source_id: Module that changed
            max_depth: Maximum traversal depth (None = use module's degree)
            
        Returns:
            List of (module_id, effective_weight, depth) tuples
        """
        affected = []
        visited = set()
        source_weight = self.get_propagation_weight(source_id)
        source_degree = self.get_module_degree(source_id)
        
        if max_depth is None:
            max_depth = int(source_degree) if source_degree != math.inf else 100
        
        # BFS traversal
        queue = [(source_id, source_weight, 0)]
        
        while queue:
            current_id, current_weight, depth = queue.pop(0)
            
            if current_id in visited or depth > max_depth:
                continue
            
            visited.add(current_id)
            
            if current_id != source_id:
                affected.append((current_id, current_weight, depth))
            
            # Get connected modules
            if current_id in self._graph_nodes:
                for connected_id in self._graph_nodes[current_id].connections:
                    if connected_id not in visited:
                        # Apply weight decay based on distance
                        new_weight = current_weight * self.get_propagation_weight(connected_id)
                        queue.append((connected_id, new_weight, depth + 1))
            
            # Also check registered modules with dependencies
            for mod_id, registration in self.module_registry.value.items():
                if current_id in registration.dependencies and mod_id not in visited:
                    new_weight = current_weight * self.get_propagation_weight(mod_id)
                    queue.append((mod_id, new_weight, depth + 1))
        
        return sorted(affected, key=lambda x: (-x[1], x[2]))  # Sort by weight desc, depth asc
    
    def propagate_change(
        self,
        source_id: str,
        change_data: Any,
        mode: PropagationMode = PropagationMode.WEIGHTED,
        weight_threshold: float = 0.1
    ) -> List[str]:
        """
        Propagate a change from a source module to all affected modules.
        
        Args:
            source_id: Module where change originated
            change_data: Data describing the change
            mode: How to propagate (IMMEDIATE, BATCHED, CONDITIONAL, WEIGHTED)
            weight_threshold: Minimum weight to propagate (for WEIGHTED mode)
            
        Returns:
            List of module IDs that were notified
        """
        affected = self.get_affected_modules(source_id)
        notified = []
        
        for module_id, weight, depth in affected:
            if mode == PropagationMode.WEIGHTED and weight < weight_threshold:
                continue
            
            # Log the propagation
            logger.debug(
                f"Propagating change from {source_id} to {module_id} "
                f"(weight={weight:.2f}, depth={depth})"
            )
            notified.append(module_id)
        
        return notified


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

# This is the single source of truth for all project configuration.
# All modules should import and use this instance.
PROJECT_CONFIG = ProjectConfiguration()


# =============================================================================
# MODULE SELF-REGISTRATION
# =============================================================================

# Register this module with the circular exchange
PROJECT_CONFIG.register_module(ModuleRegistration(
    module_id="project_config",
    file_path="shared/circular_exchange/project_config.py",
    description="Central configuration hub for variable-based project management",
    dependencies=[],
    exports=["PROJECT_CONFIG", "ProjectConfiguration", "ModuleRegistration", 
             "SecurityPolicy", "CodingStandards", "GraphNode", "GraphEdge", "PropagationMode"],
    is_circular_exchange_compliant=True,
    compliance_version="2.0.0"
))
