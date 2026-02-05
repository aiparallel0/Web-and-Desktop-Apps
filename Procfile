web: bash start_web.sh
worker: celery -A web.backend.training.celery_worker worker --loglevel=info
beat: python -c "from web.backend.training.celery_worker import configure_beat_schedule; configure_beat_schedule()" && celery -A web.backend.training.celery_worker beat --loglevel=info
