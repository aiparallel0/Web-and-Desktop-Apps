"""
Tests for ChangeNotifier class.

Tests the change notification functionality of the
circular information exchange framework.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add shared to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'shared'))

from circular_exchange.change_notifier import (
    ChangeNotifier, ChangeType, ChangeEvent, NotificationResult
)
from circular_exchange.dependency_registry import DependencyRegistry


class TestChangeEvent:
    """Tests for ChangeEvent dataclass."""

    def test_change_event_creation(self):
        """Test creating a ChangeEvent."""
        now = datetime.now()
        event = ChangeEvent(
            event_type=ChangeType.FILE_MODIFIED,
            source_module='test_module',
            timestamp=now,
            data={'file_path': 'test.py'}
        )
        
        assert event.event_type == ChangeType.FILE_MODIFIED
        assert event.source_module == 'test_module'
        assert event.timestamp == now
        assert event.data['file_path'] == 'test.py'
        assert event.propagated is False

    def test_change_event_to_dict(self):
        """Test converting ChangeEvent to dictionary."""
        event = ChangeEvent(
            event_type=ChangeType.VARIABLE_UPDATED,
            source_module='mod',
            timestamp=datetime.now(),
            affected_modules={'a', 'b'}
        )
        
        result = event.to_dict()
        
        assert result['event_type'] == 'variable_updated'
        assert result['source_module'] == 'mod'
        assert set(result['affected_modules']) == {'a', 'b'}


class TestNotificationResult:
    """Tests for NotificationResult dataclass."""

    def test_notification_result_success(self):
        """Test successful notification result."""
        result = NotificationResult(module_id='test', success=True)
        
        assert result.module_id == 'test'
        assert result.success is True
        assert result.error is None

    def test_notification_result_failure(self):
        """Test failed notification result."""
        result = NotificationResult(
            module_id='test',
            success=False,
            error='Connection failed'
        )
        
        assert result.success is False
        assert result.error == 'Connection failed'

    def test_notification_result_to_dict(self):
        """Test converting NotificationResult to dictionary."""
        result = NotificationResult(module_id='test', success=True)
        
        d = result.to_dict()
        
        assert d['module_id'] == 'test'
        assert d['success'] is True


class TestChangeNotifier:
    """Tests for ChangeNotifier class."""

    @pytest.fixture
    def notifier(self):
        """Create a fresh ChangeNotifier for each test."""
        return ChangeNotifier()

    @pytest.fixture
    def notifier_with_registry(self):
        """Create a ChangeNotifier with DependencyRegistry."""
        registry = DependencyRegistry()
        registry.register_module('a', 'a.py')
        registry.register_module('b', 'b.py')
        registry.register_module('c', 'c.py')
        registry.add_dependency('b', 'a')  # b depends on a
        registry.add_dependency('c', 'a')  # c depends on a
        
        notifier = ChangeNotifier(registry)
        return notifier, registry

    def test_initialization(self, notifier):
        """Test ChangeNotifier initialization."""
        assert notifier._dependency_registry is None
        assert len(notifier._event_history) == 0
        assert notifier._batch_mode is False

    def test_set_dependency_registry(self, notifier):
        """Test setting dependency registry."""
        registry = DependencyRegistry()
        notifier.set_dependency_registry(registry)
        
        assert notifier._dependency_registry is registry

    def test_on_event_type(self, notifier):
        """Test registering handler for event type."""
        events = []
        
        notifier.on(ChangeType.FILE_MODIFIED, lambda e: events.append(e))
        notifier.notify_change('test', ChangeType.FILE_MODIFIED)
        
        assert len(events) == 1
        assert events[0].event_type == ChangeType.FILE_MODIFIED

    def test_on_module_change(self, notifier_with_registry):
        """Test registering handler for specific module."""
        notifier, _ = notifier_with_registry
        events = []
        
        notifier.on_module_change('b', lambda e: events.append(e))
        notifier.notify_change('a', ChangeType.FILE_MODIFIED)
        
        # b should be notified because it depends on a
        assert len(events) == 1

    def test_unsubscribe_event_handler(self, notifier):
        """Test unsubscribing from event type."""
        events = []
        
        unsub = notifier.on(ChangeType.FILE_MODIFIED, lambda e: events.append(e))
        notifier.notify_change('test', ChangeType.FILE_MODIFIED)
        unsub()
        notifier.notify_change('test', ChangeType.FILE_MODIFIED)
        
        assert len(events) == 1  # Only first event recorded

    def test_notify_change_returns_results(self, notifier):
        """Test that notify_change returns results."""
        notifier.on(ChangeType.FILE_MODIFIED, lambda e: None)
        
        results = notifier.notify_change('test', ChangeType.FILE_MODIFIED)
        
        assert len(results) == 1
        assert results[0].success is True

    def test_notify_change_handles_errors(self, notifier):
        """Test that notify_change handles handler errors."""
        def failing_handler(e):
            raise RuntimeError("Handler failed")
        
        notifier.on(ChangeType.FILE_MODIFIED, failing_handler)
        
        results = notifier.notify_change('test', ChangeType.FILE_MODIFIED)
        
        assert len(results) == 1
        assert results[0].success is False
        assert 'Handler failed' in results[0].error

    def test_notify_file_modified(self, notifier):
        """Test convenience method for file modification."""
        events = []
        notifier.on(ChangeType.FILE_MODIFIED, lambda e: events.append(e))
        
        notifier.notify_file_modified('test_module', 'test.py')
        
        assert len(events) == 1
        assert events[0].data['file_path'] == 'test.py'

    def test_notify_variable_updated(self, notifier):
        """Test convenience method for variable update."""
        events = []
        notifier.on(ChangeType.VARIABLE_UPDATED, lambda e: events.append(e))
        
        notifier.notify_variable_updated('mod', 'var', 'old', 'new')
        
        assert len(events) == 1
        assert events[0].data['variable_name'] == 'var'

    def test_batch_mode(self, notifier):
        """Test batch mode batches events."""
        events = []
        notifier.on(ChangeType.FILE_MODIFIED, lambda e: events.append(e))
        
        notifier.begin_batch()
        notifier.notify_change('test', ChangeType.FILE_MODIFIED)
        notifier.notify_change('test', ChangeType.FILE_MODIFIED)
        
        assert len(events) == 0  # No events yet
        
        notifier.end_batch()
        
        assert len(events) == 1  # Events merged

    def test_batch_mode_merges_same_source(self, notifier):
        """Test that batch mode merges events from same source."""
        events = []
        notifier.on(ChangeType.FILE_MODIFIED, lambda e: events.append(e))
        
        notifier.begin_batch()
        notifier.notify_change('mod_a', ChangeType.FILE_MODIFIED, {'key1': 'val1'})
        notifier.notify_change('mod_a', ChangeType.FILE_MODIFIED, {'key2': 'val2'})
        notifier.notify_change('mod_b', ChangeType.FILE_MODIFIED)
        results = notifier.end_batch()
        
        # Should have 2 unique events (mod_a merged, mod_b separate)
        assert len(events) == 2

    def test_get_history(self, notifier):
        """Test getting event history."""
        notifier.notify_change('mod1', ChangeType.FILE_MODIFIED)
        notifier.notify_change('mod2', ChangeType.VARIABLE_UPDATED)
        
        history = notifier.get_history()
        
        assert len(history) == 2

    def test_get_history_with_limit(self, notifier):
        """Test getting limited event history."""
        for i in range(10):
            notifier.notify_change(f'mod{i}', ChangeType.FILE_MODIFIED)
        
        history = notifier.get_history(limit=3)
        
        assert len(history) == 3

    def test_get_history_by_event_type(self, notifier):
        """Test filtering history by event type."""
        notifier.notify_change('mod1', ChangeType.FILE_MODIFIED)
        notifier.notify_change('mod2', ChangeType.VARIABLE_UPDATED)
        notifier.notify_change('mod3', ChangeType.FILE_MODIFIED)
        
        history = notifier.get_history(event_type=ChangeType.FILE_MODIFIED)
        
        assert len(history) == 2
        assert all(e.event_type == ChangeType.FILE_MODIFIED for e in history)

    def test_clear_history(self, notifier):
        """Test clearing event history."""
        notifier.notify_change('mod', ChangeType.FILE_MODIFIED)
        notifier.clear_history()
        
        assert len(notifier.get_history()) == 0

    def test_get_stats(self, notifier):
        """Test getting notifier statistics."""
        notifier.on(ChangeType.FILE_MODIFIED, lambda e: None)
        notifier.notify_change('mod', ChangeType.FILE_MODIFIED)
        
        stats = notifier.get_stats()
        
        assert stats['total_events'] == 1
        assert stats['successful_notifications'] == 1
        assert stats['handler_counts']['file_modified'] == 1

    def test_affected_modules_with_registry(self, notifier_with_registry):
        """Test that affected modules are determined from registry."""
        notifier, registry = notifier_with_registry
        events = []
        
        notifier.on(ChangeType.FILE_MODIFIED, lambda e: events.append(e))
        notifier.notify_change('a', ChangeType.FILE_MODIFIED)
        
        # b and c depend on a, so they should be affected
        assert len(events) == 1
        affected = events[0].affected_modules
        assert 'a' in affected
        assert 'b' in affected
        assert 'c' in affected

    def test_update_order_with_registry(self, notifier_with_registry):
        """Test that modules are notified in dependency order."""
        notifier, registry = notifier_with_registry
        notification_order = []
        
        notifier.on_module_change('a', lambda e: notification_order.append('a'))
        notifier.on_module_change('b', lambda e: notification_order.append('b'))
        notifier.on_module_change('c', lambda e: notification_order.append('c'))
        
        notifier.notify_change('a', ChangeType.FILE_MODIFIED)
        
        # a should be notified first
        assert notification_order[0] == 'a'

    def test_unsubscribe_module_handler(self, notifier_with_registry):
        """Test unsubscribing from module change notifications."""
        notifier, _ = notifier_with_registry
        events = []
        
        unsub = notifier.on_module_change('b', lambda e: events.append(e))
        notifier.notify_change('a', ChangeType.FILE_MODIFIED)
        assert len(events) == 1  # First event received
        
        unsub()  # Unsubscribe
        notifier.notify_change('a', ChangeType.FILE_MODIFIED)
        assert len(events) == 1  # No new events after unsubscribe

    def test_event_history_max_limit(self):
        """Test that event history respects max limit."""
        notifier = ChangeNotifier(max_history=5)
        
        for i in range(10):
            notifier.notify_change(f'mod{i}', ChangeType.FILE_MODIFIED)
        
        history = notifier.get_history()
        assert len(history) == 5  # Only last 5 events kept

    def test_module_handler_error_handling(self, notifier_with_registry):
        """Test that module handler errors are caught and reported."""
        notifier, _ = notifier_with_registry
        
        def failing_handler(e):
            raise RuntimeError("Module handler failed")
        
        notifier.on_module_change('b', failing_handler)
        results = notifier.notify_change('a', ChangeType.FILE_MODIFIED)
        
        # Should have failed result for module handler
        failed_results = [r for r in results if not r.success]
        assert len(failed_results) >= 1
        assert any('Module handler failed' in r.error for r in failed_results)


class TestChangeType:
    """Tests for ChangeType enum."""

    def test_all_change_types_exist(self):
        """Test that all expected change types exist."""
        assert ChangeType.FILE_MODIFIED
        assert ChangeType.VARIABLE_UPDATED
        assert ChangeType.DEPENDENCY_ADDED
        assert ChangeType.DEPENDENCY_REMOVED
        assert ChangeType.MODULE_REGISTERED
        assert ChangeType.MODULE_UNREGISTERED

    def test_change_type_values(self):
        """Test change type values."""
        assert ChangeType.FILE_MODIFIED.value == 'file_modified'
        assert ChangeType.VARIABLE_UPDATED.value == 'variable_updated'
