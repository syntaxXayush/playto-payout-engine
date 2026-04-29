#!/bin/bash
# Apply database migrations
python manage.py migrate

# Seed the merchants
python manage.py seed_merchants

# Start the Celery worker in the background
celery -A config worker --loglevel=info --concurrency=2 &

# Start the Celery beat scheduler in the background
celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler &

# Start the Django API server
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
