"""
=============================================================================
SERVICES PACKAGE - External Service Integrations
=============================================================================

Module: shared.services
Description: External service integrations for cloud ML and storage
Compliance Version: 2.0.0

CIRCULAR EXCHANGE INTEGRATION:
This package provides integrations with external cloud services.

Modules:
- cloud_finetuning: Cloud ML platform integrations (HuggingFace, Replicate, RunPod)
- cloud_storage: Cloud storage integrations (Google Drive, Dropbox, S3)

=============================================================================
"""

try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    PROJECT_CONFIG.register_module(ModuleRegistration(
        module_id="shared.services",
        file_path=__file__,
        description="External service integrations package",
        dependencies=["shared.circular_exchange"],
        exports=["CloudFinetuningService", "CloudStorageService"]
    ))
except ImportError:
    pass

from .cloud_finetuning import (
    CloudFinetuningService,
    HuggingFaceTrainer,
    ReplicateTrainer,
    RunPodTrainer,
    TrainingJob,
    CloudProvider
)

from .cloud_storage import (
    CloudStorageService,
    GoogleDriveProvider,
    DropboxProvider,
    S3Provider,
    CloudFile,
    StorageProvider
)

__all__ = [
    'CloudFinetuningService',
    'HuggingFaceTrainer',
    'ReplicateTrainer',
    'RunPodTrainer',
    'TrainingJob',
    'CloudProvider',
    'CloudStorageService',
    'GoogleDriveProvider',
    'DropboxProvider',
    'S3Provider',
    'CloudFile',
    'StorageProvider'
]

__version__ = '1.0.0'
