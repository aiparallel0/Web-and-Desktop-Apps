"""
=============================================================================
CELERY WORKER - Background Job Processing
=============================================================================

Provides background job processing for training tasks using Celery.

Environment Variables:
- REDIS_URL: Redis connection URL (default: redis://localhost:6379/0)
- CELERY_BROKER_URL: Celery broker URL (defaults to REDIS_URL)
- CELERY_RESULT_BACKEND: Result backend URL (defaults to REDIS_URL)

Usage:
    # Start worker:
    celery -A web.backend.training.celery_worker worker --loglevel=info
    
    # Submit task:
    from training.celery_worker import start_training_task
    result = start_training_task.delay(config_dict, dataset_id, provider)

=============================================================================
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# Redis/Celery configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)

# Try to import Celery
try:
    from celery import Celery
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("Celery not installed. Run: pip install celery redis")

# Initialize Celery app (if available)
if CELERY_AVAILABLE:
    celery_app = Celery(
        'training_worker',
        broker=CELERY_BROKER_URL,
        backend=CELERY_RESULT_BACKEND
    )
    
    # Celery configuration
    celery_app.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=86400,  # 24 hours max
        task_soft_time_limit=82800,  # 23 hours soft limit
        worker_prefetch_multiplier=1,  # One task at a time per worker
        task_acks_late=True,  # Acknowledge after completion
        task_reject_on_worker_lost=True,
    )
else:
    celery_app = None


# =============================================================================
# CELERY TASKS
# =============================================================================

if CELERY_AVAILABLE:
    
    @celery_app.task(bind=True, name='training.start_training')
    def start_training_task(
        self,
        config_dict: Dict[str, Any],
        dataset_id: str,
        provider: str = 'huggingface',
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Celery task to start a training job.
        
        Args:
            config_dict: Training configuration as dictionary
            dataset_id: ID of the uploaded dataset
            provider: Training provider name
            user_id: Optional user ID
            
        Returns:
            Dictionary with job information
        """
        from .base import TrainingConfig, TrainingDataset
        from . import TrainingFactory
        
        logger.info(f"Starting training task: provider={provider}, dataset={dataset_id}")
        
        try:
            # Create config from dictionary
            config = TrainingConfig.from_dict(config_dict)
            
            # Load dataset (in real implementation, fetch from storage)
            dataset = _load_dataset(dataset_id)
            
            # Get trainer
            trainer = TrainingFactory.get_trainer(provider)
            
            # Start training
            job = trainer.start_training(config, dataset, user_id)
            
            # Update task state
            self.update_state(
                state='TRAINING',
                meta={
                    'job_id': job.job_id,
                    'status': job.status.value,
                    'progress': job.progress
                }
            )
            
            # Monitor training progress
            while job.status.value in ['pending', 'queued', 'preparing', 'training']:
                job = trainer.get_job_status(job.job_id)
                
                self.update_state(
                    state='TRAINING',
                    meta={
                        'job_id': job.job_id,
                        'status': job.status.value,
                        'progress': job.progress,
                        'metrics': job.metrics.to_dict() if job.metrics else None
                    }
                )
                
                if job.status.value == 'completed':
                    break
                elif job.status.value in ['failed', 'cancelled']:
                    raise Exception(f"Training {job.status.value}: {job.error}")
                
                # Wait before next check
                import time
                time.sleep(30)
            
            return {
                'success': True,
                'job_id': job.job_id,
                'status': job.status.value,
                'output_model_id': job.output_model_id,
                'output_model_url': job.output_model_url
            }
            
        except Exception as e:
            logger.error(f"Training task failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    
    @celery_app.task(name='training.check_job_status')
    def check_job_status_task(
        job_id: str,
        provider: str
    ) -> Dict[str, Any]:
        """
        Celery task to check training job status.
        
        Args:
            job_id: Training job ID
            provider: Training provider name
            
        Returns:
            Dictionary with job status
        """
        from . import TrainingFactory
        
        try:
            trainer = TrainingFactory.get_trainer(provider)
            job = trainer.get_job_status(job_id)
            
            if not job:
                return {
                    'success': False,
                    'error': 'Job not found'
                }
            
            return {
                'success': True,
                'job': job.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    
    @celery_app.task(name='training.cancel_job')
    def cancel_job_task(
        job_id: str,
        provider: str
    ) -> Dict[str, Any]:
        """
        Celery task to cancel a training job.
        
        Args:
            job_id: Training job ID
            provider: Training provider name
            
        Returns:
            Dictionary with cancellation result
        """
        from . import TrainingFactory
        
        try:
            trainer = TrainingFactory.get_trainer(provider)
            success = trainer.cancel_job(job_id)
            
            return {
                'success': success,
                'job_id': job_id
            }
            
        except Exception as e:
            logger.error(f"Cancel job failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    
    @celery_app.task(name='training.cleanup_old_jobs')
    def cleanup_old_jobs_task(max_age_days: int = 7) -> Dict[str, Any]:
        """
        Celery task to clean up old training jobs.
        
        Args:
            max_age_days: Maximum age of jobs to keep
            
        Returns:
            Dictionary with cleanup results
        """
        from datetime import timedelta
        from . import TrainingFactory
        
        cutoff = datetime.utcnow() - timedelta(days=max_age_days)
        cleaned = 0
        
        for provider_name in TrainingFactory.list_providers():
            try:
                trainer = TrainingFactory.get_trainer(provider_name)
                
                for job in trainer.list_jobs():
                    if job.completed_at and job.completed_at < cutoff:
                        # In real implementation, clean up resources
                        cleaned += 1
                        
            except Exception as e:
                logger.error(f"Cleanup error for {provider_name}: {e}")
        
        return {
            'success': True,
            'cleaned_jobs': cleaned
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _load_dataset(dataset_id: str):
    """
    Load a dataset from storage.
    
    Args:
        dataset_id: Dataset ID
        
    Returns:
        TrainingDataset object
    """
    from .base import TrainingDataset
    
    # In real implementation, load from database/storage
    # For now, return a mock dataset
    return TrainingDataset(
        images=[b'mock_image'] * 20,
        labels=[{'text': 'mock_label'}] * 20,
        metadata={'id': dataset_id}
    )


def get_celery_app():
    """Get the Celery application instance."""
    return celery_app


def is_celery_available() -> bool:
    """Check if Celery is available and configured."""
    return CELERY_AVAILABLE and celery_app is not None


# =============================================================================
# SYNCHRONOUS WRAPPERS
# =============================================================================

class TrainingTaskManager:
    """
    Manager for training tasks.
    
    Provides both synchronous and asynchronous interfaces.
    """
    
    @staticmethod
    def submit_training(
        config_dict: Dict[str, Any],
        dataset_id: str,
        provider: str = 'huggingface',
        user_id: str = None,
        async_mode: bool = True
    ) -> Dict[str, Any]:
        """
        Submit a training job.
        
        Args:
            config_dict: Training configuration
            dataset_id: Dataset ID
            provider: Training provider
            user_id: User ID
            async_mode: If True, run asynchronously with Celery
            
        Returns:
            Dictionary with task/job information
        """
        if async_mode and is_celery_available():
            # Submit to Celery
            task = start_training_task.delay(
                config_dict, dataset_id, provider, user_id
            )
            return {
                'success': True,
                'task_id': task.id,
                'status': 'submitted'
            }
        else:
            # Run synchronously
            from .base import TrainingConfig, TrainingDataset
            from . import TrainingFactory
            
            config = TrainingConfig.from_dict(config_dict)
            dataset = _load_dataset(dataset_id)
            trainer = TrainingFactory.get_trainer(provider)
            job = trainer.start_training(config, dataset, user_id)
            
            return {
                'success': True,
                'job_id': job.job_id,
                'status': job.status.value
            }
    
    @staticmethod
    def get_task_status(task_id: str) -> Dict[str, Any]:
        """
        Get status of a Celery task.
        
        Args:
            task_id: Celery task ID
            
        Returns:
            Dictionary with task status
        """
        if not is_celery_available():
            return {'success': False, 'error': 'Celery not available'}
        
        from celery.result import AsyncResult
        
        result = AsyncResult(task_id, app=celery_app)
        
        return {
            'success': True,
            'task_id': task_id,
            'state': result.state,
            'info': result.info if result.info else {}
        }
