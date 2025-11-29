"""
=============================================================================
CIRCULAR EXCHANGE - Module Container System
=============================================================================

Module: shared.circular_exchange.module_container
Path: shared/circular_exchange/module_container.py
Description: Docker-like container system for file isolation and connection
Compliance Version: 2.0.0

CONTAINER ARCHITECTURE:
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MODULE CONTAINER SYSTEM                              │
│                    (Like Docker, but for Python modules)                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   Container A   │    │   Container B   │    │   Container C   │         │
│  │  ┌───────────┐  │    │  ┌───────────┐  │    │  ┌───────────┐  │         │
│  │  │  Module   │  │    │  │  Module   │  │    │  │  Module   │  │         │
│  │  │  Code     │  │    │  │  Code     │  │    │  │  Code     │  │         │
│  │  └───────────┘  │    │  └───────────┘  │    │  └───────────┘  │         │
│  │  ┌───────────┐  │    │  ┌───────────┐  │    │  ┌───────────┐  │         │
│  │  │ Variables │◄─┼────┼─►│ Variables │◄─┼────┼─►│ Variables │  │         │
│  │  │ (Ports)   │  │    │  │ (Ports)   │  │    │  │ (Ports)   │  │         │
│  │  └───────────┘  │    │  └───────────┘  │    │  └───────────┘  │         │
│  │  ┌───────────┐  │    │  ┌───────────┐  │    │  ┌───────────┐  │         │
│  │  │  Imports  │  │    │  │  Imports  │  │    │  │  Imports  │  │         │
│  │  │ (Depends) │  │    │  │ (Depends) │  │    │  │ (Depends) │  │         │
│  │  └───────────┘  │    │  └───────────┘  │    │  └───────────┘  │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│           │                     │                      │                    │
│           └─────────────────────┼──────────────────────┘                    │
│                                 │                                            │
│                    ┌────────────┴────────────┐                              │
│                    │   COMPATIBILITY LAYER    │                              │
│                    │  (Format Standardization)│                              │
│                    └─────────────────────────┘                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

FEATURES:
- Container isolation: Each module runs in its own context
- Variable ports: VariablePackages act as communication ports
- Dependency management: Like Docker Compose depends_on
- Health checks: Validate module compatibility
- Format standardization: Ensure consistent code structure

AI AGENT INSTRUCTIONS:
When working with modules:
1. Treat each file as a container with defined interfaces
2. Use VariablePackages for all inter-module communication
3. Define clear dependency chains
4. Run compatibility checks before integrating new code
5. Standardize format when integrating code from different prompts

=============================================================================
"""

import logging
import threading
import hashlib
import re
import ast
from typing import Dict, Any, Optional, List, Set, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class ContainerStatus(Enum):
    """Status of a module container."""
    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    INCOMPATIBLE = "incompatible"


class CompatibilityLevel(Enum):
    """Compatibility level between modules."""
    FULL = "full"           # Fully compatible
    PARTIAL = "partial"     # Some adjustments needed
    BREAKING = "breaking"   # Breaking changes detected
    UNKNOWN = "unknown"     # Cannot determine


@dataclass
class ContainerPort:
    """
    A port for inter-container communication (like Docker ports).
    Wraps a VariablePackage for type-safe communication.
    """
    name: str
    port_type: str  # 'input', 'output', 'bidirectional'
    data_type: str  # Expected data type
    required: bool = True
    default_value: Any = None
    description: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'port_type': self.port_type,
            'data_type': self.data_type,
            'required': self.required,
            'description': self.description
        }


@dataclass
class ContainerDependency:
    """
    A dependency on another container (like Docker depends_on).
    """
    container_id: str
    condition: str = "running"  # 'running', 'healthy', 'completed'
    required: bool = True
    version_constraint: Optional[str] = None  # e.g., ">=1.0.0"
    
    def to_dict(self) -> Dict:
        return {
            'container_id': self.container_id,
            'condition': self.condition,
            'required': self.required,
            'version_constraint': self.version_constraint
        }


