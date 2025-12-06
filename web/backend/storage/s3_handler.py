"""
=============================================================================
AWS S3 STORAGE HANDLER - S3 Cloud Storage Integration
=============================================================================

Provides AWS S3 storage integration for receipt images and files.

Environment Variables:
- AWS_ACCESS_KEY_ID: AWS access key
- AWS_SECRET_ACCESS_KEY: AWS secret key
- AWS_S3_BUCKET: S3 bucket name
- AWS_REGION: AWS region (default: us-east-1)

Usage:
    from storage.s3_handler import S3StorageHandler
    
    handler = S3StorageHandler()
    result = handler.upload_file(image_bytes, 'receipts/image.png')
    url = handler.get_file_url('receipts/image.png')

=============================================================================
"""

import os
import logging
from typing import Optional, Dict, List, Union, BinaryIO
from datetime import datetime
from io import BytesIO

from .base import (
    BaseStorageHandler, StorageFile, UploadResult,
    StorageError, UploadError, DownloadError, DeleteError,
    StorageProvider
)
from shared.utils.optional_imports import OptionalImport

logger = logging.getLogger(__name__)

# Import boto3 and dependencies
_boto3_imports = OptionalImport.try_imports({
    'boto3': 'boto3',
    'ClientError': 'botocore.exceptions.ClientError',
    'NoCredentialsError': 'botocore.exceptions.NoCredentialsError'
}, install_msg='pip install boto3>=1.34.0')

boto3 = _boto3_imports['boto3']
ClientError = _boto3_imports['ClientError']
NoCredentialsError = _boto3_imports['NoCredentialsError']
BOTO3_AVAILABLE = _boto3_imports['BOTO3_AVAILABLE']


