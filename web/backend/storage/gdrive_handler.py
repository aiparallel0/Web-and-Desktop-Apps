"""
=============================================================================
GOOGLE DRIVE STORAGE HANDLER - Google Drive Integration
=============================================================================

Provides Google Drive storage integration for receipt images and files.

Environment Variables:
- GOOGLE_DRIVE_CLIENT_ID: OAuth client ID
- GOOGLE_DRIVE_CLIENT_SECRET: OAuth client secret
- GOOGLE_DRIVE_REDIRECT_URI: OAuth redirect URI

Usage:
    from storage.gdrive_handler import GoogleDriveHandler
    
    handler = GoogleDriveHandler()
    auth_url = handler.get_authorization_url()
    # After user authorizes...
    handler.handle_oauth_callback(code)
    result = handler.upload_file(image_bytes, 'receipts/image.png')

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

logger = logging.getLogger(__name__)

# Import Google Drive libraries
_gdrive_imports = OptionalImport.try_imports({
    'Credentials': 'google.oauth2.credentials.Credentials',
    'Flow': 'google_auth_oauthlib.flow.Flow',
    'build': 'googleapiclient.discovery.build',
    'MediaIoBaseUpload': 'googleapiclient.http.MediaIoBaseUpload',
    'MediaIoBaseDownload': 'googleapiclient.http.MediaIoBaseDownload'
}, install_msg='pip install google-auth google-auth-oauthlib google-api-python-client')

Credentials = _gdrive_imports['Credentials']
Flow = _gdrive_imports['Flow']
build = _gdrive_imports['build']
MediaIoBaseUpload = _gdrive_imports['MediaIoBaseUpload']
MediaIoBaseDownload = _gdrive_imports['MediaIoBaseDownload']
GDRIVE_AVAILABLE = _gdrive_imports['CREDENTIALS_AVAILABLE']  # Use any of the import keys


class GoogleDriveHandler(BaseStorageHandler):
    """
    Google Drive storage handler.
    
    Provides methods for uploading, downloading, and managing files in Google Drive.
    Requires OAuth 2.0 authorization.
    """
    
    provider = StorageProvider.GOOGLE_DRIVE
    
    # Google Drive API scopes
    SCOPES = [
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive.metadata.readonly'
    ]
    
    def __init__(
        self,
        client_id: str = None,
        client_secret: str = None,
        redirect_uri: str = None,
        credentials: Dict = None
    ):
        """
        Initialize Google Drive handler.
        
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: OAuth redirect URI
            credentials: Pre-existing OAuth credentials dict
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self._credentials = credentials
        self._service = None
        self._folder_id = None
        super().__init__()
    
    def _initialize(self) -> None:
        """Initialize Google Drive client."""
        if not GDRIVE_AVAILABLE:
            logger.error("Google Drive SDK not available")
            return
        
        # Load configuration from environment
        try:
            config = load_env_config(
                env_map={
                    'client_id': 'GOOGLE_DRIVE_CLIENT_ID',
                    'client_secret': 'GOOGLE_DRIVE_CLIENT_SECRET',
                    'redirect_uri': 'GOOGLE_DRIVE_REDIRECT_URI'
                },
                defaults={'redirect_uri': 'http://localhost:5000/api/auth/google/callback'}
            )
            
            # Override with constructor values if provided
            self.client_id = self.client_id or config.get('client_id')
            self.client_secret = self.client_secret or config.get('client_secret')
            self.redirect_uri = self.redirect_uri or config.get('redirect_uri')
            
        except Exception as e:
            logger.warning(f"Failed to load Google Drive config from environment: {e}")
        
        if not all([self.client_id, self.client_secret]):
            logger.warning("Google Drive OAuth credentials not configured")
            return
        
        # If we have existing credentials, try to initialize the service
        if self._credentials:
            try:
                creds = Credentials(**self._credentials)
                self._service = build('drive', 'v3', credentials=creds)
                self._configured = True
                log_handler_event("GoogleDriveStorage", "initialized", {'has_credentials': True})
            except Exception as e:
                logger.error(f"Failed to initialize with credentials: {e}")
        else:
            # OAuth flow will be needed
            self._configured = True  # Configured but not authenticated
            log_handler_event("GoogleDriveStorage", "configured", {'oauth_required': True})
    
    def get_authorization_url(self, state: str = None) -> str:
        """
        Get OAuth authorization URL for user consent.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL string
        """
        if not GDRIVE_AVAILABLE:
            raise StorageError("Google Drive SDK not available")
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=self.SCOPES
        )
        flow.redirect_uri = self.redirect_uri
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state
        )
        
        return auth_url
    
    def handle_oauth_callback(self, code: str) -> Dict:
        """
        Handle OAuth callback and exchange code for credentials.
        
        Args:
            code: Authorization code from callback
            
        Returns:
            Credentials dictionary
        """
        if not GDRIVE_AVAILABLE:
            raise StorageError("Google Drive SDK not available")
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=self.SCOPES
        )
        flow.redirect_uri = self.redirect_uri
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Store credentials and initialize service
        self._credentials = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': list(credentials.scopes)
        }
        
        self._service = build('drive', 'v3', credentials=credentials)
        
        return self._credentials
    
    def set_credentials(self, credentials: Dict) -> None:
        """
        Set OAuth credentials.
        
        Args:
            credentials: Credentials dictionary
        """
        self._credentials = credentials
        
        if GDRIVE_AVAILABLE and credentials:
            try:
                creds = Credentials(**credentials)
                self._service = build('drive', 'v3', credentials=creds)
            except Exception as e:
                logger.error(f"Failed to set credentials: {e}")
    
    def upload_file(
        self,
        file_data: Union[bytes, BinaryIO],
        key: str,
        content_type: str = None,
        metadata: Dict[str, str] = None
    ) -> UploadResult:
        """
        Upload a file to Google Drive.
        
        Args:
            file_data: File content as bytes or file-like object
            key: File path/name
            content_type: MIME type
            metadata: Additional metadata
            
        Returns:
            UploadResult with success status and URL
        """
        if not self._service:
            return UploadResult(
                success=False,
                key=key,
                error="Google Drive not authenticated"
            )
        
        try:
            # Get filename from key
            filename = key.split('/')[-1]
            
            # Ensure folder exists
            folder_id = self._ensure_folder_exists(key)
            
            # Prepare file metadata
            file_metadata = {
                'name': filename,
                'parents': [folder_id] if folder_id else []
            }
            
            # Convert bytes to file-like object
            if isinstance(file_data, bytes):
                file_obj = BytesIO(file_data)
                size = len(file_data)
            else:
                file_obj = file_data
                file_obj.seek(0, 2)
                size = file_obj.tell()
                file_obj.seek(0)
            
            # Determine content type
            if not content_type:
                content_type = self.get_content_type(filename)
            
            # Create media upload
            media = MediaIoBaseUpload(
                file_obj,
                mimetype=content_type,
                resumable=True
            )
            
            # Upload file
            file = self._service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink, webContentLink'
            ).execute()
            
            file_id = file.get('id')
            url = file.get('webViewLink')
            
            logger.info(f"Uploaded file to Google Drive: {key}")
            
            return UploadResult(
                success=True,
                key=file_id,
                url=url,
                size=size,
                metadata={'original_key': key}
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Google Drive upload error: {error_msg}")
            return UploadResult(
                success=False,
                key=key,
                error=error_msg
            )
    
    def download_file(self, key: str) -> Optional[bytes]:
        """
        Download a file from Google Drive.
        
        Args:
            key: File ID
            
        Returns:
            File content as bytes
        """
        if not self._service:
            logger.error("Google Drive not authenticated")
            return None
        
        try:
            request = self._service.files().get_media(fileId=key)
            file_data = BytesIO()
            downloader = MediaIoBaseDownload(file_data, request)
            
            done = False
            while not done:
                _, done = downloader.next_chunk()
            
            return file_data.getvalue()
            
        except Exception as e:
            logger.error(f"Google Drive download error: {e}")
            return None
    
    def delete_file(self, key: str) -> bool:
        """
        Delete a file from Google Drive.
        
        Args:
            key: File ID
            
        Returns:
            True if deleted successfully
        """
        if not self._service:
            logger.error("Google Drive not authenticated")
            return False
        
        try:
            self._service.files().delete(fileId=key).execute()
            logger.info(f"Deleted file from Google Drive: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Google Drive delete error: {e}")
            return False
    
    def get_file_url(
        self,
        key: str,
        expires_in: int = 3600
    ) -> Optional[str]:
        """
        Get a URL for the file.
        
        Note: Google Drive URLs don't expire but may require authentication.
        
        Args:
            key: File ID
            expires_in: Ignored for Google Drive
            
        Returns:
            Web view URL
        """
        if not self._service:
            return None
        
        try:
            file = self._service.files().get(
                fileId=key,
                fields='webViewLink, webContentLink'
            ).execute()
            
            return file.get('webViewLink') or file.get('webContentLink')
            
        except Exception as e:
            logger.error(f"Google Drive URL error: {e}")
            return None
    
    def list_files(
        self,
        prefix: str = '',
        max_results: int = 100
    ) -> List[StorageFile]:
        """
        List files in Google Drive.
        
        Args:
            prefix: Search query/folder name
            max_results: Maximum results
            
        Returns:
            List of StorageFile objects
        """
        if not self._service:
            return []
        
        try:
            query = "mimeType != 'application/vnd.google-apps.folder'"
            if prefix:
                query += f" and name contains '{prefix}'"
            
            results = self._service.files().list(
                q=query,
                pageSize=max_results,
                fields="files(id, name, size, mimeType, modifiedTime)"
            ).execute()
            
            files = []
            for item in results.get('files', []):
                files.append(StorageFile(
                    key=item['id'],
                    name=item['name'],
                    size=int(item.get('size', 0)),
                    content_type=item.get('mimeType', ''),
                    last_modified=datetime.fromisoformat(
                        item['modifiedTime'].replace('Z', '+00:00')
                    ) if 'modifiedTime' in item else None
                ))
            
            return files
            
        except Exception as e:
            logger.error(f"Google Drive list error: {e}")
            return []
    
    def file_exists(self, key: str) -> bool:
        """
        Check if a file exists in Google Drive.
        
        Args:
            key: File ID
            
        Returns:
            True if file exists
        """
        if not self._service:
            return False
        
        try:
            self._service.files().get(fileId=key).execute()
            return True
        except Exception:
            return False
    
    def _ensure_folder_exists(self, path: str) -> Optional[str]:
        """
        Ensure the folder path exists, creating if necessary.
        
        Args:
            path: Full file path
            
        Returns:
            Folder ID
        """
        if not self._service:
            return None
        
        # Get folder path (everything except the filename)
        parts = path.split('/')[:-1]
        if not parts:
            return None
        
        parent_id = 'root'
        
        for folder_name in parts:
            # Check if folder exists
            query = (
                f"name='{folder_name}' and "
                f"mimeType='application/vnd.google-apps.folder' and "
                f"'{parent_id}' in parents and "
                f"trashed=false"
            )
            
            results = self._service.files().list(
                q=query,
                fields='files(id)'
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                parent_id = files[0]['id']
            else:
                # Create folder
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [parent_id]
                }
                
                folder = self._service.files().create(
                    body=folder_metadata,
                    fields='id'
                ).execute()
                
                parent_id = folder['id']
        
        return parent_id