@dataclass
class CompatibilityReport:
    """
    Report on compatibility between code versions or modules.
    """
    source_id: str
    target_id: str
    level: CompatibilityLevel
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    auto_fixable: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'source_id': self.source_id,
            'target_id': self.target_id,
            'level': self.level.value,
            'issues': self.issues,
            'suggestions': self.suggestions,
            'auto_fixable': self.auto_fixable,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ModuleContainer:
    """
    A container wrapping a Python module (like a Docker container).
    
    Each container has:
    - Isolated context
    - Defined ports for communication
    - Dependencies on other containers
    - Health status
    - Version tracking
    """
    container_id: str
    module_path: str
    version: str = "1.0.0"
    status: ContainerStatus = ContainerStatus.CREATED
    ports: Dict[str, ContainerPort] = field(default_factory=dict)
    dependencies: List[ContainerDependency] = field(default_factory=list)
    environment: Dict[str, Any] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    health_check: Optional[Callable] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    code_hash: Optional[str] = None
    
    def add_port(self, port: ContainerPort) -> None:
        """Add a communication port."""
        self.ports[port.name] = port
    
    def add_dependency(self, dependency: ContainerDependency) -> None:
        """Add a dependency on another container."""
        self.dependencies.append(dependency)
    
    def set_environment(self, key: str, value: Any) -> None:
        """Set an environment variable."""
        self.environment[key] = value
    
    def get_environment(self, key: str, default: Any = None) -> Any:
        """Get an environment variable."""
        return self.environment.get(key, default)
    
    def is_healthy(self) -> bool:
        """Check if container is healthy."""
        if self.health_check:
            try:
                return self.health_check()
            except Exception:
                return False
        return self.status == ContainerStatus.RUNNING
    
    def to_dict(self) -> Dict:
        return {
            'container_id': self.container_id,
            'module_path': self.module_path,
            'version': self.version,
            'status': self.status.value,
            'ports': {k: v.to_dict() for k, v in self.ports.items()},
            'dependencies': [d.to_dict() for d in self.dependencies],
            'environment': self.environment,
            'labels': self.labels,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'code_hash': self.code_hash
        }


