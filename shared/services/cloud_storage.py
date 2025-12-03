"""
=============================================================================
CLOUD STORAGE SERVICE - Cloud Storage Provider Integrations
=============================================================================

Module: shared.services.cloud_storage
Description: Integration with cloud storage providers for file management
Compliance Version: 2.0.0

CIRCULAR EXCHANGE INTEGRATION:
This module is integrated with the Circular Information Exchange Framework.
It provides cloud storage access via Google Drive, Dropbox, and AWS S3.

Supported Providers:
- Google Drive: OAuth2-based access to Google Drive files
- Dropbox: Token-based access to Dropbox files
- AWS S3: Credential-based access to S3 buckets

Dependencies: shared.circular_exchange
Exports: CloudStorageService, GoogleDriveProvider, DropboxProvider, S3Provider

Environment Variables:
- GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET: Google OAuth credentials
- DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_ACCESS_TOKEN: Dropbox credentials
- AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION: AWS credentials

=============================================================================
"""

import os
import io
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, BinaryIO
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

# Import circular exchange decorator to reduce boilerplate
from shared.utils.decorators import circular_exchange_module

logger = logging.getLogger(__name__)

# Register module with Circular Exchange Framework using decorator
@circular_exchange_module(
    module_id="shared.services.cloud_storage",
    description="Cloud storage provider integration for file management",
    dependencies=["shared.circular_exchange"],
    exports=["CloudStorageService", "GoogleDriveProvider", "DropboxProvider", "S3Provider"]
)
def _register_module():
    """Module registration placeholder for decorator."""
    pass

_register_module()


class StorageProvider(Enum):
    """Supported cloud storage providers."""
    GOOGLE_DRIVE = "google_drive"
    DROPBOX = "dropbox"
    S3 = "s3"


@dataclass
class CloudFile:
    """Represents a file in cloud storage."""
    id: str
    name: str
    path: str
    size: int
    mime_type: str
    modified_at: datetime
    provider: StorageProvider
    is_folder: bool = False
    download_url: Optional[str] = None
    thumbnail_url: Optional[str] = None


