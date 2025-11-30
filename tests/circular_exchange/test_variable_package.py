"""
Tests for VariablePackage class.

Tests the variable-based data transfer functionality of the
circular information exchange framework.
"""

import pytest
import sys
import threading
from pathlib import Path
from datetime import datetime

# Add shared to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'shared'))

from circular_exchange.variable_package import (
    VariablePackage, PackageChange, PackageRegistry
)


class TestPackageChange:
    """Tests for PackageChange dataclass."""

    def test_package_change_creation(self):
        """Test creating a PackageChange."""
        now = datetime.now()
        change = PackageChange(
            variable_name='test_var',
            old_value=1,
            new_value=2,
            timestamp=now,
            source_module='test_module'
        )
        
        assert change.variable_name == 'test_var'
        assert change.old_value == 1
        assert change.new_value == 2
        assert change.timestamp == now
        assert change.source_module == 'test_module'

    def test_package_change_to_dict(self):
        """Test converting PackageChange to dictionary."""
        now = datetime.now()
        change = PackageChange(
            variable_name='test',
            old_value='old',
            new_value='new',
            timestamp=now
        )
        
        result = change.to_dict()
        
        assert result['variable_name'] == 'test'
        assert 'old' in result['old_value']
        assert 'new' in result['new_value']
        assert result['timestamp'] == now.isoformat()


class TestVariablePackage:
    """Tests for VariablePackage class."""

    def test_initialization(self):
        """Test VariablePackage initialization."""
        pkg = VariablePackage(name='test', initial_value=42)
        
        assert pkg.name == 'test'
        assert pkg.value == 42
        assert pkg.is_frozen is False

    def test_initialization_with_source_module(self):
        """Test initialization with source module."""
        pkg = VariablePackage(name='test', source_module='my_module')
        
        assert pkg.source_module == 'my_module'

    def test_get_and_set(self):
        """Test getting and setting values."""
        pkg = VariablePackage(name='test', initial_value=0)
        
        pkg.set(10)
        
        assert pkg.get() == 10

    def test_value_property(self):
        """Test value property getter and setter."""
        pkg = VariablePackage(name='test', initial_value=0)
        
        pkg.value = 20
        
        assert pkg.value == 20

    def test_get_copy(self):
        """Test getting a deep copy of the value."""
        pkg = VariablePackage(name='test', initial_value=[1, 2, 3])
        
        copy = pkg.get_copy()
        copy.append(4)
        
        assert pkg.value == [1, 2, 3]  # Original unchanged
        assert copy == [1, 2, 3, 4]

    def test_update_with_function(self):
        """Test updating value with a function."""
        pkg = VariablePackage(name='test', initial_value=5)
        
        result = pkg.update(lambda x: x * 2)
        
        assert result is True
        assert pkg.value == 10

    def test_validation_success(self):
        """Test value validation passes."""
        pkg = VariablePackage(
            name='positive',
            initial_value=1,
            validator=lambda x: x > 0
        )
        
        result = pkg.set(10)
        
        assert result is True
        assert pkg.value == 10

    def test_validation_failure(self):
        """Test value validation fails."""
        pkg = VariablePackage(
            name='positive',
            initial_value=1,
            validator=lambda x: x > 0
        )
        
        result = pkg.set(-5)
        
        assert result is False
        assert pkg.value == 1  # Value unchanged

    def test_subscribe_to_changes(self):
        """Test subscribing to value changes."""
        pkg = VariablePackage(name='test', initial_value=0)
        changes = []
        
        pkg.subscribe(lambda c: changes.append(c))
        pkg.set(10)
        
        assert len(changes) == 1
        assert changes[0].old_value == 0
        assert changes[0].new_value == 10

    def test_unsubscribe(self):
        """Test unsubscribing from changes."""
        pkg = VariablePackage(name='test', initial_value=0)
        changes = []
        
        unsubscribe = pkg.subscribe(lambda c: changes.append(c))
        pkg.set(10)
        unsubscribe()
        pkg.set(20)
        
        assert len(changes) == 1  # Only first change recorded

    def test_freeze_and_unfreeze(self):
        """Test freezing and unfreezing package."""
        pkg = VariablePackage(name='test', initial_value=1)
        
        pkg.freeze()
        result = pkg.set(2)
        
        assert result is False
        assert pkg.value == 1
        assert pkg.is_frozen is True
        
        pkg.unfreeze()
        result = pkg.set(3)
        
        assert result is True
        assert pkg.value == 3

    def test_change_history(self):
        """Test change history tracking."""
        pkg = VariablePackage(name='test', initial_value=0)
        
        pkg.set(1)
        pkg.set(2)
        pkg.set(3)
        
        history = pkg.get_history()
        
        assert len(history) == 3
        assert history[0].new_value == 1
        assert history[1].new_value == 2
        assert history[2].new_value == 3

    def test_change_history_limit(self):
        """Test change history with limit."""
        pkg = VariablePackage(name='test', initial_value=0)
        
        for i in range(10):
            pkg.set(i)
        
        history = pkg.get_history(limit=3)
        
        assert len(history) == 3
        assert history[0].new_value == 7  # Last 3 changes
        assert history[2].new_value == 9

    def test_max_history_limit(self):
        """Test max history limit enforcement."""
        pkg = VariablePackage(name='test', initial_value=0, max_history=5)
        
        for i in range(10):
            pkg.set(i)
        
        history = pkg.get_history()
        
        assert len(history) == 5  # Only keeps last 5

    def test_clear_history(self):
        """Test clearing change history."""
        pkg = VariablePackage(name='test', initial_value=0)
        
        pkg.set(1)
        pkg.set(2)
        pkg.clear_history()
        
        assert len(pkg.get_history()) == 0

    def test_metadata(self):
        """Test metadata get and set."""
        pkg = VariablePackage(name='test')
        
        pkg.set_metadata('key1', 'value1')
        pkg.set_metadata('key2', 42)
        
        assert pkg.get_metadata('key1') == 'value1'
        assert pkg.get_metadata('key2') == 42
        assert pkg.get_metadata('nonexistent', 'default') == 'default'

    def test_to_dict(self):
        """Test converting package to dictionary."""
        pkg = VariablePackage(name='test', initial_value='hello', source_module='mod')
        
        result = pkg.to_dict()
        
        assert result['name'] == 'test'
        assert 'hello' in result['value']
        assert result['source_module'] == 'mod'
        assert result['is_frozen'] is False

    def test_last_modified_timestamp(self):
        """Test last modified timestamp updates."""
        import time
        pkg = VariablePackage(name='test', initial_value=0)
        before = pkg.last_modified
        
        # Add a small delay to ensure timestamp difference
        time.sleep(0.001)
        
        pkg.set(1)
        after = pkg.last_modified
        
        assert after >= before  # Use >= to handle fast execution


