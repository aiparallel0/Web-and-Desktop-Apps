"""
Tests for DependencyRegistry class.

Tests the module dependency tracking functionality of the
circular information exchange framework.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add shared to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'shared'))

from circular_exchange.dependency_registry import DependencyRegistry, ModuleInfo


class TestModuleInfo:
    """Tests for ModuleInfo dataclass."""

    def test_module_info_creation(self):
        """Test creating ModuleInfo with minimal fields."""
        info = ModuleInfo(module_id='test', file_path='/test.py')
        
        assert info.module_id == 'test'
        assert info.file_path == '/test.py'
        assert info.exports == set()
        assert info.imports == set()
        assert info.dependencies == set()
        assert info.dependents == set()
        assert info.last_modified is None

    def test_module_info_with_all_fields(self):
        """Test creating ModuleInfo with all fields."""
        now = datetime.now()
        info = ModuleInfo(
            module_id='test',
            file_path='/test.py',
            exports={'func1', 'Class1'},
            imports={'other_module'},
            dependencies={'dep1'},
            dependents={'user1'},
            last_modified=now,
            metadata={'version': '1.0'}
        )
        
        assert info.exports == {'func1', 'Class1'}
        assert info.imports == {'other_module'}
        assert info.dependencies == {'dep1'}
        assert info.dependents == {'user1'}
        assert info.last_modified == now
        assert info.metadata == {'version': '1.0'}

    def test_module_info_to_dict(self):
        """Test converting ModuleInfo to dictionary."""
        now = datetime.now()
        info = ModuleInfo(
            module_id='test',
            file_path='/test.py',
            exports={'func1'},
            last_modified=now
        )
        
        result = info.to_dict()
        
        assert result['module_id'] == 'test'
        assert result['file_path'] == '/test.py'
        assert 'func1' in result['exports']
        assert result['last_modified'] == now.isoformat()


class TestDependencyRegistry:
    """Tests for DependencyRegistry class."""

    @pytest.fixture
    def registry(self):
        """Create a fresh DependencyRegistry for each test."""
        return DependencyRegistry()

    def test_initialization(self, registry):
        """Test DependencyRegistry initialization."""
        assert registry._modules == {}
        assert registry._dependency_graph == {}
        assert registry._dependent_graph == {}

    def test_register_module(self, registry):
        """Test registering a module."""
        result = registry.register_module(
            module_id='test.module',
            file_path='test/module.py'
        )
        
        assert isinstance(result, ModuleInfo)
        assert result.module_id == 'test.module'
        assert result.file_path == 'test/module.py'
        assert result.last_modified is not None

    def test_register_module_with_exports_imports(self, registry):
        """Test registering a module with exports and imports."""
        exports = {'function1', 'Class1'}
        imports = {'other_func'}
        
        result = registry.register_module(
            module_id='test.module',
            file_path='test/module.py',
            exports=exports,
            imports=imports
        )
        
        assert result.exports == exports
        assert result.imports == imports

    def test_register_module_update_existing(self, registry):
        """Test updating an existing module registration."""
        registry.register_module('test', 'test.py', exports={'old'})
        result = registry.register_module('test', 'test_new.py', exports={'new'})
        
        assert result.file_path == 'test_new.py'
        assert result.exports == {'new'}

    def test_unregister_module(self, registry):
        """Test unregistering a module."""
        registry.register_module('test', 'test.py')
        
        result = registry.unregister_module('test')
        
        assert result is True
        assert 'test' not in registry._modules

    def test_unregister_nonexistent_module(self, registry):
        """Test unregistering a module that doesn't exist."""
        result = registry.unregister_module('nonexistent')
        assert result is False

    def test_add_dependency(self, registry):
        """Test adding a dependency between modules."""
        registry.register_module('a', 'a.py')
        registry.register_module('b', 'b.py')
        
        result = registry.add_dependency('a', 'b')
        
        assert result is True
        assert 'b' in registry.get_dependencies('a')
        assert 'a' in registry.get_dependents('b')

    def test_add_dependency_missing_module(self, registry):
        """Test adding dependency when module doesn't exist."""
        registry.register_module('a', 'a.py')
        
        result = registry.add_dependency('a', 'nonexistent')
        
        assert result is False

    def test_remove_dependency(self, registry):
        """Test removing a dependency."""
        registry.register_module('a', 'a.py')
        registry.register_module('b', 'b.py')
        registry.add_dependency('a', 'b')
        
        result = registry.remove_dependency('a', 'b')
        
        assert result is True
        assert 'b' not in registry.get_dependencies('a')

    def test_get_dependencies(self, registry):
        """Test getting module dependencies."""
        registry.register_module('a', 'a.py')
        registry.register_module('b', 'b.py')
        registry.register_module('c', 'c.py')
        registry.add_dependency('a', 'b')
        registry.add_dependency('a', 'c')
        
        deps = registry.get_dependencies('a')
        
        assert deps == {'b', 'c'}

    def test_get_dependents(self, registry):
        """Test getting modules that depend on a given module."""
        registry.register_module('a', 'a.py')
        registry.register_module('b', 'b.py')
        registry.register_module('c', 'c.py')
        registry.add_dependency('b', 'a')
        registry.add_dependency('c', 'a')
        
        dependents = registry.get_dependents('a')
        
        assert dependents == {'b', 'c'}

    def test_get_all_dependents_recursive(self, registry):
        """Test getting all dependents recursively."""
        # a <- b <- c (c depends on b, b depends on a)
        registry.register_module('a', 'a.py')
        registry.register_module('b', 'b.py')
        registry.register_module('c', 'c.py')
        registry.add_dependency('b', 'a')
        registry.add_dependency('c', 'b')
        
        all_deps = registry.get_all_dependents('a')
        
        assert all_deps == {'b', 'c'}

    def test_circular_dependency_detection(self, registry):
        """Test that circular dependencies are detected."""
        registry.register_module('a', 'a.py')
        registry.register_module('b', 'b.py')
        registry.add_dependency('a', 'b')
        
        # This creates a cycle: a -> b -> a
        registry.add_dependency('b', 'a')
        
        # Should mark both as having circular dependency
        a_info = registry.get_module_info('a')
        b_info = registry.get_module_info('b')
        
        assert a_info.metadata.get('has_circular') is True
        assert b_info.metadata.get('has_circular') is True

    def test_get_module_info(self, registry):
        """Test getting module information."""
        registry.register_module('test', 'test.py', metadata={'key': 'value'})
        
        info = registry.get_module_info('test')
        
        assert info is not None
        assert info.module_id == 'test'
        assert info.metadata['key'] == 'value'

    def test_get_module_info_nonexistent(self, registry):
        """Test getting info for nonexistent module."""
        info = registry.get_module_info('nonexistent')
        assert info is None

    def test_get_all_modules(self, registry):
        """Test getting all modules."""
        registry.register_module('a', 'a.py')
        registry.register_module('b', 'b.py')
        
        modules = registry.get_all_modules()
        
        assert len(modules) == 2
        assert any(m.module_id == 'a' for m in modules)
        assert any(m.module_id == 'b' for m in modules)

    def test_topological_order(self, registry):
        """Test getting modules in topological order."""
        # c -> b -> a (a is dependency of b, b is dependency of c)
        registry.register_module('a', 'a.py')
        registry.register_module('b', 'b.py')
        registry.register_module('c', 'c.py')
        registry.add_dependency('b', 'a')
        registry.add_dependency('c', 'b')
        
        order = registry.get_topological_order()
        
        # a should come before b, b should come before c
        assert order.index('a') < order.index('b')
        assert order.index('b') < order.index('c')

    def test_get_update_order(self, registry):
        """Test getting update order after a change."""
        registry.register_module('a', 'a.py')
        registry.register_module('b', 'b.py')
        registry.register_module('c', 'c.py')
        registry.add_dependency('b', 'a')
        registry.add_dependency('c', 'a')
        
        order = registry.get_update_order('a')
        
        # a should be first, then b and c
        assert order[0] == 'a'
        assert 'b' in order
        assert 'c' in order

    def test_on_change_callback(self, registry):
        """Test change callback registration."""
        changes = []
        registry.on_change(lambda mid: changes.append(mid))
        registry.register_module('test', 'test.py')
        
        registry.notify_change('test')
        
        assert 'test' in changes

    def test_get_stats(self, registry):
        """Test getting registry statistics."""
        registry.register_module('a', 'a.py', exports={'func1'})
        registry.register_module('b', 'b.py', imports={'func1'})
        registry.add_dependency('b', 'a')
        
        stats = registry.get_stats()
        
        assert stats['total_modules'] == 2
        assert stats['total_dependencies'] == 1
        assert stats['modules_with_exports'] == 1
        assert stats['modules_with_imports'] == 1


class TestDependencyRegistryThreadSafety:
    """Tests for thread safety of DependencyRegistry."""

    def test_concurrent_registration(self):
        """Test concurrent module registration."""
        import threading
        
        registry = DependencyRegistry()
        results = []
        
        def register_module(i):
            result = registry.register_module(f'module_{i}', f'module_{i}.py')
            results.append(result)
        
        threads = [threading.Thread(target=register_module, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(results) == 10
        assert len(registry.get_all_modules()) == 10
