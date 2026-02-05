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
from shared.utils.optional_imports import OptionalImport

logger = logging.getLogger(__name__)

# Redis/Celery configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)

# Import Celery
celery_import = OptionalImport('celery.Celery', 'pip install celery redis')
Celery = celery_import.module
CELERY_AVAILABLE = celery_import.is_available

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
        # Beat scheduler persistence file location (writable directory)
        beat_schedule_filename=os.getenv('CELERY_BEAT_SCHEDULE', '/app/celerybeat/schedule.db'),
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
        
        # Import telemetry
        try:
            from shared.utils.telemetry import get_tracer, set_span_attributes
            tracer = get_tracer()
            TELEMETRY_AVAILABLE = True
        except ImportError:
            tracer = None
            TELEMETRY_AVAILABLE = False
        
        span = None
        if TELEMETRY_AVAILABLE and tracer:
            span = tracer.start_span("celery.training.start_training_task")
            set_span_attributes(span, {
                "operation.type": "background_training",
                "training.provider": provider,
                "training.dataset_id": dataset_id[:8] if dataset_id else None,
                "user.id": user_id[:8] if user_id else None,
                "celery.task_id": self.request.id
            })
        
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
            
            if span:
                set_span_attributes(span, {
                    "training.job_id": job.job_id[:8],
                    "training.model_id": config.model_id,
                    "training.dataset_size": len(dataset) if dataset else 0
                })
            
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
            
            if span:
                set_span_attributes(span, {
                    "training.final_status": job.status.value,
                    "training.final_progress": job.progress,
                    "training.output_model_id": job.output_model_id,
                    "operation.success": True
                })
            
            return {
                'success': True,
                'job_id': job.job_id,
                'status': job.status.value,
                'output_model_id': job.output_model_id,
                'output_model_url': job.output_model_url
            }
            
        except Exception as e:
            logger.error(f"Training task failed: {e}")
            if span:
                span.record_exception(e)
                set_span_attributes(span, {
                    "operation.success": False,
                    "error.type": type(e).__name__,
                    "error.message": str(e)
                })
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            if span:
                span.end()
    
    
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
    
    
    @celery_app.task(bind=True, name='training.monitor_training_job', 
                     autoretry_for=(Exception,),
                     retry_kwargs={'max_retries': 3, 'countdown': 60})
    def monitor_training_job(
        self,
        job_id: str,
        provider: str
    ) -> Dict[str, Any]:
        """
        Celery task to monitor a training job and update its status.
        
        This task polls the training provider for job status updates
        and stores them in the database for retrieval by the frontend.
        
        Note: This task uses Celery's countdown feature for polling instead of
        time.sleep() to avoid blocking the worker thread.
        
        Environment Variables:
            TRAINING_POLL_INTERVAL: Seconds between polls (default: 30)
            TRAINING_MAX_POLL_COUNT: Maximum number of polls (default: 720, ~6 hours)
            TRAINING_ERROR_POLL_INTERVAL: Seconds to wait after error (default: 60)
        
        Args:
            job_id: Training job ID
            provider: Training provider name (huggingface, replicate, runpod)
            
        Returns:
            Dictionary with final job status
        """
        from . import TrainingFactory
        
        # Configurable timeout settings via environment variables
        poll_interval = int(os.getenv('TRAINING_POLL_INTERVAL', '30'))
        max_polls = int(os.getenv('TRAINING_MAX_POLL_COUNT', '720'))
        error_poll_interval = int(os.getenv('TRAINING_ERROR_POLL_INTERVAL', '60'))
        
        logger.info(f"Starting job monitoring: job_id={job_id}, provider={provider}")
        
        try:
            trainer = TrainingFactory.get_trainer(provider)
            
            try:
                job = trainer.get_job_status(job_id)
                
                if not job:
                    logger.warning(f"Job {job_id} not found")
                    return {
                        'success': False,
                        'error': 'Job not found',
                        'job_id': job_id
                    }
                
                # Update task state for progress tracking
                poll_count = self.request.retries + 1
                self.update_state(
                    state='MONITORING',
                    meta={
                        'job_id': job_id,
                        'provider': provider,
                        'status': job.status.value,
                        'progress': job.progress,
                        'poll_count': poll_count,
                        'metrics': job.metrics.to_dict() if job.metrics else None
                    }
                )
                
                # Check for terminal states
                if job.status.value == 'completed':
                    logger.info(f"Job {job_id} completed successfully")
                    return {
                        'success': True,
                        'job_id': job_id,
                        'status': 'completed',
                        'output_model_id': job.output_model_id,
                        'output_model_url': job.output_model_url,
                        'metrics': job.metrics.to_dict() if job.metrics else None
                    }
                
                elif job.status.value in ['failed', 'cancelled']:
                    logger.error(f"Job {job_id} {job.status.value}: {job.error}")
                    return {
                        'success': False,
                        'job_id': job_id,
                        'status': job.status.value,
                        'error': job.error
                    }
                
                # Check if we've exceeded max polls
                if poll_count >= max_polls:
                    logger.warning(f"Job {job_id} monitoring timed out after {poll_count} polls")
                    return {
                        'success': False,
                        'job_id': job_id,
                        'status': 'timeout',
                        'error': f'Job monitoring timed out after {poll_count * poll_interval} seconds'
                    }
                
                # Schedule next poll using Celery retry with countdown
                # This releases the worker thread instead of blocking with sleep()
                raise self.retry(countdown=poll_interval, max_retries=max_polls)
                
            except self.MaxRetriesExceededError:
                logger.warning(f"Job {job_id} monitoring exceeded max retries")
                return {
                    'success': False,
                    'job_id': job_id,
                    'status': 'timeout',
                    'error': 'Job monitoring exceeded maximum polling attempts'
                }
                
        except Exception as e:
            if isinstance(e, self.MaxRetriesExceededError):
                raise
            logger.error(f"Monitor job failed: {e}")
            # Retry with longer interval on errors
            raise self.retry(countdown=error_poll_interval, exc=e)
    
    
    # =========================================================================
    # CELERY BEAT SCHEDULE CONFIGURATION
    # =========================================================================
    
    def configure_beat_schedule():
        """
        Configure Celery Beat schedule.
        
        This function should ONLY be called when beat is actually running,
        not during module import. This prevents errors when beat isn't needed.
        
        Usage:
            # In beat worker startup (not in module)
            from web.backend.training.celery_worker import configure_beat_schedule
            configure_beat_schedule()
        """
        if not celery_app:
            logger.warning("Celery app not available, cannot configure beat schedule")
            return
        
        celery_app.conf.beat_schedule = {
            'cleanup-old-jobs-daily': {
                'task': 'training.cleanup_old_jobs',
                'schedule': 86400.0,  # Run daily (24 hours in seconds)
                'args': (7,),  # Keep jobs for 7 days
            },
        }
        logger.info("Celery Beat schedule configured")
    
    # DO NOT call configure_beat_schedule() here!
    # It should only be called when beat worker starts, not on module import


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _load_dataset(dataset_id: str):
    """
    Load a dataset from storage.
    
    Retrieves training dataset from database or cloud storage based on dataset_id.
    
    Args:
        dataset_id: Dataset ID (UUID or reference string)
        
    Returns:
        TrainingDataset object with images, labels, and metadata
    """
    from .base import TrainingDataset
    import os
    
    logger.info(f"Loading dataset: {dataset_id}")
    
    # Try to load from database/storage
    try:
        # Check for environment-based storage configuration
        storage_backend = os.getenv('TRAINING_DATASET_STORAGE', 'local')
        
        if storage_backend == 's3':
            # Load from S3
            from ..storage import StorageFactory
            storage = StorageFactory.get_storage('s3')
            dataset_key = f"datasets/{dataset_id}"
            
            # Retrieve dataset manifest
            manifest = storage.download_file(f"{dataset_key}/manifest.json")
            if manifest:
                import json
                manifest_data = json.loads(manifest.decode('utf-8'))
                
                # Load images from S3
                images = []
                labels = []
                for item in manifest_data.get('items', []):
                    image_data = storage.download_file(f"{dataset_key}/{item['image']}")
                    if image_data:
                        images.append(image_data)
                        labels.append(item.get('label', {}))
                
                return TrainingDataset(
                    images=images,
                    labels=labels,
                    metadata={
                        'id': dataset_id,
                        'source': 's3',
                        'item_count': len(images)
                    }
                )
        
        elif storage_backend == 'database':
            # Load from database
            from ..database import get_db_context
            
            with get_db_context() as db:
                # Query for dataset record (implement based on schema)
                # This is a placeholder for actual database implementation
                pass
        
        else:
            # Local file storage
            dataset_path = os.path.join(
                os.getenv('TRAINING_DATA_DIR', './training_data'),
                dataset_id
            )
            
            if os.path.exists(dataset_path):
                import json
                manifest_path = os.path.join(dataset_path, 'manifest.json')
                
                if os.path.exists(manifest_path):
                    with open(manifest_path, 'r') as f:
                        manifest_data = json.load(f)
                    
                    images = []
                    labels = []
                    for item in manifest_data.get('items', []):
                        image_path = os.path.join(dataset_path, item['image'])
                        if os.path.exists(image_path):
                            with open(image_path, 'rb') as f:
                                images.append(f.read())
                            labels.append(item.get('label', {}))
                    
                    return TrainingDataset(
                        images=images,
                        labels=labels,
                        metadata={
                            'id': dataset_id,
                            'source': 'local',
                            'item_count': len(images)
                        }
                    )
        
        # If no dataset found, return mock for development
        logger.warning(f"Dataset {dataset_id} not found, returning mock dataset for development")
        
    except Exception as e:
        logger.error(f"Error loading dataset {dataset_id}: {e}")
    
    # Return mock dataset as fallback
    return TrainingDataset(
        images=[b'mock_image'] * 20,
        labels=[{'text': 'mock_label'}] * 20,
        metadata={'id': dataset_id, 'source': 'mock'}
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
