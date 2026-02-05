web: gunicorn -w 4 -b 0.0.0.0:${PORT:-8000} web.backend.app:app --timeout 120 --keep-alive 5 --log-level info
worker: celery -A web.backend.training.celery_worker worker --loglevel=info
beat: python -c "from web.backend.training.celery_worker import configure_beat_schedule; configure_beat_schedule()" && celery -A web.backend.training.celery_worker beat --loglevel=info
