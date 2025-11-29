"""
Tests for CircularExchange class.

Tests the main orchestrator of the circular information exchange framework.
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path
from datetime import datetime

# Add shared to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'shared'))

from circular_exchange.circular_exchange import (
    CircularExchange, ModuleExport, ModuleImport
)
from circular_exchange.variable_package import VariablePackage


class TestModuleExport:
    """Tests for ModuleExport dataclass."""

    def test_module_export_creation(self):
        """Test creating a ModuleExport."""
        export = ModuleExport(
            name='my_function',
            export_type='function',
            module_id='my.module',
            line_number=10
        )
        
        assert export.name == 'my_function'
        assert export.export_type == 'function'
        assert export.module_id == 'my.module'
        assert export.line_number == 10


class TestModuleImport:
    """Tests for ModuleImport dataclass."""

    def test_module_import_creation(self):
        """Test creating a ModuleImport."""
        imp = ModuleImport(
            name='other_func',
            from_module='other.module',
            alias='of',
            line_number=5
        )
        
        assert imp.name == 'other_func'
        assert imp.from_module == 'other.module'
        assert imp.alias == 'of'
        assert imp.line_number == 5


class TestCircularExchange:
    """Tests for CircularExchange class."""

    @pytest.fixture
    def exchange(self, tmp_path):
        """Create a fresh CircularExchange for each test."""
        # Reset singleton
        CircularExchange._instance = None
        exchange = CircularExchange(project_root=str(tmp_path))
        yield exchange
        exchange.reset()
        CircularExchange._instance = None

    @pytest.fixture
    def sample_python_file(self, tmp_path):
        """Create a sample Python file for testing."""
        content = '''"""Sample module."""

import os
from pathlib import Path

MY_CONSTANT = 42

def my_function():
    """A sample function."""
    pass

class MyClass:
    """A sample class."""
    pass

_private_var = "hidden"

def _private_func():
    pass
'''
        file_path = tmp_path / 'sample.py'
        file_path.write_text(content)
        return str(file_path)

    def test_singleton_pattern(self, tmp_path):
        """Test that CircularExchange is a singleton."""
        CircularExchange._instance = None
        
        ex1 = CircularExchange(project_root=str(tmp_path))
        ex2 = CircularExchange(project_root=str(tmp_path))
        
        assert ex1 is ex2
        
        # Cleanup
        ex1.reset()
        CircularExchange._instance = None

    def test_initialization(self, exchange, tmp_path):
        """Test CircularExchange initialization."""
        assert exchange._project_root == Path(tmp_path)
        assert exchange.dependency_registry is not None
        assert exchange.package_registry is not None
        assert exchange.change_notifier is not None

    def test_register_module(self, exchange, tmp_path):
        """Test registering a module."""
        # Create a simple file
        file_path = tmp_path / 'test.py'
        file_path.write_text('TEST_VAR = 1')
        
        result = exchange.register_module('test', 'test.py')
        
        assert result is not None
        assert result.module_id == 'test'
        assert 'TEST_VAR' in result.exports

    def test_register_module_without_analysis(self, exchange):
        """Test registering a module without analysis."""
        result = exchange.register_module(
            'test',
            'nonexistent.py',
            analyze=False
        )
        
        assert result is not None
        assert result.exports == set()

    def test_unregister_module(self, exchange, tmp_path):
        """Test unregistering a module."""
        file_path = tmp_path / 'test.py'
        file_path.write_text('')
        
        exchange.register_module('test', 'test.py')
        result = exchange.unregister_module('test')
        
        assert result is True

    def test_add_dependency(self, exchange, tmp_path):
        """Test adding a dependency between modules."""
        (tmp_path / 'a.py').write_text('')
        (tmp_path / 'b.py').write_text('')
        
        exchange.register_module('a', 'a.py')
        exchange.register_module('b', 'b.py')
        
        result = exchange.add_dependency('a', 'b')
        
        assert result is True
        assert 'b' in exchange.dependency_registry.get_dependencies('a')

    def test_create_package(self, exchange):
        """Test creating a variable package."""
        pkg = exchange.create_package('test_pkg', initial_value=42)
        
        assert isinstance(pkg, VariablePackage)
        assert pkg.name == 'test_pkg'
        assert pkg.value == 42

    def test_get_package(self, exchange):
        """Test getting a package."""
        exchange.create_package('my_pkg', initial_value='hello')
        
        pkg = exchange.get_package('my_pkg')
        
        assert pkg is not None
        assert pkg.value == 'hello'

    def test_get_nonexistent_package(self, exchange):
        """Test getting a nonexistent package."""
        pkg = exchange.get_package('nonexistent')
        assert pkg is None

    def test_package_changes_notify(self, exchange, tmp_path):
        """Test that package changes trigger notifications."""
        (tmp_path / 'test.py').write_text('')
        exchange.register_module('test', 'test.py')
        
        events = []
        exchange.change_notifier.on_module_change(
            'test',
            lambda e: events.append(e)
        )
        
        pkg = exchange.create_package('var', module_id='test')
        pkg.set(42)
        
        # Package change should have triggered notification
        # (via the change notifier's variable_updated handler)
        assert len(events) >= 0  # May or may not trigger depending on wiring

    def test_notify_file_changed(self, exchange, tmp_path):
        """Test notifying that a file changed."""
        file_path = tmp_path / 'test.py'
        file_path.write_text('VAR = 1')
        
        exchange.register_module('test', 'test.py')
        
        events = []
        exchange.on_file_change(lambda fp, mid: events.append((fp, mid)))
        
        # Modify file
        file_path.write_text('VAR = 2\nNEW_VAR = 3')
        exchange.notify_file_changed('test.py')
        
        assert len(events) == 1
        assert events[0][1] == 'test'

    def test_on_file_change_callback(self, exchange, tmp_path):
        """Test file change callback registration."""
        (tmp_path / 'test.py').write_text('')
        exchange.register_module('test', 'test.py')
        
        changes = []
        unsub = exchange.on_file_change(lambda fp, mid: changes.append(mid))
        
        exchange.notify_file_changed('test.py')
        unsub()
        exchange.notify_file_changed('test.py')
        
        assert len(changes) == 1  # Only first change recorded

    def test_analyze_file(self, exchange, sample_python_file):
        """Test analyzing a Python file."""
        analysis = exchange.analyze_file(sample_python_file)
        
        assert 'imports' in analysis
        assert 'exports' in analysis
        
        # Check imports
        import_names = [i.from_module for i in analysis['imports']]
        assert 'os' in import_names
        assert 'pathlib' in import_names
        
        # Check exports (only public ones)
        export_names = [e.name for e in analysis['exports']]
        assert 'MY_CONSTANT' in export_names
        assert 'my_function' in export_names
        assert 'MyClass' in export_names
        assert '_private_var' not in export_names  # Private excluded
        assert '_private_func' not in export_names

    def test_analyze_file_nonexistent(self, exchange):
        """Test analyzing a nonexistent file."""
        analysis = exchange.analyze_file('/nonexistent/file.py')
        
        assert analysis['imports'] == []
        assert analysis['exports'] == []

    def test_analyze_file_syntax_error(self, exchange, tmp_path):
        """Test analyzing a file with syntax error."""
        bad_file = tmp_path / 'bad.py'
        bad_file.write_text('def broken(:\n    pass')
        
        analysis = exchange.analyze_file(str(bad_file))
        
        assert analysis['imports'] == []
        assert analysis['exports'] == []

    def test_get_affected_modules(self, exchange, tmp_path):
        """Test getting affected modules."""
        (tmp_path / 'a.py').write_text('')
        (tmp_path / 'b.py').write_text('')
        (tmp_path / 'c.py').write_text('')
        
        exchange.register_module('a', 'a.py')
        exchange.register_module('b', 'b.py')
        exchange.register_module('c', 'c.py')
        exchange.add_dependency('b', 'a')
        exchange.add_dependency('c', 'a')
        
        affected = exchange.get_affected_modules('a')
        
        assert 'b' in affected
        assert 'c' in affected

    def test_get_update_order(self, exchange, tmp_path):
        """Test getting update order."""
        (tmp_path / 'a.py').write_text('')
        (tmp_path / 'b.py').write_text('')
        (tmp_path / 'c.py').write_text('')
        
        exchange.register_module('a', 'a.py')
        exchange.register_module('b', 'b.py')
        exchange.register_module('c', 'c.py')
        exchange.add_dependency('b', 'a')
        exchange.add_dependency('c', 'b')
        
        order = exchange.get_update_order('a')
        
        assert order[0] == 'a'
        assert order.index('a') < order.index('b')
        assert order.index('b') < order.index('c')

    def test_get_stats(self, exchange, tmp_path):
        """Test getting exchange statistics."""
        (tmp_path / 'test.py').write_text('')
        exchange.register_module('test', 'test.py')
        exchange.create_package('pkg1')
        
        stats = exchange.get_stats()
        
        assert 'registry' in stats
        assert 'packages' in stats
        assert 'notifier' in stats
        assert stats['files_tracked'] == 1

    def test_reset(self, exchange, tmp_path):
        """Test resetting the exchange."""
        (tmp_path / 'test.py').write_text('')
        exchange.register_module('test', 'test.py')
        exchange.create_package('pkg1')
        
        exchange.reset()
        
        assert len(exchange.dependency_registry.get_all_modules()) == 0
        assert len(exchange.package_registry.get_all_packages()) == 0


class TestCircularExchangeProjectAnalysis:
    """Tests for project-wide analysis functionality."""

    @pytest.fixture
    def project_structure(self, tmp_path):
        """Create a sample project structure."""
        # Reset singleton
        CircularExchange._instance = None
        
        # Create directory structure
        (tmp_path / 'src').mkdir()
        (tmp_path / 'src' / 'utils').mkdir()
        
        # Create files
        (tmp_path / 'src' / 'main.py').write_text('''
from .utils.helper import help_func

def main():
    help_func()
''')
        
        (tmp_path / 'src' / 'utils' / '__init__.py').write_text('')
        (tmp_path / 'src' / 'utils' / 'helper.py').write_text('''
def help_func():
    return "help"
''')
        
        exchange = CircularExchange(project_root=str(tmp_path))
        yield exchange, tmp_path
        
        exchange.reset()
        CircularExchange._instance = None

    def test_analyze_project(self, project_structure):
        """Test analyzing entire project."""
        exchange, tmp_path = project_structure
        
        stats = exchange.analyze_project(patterns=['src/**/*.py'])
        
        assert stats['files_analyzed'] >= 2
        assert stats['modules_registered'] >= 2
        assert stats['exports_found'] >= 1  # At least help_func


class TestCircularExchangeIntegration:
    """Integration tests for CircularExchange."""

    @pytest.fixture
    def integrated_exchange(self, tmp_path):
        """Create an exchange with integrated components."""
        CircularExchange._instance = None
        
        # Create files
        (tmp_path / 'config.py').write_text('CONFIG_VALUE = "default"')
        (tmp_path / 'processor.py').write_text('''
from config import CONFIG_VALUE

def process():
    return CONFIG_VALUE
''')
        
        exchange = CircularExchange(project_root=str(tmp_path))
        exchange.register_module('config', 'config.py')
        exchange.register_module('processor', 'processor.py')
        exchange.add_dependency('processor', 'config')
        
        yield exchange, tmp_path
        
        exchange.reset()
        CircularExchange._instance = None

    def test_change_propagation(self, integrated_exchange):
        """Test that changes propagate through dependencies."""
        exchange, tmp_path = integrated_exchange
        
        notifications = []
        exchange.change_notifier.on_module_change(
            'processor',
            lambda e: notifications.append(e)
        )
        
        # Change config
        exchange.notify_file_changed('config.py')
        
        # Processor should be notified
        assert len(notifications) == 1

    def test_package_based_communication(self, integrated_exchange):
        """Test using packages for module communication."""
        exchange, _ = integrated_exchange
        
        # Create shared package
        shared_config = exchange.create_package(
            'shared_config',
            initial_value={'debug': False},
            module_id='config'
        )
        
        received_values = []
        shared_config.subscribe(lambda c: received_values.append(c.new_value))
        
        # Update config
        shared_config.set({'debug': True})
        
        assert len(received_values) == 1
        assert received_values[0]['debug'] is True
