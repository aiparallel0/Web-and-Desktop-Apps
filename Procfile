web: bash start_web.sh
worker: celery -A shared.services.background_tasks worker --loglevel=info
beat: python -c "from shared.services.background_tasks import configure_beat_schedule; configure_beat_schedule()" && celery -A shared.services.background_tasks beat --loglevel=info