class ContainerOrchestrator:
    """
    Orchestrates module containers (like Docker Compose).
    
    Responsibilities:
    - Create and manage containers
    - Handle dependencies
    - Check compatibility
    - Standardize code format
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._containers: Dict[str, ModuleContainer] = {}
        self._lock = threading.RLock()
        self._compatibility_cache: Dict[str, CompatibilityReport] = {}
        
        # Code format standards
        self._format_standards = {
            'require_docstrings': True,
            'require_type_hints': True,
            'max_line_length': 100,
            'require_circular_exchange_header': True,
            'require_module_registration': True,
            'naming_convention': 'snake_case',
            'import_order': ['stdlib', 'third_party', 'local', 'circular_exchange']
        }
        
        self._initialized = True
        logger.info("ContainerOrchestrator initialized")
    
    def create_container(
        self,
        container_id: str,
        module_path: str,
        version: str = "1.0.0",
        ports: Optional[List[ContainerPort]] = None,
        dependencies: Optional[List[ContainerDependency]] = None,
        environment: Optional[Dict[str, Any]] = None
    ) -> ModuleContainer:
        """
        Create a new module container.
        
        Args:
            container_id: Unique identifier
            module_path: Path to the Python module
            version: Container version
            ports: Communication ports
            dependencies: Dependencies on other containers
            environment: Environment variables
            
        Returns:
            The created ModuleContainer
        """
        with self._lock:
            container = ModuleContainer(
                container_id=container_id,
                module_path=module_path,
                version=version
            )
            
            if ports:
                for port in ports:
                    container.add_port(port)
            
            if dependencies:
                for dep in dependencies:
                    container.add_dependency(dep)
            
            if environment:
                container.environment = environment
            
            # Calculate code hash
            container.code_hash = self._calculate_code_hash(module_path)
            
            self._containers[container_id] = container
            logger.info(f"Created container: {container_id}")
            return container
    
    def get_container(self, container_id: str) -> Optional[ModuleContainer]:
        """Get a container by ID."""
        return self._containers.get(container_id)
    
    def list_containers(self) -> List[ModuleContainer]:
        """List all containers."""
        return list(self._containers.values())
    
    def start_container(self, container_id: str) -> bool:
        """
        Start a container (validate and mark as running).
        
        Checks dependencies before starting.
        """
        with self._lock:
            container = self._containers.get(container_id)
            if not container:
                return False
            
            # Check dependencies
            for dep in container.dependencies:
                dep_container = self._containers.get(dep.container_id)
                if dep.required and (not dep_container or 
                                     dep_container.status != ContainerStatus.RUNNING):
                    logger.warning(
                        f"Cannot start {container_id}: dependency {dep.container_id} not running"
                    )
                    return False
            
            container.status = ContainerStatus.RUNNING
            container.last_updated = datetime.now()
            logger.info(f"Started container: {container_id}")
            return True
    
    def stop_container(self, container_id: str) -> bool:
        """Stop a container."""
        with self._lock:
            container = self._containers.get(container_id)
            if not container:
                return False
            
            container.status = ContainerStatus.STOPPED
            container.last_updated = datetime.now()
            logger.info(f"Stopped container: {container_id}")
            return True
    
    def check_compatibility(
        self,
        source_code: str,
        target_container_id: str,
        source_id: str = "new_code"
    ) -> CompatibilityReport:
        """
        Check compatibility of new code with an existing container.
        
        This is used when AI agents submit new code to ensure it's compatible
        with the existing codebase.
        
        Args:
            source_code: New code to check
            target_container_id: Container to check against
            source_id: Identifier for the source code
            
        Returns:
            CompatibilityReport with issues and suggestions
        """
        issues = []
        suggestions = []
        auto_fixable = True
        
        # Check for circular exchange header
        if 'CIRCULAR EXCHANGE COMPLIANT MODULE' not in source_code:
            issues.append("Missing Circular Exchange compliance header")
            suggestions.append("Add compliance header using PROJECT_CONFIG.get_compliance_header()")
            auto_fixable = True
        
        # Check for PROJECT_CONFIG import
        if 'PROJECT_CONFIG' not in source_code and 'project_config' not in source_code:
            issues.append("Missing PROJECT_CONFIG import")
            suggestions.append("Add: from shared.circular_exchange.project_config import PROJECT_CONFIG")
        
        # Check for module registration
        if 'register_module' not in source_code:
            issues.append("Module not registered with CircularExchange")
            suggestions.append("Add PROJECT_CONFIG.register_module() call")
        
        # Check for docstrings
        if self._format_standards['require_docstrings']:
            try:
                tree = ast.parse(source_code)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                        docstring = ast.get_docstring(node)
                        if not docstring and isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                            if not node.name.startswith('_'):
                                issues.append(f"Missing docstring for {node.name}")
            except SyntaxError as e:
                issues.append(f"Syntax error in code: {e}")
                auto_fixable = False
        
        # Check for type hints
        if self._format_standards['require_type_hints']:
            try:
                tree = ast.parse(source_code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if not node.name.startswith('_'):
                            if node.returns is None:
                                suggestions.append(f"Consider adding return type hint for {node.name}")
            except SyntaxError:
                pass  # Already caught above
        
        # Determine compatibility level
        if not issues:
            level = CompatibilityLevel.FULL
        elif all(auto_fixable for _ in issues):
            level = CompatibilityLevel.PARTIAL
        else:
            level = CompatibilityLevel.BREAKING
        
        report = CompatibilityReport(
            source_id=source_id,
            target_id=target_container_id,
            level=level,
            issues=issues,
            suggestions=suggestions,
            auto_fixable=auto_fixable
        )
        
        # Cache the report
        cache_key = f"{source_id}:{target_container_id}"
        self._compatibility_cache[cache_key] = report
        
        return report
    
    def standardize_code(self, code: str, module_id: str) -> str:
        """
        Standardize code format to match project conventions.
        
        This ensures all code from different AI prompts follows
        the same format and structure.
        
        Args:
            code: Code to standardize
            module_id: Module identifier
            
        Returns:
            Standardized code
        """
        standardized = code
        
        # Add compliance header if missing
        if 'CIRCULAR EXCHANGE COMPLIANT MODULE' not in standardized:
            header = self._generate_compliance_header(module_id)
            # Find first non-comment line
            lines = standardized.split('\n')
            insert_idx = 0
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    insert_idx = i
                    break
            lines.insert(insert_idx, header)
            standardized = '\n'.join(lines)
        
        # Ensure PROJECT_CONFIG import exists
        if 'from shared.circular_exchange.project_config import PROJECT_CONFIG' not in standardized:
            # Find import section
            lines = standardized.split('\n')
            import_idx = 0
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    import_idx = i + 1
            
            import_line = "\n# Circular Exchange Integration\ntry:\n    from shared.circular_exchange.project_config import PROJECT_CONFIG, ModuleRegistration\nexcept ImportError:\n    PROJECT_CONFIG = None\n"
            lines.insert(import_idx, import_line)
            standardized = '\n'.join(lines)
        
        return standardized
    
    def _generate_compliance_header(self, module_id: str) -> str:
        """Generate a compliance header for a module."""
        return f'''"""
