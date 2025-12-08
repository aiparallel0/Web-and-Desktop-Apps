"""
=============================================================================
DROPBOX STORAGE HANDLER - Dropbox Integration
=============================================================================

Provides Dropbox storage integration for receipt images and files.

Environment Variables:
- DROPBOX_APP_KEY: Dropbox app key
- DROPBOX_APP_SECRET: Dropbox app secret
- DROPBOX_ACCESS_TOKEN: (Optional) Pre-authenticated access token

Usage:
    from storage.dropbox_handler import DropboxStorageHandler
    
    handler = DropboxStorageHandler()
    auth_url = handler.get_authorization_url()
    # After user authorizes...
    handler.handle_oauth_callback(code)
    result = handler.upload_file(image_bytes, '/receipts/image.png')

=============================================================================
"""

import os
import logging
from typing import Optional, Dict, List, Union, BinaryIO
from datetime import datetime
from io import BytesIO

from .base import (
    BaseStorageHandler, StorageFile, UploadResult,
    StorageError, StorageProvider
)
from shared.utils.optional_imports import OptionalImport
from shared.utils.base_handler import load_env_config, log_handler_event

# Import telemetry utilities
from shared.utils.telemetry import get_tracer, set_span_attributes

logger = logging.getLogger(__name__)

# Import Dropbox SDK
_dropbox_imports = OptionalImport.try_imports({
    'dropbox': 'dropbox',
    'ApiError': 'dropbox.exceptions.ApiError',
    'AuthError': 'dropbox.exceptions.AuthError',
    'WriteMode': 'dropbox.files.WriteMode'
}, install_msg='pip install dropbox>=11.36.0')

dropbox = _dropbox_imports['dropbox']
ApiError = _dropbox_imports['ApiError']
AuthError = _dropbox_imports['AuthError']
WriteMode = _dropbox_imports['WriteMode']
DROPBOX_AVAILABLE = _dropbox_imports['DROPBOX_AVAILABLE']


