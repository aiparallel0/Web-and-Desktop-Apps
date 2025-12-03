"""
=============================================================================
BASE STORAGE HANDLER - Abstract Base Class for Cloud Storage
=============================================================================

Defines the interface for all cloud storage handlers.

Usage:
    from storage.base import BaseStorageHandler
    
    class MyStorageHandler(BaseStorageHandler):
        def upload_file(self, file_data, key, **kwargs):
            # Implementation
            pass

=============================================================================
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Union, BinaryIO
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Base exception for storage operations."""
    pass


class UploadError(StorageError):
    """Error during file upload."""
    pass


class DownloadError(StorageError):
    """Error during file download."""
    pass


class DeleteError(StorageError):
    """Error during file deletion."""
    pass


class StorageProvider(Enum):
    """Supported storage providers."""
    S3 = 's3'
    GOOGLE_DRIVE = 'gdrive'
    DROPBOX = 'dropbox'
    LOCAL = 'local'


@dataclass
class StorageFile:
    """Represents a file in cloud storage."""
    key: str
    name: str
    size: int
    content_type: str
    last_modified: Optional[datetime] = None
    url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'key': self.key,
            'name': self.name,
            'size': self.size,
            'content_type': self.content_type,
            'last_modified': self.last_modified.isoformat() if self.last_modified else None,
            'url': self.url,
            'thumbnail_url': self.thumbnail_url,
            'metadata': self.metadata or {}
        }


@dataclass
class UploadResult:
    """Result of a file upload operation."""
    success: bool
    key: str
    url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    size: int = 0
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseStorageHandler(ABC):
    """
    Abstract base class for cloud storage handlers.
    
    All storage implementations must inherit from this class and
    implement the abstract methods.
    """
    
    provider: StorageProvider = StorageProvider.LOCAL
    
    def __init__(self):
        """Initialize the storage handler."""
        self._configured = False
        self._initialize()
    
    @abstractmethod
    def _initialize(self) -> None:
        """
        Initialize the storage handler with credentials.
        
        Should set self._configured = True if successful.
        """
        pass
    
    def is_configured(self) -> bool:
        """Check if the handler is properly configured."""
        return self._configured
    
    @abstractmethod
    def upload_file(
        self,
        file_data: Union[bytes, BinaryIO],
        key: str,
        content_type: str = None,
        metadata: Dict[str, str] = None
    ) -> UploadResult:
        """
        Upload a file to cloud storage.
        
        Args:
            file_data: File content as bytes or file-like object
            key: Storage key/path for the file
            content_type: MIME type of the file
            metadata: Additional metadata to store with the file
            
        Returns:
            UploadResult with success status and file URL
        """
        pass
    
    @abstractmethod
    def download_file(self, key: str) -> Optional[bytes]:
        """
        Download a file from cloud storage.
        
        Args:
            key: Storage key/path of the file
            
        Returns:
            File content as bytes, or None if not found
        """
        pass
    
    @abstractmethod
    def delete_file(self, key: str) -> bool:
        """
        Delete a file from cloud storage.
        
        Args:
            key: Storage key/path of the file
            
        Returns:
            True if deleted successfully
        """
        pass
    
    @abstractmethod
    def get_file_url(
        self,
        key: str,
        expires_in: int = 3600
    ) -> Optional[str]:
        """
        Get a URL for accessing the file.
        
        Args:
            key: Storage key/path of the file
            expires_in: URL expiration time in seconds
            
        Returns:
            URL string or None if not available
        """
        pass
    
    @abstractmethod
    def list_files(
        self,
        prefix: str = '',
        max_results: int = 100
    ) -> List[StorageFile]:
        """
        List files in storage.
        
        Args:
            prefix: Filter files by prefix/path
            max_results: Maximum number of results to return
            
        Returns:
            List of StorageFile objects
        """
        pass
    
    @abstractmethod
    def file_exists(self, key: str) -> bool:
        """
        Check if a file exists in storage.
        
        Args:
            key: Storage key/path of the file
            
        Returns:
            True if file exists
        """
        pass
    
    def generate_key(
        self,
        filename: str,
        prefix: str = 'receipts',
        user_id: str = None
    ) -> str:
        """
        Generate a unique storage key for a file.
        
        Args:
            filename: Original filename
            prefix: Path prefix
            user_id: Optional user ID for namespacing
            
        Returns:
            Generated storage key
        """
        import uuid
        from werkzeug.utils import secure_filename
        
        safe_name = secure_filename(filename)
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.utcnow().strftime('%Y%m%d')
        
        if user_id:
            return f"{prefix}/{user_id}/{timestamp}/{unique_id}_{safe_name}"
        return f"{prefix}/{timestamp}/{unique_id}_{safe_name}"
    
    def get_content_type(self, filename: str) -> str:
        """
        Determine content type from filename.
        
        Args:
            filename: Name of the file
            
        Returns:
            MIME type string
        """
        import mimetypes
        
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or 'application/octet-stream'
    
    def validate_file(
        self,
        file_data: Union[bytes, BinaryIO],
        max_size: int = 100 * 1024 * 1024,  # 100MB
        allowed_types: List[str] = None
    ) -> bool:
        """
        Validate a file before upload.
        
        Args:
            file_data: File content
            max_size: Maximum allowed size in bytes
            allowed_types: List of allowed MIME types
            
        Returns:
            True if file is valid
            
        Raises:
            ValueError: If file is invalid
        """
        if allowed_types is None:
            allowed_types = [
                'image/jpeg', 'image/png', 'image/gif',
                'image/bmp', 'image/tiff', 'image/webp'
            ]
        
        # Check size
        if isinstance(file_data, bytes):
            size = len(file_data)
        else:
            file_data.seek(0, 2)  # Seek to end
            size = file_data.tell()
            file_data.seek(0)  # Reset position
        
        if size > max_size:
            raise ValueError(f"File size {size} exceeds maximum {max_size}")
        
        return True
