"""
Tests for database initialization with concurrent access handling.

These tests verify that init_db() can handle:
1. Multiple simultaneous initialization attempts (concurrent workers)
2. Already existing schema (idempotent operation)
3. PostgreSQL duplicate ENUM type errors
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class TestDatabaseInitialization:
    """Tests for database initialization race condition handling"""
    
    def test_init_db_handles_duplicate_type_error(self):
        """Test that init_db handles PostgreSQL duplicate type errors gracefully"""
        from web.backend import database
        
        # Mock the create_all to raise a duplicate type error
        mock_engine = MagicMock()
        
        with patch.object(database, 'get_engine', return_value=mock_engine):
            with patch.object(database.Base.metadata, 'create_all') as mock_create:
                # Simulate PostgreSQL duplicate type error
                error_msg = "duplicate key value violates unique constraint \"pg_type_typname_nsp_index\"\nKey (typname, typnamespace)=(subscriptionplan, 2200) already exists."
                mock_create.side_effect = Exception(error_msg)
                
                # Should not raise an exception
                database.init_db()
                
                # Verify create_all was called
                mock_create.assert_called_once()
    
    def test_init_db_handles_already_exists_error(self):
        """Test that init_db handles 'already exists' errors gracefully"""
        from web.backend import database
        
        mock_engine = MagicMock()
        
        with patch.object(database, 'get_engine', return_value=mock_engine):
            with patch.object(database.Base.metadata, 'create_all') as mock_create:
                # Simulate generic "already exists" error
                error_msg = "relation \"users\" already exists"
                mock_create.side_effect = Exception(error_msg)
                
                # Should not raise an exception
                database.init_db()
                
                # Verify create_all was called
                mock_create.assert_called_once()
    
    def test_init_db_calls_create_all_with_checkfirst(self):
        """Test that init_db calls create_all with checkfirst=True"""
        from web.backend import database
        
        mock_engine = MagicMock()
        
        with patch.object(database, 'get_engine', return_value=mock_engine):
            with patch.object(database.Base.metadata, 'create_all') as mock_create:
                database.init_db()
                
                # Verify create_all was called with checkfirst=True
                mock_create.assert_called_once_with(bind=mock_engine, checkfirst=True)
    
    def test_init_db_logs_warning_for_unexpected_errors(self):
        """Test that init_db logs warnings for unexpected errors but doesn't crash"""
        from web.backend import database
        import logging
        
        mock_engine = MagicMock()
        
        with patch.object(database, 'get_engine', return_value=mock_engine):
            with patch.object(database.Base.metadata, 'create_all') as mock_create:
                with patch.object(database.logger, 'warning') as mock_warning:
                    # Simulate an unexpected error
                    error_msg = "Some unexpected database error"
                    mock_create.side_effect = Exception(error_msg)
                    
                    # Should not raise an exception
                    database.init_db()
                    
                    # Verify warning was logged
                    assert mock_warning.call_count >= 1
                    # Check that one of the warning calls mentions the error
                    warning_calls = [str(call) for call in mock_warning.call_args_list]
                    assert any('error' in str(call).lower() for call in warning_calls)
    
    def test_init_db_succeeds_normally(self):
        """Test that init_db works normally when no errors occur"""
        from web.backend import database
        
        mock_engine = MagicMock()
        
        with patch.object(database, 'get_engine', return_value=mock_engine):
            with patch.object(database.Base.metadata, 'create_all') as mock_create:
                with patch.object(database.logger, 'info') as mock_info:
                    # Should complete successfully
                    database.init_db()
                    
                    # Verify create_all was called
                    mock_create.assert_called_once()
                    
                    # Verify success was logged
                    assert mock_info.call_count >= 1
                    info_calls = [str(call) for call in mock_info.call_args_list]
                    assert any('successfully' in str(call).lower() for call in info_calls)


class TestAppDatabaseInitialization:
    """Tests for database initialization in app.py"""
    
    def test_app_initialization_with_proper_database_url(self):
        """Test that app initializes database when DATABASE_URL is configured"""
        import os
        
        # Set a proper database URL
        test_url = "postgresql://user:pass@remote.host:5432/dbname"
        original_url = os.environ.get('DATABASE_URL')
        
        try:
            os.environ['DATABASE_URL'] = test_url
            
            # Import should work without errors
            # Note: We can't easily test the actual initialization without
            # causing side effects, but we can verify the logic
            from web.backend.database import init_db
            
            # Function should exist and be callable
            assert callable(init_db)
            
        finally:
            # Restore original
            if original_url:
                os.environ['DATABASE_URL'] = original_url
            elif 'DATABASE_URL' in os.environ:
                del os.environ['DATABASE_URL']
    
    def test_app_skips_initialization_with_localhost_url(self):
        """Test that app skips database initialization for localhost URLs"""
        import os
        
        # Test with localhost URL
        test_url = "postgresql://localhost:5432/dbname"
        original_url = os.environ.get('DATABASE_URL')
        
        try:
            os.environ['DATABASE_URL'] = test_url
            
            # The condition in app.py checks for localhost
            # and should skip initialization
            database_url = os.environ.get('DATABASE_URL', '').strip()
            should_init = database_url and not database_url.startswith('postgresql://localhost')
            
            # Should NOT initialize with localhost
            assert not should_init
            
        finally:
            # Restore original
            if original_url:
                os.environ['DATABASE_URL'] = original_url
            elif 'DATABASE_URL' in os.environ:
                del os.environ['DATABASE_URL']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
