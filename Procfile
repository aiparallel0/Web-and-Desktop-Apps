web: gunicorn -w 4 -b 0.0.0.0:${PORT:-8000} web.backend.app:app --timeout 120 --keep-alive 5 --log-level info
worker: celery -A web.backend.training.celery_worker worker --loglevel=info
beat: celery -A web.backend.training.celery_worker beat --loglevel=info --schedule=/tmp/celerybeat-schedule