class GoogleDriveProvider:
    """
    Google Drive storage provider.
    
    Provides access to Google Drive files using OAuth2 authentication.
    
    Usage:
        provider = GoogleDriveProvider(credentials=oauth_credentials)
        files = provider.list_files('/receipts')
        local_path = provider.download_file(file_id, '/tmp/receipt.jpg')
    """
    
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    def __init__(
        self,
        credentials: Dict = None,
        client_id: str = None,
        client_secret: str = None,
        access_token: str = None,
        refresh_token: str = None
    ):
        """
        Initialize Google Drive provider.
        
        Args:
            credentials: OAuth2 credentials dict
            client_id: Google OAuth client ID
            client_secret: Google OAuth client secret
            access_token: OAuth access token
            refresh_token: OAuth refresh token
        """
        self.client_id = client_id or os.environ.get('GOOGLE_CLIENT_ID')
        self.client_secret = client_secret or os.environ.get('GOOGLE_CLIENT_SECRET')
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.credentials = credentials
        self.service = None
        
        if credentials:
            self._init_from_credentials(credentials)
        elif access_token:
            self._init_from_token()
        
        logger.info("GoogleDriveProvider initialized")
    
    def _init_from_credentials(self, credentials: Dict):
        """Initialize from credentials dict."""
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            
            creds = Credentials(
                token=credentials.get('access_token'),
                refresh_token=credentials.get('refresh_token'),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            self.service = build('drive', 'v3', credentials=creds)
            
        except ImportError:
            raise ImportError(
                "Google API client required. Install with: "
                "pip install google-api-python-client google-auth-oauthlib"
            )
    
    def _init_from_token(self):
        """Initialize from access token."""
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            
            creds = Credentials(
                token=self.access_token,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            self.service = build('drive', 'v3', credentials=creds)
            
        except ImportError:
            raise ImportError(
                "Google API client required. Install with: "
                "pip install google-api-python-client google-auth-oauthlib"
            )
    
    def authenticate(self, auth_code: str = None) -> Dict:
        """
        Authenticate with Google Drive.
        
        Args:
            auth_code: OAuth authorization code (for initial auth)
            
        Returns:
            Credentials dict with access_token and refresh_token
        """
        try:
            from google_auth_oauthlib.flow import Flow
            
            flow = Flow.from_client_config(
                {
                    "installed": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token"
                    }
                },
                scopes=self.SCOPES,
                redirect_uri="urn:ietf:wg:oauth:2.0:oob"
            )
            
            if auth_code:
                flow.fetch_token(code=auth_code)
                creds = flow.credentials
                
                return {
                    'access_token': creds.token,
                    'refresh_token': creds.refresh_token,
                    'expiry': creds.expiry.isoformat() if creds.expiry else None
                }
            else:
                auth_url, _ = flow.authorization_url(prompt='consent')
                return {'auth_url': auth_url}
                
        except ImportError:
            raise ImportError(
                "Google auth library required. Install with: "
                "pip install google-auth-oauthlib"
            )
    
    def list_files(self, folder_path: str = '/', page_size: int = 100) -> List[CloudFile]:
        """
        List files in a folder.
        
        Args:
            folder_path: Path to folder (use 'root' for root folder)
            page_size: Number of files to return
            
        Returns:
            List of CloudFile objects
        """
        if not self.service:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        try:
            # Get folder ID from path
            folder_id = 'root' if folder_path in ('/', 'root') else self._get_folder_id(folder_path)
            
            query = f"'{folder_id}' in parents and trashed = false"
            
            results = self.service.files().list(
                q=query,
                pageSize=page_size,
                fields="files(id, name, mimeType, size, modifiedTime, webContentLink, thumbnailLink)"
            ).execute()
            
            files = []
            for item in results.get('files', []):
                is_folder = item['mimeType'] == 'application/vnd.google-apps.folder'
                
                files.append(CloudFile(
                    id=item['id'],
                    name=item['name'],
                    path=f"{folder_path}/{item['name']}",
                    size=int(item.get('size', 0)),
                    mime_type=item['mimeType'],
                    modified_at=datetime.fromisoformat(item['modifiedTime'].replace('Z', '+00:00')) if item.get('modifiedTime') else datetime.now(),
                    provider=StorageProvider.GOOGLE_DRIVE,
                    is_folder=is_folder,
                    download_url=item.get('webContentLink'),
                    thumbnail_url=item.get('thumbnailLink')
                ))
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list Google Drive files: {e}")
            raise
    
    def _get_folder_id(self, path: str) -> str:
        """Get folder ID from path."""
        parts = path.strip('/').split('/')
        parent_id = 'root'
        
        for part in parts:
            query = f"'{parent_id}' in parents and name = '{part}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            results = self.service.files().list(q=query, fields="files(id)").execute()
            
            if not results.get('files'):
                raise ValueError(f"Folder not found: {part}")
            
            parent_id = results['files'][0]['id']
        
        return parent_id
    
    def download_file(self, file_id: str, local_path: str) -> str:
        """
        Download a file from Google Drive.
        
        Args:
            file_id: Google Drive file ID
            local_path: Local path to save file
            
        Returns:
            Path to downloaded file
        """
        if not self.service:
            raise ValueError("Not authenticated")
        
        try:
            from googleapiclient.http import MediaIoBaseDownload
            
            request = self.service.files().get_media(fileId=file_id)
            
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(local_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            
            logger.info(f"Downloaded file to: {local_path}")
            return local_path
            
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            raise


class DropboxProvider:
    """
    Dropbox storage provider.
    
    Provides access to Dropbox files using OAuth2 or access token.
    
    Usage:
        provider = DropboxProvider(access_token="xxxx")
        files = provider.list_files('/receipts')
        local_path = provider.download_file('/receipts/receipt.jpg', '/tmp/receipt.jpg')
    """
    
    def __init__(
        self,
        access_token: str = None,
        app_key: str = None,
        app_secret: str = None,
        refresh_token: str = None
    ):
        """
        Initialize Dropbox provider.
        
        Args:
            access_token: Dropbox access token
            app_key: Dropbox app key
            app_secret: Dropbox app secret
            refresh_token: OAuth refresh token
        """
        self.access_token = access_token or os.environ.get('DROPBOX_ACCESS_TOKEN')
        self.app_key = app_key or os.environ.get('DROPBOX_APP_KEY')
        self.app_secret = app_secret or os.environ.get('DROPBOX_APP_SECRET')
        self.refresh_token = refresh_token
        self.dbx = None
        
        if self.access_token:
            self._init_client()
        
        logger.info("DropboxProvider initialized")
    
    def _init_client(self):
        """Initialize Dropbox client."""
        try:
            import dropbox
            
            if self.refresh_token and self.app_key and self.app_secret:
                self.dbx = dropbox.Dropbox(
                    oauth2_refresh_token=self.refresh_token,
                    app_key=self.app_key,
                    app_secret=self.app_secret
                )
            else:
                self.dbx = dropbox.Dropbox(self.access_token)
            
        except ImportError:
            raise ImportError("Dropbox SDK required. Install with: pip install dropbox")
    
    def authenticate(self, auth_code: str = None) -> Dict:
        """
        Authenticate with Dropbox.
        
        Args:
            auth_code: OAuth authorization code
            
        Returns:
            Credentials dict
        """
        try:
            import dropbox
            
            if not self.app_key or not self.app_secret:
                raise ValueError("App key and secret required for authentication")
            
            auth_flow = dropbox.DropboxOAuth2FlowNoRedirect(
                self.app_key,
                self.app_secret,
                token_access_type='offline'
            )
            
            if auth_code:
                oauth_result = auth_flow.finish(auth_code)
                
                self.access_token = oauth_result.access_token
                self.refresh_token = oauth_result.refresh_token
                self._init_client()
                
                return {
                    'access_token': oauth_result.access_token,
                    'refresh_token': oauth_result.refresh_token
                }
            else:
                auth_url = auth_flow.start()
                return {'auth_url': auth_url}
                
        except ImportError:
            raise ImportError("Dropbox SDK required. Install with: pip install dropbox")
    
    def list_files(self, folder_path: str = '/', recursive: bool = False) -> List[CloudFile]:
        """
        List files in a folder.
        
        Args:
            folder_path: Path to folder
            recursive: Include subfolders
            
        Returns:
            List of CloudFile objects
        """
        if not self.dbx:
            raise ValueError("Not authenticated")
        
        try:
            import dropbox
            
            # Dropbox uses empty string for root
            path = '' if folder_path == '/' else folder_path
            
            result = self.dbx.files_list_folder(path, recursive=recursive)
            
            files = []
            for entry in result.entries:
                is_folder = isinstance(entry, dropbox.files.FolderMetadata)
                
                if is_folder:
                    files.append(CloudFile(
                        id=entry.id,
                        name=entry.name,
                        path=entry.path_display,
                        size=0,
                        mime_type='folder',
                        modified_at=datetime.now(),
                        provider=StorageProvider.DROPBOX,
                        is_folder=True
                    ))
                else:
                    files.append(CloudFile(
                        id=entry.id,
                        name=entry.name,
                        path=entry.path_display,
                        size=entry.size,
                        mime_type=self._get_mime_type(entry.name),
                        modified_at=entry.server_modified,
                        provider=StorageProvider.DROPBOX,
                        is_folder=False
                    ))
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list Dropbox files: {e}")
            raise
    
    def _get_mime_type(self, filename: str) -> str:
        """Get MIME type from filename."""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'
    
    def download_file(self, dropbox_path: str, local_path: str) -> str:
        """
        Download a file from Dropbox.
        
        Args:
            dropbox_path: Path in Dropbox
            local_path: Local path to save file
            
        Returns:
            Path to downloaded file
        """
        if not self.dbx:
            raise ValueError("Not authenticated")
        
        try:
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.dbx.files_download_to_file(local_path, dropbox_path)
            
            logger.info(f"Downloaded file to: {local_path}")
            return local_path
            
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            raise


class S3Provider:
    """
    AWS S3 storage provider.
    
    Provides access to S3 buckets using AWS credentials.
    
    Usage:
        provider = S3Provider(bucket='my-bucket')
        files = provider.list_files('receipts/')
        local_path = provider.download_file('receipts/receipt.jpg', '/tmp/receipt.jpg')
    """
    
    def __init__(
        self,
        bucket: str = None,
        access_key_id: str = None,
        secret_access_key: str = None,
        region: str = None,
        endpoint_url: str = None
    ):
        """
        Initialize S3 provider.
        
        Args:
            bucket: S3 bucket name
            access_key_id: AWS access key ID
            secret_access_key: AWS secret access key
            region: AWS region
            endpoint_url: Custom endpoint URL (for S3-compatible services)
        """
        self.bucket = bucket or os.environ.get('AWS_S3_BUCKET')
        self.access_key_id = access_key_id or os.environ.get('AWS_ACCESS_KEY_ID')
        self.secret_access_key = secret_access_key or os.environ.get('AWS_SECRET_ACCESS_KEY')
        self.region = region or os.environ.get('AWS_REGION', 'us-east-1')
        self.endpoint_url = endpoint_url
        self.s3_client = None
        
        if self.access_key_id and self.secret_access_key:
            self._init_client()
        
        logger.info(f"S3Provider initialized for bucket: {self.bucket}")
    
    def _init_client(self):
        """Initialize S3 client."""
        try:
            import boto3
            
            client_kwargs = {
                'aws_access_key_id': self.access_key_id,
                'aws_secret_access_key': self.secret_access_key,
                'region_name': self.region
            }
            
            if self.endpoint_url:
                client_kwargs['endpoint_url'] = self.endpoint_url
            
            self.s3_client = boto3.client('s3', **client_kwargs)
            
        except ImportError:
            raise ImportError("boto3 required. Install with: pip install boto3")
    
    def list_files(self, prefix: str = '', max_keys: int = 1000) -> List[CloudFile]:
        """
        List files in S3 bucket.
        
        Args:
            prefix: Key prefix (folder path)
            max_keys: Maximum number of files to return
            
        Returns:
            List of CloudFile objects
        """
        if not self.s3_client:
            raise ValueError("Not authenticated")
        
        if not self.bucket:
            raise ValueError("Bucket name required")
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            files = []
            for obj in response.get('Contents', []):
                key = obj['Key']
                is_folder = key.endswith('/')
                
                files.append(CloudFile(
                    id=key,
                    name=Path(key).name,
                    path=key,
                    size=obj['Size'],
                    mime_type=self._get_mime_type(key),
                    modified_at=obj['LastModified'],
                    provider=StorageProvider.S3,
                    is_folder=is_folder
                ))
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list S3 files: {e}")
            raise
    
    def _get_mime_type(self, key: str) -> str:
        """Get MIME type from key."""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(key)
        return mime_type or 'application/octet-stream'
    
    def download_file(self, s3_key: str, local_path: str) -> str:
        """
        Download a file from S3.
        
        Args:
            s3_key: S3 object key
            local_path: Local path to save file
            
        Returns:
            Path to downloaded file
        """
        if not self.s3_client:
            raise ValueError("Not authenticated")
        
        if not self.bucket:
            raise ValueError("Bucket name required")
        
        try:
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.s3_client.download_file(self.bucket, s3_key, local_path)
            
            logger.info(f"Downloaded file to: {local_path}")
            return local_path
            
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            raise
    
    def get_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for downloading.
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration in seconds
            
        Returns:
            Presigned URL
        """
        if not self.s3_client:
            raise ValueError("Not authenticated")
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise


class CloudStorageService:
    """
    Unified interface for cloud storage providers.
    
    Provides a consistent API across multiple storage providers.
    
    Usage:
        service = CloudStorageService()
        service.configure_google_drive(credentials)
        files = service.list_files('google_drive', '/receipts')
        local_path = service.download_file('google_drive', file_id, '/tmp/receipt.jpg')
    """
    
    def __init__(self):
        """Initialize cloud storage service."""
        self.providers = {}
        logger.info("CloudStorageService initialized")
    
    def configure_google_drive(
        self,
        credentials: Dict = None,
        client_id: str = None,
        client_secret: str = None,
        access_token: str = None
    ):
        """Configure Google Drive provider."""
        self.providers['google_drive'] = GoogleDriveProvider(
            credentials=credentials,
            client_id=client_id,
            client_secret=client_secret,
            access_token=access_token
        )
    
    def configure_dropbox(
        self,
        access_token: str = None,
        app_key: str = None,
        app_secret: str = None
    ):
        """Configure Dropbox provider."""
        self.providers['dropbox'] = DropboxProvider(
            access_token=access_token,
            app_key=app_key,
            app_secret=app_secret
        )
    
    def configure_s3(
        self,
        bucket: str = None,
        access_key_id: str = None,
        secret_access_key: str = None,
        region: str = None
    ):
        """Configure S3 provider."""
        self.providers['s3'] = S3Provider(
            bucket=bucket,
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            region=region
        )
    
    def get_available_providers(self) -> List[str]:
        """Get list of configured providers."""
        return list(self.providers.keys())
    
    def authenticate(self, provider: str, auth_code: str = None) -> Dict:
        """
        Authenticate with a provider.
        
        Args:
            provider: Provider name
            auth_code: OAuth authorization code
            
        Returns:
            Authentication result
        """
        if provider not in self.providers:
            raise ValueError(f"Provider '{provider}' not configured")
        
        return self.providers[provider].authenticate(auth_code)
    
    def list_files(self, provider: str, path: str = '/') -> List[CloudFile]:
        """
        List files from a provider.
        
        Args:
            provider: Provider name
            path: Folder path
            
        Returns:
            List of CloudFile objects
        """
        if provider not in self.providers:
            raise ValueError(f"Provider '{provider}' not configured")
        
        return self.providers[provider].list_files(path)
    
    def download_file(self, provider: str, file_id_or_path: str, local_path: str) -> str:
        """
        Download a file from a provider.
        
        Args:
            provider: Provider name
            file_id_or_path: File ID or path in cloud storage
            local_path: Local path to save file
            
        Returns:
            Path to downloaded file
        """
        if provider not in self.providers:
            raise ValueError(f"Provider '{provider}' not configured")
        
        return self.providers[provider].download_file(file_id_or_path, local_path)


__all__ = [
    'CloudStorageService',
    'GoogleDriveProvider',
    'DropboxProvider',
    'S3Provider',
    'CloudFile',
    'StorageProvider'
]
