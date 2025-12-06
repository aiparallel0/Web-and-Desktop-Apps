"""
=============================================================================
HUGGINGFACE TRAINER - HuggingFace Spaces Training Integration
=============================================================================

Provides training integration using HuggingFace infrastructure.

Environment Variables:
- HUGGINGFACE_API_KEY: HuggingFace API token

Usage:
    from training.hf_trainer import HuggingFaceTrainer
    
    trainer = HuggingFaceTrainer()
    job = trainer.start_training(config, dataset)
    status = trainer.get_job_status(job.job_id)

=============================================================================
"""

import os
import logging
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

from .base import (
    BaseTrainer, TrainingJob, TrainingConfig, TrainingDataset,
    TrainingStatus, TrainingProvider, TrainingMetrics,
    TrainingError, TrainingStartError
)
from shared.utils.optional_imports import OptionalImport

logger = logging.getLogger(__name__)

# Import HuggingFace libraries
_hf_imports = OptionalImport.try_imports({
    'HfApi': 'huggingface_hub.HfApi',
    'HfFolder': 'huggingface_hub.HfFolder',
    'create_repo': 'huggingface_hub.create_repo',
    'upload_file': 'huggingface_hub.upload_file',
    'upload_folder': 'huggingface_hub.upload_folder'
}, install_msg='pip install huggingface-hub>=0.20.0')

HfApi = _hf_imports['HfApi']
HfFolder = _hf_imports['HfFolder']
create_repo = _hf_imports['create_repo']
upload_file = _hf_imports['upload_file']
upload_folder = _hf_imports['upload_folder']
HF_AVAILABLE = _hf_imports['HF_AVAILABLE']


