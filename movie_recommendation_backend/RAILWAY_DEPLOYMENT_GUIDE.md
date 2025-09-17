# Railway Deployment Guide - Movie Recommendation Backend

## Overview
This guide will walk you through deploying your Django movie recommendation backend to Railway, which offers a generous free tier without requiring credit card verification.

## Prerequisites
- GitHub account with your code pushed to a repository
- Railway account (sign up at [railway.app](https://railway.app))
- Your Django project ready for deployment

## Step 1: Prepare Your Project

### 1.1 Verify Required Files
Ensure these files exist in your project root:

✅ `requirements.txt` (already exists)
✅ `Procfile` (already created)
✅ `production_settings.py` (already configured)

### 1.2 Create Railway-specific Files

**Create `railway.json` (optional but recommended):**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn movie_backend.wsgi:application --bind 0.0.0.0:$PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

## Step 2: Deploy on Railway

### 2.1 Create New Project
1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your movie recommendation backend repository
5. Click "Deploy Now"

### 2.2 Configure Environment Variables
After deployment starts, go to your project settings and add these variables:

**Required Environment Variables:**
```
DJANGO_SETTINGS_MODULE=movie_backend.production_settings
SECRET_KEY=your-django-secret-key-here
DEBUG=False
PORT=8000
RAILWAY_ENVIRONMENT=production
```

**Optional Environment Variables:**
```
FRONTEND_URL=https://project-nexus-alx.netlify.app
DATABASE_URL=postgresql://user:pass@host:port/dbname
REDIS_URL=redis://user:pass@host:port
```

### 2.3 Database Setup Options

#### Option A: Railway PostgreSQL (Recommended)
1. In your Railway project dashboard
2. Click "New" → "Database" → "Add PostgreSQL"
3. Railway will automatically create a `DATABASE_URL` environment variable
4. Your Django app will automatically use this database

#### Option B: External Database
Use free PostgreSQL from:
- **Supabase**: 500MB free
- **ElephantSQL**: 20MB free
- **Aiven**: 1 month free trial

Add the `DATABASE_URL` to your environment variables.

#### Option C: SQLite (Simple but not recommended for production)
- No additional setup needed
- Data will be lost on redeploys

## Step 3: Configure Build and Deploy

### 3.1 Build Settings
Railway should automatically detect your Python project. If not:

1. Go to Settings → Build
2. Set Build Command: `pip install -r requirements.txt`
3. Set Start Command: `gunicorn movie_backend.wsgi:application --bind 0.0.0.0:$PORT`

### 3.2 Domain Configuration
1. Go to Settings → Networking
2. Click "Generate Domain" to get a free Railway subdomain
3. Your app will be available at: `https://your-app-name.up.railway.app`

## Step 4: Post-Deployment Configuration

### 4.1 Update Production Settings
Add your Railway domain to `ALLOWED_HOSTS` in production_settings.py:
```python
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.up.railway.app',  # Railway hosting
    # ... other hosts
]
```

### 4.2 Update Frontend Configuration
Update your frontend to use the new Railway backend URL:
- Replace any localhost URLs with your Railway domain
- Update CORS settings if needed

### 4.3 Run Database Migrations
1. Go to your Railway project
2. Click on "Deployments"
3. In the latest deployment, click "View Logs"
4. Railway should automatically run migrations via the `release` command in Procfile

## Step 5: Testing Your Deployment

### 5.1 Check Application Health
1. Visit your Railway domain
2. Test API endpoints:
   - `GET /api/movies/` - List movies
   - `GET /api/health/` - Health check (if implemented)

### 5.2 Monitor Logs
1. In Railway dashboard, go to your service
2. Click "Logs" to see real-time application logs
3. Look for any errors or warnings

## Step 6: Environment Variables Reference

### Required Variables
```bash
DJANGO_SETTINGS_MODULE=movie_backend.production_settings
SECRET_KEY=your-secret-key-here
DEBUG=False
PORT=8000
```

### Database Variables (if using external DB)
```bash
DATABASE_URL=postgresql://username:password@host:port/database
```

### Frontend Integration
```bash
FRONTEND_URL=https://project-nexus-alx.netlify.app
```

### Optional Performance Variables
```bash
REDIS_URL=redis://username:password@host:port
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## Troubleshooting

### Common Issues

**1. Build Failures:**
- Check `requirements.txt` for correct package versions
- Ensure Python version compatibility
- Review build logs in Railway dashboard

**2. Application Won't Start:**
- Verify `Procfile` web command is correct
- Check that all required environment variables are set
- Review application logs for startup errors

**3. Database Connection Issues:**
- Ensure `DATABASE_URL` is correctly formatted
- Check database service is running
- Verify database credentials

**4. CORS Errors:**
- Add your frontend URL to `CORS_ALLOWED_ORIGINS`
- Set `FRONTEND_URL` environment variable
- Check that CORS middleware is properly configured

**5. Static Files Not Loading:**
- Ensure `STATIC_ROOT` is set correctly
- Verify Whitenoise is in `MIDDLEWARE`
- Check static files configuration

### Debug Commands
To debug issues, you can use Railway's CLI:
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Connect to your project
railway link

# View logs
railway logs

# Run commands in production environment
railway run python manage.py shell
```

## Railway Free Tier Limits

- **Execution Time**: 500 hours/month
- **Memory**: 512MB RAM
- **Storage**: 1GB
- **Bandwidth**: 100GB/month
- **Build Time**: 500 minutes/month
- **No credit card required**

## Performance Optimization

### 1. Enable Gzip Compression
Add to your production settings:
```python
MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',
    # ... other middleware
]
```

### 2. Configure Gunicorn
Update your Procfile for better performance:
```
web: gunicorn movie_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

### 3. Database Connection Pooling
Add to requirements.txt:
```
psycopg2-pool==1.1
```

## Next Steps

1. **Custom Domain** (Paid plans): Add your own domain
2. **Monitoring**: Set up error tracking with Sentry
3. **Backup**: Configure database backups
4. **CI/CD**: Set up automatic deployments from GitHub
5. **Scaling**: Monitor usage and upgrade plan if needed

## Support Resources

- [Railway Documentation](https://docs.railway.app/)
- [Railway Discord Community](https://discord.gg/railway)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)

---

**Your Railway deployment URL will be**: `https://your-project-name.up.railway.app`

Remember to update your frontend configuration to use this new backend URL!