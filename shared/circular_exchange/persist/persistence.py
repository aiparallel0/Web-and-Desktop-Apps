"""
=============================================================================
PERSISTENCE LAYER - SQLite-based Data Persistence for CEF
=============================================================================

This module implements persistent storage for the Circular Exchange Framework:
- SQLite database for collected data
- Query interface for historical analysis
- Migration support for schema updates
- Export/import functionality

Circular Exchange Framework Integration:
-----------------------------------------
Module ID: shared.circular_exchange.persistence
Description: SQLite-based persistence layer for CEF data
Dependencies: [shared.circular_exchange.data_collector]
Exports: [PersistenceLayer, DBConnection, PERSISTENCE_LAYER]

=============================================================================
"""

import logging
import threading
import sqlite3
import json
import os
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class DBConfig:
    """Database configuration."""
    db_path: str
    pool_size: int = 5
    timeout: float = 30.0
    enable_wal: bool = True
    auto_vacuum: bool = True
    cache_size: int = 2000


class ConnectionPool:
    """Simple SQLite connection pool."""
    
    def __init__(self, config: DBConfig):
        self.config = config
        self._connections: List[sqlite3.Connection] = []
        self._lock = threading.Lock()
        self._in_use: Dict[int, sqlite3.Connection] = {}
        
        # Ensure directory exists
        Path(config.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a connection from the pool."""
        thread_id = threading.get_ident()
        
        with self._lock:
            # Return existing connection for this thread
            if thread_id in self._in_use:
                return self._in_use[thread_id]
            
            # Reuse pooled connection
            if self._connections:
                conn = self._connections.pop()
            else:
                # Create new connection
                conn = sqlite3.connect(
                    self.config.db_path,
                    timeout=self.config.timeout,
                    check_same_thread=False
                )
                conn.row_factory = sqlite3.Row
                
                # Enable WAL mode for better concurrency
                if self.config.enable_wal:
                    conn.execute('PRAGMA journal_mode=WAL')
                
                # Set cache size
                conn.execute(f'PRAGMA cache_size={self.config.cache_size}')
            
            self._in_use[thread_id] = conn
            return conn
    
    def release_connection(self) -> None:
        """Release the connection back to the pool."""
        thread_id = threading.get_ident()
        
        with self._lock:
            if thread_id in self._in_use:
                conn = self._in_use.pop(thread_id)
                if len(self._connections) < self.config.pool_size:
                    self._connections.append(conn)
                else:
                    conn.close()
    
    def close_all(self) -> None:
        """Close all connections."""
        with self._lock:
            for conn in self._connections:
                conn.close()
            for conn in self._in_use.values():
                conn.close()
            self._connections.clear()
            self._in_use.clear()


class PersistenceLayer:
    """
    SQLite-based persistence layer for CEF data.
    
    Stores:
    - Test results
    - Log entries
    - Extraction events
    - Patterns and insights
    - Configuration history
    
    Features:
    - Connection pooling
    - Query interface
    - Automatic schema migrations
    - Data export/import
    """
    
    _instance = None
    _lock = threading.Lock()
    
    # Schema version for migrations
    SCHEMA_VERSION = 1
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the persistence layer."""
        if self._initialized:
            return
        
        # Configuration from environment
        db_path = os.getenv('CEF_DB_PATH', 'data/cef_data.db')
        
        self.config = DBConfig(
            db_path=db_path,
            pool_size=int(os.getenv('CEF_DB_POOL_SIZE', 5)),
            timeout=float(os.getenv('CEF_DB_TIMEOUT', 30.0)),
            enable_wal=os.getenv('CEF_DB_WAL', 'true').lower() == 'true'
        )
        
        self._pool = ConnectionPool(self.config)
        self._lock = threading.RLock()
        
        # Initialize schema
        self._init_schema()
        
        self._initialized = True
        logger.info("PersistenceLayer initialized with database: %s", db_path)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = self._pool.get_connection()
        try:
            yield conn
        finally:
            self._pool.release_connection()
    
    def _init_schema(self) -> None:
        """Initialize database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Schema version table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )
            ''')
            
            # Check current version
            cursor.execute('SELECT MAX(version) FROM schema_version')
            row = cursor.fetchone()
            current_version = row[0] if row[0] else 0
            
            # Apply migrations
            if current_version < 1:
                self._apply_v1_schema(cursor)
                cursor.execute(
                    'INSERT INTO schema_version (version, applied_at) VALUES (?, ?)',
                    (1, datetime.now().isoformat())
                )
            
            conn.commit()
            logger.info("Database schema initialized (version %d)", self.SCHEMA_VERSION)
    
    def _apply_v1_schema(self, cursor) -> None:
        """Apply version 1 schema."""
        
        # Test results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id TEXT NOT NULL,
                test_name TEXT NOT NULL,
                module_path TEXT,
                status TEXT NOT NULL,
                duration_ms REAL,
                error_message TEXT,
                error_traceback TEXT,
                assertions INTEGER DEFAULT 0,
                coverage_lines INTEGER DEFAULT 0,
                metadata TEXT,
                timestamp TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_test_results_status ON test_results(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_test_results_timestamp ON test_results(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_test_results_name ON test_results(test_name)')
        
        # Log entries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS log_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_id TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                module TEXT,
                function TEXT,
                line_number INTEGER,
                correlation_id TEXT,
                user_id TEXT,
                request_id TEXT,
                exception_info TEXT,
                extra_data TEXT,
                timestamp TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_log_entries_level ON log_entries(level)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_log_entries_timestamp ON log_entries(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_log_entries_module ON log_entries(module)')
        
        # Extraction events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS extraction_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL,
                model_id TEXT NOT NULL,
                image_path TEXT,
                success INTEGER NOT NULL,
                processing_time_ms REAL,
                confidence_score REAL,
                extracted_data TEXT,
                ground_truth TEXT,
                error_type TEXT,
                metadata TEXT,
                timestamp TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_extraction_events_model ON extraction_events(model_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_extraction_events_success ON extraction_events(success)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_extraction_events_timestamp ON extraction_events(timestamp)')
        
        # Patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id TEXT UNIQUE NOT NULL,
                pattern_type TEXT NOT NULL,
                description TEXT,
                occurrences INTEGER DEFAULT 0,
                first_seen TEXT,
                last_seen TEXT,
                affected_modules TEXT,
                affected_tests TEXT,
                sample_data TEXT,
                confidence REAL,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_patterns_type ON patterns(pattern_type)')
        
        # Insights table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                insight_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                priority INTEGER,
                category TEXT,
                source_patterns TEXT,
                recommended_actions TEXT,
                estimated_impact TEXT,
                auto_fixable INTEGER DEFAULT 0,
                fix_suggestion TEXT,
                metadata TEXT,
                timestamp TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_insights_priority ON insights(priority)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_insights_category ON insights(category)')
        
        # Tuning decisions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tuning_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id TEXT UNIQUE NOT NULL,
                action TEXT NOT NULL,
                target TEXT NOT NULL,
                current_value TEXT,
                suggested_value TEXT,
                confidence REAL,
                applied INTEGER DEFAULT 0,
                applied_at TEXT,
                result TEXT,
                metadata TEXT,
                timestamp TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Metrics snapshots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id TEXT NOT NULL,
                category TEXT NOT NULL,
                metrics TEXT NOT NULL,
                tags TEXT,
                timestamp TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_category ON metrics_snapshots(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics_snapshots(timestamp)')
    
    # =========================================================================
    # TEST RESULTS
    # =========================================================================
    
    def save_test_result(self, result) -> int:
        """Save a test result to the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO test_results 
                (test_id, test_name, module_path, status, duration_ms, error_message,
                 error_traceback, assertions, coverage_lines, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.test_id,
                result.test_name,
                result.module_path,
                result.status.value if hasattr(result.status, 'value') else result.status,
                result.duration_ms,
                result.error_message,
                result.error_traceback,
                result.assertions,
                result.coverage_lines,
                json.dumps(result.metadata) if result.metadata else None,
                result.timestamp.isoformat()
            ))
            conn.commit()
            return cursor.lastrowid
    
    def query_test_results(
        self,
        status: Optional[str] = None,
        module_path: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query test results from the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM test_results WHERE 1=1'
            params = []
            
            if status:
                query += ' AND status = ?'
                params.append(status)
            
            if module_path:
                query += ' AND module_path LIKE ?'
                params.append(f'%{module_path}%')
            
            if since:
                query += ' AND timestamp >= ?'
                params.append(since.isoformat())
            
            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            
            return [dict(row) for row in cursor.fetchall()]
    
    # =========================================================================
    # LOG ENTRIES
    # =========================================================================
    
    def save_log_entry(self, entry) -> int:
        """Save a log entry to the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO log_entries 
                (log_id, level, message, module, function, line_number, correlation_id,
                 user_id, request_id, exception_info, extra_data, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.log_id,
                entry.level,
                entry.message,
                entry.module,
                entry.function,
                entry.line_number,
                entry.correlation_id,
                entry.user_id,
                entry.request_id,
                entry.exception_info,
                json.dumps(entry.extra_data) if entry.extra_data else None,
                entry.timestamp.isoformat()
            ))
            conn.commit()
            return cursor.lastrowid
    
    def query_log_entries(
        self,
        level: Optional[str] = None,
        module: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query log entries from the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM log_entries WHERE 1=1'
            params = []
            
            if level:
                query += ' AND level = ?'
                params.append(level)
            
            if module:
                query += ' AND module LIKE ?'
                params.append(f'%{module}%')
            
            if since:
                query += ' AND timestamp >= ?'
                params.append(since.isoformat())
            
            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            
            return [dict(row) for row in cursor.fetchall()]
    
    # =========================================================================
    # EXTRACTION EVENTS
    # =========================================================================
    
    def save_extraction_event(self, event) -> int:
        """Save an extraction event to the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO extraction_events 
                (event_id, model_id, image_path, success, processing_time_ms, 
                 confidence_score, extracted_data, ground_truth, error_type, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.event_id,
                event.model_id,
                event.image_path,
                1 if event.success else 0,
                event.processing_time_ms,
                event.confidence_score,
                json.dumps(event.extracted_data) if event.extracted_data else None,
                json.dumps(event.ground_truth) if event.ground_truth else None,
                event.error_type,
                json.dumps(event.metadata) if event.metadata else None,
                event.timestamp.isoformat()
            ))
            conn.commit()
            return cursor.lastrowid
    
    def query_extraction_events(
        self,
        model_id: Optional[str] = None,
        success: Optional[bool] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query extraction events from the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM extraction_events WHERE 1=1'
            params = []
            
            if model_id:
                query += ' AND model_id = ?'
                params.append(model_id)
            
            if success is not None:
                query += ' AND success = ?'
                params.append(1 if success else 0)
            
            if since:
                query += ' AND timestamp >= ?'
                params.append(since.isoformat())
            
            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            
            return [dict(row) for row in cursor.fetchall()]
    
    # =========================================================================
    # PATTERNS AND INSIGHTS
    # =========================================================================
    
    def save_pattern(self, pattern) -> int:
        """Save or update a pattern."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO patterns 
                (pattern_id, pattern_type, description, occurrences, first_seen, last_seen,
                 affected_modules, affected_tests, sample_data, confidence, metadata, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pattern.pattern_id,
                pattern.pattern_type.value if hasattr(pattern.pattern_type, 'value') else pattern.pattern_type,
                pattern.description,
                pattern.occurrences,
                pattern.first_seen.isoformat(),
                pattern.last_seen.isoformat(),
                json.dumps(pattern.affected_modules),
                json.dumps(pattern.affected_tests),
                json.dumps(pattern.sample_data),
                pattern.confidence,
                json.dumps(pattern.metadata) if pattern.metadata else None,
                datetime.now().isoformat()
            ))
            conn.commit()
            return cursor.lastrowid
    
    def save_insight(self, insight) -> int:
        """Save an insight."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO insights 
                (insight_id, title, description, priority, category, source_patterns,
                 recommended_actions, estimated_impact, auto_fixable, fix_suggestion, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                insight.insight_id,
                insight.title,
                insight.description,
                insight.priority.value if hasattr(insight.priority, 'value') else insight.priority,
                insight.category.value if hasattr(insight.category, 'value') else insight.category,
                json.dumps(insight.source_patterns),
                json.dumps(insight.recommended_actions),
                insight.estimated_impact,
                1 if insight.auto_fixable else 0,
                insight.fix_suggestion,
                json.dumps(insight.metadata) if insight.metadata else None,
                insight.timestamp.isoformat()
            ))
            conn.commit()
            return cursor.lastrowid
    
    # =========================================================================
    # STATISTICS AND REPORTS
    # =========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            cursor.execute('SELECT COUNT(*) FROM test_results')
            stats['total_test_results'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM log_entries')
            stats['total_log_entries'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM extraction_events')
            stats['total_extraction_events'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM patterns')
            stats['total_patterns'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM insights')
            stats['total_insights'] = cursor.fetchone()[0]
            
            # Test pass rate (last 24 hours)
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END) as passed
                FROM test_results 
                WHERE timestamp >= ?
            ''', ((datetime.now() - timedelta(hours=24)).isoformat(),))
            row = cursor.fetchone()
            if row['total'] > 0:
                stats['test_pass_rate_24h'] = row['passed'] / row['total']
            else:
                stats['test_pass_rate_24h'] = 0.0
            
            # Extraction success rate (last 24 hours)
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(success) as successful
                FROM extraction_events 
                WHERE timestamp >= ?
            ''', ((datetime.now() - timedelta(hours=24)).isoformat(),))
            row = cursor.fetchone()
            if row['total'] > 0:
                stats['extraction_success_rate_24h'] = row['successful'] / row['total']
            else:
                stats['extraction_success_rate_24h'] = 0.0
            
            return stats
    
    def cleanup_old_data(self, days: int = 30) -> Dict[str, int]:
        """Clean up data older than specified days."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        deleted = {}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for table in ['test_results', 'log_entries', 'extraction_events', 'metrics_snapshots']:
                cursor.execute(f'DELETE FROM {table} WHERE timestamp < ?', (cutoff,))
                deleted[table] = cursor.rowcount
            
            conn.commit()
            
            # Vacuum to reclaim space
            conn.execute('VACUUM')
        
        logger.info("Cleaned up old data: %s", deleted)
        return deleted
    
    def export_to_json(self, output_dir: str) -> Dict[str, str]:
        """Export all data to JSON files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        exported = {}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for table in ['test_results', 'log_entries', 'extraction_events', 'patterns', 'insights']:
                cursor.execute(f'SELECT * FROM {table}')
                rows = [dict(row) for row in cursor.fetchall()]
                
                file_path = output_path / f'{table}.json'
                with open(file_path, 'w') as f:
                    json.dump(rows, f, indent=2)
                
                exported[table] = str(file_path)
        
        logger.info("Exported data to %s", output_dir)
        return exported


# Global singleton instance
PERSISTENCE_LAYER = PersistenceLayer()


# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.circular_exchange.persistence",
            file_path=__file__,
            description="SQLite-based persistence layer for CEF data",
            dependencies=["shared.circular_exchange.data_collector"],
            exports=["PersistenceLayer", "DBConfig", "ConnectionPool", "PERSISTENCE_LAYER"]
        ))
    except Exception:
        pass  # Ignore registration errors during import
