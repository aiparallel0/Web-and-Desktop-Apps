"""
=============================================================================
OPTIONAL IMPORTS UTILITY - Graceful Handling of Optional Dependencies
=============================================================================

Provides utilities for gracefully handling optional dependencies across
the application. Eliminates repetitive try/except ImportError patterns.

Usage:
    from shared.utils.optional_imports import OptionalImport
    
    # Simple import
    boto3 = OptionalImport('boto3', 'pip install boto3>=1.34.0')
    if boto3.is_available:
        s3_client = boto3.module.client('s3')
    
    # Multiple imports from same package
    imports = OptionalImport.try_imports({
        'boto3': 'boto3',
        'ClientError': 'botocore.exceptions.ClientError',
        'NoCredentialsError': 'botocore.exceptions.NoCredentialsError'
    }, install_msg='pip install boto3>=1.34.0')

=============================================================================
"""

import logging
import importlib
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)


class OptionalImport:
    """
    Wrapper for optional imports that may not be installed.
    
    Provides clean interface for checking availability and accessing
    the imported module or attribute.
    """
    
    def __init__(
        self,
        import_path: str,
        install_msg: Optional[str] = None,
        warning_msg: Optional[str] = None,
        suppress_warning: bool = False
    ):
        """
        Initialize optional import.
        
        Args:
            import_path: Full import path (e.g., 'boto3' or 'botocore.exceptions.ClientError')
            install_msg: Installation instruction to show on import failure
            warning_msg: Custom warning message (overrides default)
            suppress_warning: If True, don't log warning on import failure
        """
        self.import_path = import_path
        self.install_msg = install_msg
        self._module = None
        self._is_available = False
        self._error = None
        
        # Try to import
        try:
            parts = import_path.split('.')
            if len(parts) == 1:
                # Simple module import
                self._module = importlib.import_module(parts[0])
            else:
                # Import attribute from module
                module_path = '.'.join(parts[:-1])
                attr_name = parts[-1]
                module = importlib.import_module(module_path)
                self._module = getattr(module, attr_name)
            
            self._is_available = True
            
        except (ImportError, AttributeError) as e:
            self._error = e
            self._is_available = False
            
            if not suppress_warning:
                if warning_msg:
                    logger.warning(warning_msg)
                else:
                    msg = f"{import_path} not installed."
                    if install_msg:
                        msg += f" Run: {install_msg}"
                    logger.warning(msg)
    
    @property
    def is_available(self) -> bool:
        """Check if the import was successful."""
        return self._is_available
    
    @property
    def module(self) -> Any:
        """
        Get the imported module/class/function.
        
        Returns None if import failed.
        """
        return self._module
    
    @property
    def error(self) -> Optional[Exception]:
        """Get the import error if one occurred."""
        return self._error
    
    def __bool__(self) -> bool:
        """Allow using in boolean context."""
        return self._is_available
    
    def __getattr__(self, name: str) -> Any:
        """
        Allow direct attribute access on the imported module.
        
        Raises AttributeError if module not available.
        """
        if not self._is_available:
            raise AttributeError(
                f"Cannot access '{name}' - {self.import_path} is not available"
            )
        return getattr(self._module, name)
    
    @staticmethod
    def try_imports(
        imports: Dict[str, str],
        install_msg: Optional[str] = None,
        suppress_warning: bool = False
    ) -> Dict[str, Any]:
        """
        Try importing multiple modules/attributes.
        
        Args:
            imports: Dict mapping result names to import paths
                    e.g., {'boto3': 'boto3', 'ClientError': 'botocore.exceptions.ClientError'}
            install_msg: Installation instruction for all imports
            suppress_warning: If True, suppress individual warnings
        
        Returns:
            Dict with same keys, values are imported objects or None if failed.
            Also includes '{NAME}_AVAILABLE' boolean for each import.
        
        Example:
            >>> imports = OptionalImport.try_imports({
            ...     'boto3': 'boto3',
            ...     'ClientError': 'botocore.exceptions.ClientError'
            ... }, install_msg='pip install boto3')
            >>> if imports['BOTO3_AVAILABLE']:
            ...     client = imports['boto3'].client('s3')
        """
        results = {}
        all_available = True
        
        for name, import_path in imports.items():
            opt_import = OptionalImport(
                import_path,
                install_msg=None,  # Don't show message for individual imports
                suppress_warning=True
            )
            results[name] = opt_import.module
            results[f"{name.upper()}_AVAILABLE"] = opt_import.is_available
            
            if not opt_import.is_available:
                all_available = False
        
        # Show single warning if any import failed
        if not all_available and not suppress_warning:
            package_name = list(imports.values())[0].split('.')[0]
            msg = f"Some {package_name} dependencies not installed."
            if install_msg:
                msg += f" Run: {install_msg}"
            logger.warning(msg)
        
        return results
    
    @staticmethod
    def create_availability_flag(
        import_paths: Union[str, List[str]],
        install_msg: Optional[str] = None,
        suppress_warning: bool = False
    ) -> tuple:
        """
        Create module imports with availability flag.
        
        This is a convenience method that returns a tuple of
        (modules_dict, is_available_flag) for use in the common pattern.
        
        Args:
            import_paths: Single import path or list of import paths
            install_msg: Installation instruction
        
        Returns:
            Tuple of (dict of imported modules, bool indicating if all available)
        
        Example:
            >>> imports, BOTO3_AVAILABLE = OptionalImport.create_availability_flag(
            ...     ['boto3', 'botocore.exceptions.ClientError'],
            ...     'pip install boto3>=1.34.0'
            ... )
            >>> if BOTO3_AVAILABLE:
            ...     client = imports['boto3'].client('s3')
        """
        if isinstance(import_paths, str):
            import_paths = [import_paths]
        
        modules = {}
        all_available = True
        
        for import_path in import_paths:
            opt_import = OptionalImport(import_path, install_msg, suppress_warning=True)
            # Use last part of path as key
            key = import_path.split('.')[-1]
            modules[key] = opt_import.module
            if not opt_import.is_available:
                all_available = False
        
        # Show warning if any failed
        if not all_available and install_msg and not suppress_warning:
            package_name = import_paths[0].split('.')[0]
            logger.warning(f"{package_name} not installed. Run: {install_msg}")
        
        return modules, all_available


# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    PROJECT_CONFIG.register_module(ModuleRegistration(
        module_id="shared.utils.optional_imports",
        file_path=__file__,
        description="Utilities for gracefully handling optional dependencies",
        dependencies=[],
        exports=["OptionalImport"]
    ))
except Exception:
    pass  # Ignore registration errors