=============================================================================
CIRCULAR EXCHANGE COMPLIANT MODULE
=============================================================================

Module: {module_id}
Compliance Version: 2.0.0
Container System: Enabled

CIRCULAR EXCHANGE INTEGRATION:
This module is integrated with the Circular Information Exchange Framework.
It operates as an isolated container with defined ports for communication.

AI AGENT INSTRUCTIONS:
- Use PROJECT_CONFIG for all configuration values
- Define clear input/output ports using ContainerPort
- Register dependencies using ContainerDependency
- Run compatibility checks before integrating new code

=============================================================================
"""
'''
    
    def _calculate_code_hash(self, module_path: str) -> Optional[str]:
        """Calculate hash of module code for change detection."""
        try:
            path = Path(module_path)
            if path.exists():
                content = path.read_text()
                return hashlib.sha256(content.encode()).hexdigest()[:16]
        except Exception:
            pass
        return None
    
    def validate_all_containers(self) -> Dict[str, bool]:
        """
        Validate all containers and their dependencies.
        
        Returns:
            Dict mapping container_id to validation status
        """
        results = {}
        
        for container_id, container in self._containers.items():
            # Check dependencies
            deps_valid = True
            for dep in container.dependencies:
                if dep.required and dep.container_id not in self._containers:
                    deps_valid = False
                    break
            
            # Check health
            is_healthy = container.is_healthy()
            
            results[container_id] = deps_valid and is_healthy
        
        return results


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

CONTAINER_ORCHESTRATOR = ContainerOrchestrator()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_container(
    container_id: str,
    module_path: str,
    **kwargs
) -> ModuleContainer:
    """Create a new module container."""
    return CONTAINER_ORCHESTRATOR.create_container(container_id, module_path, **kwargs)


def check_compatibility(source_code: str, target_id: str) -> CompatibilityReport:
    """Check code compatibility with existing module."""
    return CONTAINER_ORCHESTRATOR.check_compatibility(source_code, target_id)


def standardize_code(code: str, module_id: str) -> str:
    """Standardize code to project conventions."""
    return CONTAINER_ORCHESTRATOR.standardize_code(code, module_id)
