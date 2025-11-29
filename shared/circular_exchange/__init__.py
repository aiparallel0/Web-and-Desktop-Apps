"""
Circular Information Exchange Framework

This framework provides a base model for project development which works like a 
circular information exchange. When a file is updated and changed, imports of 
this file to other files are automatically notified since the data transfer 
buses work with variable-based packages.

Key Components:
- DependencyRegistry: Tracks module dependencies
- VariablePackage: Variable-based data transfer container
- ChangeNotifier: Propagates updates when files change
- CircularExchange: Main orchestrator for the exchange mechanism
"""

from .dependency_registry import DependencyRegistry
from .variable_package import VariablePackage
from .change_notifier import ChangeNotifier
from .circular_exchange import CircularExchange

__all__ = [
    'DependencyRegistry',
    'VariablePackage',
    'ChangeNotifier',
    'CircularExchange'
]
