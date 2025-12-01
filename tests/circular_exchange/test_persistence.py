"""
Tests for the Persistence Layer module.
"""

import pytest
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from shared.circular_exchange.persistence import (
    PersistenceLayer,
    ConnectionPool,
    DBConfig,
    PERSISTENCE_LAYER
)
from shared.circular_exchange.data_collector import (
    TestResult,
    TestStatus,
    LogEntry,
    ExtractionEvent
)


class TestDBConfig:
    """Tests for DBConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = DBConfig(db_path="test.db")
        
        assert config.db_path == "test.db"
        assert config.pool_size == 5
        assert config.timeout == 30.0
        assert config.enable_wal is True
        assert config.auto_vacuum is True
        assert config.cache_size == 2000
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = DBConfig(
            db_path="custom.db",
            pool_size=10,
            timeout=60.0,
            enable_wal=False,
            cache_size=4000
        )
        
        assert config.pool_size == 10
        assert config.timeout == 60.0
        assert config.enable_wal is False
        assert config.cache_size == 4000


class TestConnectionPool:
    """Tests for ConnectionPool."""
    
    def test_get_connection(self):
        """Test getting a connection from the pool."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DBConfig(db_path=os.path.join(tmpdir, "test.db"))
            pool = ConnectionPool(config)
            
            conn = pool.get_connection()
            assert conn is not None
            
            # Same thread should get same connection
            conn2 = pool.get_connection()
            assert conn is conn2
            
            pool.release_connection()
            pool.close_all()
    
    def test_release_connection(self):
        """Test releasing a connection back to the pool."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DBConfig(db_path=os.path.join(tmpdir, "test.db"))
            pool = ConnectionPool(config)
            
            conn = pool.get_connection()
            pool.release_connection()
            
            # Connection should be pooled
            assert len(pool._connections) <= config.pool_size
            
            pool.close_all()
    
    def test_close_all(self):
        """Test closing all connections."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DBConfig(db_path=os.path.join(tmpdir, "test.db"))
            pool = ConnectionPool(config)
            
            pool.get_connection()
            pool.close_all()
            
            assert len(pool._connections) == 0
            assert len(pool._in_use) == 0


