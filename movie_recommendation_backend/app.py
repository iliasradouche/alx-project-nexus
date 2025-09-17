# This file helps Railpack detect this as a Python application
# The actual Django application is managed through manage.py and wsgi.py

if __name__ == "__main__":
    import os
    import sys
    
    # Add the current directory to Python path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_backend.production_settings')
    
    # Import Django and start the application
    import django
    django.setup()
    
    print("Django Movie Recommendation Backend - Ready for deployment")