class S3StorageHandler(BaseStorageHandler):
    """
    AWS S3 storage handler.
    
    Provides methods for uploading, downloading, and managing files in S3.
    """
    
    provider = StorageProvider.S3
    
    def __init__(
        self,
        bucket_name: str = None,
        region: str = None,
        access_key: str = None,
        secret_key: str = None
    ):
        """
        Initialize S3 storage handler.
        
        Args:
            bucket_name: S3 bucket name (defaults to AWS_S3_BUCKET env var)
            region: AWS region (defaults to AWS_REGION env var)
            access_key: AWS access key (defaults to AWS_ACCESS_KEY_ID env var)
            secret_key: AWS secret key (defaults to AWS_SECRET_ACCESS_KEY env var)
        """
        self.bucket_name = bucket_name
        self.region = region
        self.access_key = access_key
        self.secret_key = secret_key
        self._client = None
        self._resource = None
        super().__init__()
    
    def _initialize(self) -> None:
        """Initialize S3 client."""
        if not BOTO3_AVAILABLE:
            logger.error("boto3 not available")
            return
        
        self.bucket_name = self.bucket_name or os.getenv('AWS_S3_BUCKET')
        self.region = self.region or os.getenv('AWS_REGION', 'us-east-1')
        self.access_key = self.access_key or os.getenv('AWS_ACCESS_KEY_ID')
        self.secret_key = self.secret_key or os.getenv('AWS_SECRET_ACCESS_KEY')
        
        if not self.bucket_name:
            logger.warning("AWS_S3_BUCKET not configured")
            return
        
        try:
            session_kwargs = {'region_name': self.region}
            
            if self.access_key and self.secret_key:
                session_kwargs['aws_access_key_id'] = self.access_key
                session_kwargs['aws_secret_access_key'] = self.secret_key
            
            self._client = boto3.client('s3', **session_kwargs)
            self._resource = boto3.resource('s3', **session_kwargs)
            
            # Verify bucket exists
            self._client.head_bucket(Bucket=self.bucket_name)
            
            self._configured = True
            logger.info(f"S3 storage initialized: bucket={self.bucket_name}")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found")
        except ClientError as e:
            logger.error(f"S3 initialization error: {e}")
        except Exception as e:
            logger.error(f"S3 initialization failed: {e}")
    
    def upload_file(
        self,
        file_data: Union[bytes, BinaryIO],
        key: str,
        content_type: str = None,
        metadata: Dict[str, str] = None
    ) -> UploadResult:
        """
        Upload a file to S3.
        
        Args:
            file_data: File content as bytes or file-like object
            key: S3 object key
            content_type: MIME type
            metadata: Additional metadata
            
        Returns:
            UploadResult with success status and URL
        """
        if not self._configured:
            return UploadResult(
                success=False,
                key=key,
                error="S3 not configured"
            )
        
        try:
            # Convert bytes to file-like object
            if isinstance(file_data, bytes):
                file_obj = BytesIO(file_data)
                size = len(file_data)
            else:
                file_obj = file_data
                file_obj.seek(0, 2)
                size = file_obj.tell()
                file_obj.seek(0)
            
            # Prepare extra args
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            if metadata:
                extra_args['Metadata'] = metadata
            
            # Upload file
            self._client.upload_fileobj(
                file_obj,
                self.bucket_name,
                key,
                ExtraArgs=extra_args if extra_args else None
            )
            
            # Generate URL
            url = self.get_file_url(key)
            
            logger.info(f"Uploaded file to S3: {key}")
            
            return UploadResult(
                success=True,
                key=key,
                url=url,
                size=size,
                metadata=metadata
            )
            
        except ClientError as e:
            error_msg = str(e)
            logger.error(f"S3 upload error: {error_msg}")
            return UploadResult(
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
    
    def download_file(self, key: str) -> Optional[bytes]:
        """
        Download a file from S3.
        
        Args:
            key: S3 object key
            
        Returns:
            File content as bytes
        """
        if not self._configured:
            logger.error("S3 not configured")
            return None
        
        try:
            response = self._client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return response['Body'].read()
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"File not found: {key}")
            else:
                logger.error(f"S3 download error: {e}")
            return None
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None
    
    def delete_file(self, key: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            key: S3 object key
            
        Returns:
            True if deleted successfully
        """
        if not self._configured:
            logger.error("S3 not configured")
            return False
        
        try:
            self._client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            logger.info(f"Deleted file from S3: {key}")
            return True
            
        except ClientError as e:
            logger.error(f"S3 delete error: {e}")
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
        Generate a presigned URL for the file.
        
        Args:
            key: S3 object key
            expires_in: URL expiration time in seconds (default 1 hour)
            
        Returns:
            Presigned URL string
        """
        if not self._configured:
            return None
        
        try:
            url = self._client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key
                },
                ExpiresIn=expires_in
            )
            return url
            
        except ClientError as e:
            logger.error(f"URL generation error: {e}")
            return None
    
    def get_download_url(
        self,
        key: str,
        expires_in: int = 3600
    ) -> Optional[str]:
        """
        Generate a presigned download URL for the file.
        
        This is an alias for get_file_url for API compatibility.
        
        Args:
            key: S3 object key
            expires_in: URL expiration time in seconds (default 1 hour)
            
        Returns:
            Presigned URL string
        """
        return self.get_file_url(key, expires_in)
    
    def list_files(
        self,
        prefix: str = '',
        max_results: int = 100
    ) -> List[StorageFile]:
        """
        List files in the S3 bucket.
        
        Args:
            prefix: Filter by key prefix
            max_results: Maximum number of results
            
        Returns:
            List of StorageFile objects
        """
        if not self._configured:
            return []
        
        try:
            response = self._client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_results
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append(StorageFile(
                    key=obj['Key'],
                    name=obj['Key'].split('/')[-1],
                    size=obj['Size'],
                    content_type=self._get_content_type(obj['Key']),
                    last_modified=obj['LastModified']
                ))
            
            return files
            
        except ClientError as e:
            logger.error(f"S3 list error: {e}")
            return []
    
    def file_exists(self, key: str) -> bool:
        """
        Check if a file exists in S3.
        
        Args:
            key: S3 object key
            
        Returns:
            True if file exists
        """
        if not self._configured:
            return False
        
        try:
            self._client.head_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
        except ClientError:
            return False
    
    def _get_content_type(self, key: str) -> str:
        """Get content type from object metadata or filename."""
        try:
            response = self._client.head_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return response.get('ContentType', 'application/octet-stream')
        except Exception:
            return self.get_content_type(key)
    
    def copy_file(
        self,
        source_key: str,
        dest_key: str
    ) -> bool:
        """
        Copy a file within S3.
        
        Args:
            source_key: Source object key
            dest_key: Destination object key
            
        Returns:
            True if copied successfully
        """
        if not self._configured:
            return False
        
        try:
            copy_source = {
                'Bucket': self.bucket_name,
                'Key': source_key
            }
            self._client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=dest_key
            )
            return True
        except ClientError as e:
            logger.error(f"S3 copy error: {e}")
            return False
    
    def get_bucket_info(self) -> Dict[str, any]:
        """Get bucket information."""
        if not self._configured:
            return {}
        
        return {
            'bucket_name': self.bucket_name,
            'region': self.region,
            'configured': self._configured
        }