class DropboxStorageHandler(BaseStorageHandler):
    """
    Dropbox storage handler.
    
    Provides methods for uploading, downloading, and managing files in Dropbox.
    """
    
    provider = StorageProvider.DROPBOX
    
    # Chunk size for large file uploads (4MB)
    CHUNK_SIZE = 4 * 1024 * 1024
    
    def __init__(
        self,
        app_key: str = None,
        app_secret: str = None,
        access_token: str = None,
        refresh_token: str = None
    ):
        """
        Initialize Dropbox handler.
        
        Args:
            app_key: Dropbox app key
            app_secret: Dropbox app secret
            access_token: OAuth access token
            refresh_token: OAuth refresh token
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        self._client = None
        super().__init__()
    
    def _initialize(self) -> None:
        """Initialize Dropbox client."""
        if not DROPBOX_AVAILABLE:
            logger.error("Dropbox SDK not available")
            return
        
        # Load configuration from environment
        try:
            config = load_env_config(
                env_map={
                    'app_key': 'DROPBOX_APP_KEY',
                    'app_secret': 'DROPBOX_APP_SECRET',
                    'access_token': 'DROPBOX_ACCESS_TOKEN',
                    'refresh_token': 'DROPBOX_REFRESH_TOKEN'
                }
            )
            
            # Override with constructor values if provided
            self.app_key = self.app_key or config.get('app_key')
            self.app_secret = self.app_secret or config.get('app_secret')
            self.access_token = self.access_token or config.get('access_token')
            self.refresh_token = self.refresh_token or config.get('refresh_token')
            
        except Exception as e:
            logger.warning(f"Failed to load Dropbox config from environment: {e}")
        
        if not all([self.app_key, self.app_secret]):
            logger.warning("Dropbox OAuth credentials not configured")
            return
        
        # If we have an access token, initialize the client
        if self.access_token:
            try:
                self._client = dropbox.Dropbox(
                    oauth2_access_token=self.access_token,
                    oauth2_refresh_token=self.refresh_token,
                    app_key=self.app_key,
                    app_secret=self.app_secret
                )
                # Verify the token works
                self._client.users_get_current_account()
                self._configured = True
                log_handler_event("DropboxStorage", "initialized", {'has_token': True})
            except AuthError as e:
                logger.error(f"Dropbox auth error: {e}")
        else:
            self._configured = True  # Configured but not authenticated
            log_handler_event("DropboxStorage", "configured", {'oauth_required': True})
    
    def get_authorization_url(self, redirect_uri: str = None) -> str:
        """
        Get OAuth authorization URL for user consent.
        
        Args:
            redirect_uri: OAuth redirect URI
            
        Returns:
            Authorization URL string
        """
        tracer = get_tracer()
        with tracer.start_as_current_span("storage.dropbox.get_auth_url") as span:
            set_span_attributes(span, {
                "storage.provider": "dropbox",
                "storage.operation": "get_authorization_url"
            })
            
            if not DROPBOX_AVAILABLE:
                raise StorageError("Dropbox SDK not available")
            
            redirect_uri = redirect_uri or os.getenv(
                'DROPBOX_REDIRECT_URI',
                'http://localhost:5000/api/auth/dropbox/callback'
            )
            
            auth_flow = dropbox.DropboxOAuth2Flow(
                consumer_key=self.app_key,
                consumer_secret=self.app_secret,
                redirect_uri=redirect_uri,
                session={},
                csrf_token_session_key='dropbox-auth-csrf-token',
                token_access_type='offline'
            )
            
            auth_url = auth_flow.start()
            
            set_span_attributes(span, {
                "oauth.url_generated": True
            })
            
            return auth_url
    
    def handle_oauth_callback(
        self,
        code: str,
        redirect_uri: str = None
    ) -> Dict:
        """
        Handle OAuth callback and exchange code for tokens.
        
        Args:
            code: Authorization code from callback
            redirect_uri: OAuth redirect URI
            
        Returns:
            Dictionary with access_token and refresh_token
        """
        tracer = get_tracer()
        with tracer.start_as_current_span("storage.dropbox.oauth_callback") as span:
            set_span_attributes(span, {
                "storage.provider": "dropbox",
                "storage.operation": "oauth_callback"
            })
            
            if not DROPBOX_AVAILABLE:
                raise StorageError("Dropbox SDK not available")
            
            redirect_uri = redirect_uri or os.getenv(
                'DROPBOX_REDIRECT_URI',
                'http://localhost:5000/api/auth/dropbox/callback'
            )
            
            # Exchange code for tokens
            auth_flow = dropbox.DropboxOAuth2FlowNoRedirect(
                consumer_key=self.app_key,
                consumer_secret=self.app_secret,
                token_access_type='offline'
            )
            
            oauth_result = auth_flow.finish(code)
            
            self.access_token = oauth_result.access_token
            self.refresh_token = oauth_result.refresh_token
            
            # Initialize client with new tokens
            self._client = dropbox.Dropbox(
                oauth2_access_token=self.access_token,
                oauth2_refresh_token=self.refresh_token,
                app_key=self.app_key,
                app_secret=self.app_secret
            )
            
            set_span_attributes(span, {
                "oauth.token_exchanged": True,
                "oauth.has_refresh_token": self.refresh_token is not None,
                "oauth.account_id": oauth_result.account_id[:8] + "..." if oauth_result.account_id else None
            })
            
            logger.info("Dropbox OAuth callback handled successfully")
            
            return {
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'account_id': oauth_result.account_id
            }
    
    def set_tokens(self, access_token: str, refresh_token: str = None) -> None:
        """
        Set OAuth tokens.
        
        Args:
            access_token: Access token
            refresh_token: Refresh token
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        
        if DROPBOX_AVAILABLE:
            self._client = dropbox.Dropbox(
                oauth2_access_token=self.access_token,
                oauth2_refresh_token=self.refresh_token,
                app_key=self.app_key,
                app_secret=self.app_secret
            )
    
    def upload_file(
        self,
        file_data: Union[bytes, BinaryIO],
        key: str,
        content_type: str = None,
        metadata: Dict[str, str] = None
    ) -> UploadResult:
        """
        Upload a file to Dropbox.
        
        Args:
            file_data: File content as bytes or file-like object
            key: Dropbox path (must start with /)
            content_type: MIME type (not used by Dropbox)
            metadata: Additional metadata
            
        Returns:
            UploadResult with success status and URL
        """
        tracer = get_tracer()
        with tracer.start_as_current_span("storage.dropbox.upload") as span:
            if not self._client:
                set_span_attributes(span, {
                    "storage.provider": "dropbox",
                    "storage.operation": "upload",
                    "storage.authenticated": False
                })
                return UploadResult(
                    success=False,
                    key=key,
                    error="Dropbox not authenticated"
                )
            
            # Ensure key starts with /
            if not key.startswith('/'):
                key = '/' + key
            
            try:
                # Convert to bytes if file-like object
                if hasattr(file_data, 'read'):
                    file_data = file_data.read()
                
                size = len(file_data)
                use_chunked = size > self.CHUNK_SIZE
                
                set_span_attributes(span, {
                    "storage.provider": "dropbox",
                    "storage.operation": "upload",
                    "storage.file_size": size,
                    "storage.use_chunked_upload": use_chunked
                })
                
                # Use chunked upload for large files
                if use_chunked:
                    result = self._chunked_upload(file_data, key)
                else:
                    result = self._client.files_upload(
                        file_data,
                        key,
                        mode=WriteMode.overwrite
                    )
                
                # Try to get a shared link
                url = None
                try:
                    shared_link = self._client.sharing_create_shared_link_with_settings(
                        key
                    )
                    url = shared_link.url
                except ApiError:
                    # Link might already exist
                    links = self._client.sharing_list_shared_links(path=key)
                    url = links.links[0].url if links.links else None
                
                set_span_attributes(span, {
                    "storage.success": True,
                    "storage.has_shared_link": url is not None
                })
                
                logger.info(f"Uploaded file to Dropbox: {key}")
                
                return UploadResult(
                    success=True,
                    key=key,
                    url=url,
                    size=size,
                    metadata=metadata
                )
                
            except ApiError as e:
                error_msg = str(e)
                logger.error(f"Dropbox upload error: {error_msg}")
                span.record_exception(e)
                
                set_span_attributes(span, {
                    "storage.success": False,
                    "storage.error_type": "ApiError"
                })
                
                return UploadResult(
                    success=False,
                    key=key,
                    error=error_msg
                )
                success=False,
                key=key,
                error=error_msg
            )
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Upload failed: {error_msg}")
            return UploadResult(
                success=False,
                key=key,
                error=error_msg
            )
    
    def _chunked_upload(self, file_data: bytes, path: str):
        """
        Upload a large file in chunks.
        
        Args:
            file_data: File content
            path: Dropbox path
            
        Returns:
            Upload result
        """
        file_size = len(file_data)
        
        # Start upload session
        session = self._client.files_upload_session_start(
            file_data[:self.CHUNK_SIZE]
        )
        
        cursor = dropbox.files.UploadSessionCursor(
            session_id=session.session_id,
            offset=self.CHUNK_SIZE
        )
        
        # Upload chunks
        while cursor.offset < file_size - self.CHUNK_SIZE:
            self._client.files_upload_session_append_v2(
                file_data[cursor.offset:cursor.offset + self.CHUNK_SIZE],
                cursor
            )
            cursor.offset += self.CHUNK_SIZE
        
        # Finish upload
        commit = dropbox.files.CommitInfo(
            path=path,
            mode=WriteMode.overwrite
        )
        
        return self._client.files_upload_session_finish(
            file_data[cursor.offset:],
            cursor,
            commit
        )
    
    def download_file(self, key: str) -> Optional[bytes]:
        """
        Download a file from Dropbox.
        
        Args:
            key: Dropbox path
            
        Returns:
            File content as bytes
        """
        tracer = get_tracer()
        with tracer.start_as_current_span("storage.dropbox.download") as span:
            set_span_attributes(span, {
                "storage.provider": "dropbox",
                "storage.operation": "download"
            })
            
            if not self._client:
                logger.error("Dropbox not authenticated")
                set_span_attributes(span, {
                    "storage.authenticated": False,
                    "storage.success": False
                })
                return None
            
            # Ensure key starts with /
            if not key.startswith('/'):
                key = '/' + key
            
            try:
                _, response = self._client.files_download(key)
                content = response.content
                
                set_span_attributes(span, {
                    "storage.authenticated": True,
                    "storage.success": True,
                    "storage.file_size": len(content)
                })
                
                logger.info(f"Downloaded file from Dropbox: {key}, size: {len(content)} bytes")
                return content
                
            except ApiError as e:
                logger.error(f"Dropbox download error: {e}")
                span.record_exception(e)
                
                set_span_attributes(span, {
                    "storage.success": False,
                    "storage.error_type": "ApiError"
                })
                
                return None
            except Exception as e:
                logger.error(f"Download failed: {e}")
                span.record_exception(e)
                
                set_span_attributes(span, {
                    "storage.success": False,
                    "storage.error_type": type(e).__name__
                })
                
                return None
    
    def delete_file(self, key: str) -> bool:
        """
        Delete a file from Dropbox.
        
        Args:
            key: Dropbox path
            
        Returns:
            True if deleted successfully
        """
        if not self._client:
            logger.error("Dropbox not authenticated")
            return False
        
        # Ensure key starts with /
        if not key.startswith('/'):
            key = '/' + key
        
        try:
            self._client.files_delete_v2(key)
            logger.info(f"Deleted file from Dropbox: {key}")
            return True
            
        except ApiError as e:
            logger.error(f"Dropbox delete error: {e}")
            return False
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False
    
    def get_file_url(
        self,
        key: str,
        expires_in: int = 3600
    ) -> Optional[str]:
        """
        Get a temporary link for the file.
        
        Args:
            key: Dropbox path
            expires_in: Ignored (Dropbox links expire in 4 hours)
            
        Returns:
            Temporary link URL
        """
        if not self._client:
            return None
        
        # Ensure key starts with /
        if not key.startswith('/'):
            key = '/' + key
        
        try:
            result = self._client.files_get_temporary_link(key)
            return result.link
            
        except ApiError as e:
            logger.error(f"Dropbox URL error: {e}")
            return None
    
    def list_files(
        self,
        prefix: str = '',
        max_results: int = 100
    ) -> List[StorageFile]:
        """
        List files in Dropbox.
        
        Args:
            prefix: Folder path
            max_results: Maximum results
            
        Returns:
            List of StorageFile objects
        """
        if not self._client:
            return []
        
        # Ensure prefix starts with / or is empty
        if prefix and not prefix.startswith('/'):
            prefix = '/' + prefix
        
        try:
            result = self._client.files_list_folder(
                prefix or '',
                limit=max_results
            )
            
            files = []
            for entry in result.entries:
                if hasattr(entry, 'size'):  # Is a file, not a folder
                    files.append(StorageFile(
                        key=entry.path_lower,
                        name=entry.name,
                        size=entry.size,
                        content_type=self.get_content_type(entry.name),
                        last_modified=entry.server_modified if hasattr(entry, 'server_modified') else None
                    ))
            
            return files
            
        except ApiError as e:
            logger.error(f"Dropbox list error: {e}")
            return []
    
    def file_exists(self, key: str) -> bool:
        """
        Check if a file exists in Dropbox.
        
        Args:
            key: Dropbox path
            
        Returns:
            True if file exists
        """
        if not self._client:
            return False
        
        # Ensure key starts with /
        if not key.startswith('/'):
            key = '/' + key
        
        try:
            self._client.files_get_metadata(key)
            return True
        except ApiError:
            return False
    
    def get_account_info(self) -> Optional[Dict]:
        """Get Dropbox account information."""
        if not self._client:
            return None
        
        try:
            account = self._client.users_get_current_account()
            return {
                'account_id': account.account_id,
                'name': account.name.display_name,
                'email': account.email
            }
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return None
