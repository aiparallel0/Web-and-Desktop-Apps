"""
=============================================================================
STORAGE MODULE - Cloud Storage Integration
=============================================================================

This module provides cloud storage integration for the Receipt Extractor
platform, supporting multiple storage providers.

Components:
- base.py: Abstract base class for storage handlers
- s3_handler.py: AWS S3 storage handler
- gdrive_handler.py: Google Drive storage handler
- dropbox_handler.py: Dropbox storage handler

Environment Variables Required:
- AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET (for S3)
- GOOGLE_DRIVE_CLIENT_ID, GOOGLE_DRIVE_CLIENT_SECRET (for Google Drive)
- DROPBOX_APP_KEY, DROPBOX_APP_SECRET (for Dropbox)

=============================================================================
"""

from .base import BaseStorageHandler, StorageFile, StorageError
from .s3_handler import S3StorageHandler
from .gdrive_handler import GoogleDriveHandler
from .dropbox_handler import DropboxStorageHandler

__all__ = [
    # Base
    'BaseStorageHandler',
    'StorageFile',
    'StorageError',
    # Handlers
    'S3StorageHandler',
    'GoogleDriveHandler',
    'DropboxStorageHandler',
    # Factory
    'StorageFactory',
    'get_storage_handler',
]


class StorageFactory:
    """
    Factory for creating storage handler instances.
    
    Usage:
        handler = StorageFactory.get_handler('s3')
        handler.upload_file(file_data, 'receipts/image.png')
    """
    
    _handlers = {
        's3': S3StorageHandler,
        'aws': S3StorageHandler,
        'gdrive': GoogleDriveHandler,
        'google_drive': GoogleDriveHandler,
        'dropbox': DropboxStorageHandler,
    }
    
    @classmethod
    def get_handler(cls, provider: str) -> BaseStorageHandler:
        """
        Get a storage handler for the specified provider.
        
        Args:
            provider: Storage provider name ('s3', 'gdrive', 'dropbox')
            
        Returns:
            Configured storage handler instance
            
        Raises:
            ValueError: If provider is not supported
        """
        provider = provider.lower().strip()
        
        if provider not in cls._handlers:
            supported = list(cls._handlers.keys())
            raise ValueError(
                f"Unsupported storage provider: {provider}. "
                f"Supported providers: {supported}"
            )
        
        handler_class = cls._handlers[provider]
        return handler_class()
    
    @classmethod
    def list_providers(cls) -> list:
        """Get list of supported storage providers."""
        return list(set(cls._handlers.values()))
    
    @classmethod
    def is_provider_available(cls, provider: str) -> bool:
        """Check if a provider is available and configured."""
        try:
            handler = cls.get_handler(provider)
            return handler.is_configured()
        except (ValueError, ImportError):
            return False


def get_storage_handler(provider: str = 's3') -> BaseStorageHandler:
    """
    Convenience function to get a storage handler.
    
    Args:
        provider: Storage provider name
        
    Returns:
        Configured storage handler
    """
    return StorageFactory.get_handler(provider)