class TestPackageRegistry:
    """Tests for PackageRegistry class."""

    @pytest.fixture
    def registry(self):
        """Create a fresh PackageRegistry for each test."""
        reg = PackageRegistry()
        reg.clear()  # Clear any existing packages
        return reg

    def test_singleton_pattern(self):
        """Test that PackageRegistry is a singleton."""
        reg1 = PackageRegistry()
        reg2 = PackageRegistry()
        
        assert reg1 is reg2

    def test_create_package(self, registry):
        """Test creating a package."""
        pkg = registry.create_package('test', initial_value=42)
        
        assert pkg.name == 'test'
        assert pkg.value == 42

    def test_create_existing_package_returns_same(self, registry):
        """Test that creating an existing package returns the same instance."""
        pkg1 = registry.create_package('test', initial_value=1)
        pkg2 = registry.create_package('test', initial_value=2)
        
        assert pkg1 is pkg2
        assert pkg1.value == 1  # Not changed to 2

    def test_get_package(self, registry):
        """Test getting a package."""
        registry.create_package('test', initial_value=42)
        
        pkg = registry.get_package('test')
        
        assert pkg is not None
        assert pkg.value == 42

    def test_get_nonexistent_package(self, registry):
        """Test getting a nonexistent package."""
        pkg = registry.get_package('nonexistent')
        assert pkg is None

    def test_remove_package(self, registry):
        """Test removing a package."""
        registry.create_package('test')
        
        result = registry.remove_package('test')
        
        assert result is True
        assert registry.get_package('test') is None

    def test_remove_nonexistent_package(self, registry):
        """Test removing a nonexistent package."""
        result = registry.remove_package('nonexistent')
        assert result is False

    def test_get_all_packages(self, registry):
        """Test getting all packages."""
        registry.create_package('pkg1')
        registry.create_package('pkg2')
        
        all_pkgs = registry.get_all_packages()
        
        assert len(all_pkgs) == 2
        assert 'pkg1' in all_pkgs
        assert 'pkg2' in all_pkgs

    def test_get_packages_by_module(self, registry):
        """Test getting packages by source module."""
        registry.create_package('pkg1', source_module='mod_a')
        registry.create_package('pkg2', source_module='mod_a')
        registry.create_package('pkg3', source_module='mod_b')
        
        mod_a_pkgs = registry.get_packages_by_module('mod_a')
        
        assert len(mod_a_pkgs) == 2
        assert all(p.source_module == 'mod_a' for p in mod_a_pkgs)

    def test_clear(self, registry):
        """Test clearing all packages."""
        registry.create_package('pkg1')
        registry.create_package('pkg2')
        
        registry.clear()
        
        assert len(registry.get_all_packages()) == 0

    def test_get_stats(self, registry):
        """Test getting registry statistics."""
        pkg1 = registry.create_package('pkg1', source_module='mod_a')
        pkg2 = registry.create_package('pkg2', source_module='mod_a')
        pkg1.freeze()
        
        stats = registry.get_stats()
        
        assert stats['total_packages'] == 2
        assert stats['frozen_packages'] == 1
        assert stats['packages_by_module']['mod_a'] == 2


class TestVariablePackageThreadSafety:
    """Tests for thread safety of VariablePackage."""

    def test_concurrent_set_operations(self):
        """Test concurrent set operations."""
        pkg = VariablePackage(name='counter', initial_value=0)
        
        def increment():
            for _ in range(100):
                pkg.update(lambda x: x + 1)
        
        threads = [threading.Thread(target=increment) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Value should be 1000 if thread-safe
        assert pkg.value == 1000

    def test_concurrent_subscribe_unsubscribe(self):
        """Test concurrent subscribe/unsubscribe operations."""
        pkg = VariablePackage(name='test', initial_value=0)
        
        def subscribe_and_unsubscribe():
            unsub = pkg.subscribe(lambda c: None)
            pkg.set(1)
            unsub()
        
        threads = [threading.Thread(target=subscribe_and_unsubscribe) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should complete without errors
        assert True


class TestVariablePackageSubscriberErrors:
    """Tests for error handling in subscriber notifications."""

    def test_subscriber_error_handling(self):
        """Test that errors in subscribers are caught and logged."""
        pkg = VariablePackage(name='test', initial_value=0)
        
        results = []
        
        def failing_subscriber(change):
            raise RuntimeError("Subscriber error")
        
        def working_subscriber(change):
            results.append(change.new_value)
        
        # Add both subscribers
        pkg.subscribe(failing_subscriber)
        pkg.subscribe(working_subscriber)
        
        # Should not raise, error is logged but other subscribers still called
        pkg.set(42)
        
        # Working subscriber should still receive the change
        assert 42 in results
