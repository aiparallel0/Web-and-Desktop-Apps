web: bash start_web.sh
worker: celery -A web.backend.training.celery_worker worker --loglevel=info
beat: celery -A web.backend.training.celery_worker beat --loglevel=info --schedule=/tmp/celerybeat-schedule
