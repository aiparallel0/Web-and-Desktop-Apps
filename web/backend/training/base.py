"""
=============================================================================
BASE TRAINER - Abstract Base Class for Cloud Training
=============================================================================

Defines the interface for all cloud training handlers.

Usage:
    from training.base import BaseTrainer, TrainingConfig
    
    class MyTrainer(BaseTrainer):
        def start_training(self, config, dataset):
            # Implementation
            pass

=============================================================================
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class TrainingStatus(Enum):
    """Training job status."""
    PENDING = 'pending'
    QUEUED = 'queued'
    PREPARING = 'preparing'
    TRAINING = 'training'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class TrainingProvider(Enum):
    """Supported training providers."""
    HUGGINGFACE = 'huggingface'
    REPLICATE = 'replicate'
    RUNPOD = 'runpod'
    LOCAL = 'local'


@dataclass
class TrainingConfig:
    """Configuration for a training job."""
    model_id: str = 'default_model'
    epochs: int = 3
    batch_size: int = 4
    learning_rate: float = 5e-5
    warmup_steps: int = 100
    weight_decay: float = 0.01
    max_steps: int = -1  # -1 means use epochs
    gradient_accumulation_steps: int = 1
    fp16: bool = True
    output_dir: str = 'output'
    save_steps: int = 500
    eval_steps: int = 500
    logging_steps: int = 100
    extra_params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'model_id': self.model_id,
            'epochs': self.epochs,
            'batch_size': self.batch_size,
            'learning_rate': self.learning_rate,
            'warmup_steps': self.warmup_steps,
            'weight_decay': self.weight_decay,
            'max_steps': self.max_steps,
            'gradient_accumulation_steps': self.gradient_accumulation_steps,
            'fp16': self.fp16,
            'output_dir': self.output_dir,
            'save_steps': self.save_steps,
            'eval_steps': self.eval_steps,
            'logging_steps': self.logging_steps,
            **self.extra_params
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrainingConfig':
        """Create from dictionary."""
        known_fields = {
            'model_id', 'epochs', 'batch_size', 'learning_rate',
            'warmup_steps', 'weight_decay', 'max_steps',
            'gradient_accumulation_steps', 'fp16', 'output_dir',
            'save_steps', 'eval_steps', 'logging_steps'
        }
        
        base_params = {k: v for k, v in data.items() if k in known_fields}
        extra_params = {k: v for k, v in data.items() if k not in known_fields}
        
        return cls(**base_params, extra_params=extra_params)


@dataclass
class TrainingMetrics:
    """Metrics from training."""
    loss: float = 0.0
    learning_rate: float = 0.0
    epoch: float = 0.0
    step: int = 0
    eval_loss: Optional[float] = None
    accuracy: Optional[float] = None
    extra_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'loss': self.loss,
            'learning_rate': self.learning_rate,
            'epoch': self.epoch,
            'step': self.step,
            'eval_loss': self.eval_loss,
            'accuracy': self.accuracy,
            **self.extra_metrics
        }


@dataclass
class TrainingJob:
    """Represents a training job."""
    job_id: str
    provider: TrainingProvider
    model_id: str
    status: TrainingStatus = TrainingStatus.PENDING
    progress: float = 0.0
    config: Optional[TrainingConfig] = None
    metrics: Optional[TrainingMetrics] = None
    logs: List[str] = field(default_factory=list)
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output_model_url: Optional[str] = None
    output_model_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'job_id': self.job_id,
            'provider': self.provider.value,
            'model_id': self.model_id,
            'status': self.status.value,
            'progress': self.progress,
            'config': self.config.to_dict() if self.config else None,
            'metrics': self.metrics.to_dict() if self.metrics else None,
            'logs': self.logs[-100:],  # Last 100 log lines
            'error': self.error,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'output_model_url': self.output_model_url,
            'output_model_id': self.output_model_id,
            'user_id': self.user_id,
            'metadata': self.metadata
        }
    
    def add_log(self, message: str) -> None:
        """Add a log message."""
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        self.logs.append(f"[{timestamp}] {message}")
    
    def update_status(self, status: TrainingStatus) -> None:
        """Update job status with timestamps."""
        self.status = status

        if status == TrainingStatus.TRAINING and not self.started_at:
            self.started_at = datetime.now(timezone.utc)
        elif status in [TrainingStatus.COMPLETED, TrainingStatus.FAILED, TrainingStatus.CANCELLED]:
            self.completed_at = datetime.now(timezone.utc)


@dataclass
class TrainingDataset:
    """Represents a training dataset."""
    images: List[bytes]
    labels: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None
    
    def __len__(self) -> int:
        return len(self.images)
    
    def validate(self) -> bool:
        """Validate dataset."""
        if len(self.images) != len(self.labels):
            return False
        if len(self.images) < 10:  # Minimum dataset size
            return False
        return True


class TrainingError(Exception):
    """Base exception for training operations."""
    pass


class TrainingConfigError(TrainingError):
    """Error in training configuration."""
    pass


class TrainingStartError(TrainingError):
    """Error starting training."""
    pass


class BaseTrainer(ABC):
    """
    Abstract base class for cloud training handlers.
    
    All training implementations must inherit from this class and
    implement the abstract methods.
    """
    
    provider: TrainingProvider = TrainingProvider.LOCAL
    
    def __init__(self):
        """Initialize the trainer."""
        self._configured = False
        self._jobs: Dict[str, TrainingJob] = {}
        self._callbacks: Dict[str, List[Callable]] = {}
        self._initialize()
    
    @abstractmethod
    def _initialize(self) -> None:
        """
        Initialize the trainer with credentials.
        
        Should set self._configured = True if successful.
        """
        pass
    
    def is_configured(self) -> bool:
        """Check if the trainer is properly configured."""
        return self._configured
    
    @abstractmethod
    def start_training(
        self,
        config: TrainingConfig,
        dataset: TrainingDataset,
        user_id: str = None
    ) -> TrainingJob:
        """
        Start a training job.
        
        Args:
            config: Training configuration
            dataset: Training dataset
            user_id: Optional user ID
            
        Returns:
            TrainingJob with job ID and initial status
        """
        pass
    
    @abstractmethod
    def get_job_status(self, job_id: str) -> Optional[TrainingJob]:
        """
        Get the status of a training job.
        
        Args:
            job_id: Training job ID
            
        Returns:
            TrainingJob with current status
        """
        pass
    
    @abstractmethod
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a training job.
        
        Args:
            job_id: Training job ID
            
        Returns:
            True if cancelled successfully
        """
        pass
    
    @abstractmethod
    def get_job_logs(self, job_id: str, tail: int = 100) -> List[str]:
        """
        Get logs from a training job.
        
        Args:
            job_id: Training job ID
            tail: Number of log lines to return
            
        Returns:
            List of log lines
        """
        pass
    
    @abstractmethod
    def download_model(self, job_id: str) -> Optional[bytes]:
        """
        Download the trained model.
        
        Args:
            job_id: Training job ID
            
        Returns:
            Model weights as bytes
        """
        pass
    
    def generate_job_id(self) -> str:
        """Generate a unique job ID."""
        return f"train_{uuid.uuid4().hex[:12]}"
    
    def validate_config(self, config: TrainingConfig) -> bool:
        """
        Validate training configuration.
        
        Args:
            config: Training configuration
            
        Returns:
            True if valid
            
        Raises:
            TrainingConfigError: If configuration is invalid
        """
        if not config.model_id:
            raise TrainingConfigError("model_id is required")
        
        if config.epochs < 1:
            raise TrainingConfigError("epochs must be at least 1")
        
        if config.batch_size < 1:
            raise TrainingConfigError("batch_size must be at least 1")
        
        if config.learning_rate <= 0:
            raise TrainingConfigError("learning_rate must be positive")
        
        return True
    
    def validate_dataset(self, dataset: TrainingDataset) -> bool:
        """
        Validate training dataset.
        
        Args:
            dataset: Training dataset
            
        Returns:
            True if valid
            
        Raises:
            TrainingConfigError: If dataset is invalid
        """
        if not dataset.validate():
            raise TrainingConfigError(
                "Invalid dataset: must have at least 10 samples with matching labels"
            )
        
        return True
    
    def list_jobs(self, user_id: str = None) -> List[TrainingJob]:
        """
        List all training jobs.
        
        Args:
            user_id: Filter by user ID
            
        Returns:
            List of TrainingJob objects
        """
        jobs = list(self._jobs.values())
        
        if user_id:
            jobs = [j for j in jobs if j.user_id == user_id]
        
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)
    
    def register_callback(
        self,
        event: str,
        callback: Callable[[TrainingJob], None]
    ) -> None:
        """
        Register a callback for training events.
        
        Args:
            event: Event name ('started', 'progress', 'completed', 'failed')
            callback: Callback function
        """
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)
    
    def _emit_event(self, event: str, job: TrainingJob) -> None:
        """Emit an event to registered callbacks."""
        for callback in self._callbacks.get(event, []):
            try:
                callback(job)
            except Exception as e:
                logger.error(f"Callback error for {event}: {e}")
    
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
        # Default implementation - override in subclasses
        return {
            'estimated_time_hours': 1.0,
            'estimated_cost_usd': 0.0,
            'currency': 'USD',
            'note': 'Cost estimation not available for this provider'
        }
