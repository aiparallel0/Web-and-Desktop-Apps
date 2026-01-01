"""
=============================================================================
CLOUD FINETUNING SERVICE - Remote Model Training Integration
=============================================================================

Module: shared.services.cloud_finetuning
Description: Integration with cloud ML platforms for model finetuning
Compliance Version: 2.0.0

CIRCULAR EXCHANGE INTEGRATION:
This module is integrated with the Circular Information Exchange Framework.
It provides cloud-based model finetuning via HuggingFace, Replicate, and RunPod.

Supported Platforms:
- HuggingFace Spaces: For training models on HuggingFace infrastructure
- Replicate: For running custom training workflows
- RunPod: For GPU-based training on demand

Dependencies: shared.circular_exchange
Exports: CloudFinetuningService, HuggingFaceTrainer, ReplicateTrainer, RunPodTrainer

Environment Variables Required:
- HUGGINGFACE_TOKEN: HuggingFace API token
- REPLICATE_API_TOKEN: Replicate API token
- RUNPOD_API_KEY: RunPod API key

=============================================================================
"""

import os
import json
import logging
import time
import base64
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

# Import circular exchange decorator to reduce boilerplate
from shared.utils.decorators import circular_exchange_module

logger = logging.getLogger(__name__)

# Register module with Circular Exchange Framework using decorator
@circular_exchange_module(
    module_id="shared.services.cloud_finetuning",
    description="Cloud ML platform integration for model finetuning",
    dependencies=["shared.circular_exchange"],
    exports=["CloudFinetuningService", "HuggingFaceTrainer", "ReplicateTrainer", "RunPodTrainer"]
)
def _register_module():
    """Module registration placeholder for decorator."""
    pass

_register_module()


class CloudProvider(Enum):
    """Supported cloud training providers."""
    HUGGINGFACE = "huggingface"
    REPLICATE = "replicate"
    RUNPOD = "runpod"


@dataclass
class TrainingJob:
    """Represents a cloud training job."""
    job_id: str
    provider: CloudProvider
    status: str
    model_id: str
    created_at: float
    updated_at: float
    progress: float = 0.0
    metrics: Optional[Dict] = None
    error: Optional[str] = None
    output_url: Optional[str] = None


