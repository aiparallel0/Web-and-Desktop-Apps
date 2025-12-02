"""Core components of the Circular Exchange Framework."""
from .variable_package import VariablePackage, PackageRegistry, PackageChange
from .project_config import PROJECT_CONFIG, ModuleRegistration
from .change_notifier import ChangeNotifier
from .dependency_registry import DependencyRegistry
from .circular_exchange import CircularExchange
from .module_container import ModuleContainer
from .style_checker import StyleChecker
