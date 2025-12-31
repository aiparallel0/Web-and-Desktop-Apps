"""
Circular Exchange Framework (CEF) - Minimal Core
================================================

Core module registry components for developer tooling.
Used by static analysis tools in tools/cefr/.

Note: Runtime module registration has been removed. This module
is kept for backward compatibility and future static analysis tools.
"""

# Core components - minimal set
from .core.project_config import (
    PROJECT_CONFIG, ProjectConfiguration, ModuleRegistration,
)

__all__ = [
    # Core registry components
    'PROJECT_CONFIG', 
    'ProjectConfiguration', 
    'ModuleRegistration',
]

__version__ = '4.0.0'
