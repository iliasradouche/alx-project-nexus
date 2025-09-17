# 🚀 Heroku Deployment Guide for Movie Recommendation Backend

This guide will help you deploy the Django backend to Heroku in just a few steps.

## 📋 Prerequisites

Before starting, make sure you have:

- ✅ **Heroku CLI installed** - [Download here](https://devcenter.heroku.com/articles/heroku-cli)
- ✅ **Git installed** - [Download here](https://git-scm.com/downloads)
- ✅ **Heroku account** - [Sign up here](https://signup.heroku.com/)
- ✅ **Python 3.11+** installed
- ✅ **Your frontend deployed on Netlify** (we'll connect them)

## 🎯 Quick Deployment (Automated)

### For Windows Users:
```cmd
.\deploy_heroku.bat
```

### For Linux/Mac Users:
```bash
chmod +x deploy_heroku.sh
./deploy_heroku.sh
```

The script will:
1. Create a Heroku app
2. Add PostgreSQL database
3. Set environment variables
4. Deploy your code
5. Run migrations
6. Collect static files

## 🔧 Manual Deployment Steps

If you prefer to deploy manually:

### 1. Install and Login to Heroku

```bash
# Install Heroku CLI (if not installed)
# Windows: Download from https://devcenter.heroku.com/articles/heroku-cli
# Mac: brew tap heroku/brew && brew install heroku
# Linux: curl https://cli-assets.heroku.com/install.sh | sh

# Login to Heroku
heroku login
```

### 2. Create Heroku App

```bash
# Replace 'your-app-name' with your desired app name
heroku create your-movie-backend
```

### 3. Add PostgreSQL Database

```bash
heroku addons:create heroku-postgresql:essential-0 --app your-movie-backend
```

### 4. Set Environment Variables

```bash
# Generate a secret key
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Set the variables (replace values as needed)
heroku config:set DJANGO_SETTINGS_MODULE=movie_backend.production_settings --app your-movie-backend
heroku config:set SECRET_KEY="your-generated-secret-key" --app your-movie-backend
heroku config:set DEBUG=False --app your-movie-backend
heroku config:set ALLOWED_HOSTS="your-movie-backend.herokuapp.com" --app your-movie-backend
heroku config:set CORS_ALLOWED_ORIGINS="https://your-netlify-app.netlify.app,http://localhost:3000" --app your-movie-backend
```

### 5. Deploy to Heroku

```bash
# Add and commit changes
git add .
git commit -m "Deploy to Heroku"

# Push to Heroku
git push heroku main
```

### 6. Run Database Migrations

```bash
heroku run python manage.py migrate --app your-movie-backend
```

### 7. Collect Static Files

```bash
heroku run python manage.py collectstatic --noinput --app your-movie-backend
```

### 8. Create Superuser (Optional)

```bash
heroku run python manage.py createsuperuser --app your-movie-backend
```

## 🔗 Connect Frontend to Backend

After deployment, update your Netlify frontend environment variables:

1. Go to your Netlify dashboard
2. Select your frontend app
3. Go to **Site settings** → **Environment variables**
4. Update `REACT_APP_API_URL` to: `https://your-movie-backend.herokuapp.com`
5. Redeploy your frontend

## 📊 Monitoring and Management

### View Logs
```bash
heroku logs --tail --app your-movie-backend
```

### Open App in Browser
```bash
heroku open --app your-movie-backend
```

### Access Django Admin
Visit: `https://your-movie-backend.herokuapp.com/admin/`

### Heroku Dashboard
Manage your app at: `https://dashboard.heroku.com/apps/your-movie-backend`

## 🔧 Environment Variables Reference

Your Heroku app needs these environment variables:

| Variable | Description | Example |
|----------|-------------|----------|
| `DJANGO_SETTINGS_MODULE` | Django settings module | `movie_backend.production_settings` |
| `SECRET_KEY` | Django secret key | `django-insecure-xyz...` |
| `DEBUG` | Debug mode | `False` |
| `ALLOWED_HOSTS` | Allowed hosts | `your-app.herokuapp.com` |
| `DATABASE_URL` | PostgreSQL URL | *Auto-set by Heroku* |
| `CORS_ALLOWED_ORIGINS` | Frontend URLs | `https://your-app.netlify.app` |
| `TMDB_API_KEY` | TMDB API key | `your-tmdb-api-key` |

## 🚨 Troubleshooting

### Common Issues:

1. **Build fails**: Check `heroku logs --tail`
2. **Database errors**: Ensure migrations ran successfully
3. **CORS errors**: Verify `CORS_ALLOWED_ORIGINS` includes your frontend URL
4. **Static files not loading**: Run `collectstatic` command

### Useful Commands:

```bash
# Restart app
heroku restart --app your-movie-backend

# Run Django shell
heroku run python manage.py shell --app your-movie-backend

# Check config vars
heroku config --app your-movie-backend

# Scale dynos
heroku ps:scale web=1 --app your-movie-backend
```

## 🎉 Success!

Once deployed, your backend will be available at:
`https://your-movie-backend.herokuapp.com`

Your API endpoints will be:
- Movies: `https://your-movie-backend.herokuapp.com/api/movies/`
- Recommendations: `https://your-movie-backend.herokuapp.com/api/recommendations/`
- Admin: `https://your-movie-backend.herokuapp.com/admin/`

---

**Need help?** Check the [Heroku documentation](https://devcenter.heroku.com/) or the main [DEPLOYMENT.md](../DEPLOYMENT.md) file.