class HuggingFaceTrainer:
    """
    HuggingFace Spaces trainer for cloud-based model finetuning.
    
    Uses HuggingFace's infrastructure to train models. Requires:
    - HuggingFace account with API token
    - Sufficient compute quota
    
    Usage:
        trainer = HuggingFaceTrainer(token="hf_xxxxx")
        job = trainer.start_training(model_id, training_data, config)
        status = trainer.get_status(job.job_id)
    """
    
    API_BASE = "https://huggingface.co/api"
    
    def __init__(self, token: str = None):
        """
        Initialize HuggingFace trainer.
        
        Args:
            token: HuggingFace API token (or set HUGGINGFACE_TOKEN env var)
        """
        self.token = token or os.environ.get('HUGGINGFACE_TOKEN')
        if not self.token:
            raise ValueError(
                "HuggingFace token required. Pass token parameter or set HUGGINGFACE_TOKEN environment variable."
            )
        
        self.headers = {"Authorization": f"Bearer {self.token}"}
        logger.info("HuggingFaceTrainer initialized")
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make authenticated request to HuggingFace API."""
        import requests
        
        url = f"{self.API_BASE}/{endpoint}"
        
        if method == "GET":
            response = requests.get(url, headers=self.headers)
        elif method == "POST":
            response = requests.post(url, headers=self.headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    def upload_training_data(self, training_data: List[Dict], repo_id: str) -> str:
        """
        Upload training data to HuggingFace dataset repository.
        
        Args:
            training_data: List of training samples
            repo_id: HuggingFace repository ID (e.g., "username/dataset-name")
            
        Returns:
            URL of the uploaded dataset
        """
        try:
            from huggingface_hub import HfApi, create_repo
            
            api = HfApi(token=self.token)
            
            # Create dataset repo if needed
            try:
                create_repo(repo_id, repo_type="dataset", token=self.token)
            except Exception:
                pass  # Repo may already exist
            
            # Prepare data file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(training_data, f)
                temp_path = f.name
            
            # Upload
            api.upload_file(
                path_or_fileobj=temp_path,
                path_in_repo="train.json",
                repo_id=repo_id,
                repo_type="dataset"
            )
            
            os.unlink(temp_path)
            
            return f"https://huggingface.co/datasets/{repo_id}"
            
        except ImportError:
            raise ImportError("huggingface_hub required. Install with: pip install huggingface_hub")
    
    def start_training(
        self,
        model_id: str,
        training_data: List[Dict],
        config: Dict
    ) -> TrainingJob:
        """
        Start a training job on HuggingFace.
        
        Args:
            model_id: Base model to finetune
            training_data: Training samples
            config: Training configuration (epochs, lr, etc.)
            
        Returns:
            TrainingJob with job details
        """
        try:
            from huggingface_hub import HfApi
            
            job_id = f"hf_{model_id}_{int(time.time())}"
            
            # For HuggingFace AutoTrain or Spaces-based training
            # This is a simplified example - full implementation would use AutoTrain API
            
            logger.info(f"Starting HuggingFace training job: {job_id}")
            
            # Create training job
            job = TrainingJob(
                job_id=job_id,
                provider=CloudProvider.HUGGINGFACE,
                status="pending",
                model_id=model_id,
                created_at=time.time(),
                updated_at=time.time()
            )
            
            # In production, this would:
            # 1. Upload training data to HuggingFace
            # 2. Create AutoTrain project
            # 3. Start training
            
            logger.info(f"HuggingFace training job created: {job_id}")
            return job
            
        except Exception as e:
            logger.error(f"Failed to start HuggingFace training: {e}")
            raise
    
    def get_status(self, job_id: str) -> TrainingJob:
        """Get status of a training job."""
        # In production, query HuggingFace AutoTrain API
        return TrainingJob(
            job_id=job_id,
            provider=CloudProvider.HUGGINGFACE,
            status="running",
            model_id="unknown",
            created_at=time.time(),
            updated_at=time.time(),
            progress=0.5
        )
    
    def download_model(self, job_id: str, output_path: str) -> str:
        """Download trained model from HuggingFace."""
        try:
            from huggingface_hub import snapshot_download
            
            # In production, use the actual model repo from the job
            model_path = snapshot_download(
                repo_id=f"receipt-extractor/{job_id}",
                local_dir=output_path,
                token=self.token
            )
            
            return model_path
            
        except Exception as e:
            logger.error(f"Failed to download model: {e}")
            raise


class ReplicateTrainer:
    """
    Replicate trainer for cloud-based model finetuning.
    
    Uses Replicate's API to run custom training workflows.
    
    Usage:
        trainer = ReplicateTrainer(token="r8_xxxxx")
        job = trainer.start_training(model_id, training_data, config)
        status = trainer.get_status(job.job_id)
    """
    
    API_BASE = "https://api.replicate.com/v1"
    
    def __init__(self, token: str = None):
        """
        Initialize Replicate trainer.
        
        Args:
            token: Replicate API token (or set REPLICATE_API_TOKEN env var)
        """
        self.token = token or os.environ.get('REPLICATE_API_TOKEN')
        if not self.token:
            raise ValueError(
                "Replicate token required. Pass token parameter or set REPLICATE_API_TOKEN environment variable."
            )
        
        self.headers = {
            "Authorization": f"Token {self.token}",
            "Content-Type": "application/json"
        }
        logger.info("ReplicateTrainer initialized")
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make authenticated request to Replicate API."""
        import requests
        
        url = f"{self.API_BASE}/{endpoint}"
        
        if method == "GET":
            response = requests.get(url, headers=self.headers)
        elif method == "POST":
            response = requests.post(url, headers=self.headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    def start_training(
        self,
        model_id: str,
        training_data: List[Dict],
        config: Dict
    ) -> TrainingJob:
        """
        Start a training job on Replicate.
        
        Args:
            model_id: Base model version to finetune
            training_data: Training samples
            config: Training configuration
            
        Returns:
            TrainingJob with job details
        """
        try:
            # Prepare training data as base64 zip
            training_zip = self._prepare_training_data(training_data)
            
            # Start training via Replicate API
            response = self._make_request("POST", "trainings", {
                "version": model_id,
                "input": {
                    "training_data": training_zip,
                    "epochs": config.get('epochs', 3),
                    "learning_rate": config.get('learning_rate', 5e-5),
                    "batch_size": config.get('batch_size', 4)
                }
            })
            
            job_id = response.get('id', f"rep_{int(time.time())}")
            
            job = TrainingJob(
                job_id=job_id,
                provider=CloudProvider.REPLICATE,
                status=response.get('status', 'pending'),
                model_id=model_id,
                created_at=time.time(),
                updated_at=time.time()
            )
            
            logger.info(f"Replicate training job created: {job_id}")
            return job
            
        except Exception as e:
            logger.error(f"Failed to start Replicate training: {e}")
            raise
    
    def _prepare_training_data(self, training_data: List[Dict]) -> str:
        """Prepare training data as base64-encoded zip."""
        import zipfile
        import io
        
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('train.json', json.dumps(training_data))
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    def get_status(self, job_id: str) -> TrainingJob:
        """Get status of a training job."""
        try:
            response = self._make_request("GET", f"trainings/{job_id}")
            
            return TrainingJob(
                job_id=job_id,
                provider=CloudProvider.REPLICATE,
                status=response.get('status', 'unknown'),
                model_id=response.get('version', 'unknown'),
                created_at=response.get('created_at', time.time()),
                updated_at=time.time(),
                progress=self._calculate_progress(response),
                metrics=response.get('metrics'),
                output_url=response.get('output', {}).get('model')
            )
            
        except Exception as e:
            logger.error(f"Failed to get training status: {e}")
            raise
    
    def _calculate_progress(self, response: Dict) -> float:
        """Calculate progress from Replicate response."""
        status = response.get('status', '')
        if status == 'succeeded':
            return 1.0
        elif status == 'failed':
            return 0.0
        elif status == 'processing':
            logs = response.get('logs', '')
            # Parse progress from logs if available
            return 0.5
        return 0.0
    
    def download_model(self, job_id: str, output_path: str) -> str:
        """Download trained model from Replicate."""
        import requests
        
        status = self.get_status(job_id)
        if not status.output_url:
            raise ValueError("Model not ready for download")
        
        response = requests.get(status.output_url)
        response.raise_for_status()
        
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        model_file = output_dir / 'model.tar.gz'
        with open(model_file, 'wb') as f:
            f.write(response.content)
        
        return str(model_file)


class RunPodTrainer:
    """
    RunPod trainer for GPU-based model finetuning.
    
    Uses RunPod's serverless GPU infrastructure for training.
    
    Usage:
        import os
        trainer = RunPodTrainer(api_key=os.getenv('RUNPOD_API_KEY'))
        job = trainer.start_training(model_id, training_data, config)
        status = trainer.get_status(job.job_id)
    """
    
    API_BASE = "https://api.runpod.io/v2"
    
    # Default training endpoint (can be customized)
    DEFAULT_ENDPOINT = "receipt-training"
    
    def __init__(self, api_key: str = None, endpoint_id: str = None):
        """
        Initialize RunPod trainer.
        
        Args:
            api_key: RunPod API key (or set RUNPOD_API_KEY env var)
            endpoint_id: RunPod serverless endpoint ID
        """
        self.api_key = api_key or os.environ.get('RUNPOD_API_KEY')
        if not self.api_key:
            raise ValueError(
                "RunPod API key required. Pass api_key parameter or set RUNPOD_API_KEY environment variable."
            )
        
        self.endpoint_id = endpoint_id or os.environ.get('RUNPOD_ENDPOINT_ID', self.DEFAULT_ENDPOINT)
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        logger.info(f"RunPodTrainer initialized with endpoint: {self.endpoint_id}")
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make authenticated request to RunPod API."""
        import requests
        
        url = f"{self.API_BASE}/{endpoint}"
        
        if method == "GET":
            response = requests.get(url, headers=self.headers)
        elif method == "POST":
            response = requests.post(url, headers=self.headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    def start_training(
        self,
        model_id: str,
        training_data: List[Dict],
        config: Dict
    ) -> TrainingJob:
        """
        Start a training job on RunPod.
        
        Args:
            model_id: Base model to finetune
            training_data: Training samples
            config: Training configuration
            
        Returns:
            TrainingJob with job details
        """
        try:
            # Submit training job to RunPod serverless endpoint
            response = self._make_request(
                "POST",
                f"{self.endpoint_id}/run",
                {
                    "input": {
                        "model_id": model_id,
                        "training_data": training_data,
                        "epochs": config.get('epochs', 3),
                        "learning_rate": config.get('learning_rate', 5e-5),
                        "batch_size": config.get('batch_size', 4)
                    }
                }
            )
            
            job_id = response.get('id', f"rp_{int(time.time())}")
            
            job = TrainingJob(
                job_id=job_id,
                provider=CloudProvider.RUNPOD,
                status=response.get('status', 'IN_QUEUE'),
                model_id=model_id,
                created_at=time.time(),
                updated_at=time.time()
            )
            
            logger.info(f"RunPod training job created: {job_id}")
            return job
            
        except Exception as e:
            logger.error(f"Failed to start RunPod training: {e}")
            raise
    
    def get_status(self, job_id: str) -> TrainingJob:
        """Get status of a training job."""
        try:
            response = self._make_request("GET", f"{self.endpoint_id}/status/{job_id}")
            
            status_map = {
                'IN_QUEUE': 'pending',
                'IN_PROGRESS': 'running',
                'COMPLETED': 'completed',
                'FAILED': 'failed'
            }
            
            runpod_status = response.get('status', 'unknown')
            
            return TrainingJob(
                job_id=job_id,
                provider=CloudProvider.RUNPOD,
                status=status_map.get(runpod_status, runpod_status),
                model_id=response.get('input', {}).get('model_id', 'unknown'),
                created_at=time.time(),
                updated_at=time.time(),
                progress=1.0 if runpod_status == 'COMPLETED' else 0.5,
                metrics=response.get('output', {}).get('metrics'),
                output_url=response.get('output', {}).get('model_url')
            )
            
        except Exception as e:
            logger.error(f"Failed to get RunPod job status: {e}")
            raise
    
    def download_model(self, job_id: str, output_path: str) -> str:
        """Download trained model from RunPod."""
        import requests
        
        status = self.get_status(job_id)
        if not status.output_url:
            raise ValueError("Model not ready for download")
        
        response = requests.get(status.output_url)
        response.raise_for_status()
        
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        model_file = output_dir / 'model.tar.gz'
        with open(model_file, 'wb') as f:
            f.write(response.content)
        
        return str(model_file)


class CloudFinetuningService:
    """
    Unified interface for cloud-based model finetuning.
    
    Provides a consistent API across multiple cloud providers.
    
    Usage:
        service = CloudFinetuningService()
        job = service.start_training('huggingface', model_id, data, config)
        status = service.get_status('huggingface', job.job_id)
    """
    
    def __init__(
        self,
        huggingface_token: str = None,
        replicate_token: str = None,
        runpod_api_key: str = None
    ):
        """
        Initialize cloud finetuning service.
        
        Args:
            huggingface_token: HuggingFace API token
            replicate_token: Replicate API token
            runpod_api_key: RunPod API key
        """
        self.trainers = {}
        
        # Initialize available trainers
        if huggingface_token or os.environ.get('HUGGINGFACE_TOKEN'):
            try:
                self.trainers['huggingface'] = HuggingFaceTrainer(huggingface_token)
            except Exception as e:
                logger.warning(f"HuggingFace trainer not available: {e}")
        
        if replicate_token or os.environ.get('REPLICATE_API_TOKEN'):
            try:
                self.trainers['replicate'] = ReplicateTrainer(replicate_token)
            except Exception as e:
                logger.warning(f"Replicate trainer not available: {e}")
        
        if runpod_api_key or os.environ.get('RUNPOD_API_KEY'):
            try:
                self.trainers['runpod'] = RunPodTrainer(runpod_api_key)
            except Exception as e:
                logger.warning(f"RunPod trainer not available: {e}")
        
        logger.info(f"CloudFinetuningService initialized with providers: {list(self.trainers.keys())}")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available cloud providers."""
        return list(self.trainers.keys())
    
    def start_training(
        self,
        provider: str,
        model_id: str,
        training_data: List[Dict],
        config: Dict
    ) -> TrainingJob:
        """
        Start training on specified provider.
        
        Args:
            provider: Cloud provider name
            model_id: Model to finetune
            training_data: Training samples
            config: Training configuration
            
        Returns:
            TrainingJob with job details
        """
        if provider not in self.trainers:
            raise ValueError(
                f"Provider '{provider}' not available. "
                f"Available: {self.get_available_providers()}"
            )
        
        return self.trainers[provider].start_training(model_id, training_data, config)
    
    def get_status(self, provider: str, job_id: str) -> TrainingJob:
        """Get status of a training job."""
        if provider not in self.trainers:
            raise ValueError(f"Provider '{provider}' not available")
        
        return self.trainers[provider].get_status(job_id)
    
    def download_model(self, provider: str, job_id: str, output_path: str) -> str:
        """Download trained model."""
        if provider not in self.trainers:
            raise ValueError(f"Provider '{provider}' not available")
        
        return self.trainers[provider].download_model(job_id, output_path)


__all__ = [
    'CloudFinetuningService',
    'HuggingFaceTrainer',
    'ReplicateTrainer', 
    'RunPodTrainer',
    'TrainingJob',
    'CloudProvider'
]