class HuggingFaceTrainer(BaseTrainer):
    """
    HuggingFace Spaces trainer.
    
    Uses HuggingFace infrastructure for model training.
    """
    
    provider = TrainingProvider.HUGGINGFACE
    
    # Default training script template
    TRAINING_SCRIPT = '''
import os
import json
from datasets import Dataset
from transformers import (
    AutoModelForVision2Seq, AutoProcessor,
    Seq2SeqTrainingArguments, Seq2SeqTrainer
)

# Load configuration
config = json.loads(os.environ.get('TRAINING_CONFIG', '{}'))

# Load dataset
dataset = Dataset.from_json('dataset.json')

# Load model and processor
model = AutoModelForVision2Seq.from_pretrained(config['model_id'])
processor = AutoProcessor.from_pretrained(config['model_id'])

# Training arguments
training_args = Seq2SeqTrainingArguments(
    output_dir=config.get('output_dir', './output'),
    num_train_epochs=config.get('epochs', 3),
    per_device_train_batch_size=config.get('batch_size', 4),
    learning_rate=config.get('learning_rate', 5e-5),
    warmup_steps=config.get('warmup_steps', 100),
    weight_decay=config.get('weight_decay', 0.01),
    logging_steps=config.get('logging_steps', 100),
    save_steps=config.get('save_steps', 500),
    eval_steps=config.get('eval_steps', 500),
    fp16=config.get('fp16', True),
)

# Initialize trainer
trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
)

# Train
trainer.train()

# Save model
trainer.save_model('./output/final_model')
'''
    
    def __init__(self, api_key: str = None):
        """
        Initialize HuggingFace trainer.
        
        Args:
            api_key: HuggingFace API token
        """
        self.api_key = api_key
        self._api = None
        super().__init__()
    
    def _initialize(self) -> None:
        """Initialize HuggingFace API client."""
        if not HF_AVAILABLE:
            logger.error("HuggingFace Hub not available")
            return
        
        self.api_key = self.api_key or os.getenv('HUGGINGFACE_API_KEY') or os.getenv('HUGGINGFACE_TOKEN')
        
        if not self.api_key:
            logger.warning("HUGGINGFACE_API_KEY not configured")
            return
        
        try:
            self._api = HfApi(token=self.api_key)
            # Verify token works
            self._api.whoami()
            self._configured = True
            logger.info("HuggingFace trainer initialized")
        except Exception as e:
            logger.error(f"HuggingFace initialization error: {e}")
    
    def start_training(
        self,
        config: TrainingConfig,
        dataset: TrainingDataset,
        user_id: str = None
    ) -> TrainingJob:
        """
        Start a training job on HuggingFace.
        
        Args:
            config: Training configuration
            dataset: Training dataset
            user_id: Optional user ID
            
        Returns:
            TrainingJob with job ID and initial status
        """
        if not self._configured:
            raise TrainingStartError("HuggingFace trainer not configured")
        
        # Validate inputs
        self.validate_config(config)
        self.validate_dataset(dataset)
        
        # Generate job ID
        job_id = self.generate_job_id()
        
        # Create job
        job = TrainingJob(
            job_id=job_id,
            provider=self.provider,
            model_id=config.model_id,
            config=config,
            user_id=user_id,
            status=TrainingStatus.PREPARING
        )
        
        job.add_log(f"Starting training job: {job_id}")
        job.add_log(f"Model: {config.model_id}")
        job.add_log(f"Dataset size: {len(dataset)} samples")
        
        try:
            # Create a private Space for training
            space_id = self._create_training_space(job, config, dataset)
            
            job.metadata['space_id'] = space_id
            job.update_status(TrainingStatus.QUEUED)
            job.add_log(f"Created training Space: {space_id}")
            
            # Store job
            self._jobs[job_id] = job
            
            # Emit event
            self._emit_event('started', job)
            
            return job
            
        except Exception as e:
            job.update_status(TrainingStatus.FAILED)
            job.error = str(e)
            job.add_log(f"ERROR: {e}")
            self._jobs[job_id] = job
            raise TrainingStartError(f"Failed to start training: {e}")
    
    def _create_training_space(
        self,
        job: TrainingJob,
        config: TrainingConfig,
        dataset: TrainingDataset
    ) -> str:
        """Create a HuggingFace Space for training."""
        # Get username
        user_info = self._api.whoami()
        username = user_info['name']
        
        # Create space name
        space_name = f"{username}/receipt-training-{job.job_id}"
        
        # Create repository
        try:
            create_repo(
                repo_id=space_name,
                repo_type='space',
                space_sdk='docker',
                private=True,
                token=self.api_key
            )
        except Exception as e:
            if 'already exists' not in str(e).lower():
                raise
        
        # Upload training files (in real implementation)
        # For now, we'll simulate the process
        job.add_log("Uploading training files...")
        
        return space_name
    
    def get_job_status(self, job_id: str) -> Optional[TrainingJob]:
        """
        Get the status of a training job.
        
        Args:
            job_id: Training job ID
            
        Returns:
            TrainingJob with current status
        """
        job = self._jobs.get(job_id)
        if not job:
            return None
        
        # In real implementation, poll HuggingFace API for status
        # For now, simulate progress
        if job.status == TrainingStatus.QUEUED:
            job.update_status(TrainingStatus.TRAINING)
            job.add_log("Training started")
        elif job.status == TrainingStatus.TRAINING:
            # Simulate progress
            job.progress = min(job.progress + 10, 100)
            job.metrics = TrainingMetrics(
                loss=1.0 - (job.progress / 100) * 0.8,
                epoch=job.progress / 100 * job.config.epochs,
                step=int(job.progress * 10)
            )
            
            if job.progress >= 100:
                job.update_status(TrainingStatus.COMPLETED)
                job.add_log("Training completed successfully")
                self._emit_event('completed', job)
        
        return job
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a training job.
        
        Args:
            job_id: Training job ID
            
        Returns:
            True if cancelled successfully
        """
        job = self._jobs.get(job_id)
        if not job:
            return False
        
        if job.status in [TrainingStatus.COMPLETED, TrainingStatus.FAILED, TrainingStatus.CANCELLED]:
            return False
        
        try:
            # In real implementation, delete the Space
            space_id = job.metadata.get('space_id')
            if space_id:
                self._api.delete_repo(
                    repo_id=space_id,
                    repo_type='space',
                    token=self.api_key
                )
            
            job.update_status(TrainingStatus.CANCELLED)
            job.add_log("Training cancelled by user")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel job: {e}")
            return False
    
    def get_job_logs(self, job_id: str, tail: int = 100) -> List[str]:
        """
        Get logs from a training job.
        
        Args:
            job_id: Training job ID
            tail: Number of log lines to return
            
        Returns:
            List of log lines
        """
        job = self._jobs.get(job_id)
        if not job:
            return []
        
        return job.logs[-tail:]
    
    def download_model(self, job_id: str) -> Optional[bytes]:
        """
        Download the trained model.
        
        Args:
            job_id: Training job ID
            
        Returns:
            Model weights as bytes (or None)
        """
        job = self._jobs.get(job_id)
        if not job or job.status != TrainingStatus.COMPLETED:
            return None
        
        # In real implementation, download from HuggingFace
        logger.info(f"Downloading model for job: {job_id}")
        return None
    
    def estimate_cost(
        self,
        config: TrainingConfig,
        dataset_size: int
    ) -> Dict[str, Any]:
        """
        Estimate training cost.
        
        Args:
            config: Training configuration
            dataset_size: Number of training samples
            
        Returns:
            Dictionary with cost estimate
        """
        # Estimate based on HuggingFace pricing
        # A10G: ~$0.60/hour
        
        # Rough estimate: 1 hour per 1000 samples per epoch
        estimated_hours = (dataset_size / 1000) * config.epochs
        estimated_hours = max(0.5, min(estimated_hours, 24))  # Between 0.5 and 24 hours
        
        return {
            'provider': 'HuggingFace Spaces',
            'gpu_type': 'A10G',
            'estimated_time_hours': estimated_hours,
            'estimated_cost_usd': estimated_hours * 0.60,
            'currency': 'USD',
            'pricing_note': 'Free tier available for limited usage'
        }