class TestPersistenceLayer:
    """Tests for the PersistenceLayer class."""
    
    @pytest.fixture
    def fresh_persistence(self):
        """Create a fresh persistence layer for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Override the default path
            original_path = os.environ.get('CEF_DB_PATH')
            os.environ['CEF_DB_PATH'] = os.path.join(tmpdir, "test.db")
            
            # Create new instance (bypass singleton for testing)
            layer = PersistenceLayer.__new__(PersistenceLayer)
            layer._initialized = False
            layer.__init__()
            
            yield layer
            
            # Clean up
            layer._pool.close_all()
            if original_path:
                os.environ['CEF_DB_PATH'] = original_path
            elif 'CEF_DB_PATH' in os.environ:
                del os.environ['CEF_DB_PATH']
    
    def test_singleton_pattern(self):
        """Test that PersistenceLayer is a singleton."""
        layer1 = PersistenceLayer()
        layer2 = PersistenceLayer()
        
        assert layer1 is layer2
    
    def test_schema_initialization(self):
        """Test that schema is properly initialized."""
        # The global instance should have schema initialized
        layer = PERSISTENCE_LAYER
        
        with layer.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check that tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
            
            expected_tables = {
                'schema_version',
                'test_results',
                'log_entries',
                'extraction_events',
                'patterns',
                'insights',
                'tuning_decisions',
                'metrics_snapshots'
            }
            
            for table in expected_tables:
                assert table in tables, f"Table {table} not found"
    
    def test_save_test_result(self):
        """Test saving a test result."""
        layer = PERSISTENCE_LAYER
        
        result = TestResult(
            test_id="test_save_001",
            test_name="test_save_function",
            module_path="tests/test_module.py",
            status=TestStatus.PASSED,
            duration_ms=150.0,
            assertions=5
        )
        
        row_id = layer.save_test_result(result)
        assert row_id > 0
    
    def test_query_test_results(self):
        """Test querying test results."""
        layer = PERSISTENCE_LAYER
        
        # Save a unique test result
        unique_name = f"test_query_{datetime.now().timestamp()}"
        result = TestResult(
            test_id=f"test_{unique_name}",
            test_name=unique_name,
            module_path="tests/query_test.py",
            status=TestStatus.FAILED,
            duration_ms=200.0,
            error_message="Test error"
        )
        layer.save_test_result(result)
        
        # Query by status
        results = layer.query_test_results(status="failed", limit=100)
        assert len(results) > 0
        assert any(r['test_name'] == unique_name for r in results)
    
    def test_save_log_entry(self):
        """Test saving a log entry."""
        layer = PERSISTENCE_LAYER
        
        entry = LogEntry(
            log_id="log_save_001",
            level="ERROR",
            message="Test error message",
            module="test_module",
            function="test_function",
            line_number=42
        )
        
        row_id = layer.save_log_entry(entry)
        assert row_id > 0
    
    def test_query_log_entries(self):
        """Test querying log entries."""
        layer = PERSISTENCE_LAYER
        
        # Save a unique log entry
        unique_msg = f"unique_log_{datetime.now().timestamp()}"
        entry = LogEntry(
            log_id=f"log_{unique_msg}",
            level="ERROR",
            message=unique_msg,
            module="test_module",
            function="test_function",
            line_number=100
        )
        layer.save_log_entry(entry)
        
        # Query by level
        entries = layer.query_log_entries(level="ERROR", limit=100)
        assert len(entries) > 0
    
    def test_save_extraction_event(self):
        """Test saving an extraction event."""
        layer = PERSISTENCE_LAYER
        
        event = ExtractionEvent(
            event_id="extract_save_001",
            model_id="test_model",
            image_path="/path/to/image.jpg",
            success=True,
            processing_time_ms=500.0,
            confidence_score=0.95
        )
        
        row_id = layer.save_extraction_event(event)
        assert row_id > 0
    
    def test_query_extraction_events(self):
        """Test querying extraction events."""
        layer = PERSISTENCE_LAYER
        
        # Save a unique extraction event
        unique_id = f"extract_{datetime.now().timestamp()}"
        event = ExtractionEvent(
            event_id=unique_id,
            model_id="query_test_model",
            image_path="/path/to/image.jpg",
            success=True,
            processing_time_ms=300.0,
            confidence_score=0.85
        )
        layer.save_extraction_event(event)
        
        # Query by model
        events = layer.query_extraction_events(model_id="query_test_model", limit=100)
        assert len(events) > 0
        
        # Query by success
        events = layer.query_extraction_events(success=True, limit=100)
        assert len(events) > 0
    
    def test_get_stats(self):
        """Test getting database statistics."""
        layer = PERSISTENCE_LAYER
        
        stats = layer.get_stats()
        
        assert "total_test_results" in stats
        assert "total_log_entries" in stats
        assert "total_extraction_events" in stats
        assert "total_patterns" in stats
        assert "total_insights" in stats
        assert "test_pass_rate_24h" in stats
        assert "extraction_success_rate_24h" in stats
        
        # Values should be non-negative
        assert stats["total_test_results"] >= 0
        assert 0.0 <= stats["test_pass_rate_24h"] <= 1.0
        assert 0.0 <= stats["extraction_success_rate_24h"] <= 1.0
    
    def test_query_with_since_filter(self):
        """Test querying with time filter."""
        layer = PERSISTENCE_LAYER
        
        # Query results from the last hour
        since = datetime.now() - timedelta(hours=1)
        results = layer.query_test_results(since=since, limit=10)
        
        assert isinstance(results, list)
    
    def test_export_to_json(self):
        """Test exporting data to JSON."""
        layer = PERSISTENCE_LAYER
        
        with tempfile.TemporaryDirectory() as tmpdir:
            exported = layer.export_to_json(tmpdir)
            
            assert "test_results" in exported
            assert "log_entries" in exported
            assert "extraction_events" in exported
            
            # Check files exist
            for table, path in exported.items():
                assert Path(path).exists()


class TestGlobalInstance:
    """Tests for the global PERSISTENCE_LAYER instance."""
    
    def test_global_instance_exists(self):
        """Test that the global instance exists."""
        assert PERSISTENCE_LAYER is not None
        assert isinstance(PERSISTENCE_LAYER, PersistenceLayer)
    
    def test_global_instance_is_singleton(self):
        """Test that global instance is the singleton."""
        assert PERSISTENCE_LAYER is PersistenceLayer()
    
    def test_global_instance_initialized(self):
        """Test that global instance is properly initialized."""
        assert PERSISTENCE_LAYER._initialized is True
        assert PERSISTENCE_LAYER.config is not None
        assert PERSISTENCE_LAYER._pool is not None
