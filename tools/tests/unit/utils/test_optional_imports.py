"""
Tests for optional_imports utility module.
"""

import pytest
import sys
from unittest.mock import patch, MagicMock
from shared.utils.optional_imports import OptionalImport


class TestOptionalImport:
    """Test OptionalImport class."""
    
    def test_successful_module_import(self):
        """Test importing an available module."""
        opt_import = OptionalImport('os', suppress_warning=True)
        
        assert opt_import.is_available
        assert opt_import.module is not None
        assert opt_import.error is None
        assert bool(opt_import) is True
    
    def test_failed_module_import(self):
        """Test importing a non-existent module."""
        opt_import = OptionalImport('nonexistent_module_xyz', suppress_warning=True)
        
        assert not opt_import.is_available
        assert opt_import.module is None
        assert opt_import.error is not None
        assert bool(opt_import) is False
    
    def test_attribute_import(self):
        """Test importing a specific attribute from a module."""
        opt_import = OptionalImport('os.path.join', suppress_warning=True)
        
        assert opt_import.is_available
        assert opt_import.module is not None
        assert callable(opt_import.module)
    
    def test_install_message_in_warning(self, caplog):
        """Test that install message appears in warning."""
        OptionalImport(
            'nonexistent_module_xyz',
            install_msg='pip install nonexistent>=1.0.0'
        )
        
        assert 'pip install nonexistent>=1.0.0' in caplog.text
    
    def test_custom_warning_message(self, caplog):
        """Test custom warning message."""
        custom_msg = "Custom warning message here"
        OptionalImport(
            'nonexistent_module_xyz',
            warning_msg=custom_msg
        )
        
        assert custom_msg in caplog.text
    
    def test_suppress_warning(self, caplog):
        """Test suppressing warning on import failure."""
        caplog.clear()
        OptionalImport('nonexistent_module_xyz', suppress_warning=True)
        
        # Should not have any warnings
        assert len(caplog.records) == 0
    
    def test_attribute_access_on_available_module(self):
        """Test accessing attributes on successfully imported module."""
        opt_import = OptionalImport('os', suppress_warning=True)
        
        # Should be able to access os.path
        assert hasattr(opt_import.module, 'path')
    
    def test_attribute_access_on_unavailable_module(self):
        """Test accessing attributes on failed import raises AttributeError."""
        opt_import = OptionalImport('nonexistent_module_xyz', suppress_warning=True)
        
        with pytest.raises(AttributeError, match="is not available"):
            _ = opt_import.some_attribute
    
    def test_try_imports_all_successful(self):
        """Test try_imports with all successful imports."""
        imports = OptionalImport.try_imports({
            'os': 'os',
            'sys': 'sys',
            'join': 'os.path.join'
        }, suppress_warning=True)
        
        assert imports['OS_AVAILABLE'] is True
        assert imports['SYS_AVAILABLE'] is True
        assert imports['JOIN_AVAILABLE'] is True
        assert imports['os'] is not None
        assert imports['sys'] is not None
        assert imports['join'] is not None
    
    def test_try_imports_partial_failure(self):
        """Test try_imports with some failed imports."""
        imports = OptionalImport.try_imports({
            'os': 'os',
            'fake': 'nonexistent_module_xyz'
        }, suppress_warning=True)
        
        assert imports['OS_AVAILABLE'] is True
        assert imports['FAKE_AVAILABLE'] is False
        assert imports['os'] is not None
        assert imports['fake'] is None
    
    def test_try_imports_shows_warning(self, caplog):
        """Test try_imports shows warning when imports fail."""
        caplog.clear()
        OptionalImport.try_imports({
            'fake': 'nonexistent_module_xyz'
        }, install_msg='pip install fake')
        
        assert 'pip install fake' in caplog.text
    
    def test_create_availability_flag_single_import(self):
        """Test create_availability_flag with single import."""
        modules, available = OptionalImport.create_availability_flag(
            'os',
            suppress_warning=True
        )
        
        assert available is True
        assert 'os' in modules
        assert modules['os'] is not None
    
    def test_create_availability_flag_multiple_imports(self):
        """Test create_availability_flag with multiple imports."""
        modules, available = OptionalImport.create_availability_flag(
            ['os', 'sys', 'json'],
            suppress_warning=True
        )
        
        assert available is True
        assert 'os' in modules
        assert 'sys' in modules
        assert 'json' in modules
    
    def test_create_availability_flag_with_failure(self):
        """Test create_availability_flag when some imports fail."""
        modules, available = OptionalImport.create_availability_flag(
            ['os', 'nonexistent_module_xyz'],
            suppress_warning=True
        )
        
        assert available is False
        assert 'os' in modules
        assert 'nonexistent_module_xyz' in modules
        assert modules['os'] is not None
        assert modules['nonexistent_module_xyz'] is None


class TestOptionalImportIntegration:
    """Integration tests for OptionalImport usage patterns."""
    
    def test_common_pattern_storage_handler(self):
        """Test pattern used in storage handlers."""
        # Simulate the pattern from s3_handler.py
        imports = OptionalImport.try_imports({
            'json': 'json',  # Use json as stand-in for boto3
            'JSONDecodeError': 'json.JSONDecodeError'
        }, install_msg='pip install json', suppress_warning=True)
        
        JSON_AVAILABLE = imports['JSON_AVAILABLE']
        json_module = imports['json']
        
        assert JSON_AVAILABLE is True
        assert json_module is not None
        
        # Should be able to use the module
        result = json_module.dumps({'test': 'data'})
        assert isinstance(result, str)
    
    def test_common_pattern_training_handler(self):
        """Test pattern used in training handlers."""
        # Simulate checking availability before use
        opt_import = OptionalImport('os', suppress_warning=True)
        
        if opt_import.is_available:
            # Use the module
            path = opt_import.module.path.join('a', 'b')
            assert 'a' in path
    
    def test_graceful_degradation(self):
        """Test graceful degradation when module unavailable."""
        opt_import = OptionalImport('nonexistent_module', suppress_warning=True)
        
        if not opt_import.is_available:
            # Should handle gracefully
            assert opt_import.module is None
            
            # Can still check error
            assert opt_import.error is not None
            assert isinstance(opt_import.error, ImportError)
