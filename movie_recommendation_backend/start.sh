#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Start the Django application with Gunicorn
gunicorn movie_backend.wsgi:application --bind 0.0.0.0:$PORT