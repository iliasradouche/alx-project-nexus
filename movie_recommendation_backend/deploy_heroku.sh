#!/bin/bash

# Heroku Deployment Script for Movie Recommendation Backend
# Make sure you have Heroku CLI installed and are logged in

echo "🚀 Starting Heroku deployment for Movie Recommendation Backend..."

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI is not installed. Please install it first."
    echo "Visit: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Check if user is logged in to Heroku
if ! heroku auth:whoami &> /dev/null; then
    echo "❌ Please login to Heroku first: heroku login"
    exit 1
fi

# Get app name from user
read -p "Enter your Heroku app name (e.g., my-movie-backend): " APP_NAME

if [ -z "$APP_NAME" ]; then
    echo "❌ App name cannot be empty"
    exit 1
fi

echo "📦 Creating Heroku app: $APP_NAME"
heroku create $APP_NAME

echo "🗄️ Adding PostgreSQL database..."
heroku addons:create heroku-postgresql:essential-0 --app $APP_NAME

echo "🔧 Setting environment variables..."
# Generate a secret key
SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

heroku config:set DJANGO_SETTINGS_MODULE=movie_backend.production_settings --app $APP_NAME
heroku config:set SECRET_KEY="$SECRET_KEY" --app $APP_NAME
heroku config:set DEBUG=False --app $APP_NAME
heroku config:set ALLOWED_HOSTS="$APP_NAME.herokuapp.com" --app $APP_NAME

# Get frontend URL from user
read -p "Enter your Netlify frontend URL (e.g., https://my-app.netlify.app): " FRONTEND_URL

if [ ! -z "$FRONTEND_URL" ]; then
    heroku config:set CORS_ALLOWED_ORIGINS="$FRONTEND_URL,http://localhost:3000" --app $APP_NAME
fi

echo "📤 Deploying to Heroku..."
git add .
git commit -m "Deploy to Heroku: $APP_NAME" || echo "No changes to commit"
git push heroku main

echo "🔄 Running database migrations..."
heroku run python manage.py migrate --app $APP_NAME

echo "📁 Collecting static files..."
heroku run python manage.py collectstatic --noinput --app $APP_NAME

echo "✅ Deployment completed!"
echo "🌐 Your backend is available at: https://$APP_NAME.herokuapp.com"
echo "📊 View logs: heroku logs --tail --app $APP_NAME"
echo "⚙️ Manage app: https://dashboard.heroku.com/apps/$APP_NAME"

# Optional: Create superuser
read -p "Do you want to create a Django superuser? (y/n): " CREATE_SUPERUSER
if [ "$CREATE_SUPERUSER" = "y" ] || [ "$CREATE_SUPERUSER" = "Y" ]; then
    heroku run python manage.py createsuperuser --app $APP_NAME
fi

echo "🎉 Deployment script completed!"