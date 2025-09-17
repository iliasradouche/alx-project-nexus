#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Populate database with movie data if empty
python manage.py shell -c "from movies.models import Movie; import sys; sys.exit(0 if Movie.objects.count() > 0 else 1)" || python manage.py populate_movies --pages 3

# Start the Django application with Gunicorn
gunicorn movie_backend.wsgi:application --bind 0.0.0.0:$PORT