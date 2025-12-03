"""
=============================================================================
TRAINING MODULE - Cloud-Based Model Training
=============================================================================

This module provides cloud-based model training capabilities for the
Receipt Extractor platform.

Components:
- base.py: Abstract base class for training handlers
- hf_trainer.py: HuggingFace Spaces trainer
- replicate_trainer.py: Replicate trainer
- runpod_trainer.py: RunPod trainer
- celery_worker.py: Background job processing

Environment Variables Required:
- HUGGINGFACE_API_KEY: HuggingFace token (for HF trainer)
- REPLICATE_API_TOKEN: Replicate token (for Replicate trainer)
- RUNPOD_API_KEY: RunPod API key (for RunPod trainer)
- REDIS_URL: Redis connection (for Celery)

=============================================================================
"""

from .base import BaseTrainer, TrainingJob, TrainingConfig, TrainingStatus
from .hf_trainer import HuggingFaceTrainer
from .replicate_trainer import ReplicateTrainer
from .runpod_trainer import RunPodTrainer

__all__ = [
    # Base
    'BaseTrainer',
    'TrainingJob',
    'TrainingConfig',
    'TrainingStatus',
    # Trainers
    'HuggingFaceTrainer',
    'ReplicateTrainer',
    'RunPodTrainer',
    # Factory
    'TrainingFactory',
    'get_trainer',
]


class TrainingFactory:
    """
    Factory for creating training handler instances.
    
    Usage:
        trainer = TrainingFactory.get_trainer('huggingface')
        job = trainer.start_training(config, dataset)
    """
    
    _trainers = {
        'huggingface': HuggingFaceTrainer,
        'hf': HuggingFaceTrainer,
        'replicate': ReplicateTrainer,
        'runpod': RunPodTrainer,
    }
    
    @classmethod
    def get_trainer(cls, provider: str, **kwargs) -> BaseTrainer:
        """
        Get a trainer for the specified provider.
        
        Args:
            provider: Training provider name ('huggingface', 'replicate', 'runpod')
            **kwargs: Additional arguments for the trainer
            
        Returns:
            Configured trainer instance
            
        Raises:
            ValueError: If provider is not supported
        """
        provider = provider.lower().strip()
        
        if provider not in cls._trainers:
            supported = list(cls._trainers.keys())
            raise ValueError(
                f"Unsupported training provider: {provider}. "
                f"Supported providers: {supported}"
            )
        
        trainer_class = cls._trainers[provider]
        return trainer_class(**kwargs)
    
    @classmethod
    def list_providers(cls) -> list:
        """Get list of supported training providers."""
        return ['huggingface', 'replicate', 'runpod']
    
    @classmethod
    def is_provider_available(cls, provider: str) -> bool:
        """Check if a provider is available and configured."""
        try:
            trainer = cls.get_trainer(provider)
            return trainer.is_configured()
        except (ValueError, ImportError):
            return False
    
    @classmethod
    def get_provider_info(cls, provider: str) -> dict:
        """Get information about a training provider."""
        info = {
            'huggingface': {
                'name': 'HuggingFace Spaces',
                'description': 'Train models using HuggingFace infrastructure',
                'pricing': 'Free tier available, ~$0.60/hour for A10G GPU',
                'gpu_types': ['T4', 'A10G', 'A100'],
                'docs_url': 'https://huggingface.co/docs/hub/spaces'
            },
            'replicate': {
                'name': 'Replicate',
                'description': 'Train and deploy models with Replicate',
                'pricing': '~$0.80/hour for training',
                'gpu_types': ['T4', 'A40', 'A100'],
                'docs_url': 'https://replicate.com/docs/reference/http#trainings.create'
            },
            'runpod': {
                'name': 'RunPod',
                'description': 'Serverless GPU training with RunPod',
                'pricing': '~$0.50-$2.00/hour depending on GPU',
                'gpu_types': ['A4000', 'A6000', 'A100', 'H100'],
                'docs_url': 'https://docs.runpod.io/serverless/overview'
            }
        }
        return info.get(provider, {})


def get_trainer(provider: str = 'huggingface', **kwargs) -> BaseTrainer:
    """
    Convenience function to get a trainer.
    
    Args:
        provider: Training provider name
        **kwargs: Additional arguments
        
    Returns:
        Configured trainer
    """
    return TrainingFactory.get_trainer(provider, **kwargs)
