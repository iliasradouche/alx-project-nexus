# Render Deployment Guide for Movie Recommendation Backend

## Overview
This guide will help you deploy your Django movie recommendation backend to Render for **FREE**.

## Prerequisites
- GitHub account
- Render account (free at https://render.com)
- Your code pushed to a GitHub repository

## Step 1: Prepare Your Repository

1. **Push your code to GitHub**:
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

## Step 2: Deploy to Render

### Option A: Using render.yaml (Recommended)

1. **Connect GitHub to Render**:
   - Go to https://render.com
   - Sign up/Login with GitHub
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect the `render.yaml` file

2. **Configure Environment Variables**:
   - `DJANGO_SETTINGS_MODULE`: `movie_backend.production_settings`
   - `DEBUG`: `False`
   - `FRONTEND_URL`: Your Netlify frontend URL (e.g., `https://project-nexus-alx.netlify.app`)
   - `SECRET_KEY`: Will be auto-generated
   - `DATABASE_URL`: Will be auto-configured

### Option B: Manual Setup

1. **Create Web Service**:
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name**: `movie-recommendation-backend`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn movie_backend.wsgi:application`

2. **Create Database**:
   - Click "New" → "PostgreSQL"
   - **Name**: `movie-recommendation-db`
   - **Plan**: Free
   - Copy the connection string

3. **Set Environment Variables**:
   ```
   DJANGO_SETTINGS_MODULE=movie_backend.production_settings
   DEBUG=False
   DATABASE_URL=<your-postgres-connection-string>
   FRONTEND_URL=https://project-nexus-alx.netlify.app
   SECRET_KEY=<generate-a-secret-key>
   ```

## Step 3: Post-Deployment Setup

1. **Run Migrations**:
   - Go to your service dashboard
   - Open "Shell" tab
   - Run: `python manage.py migrate`

2. **Collect Static Files**:
   ```bash
   python manage.py collectstatic --noinput
   ```

3. **Create Superuser** (Optional):
   ```bash
   python manage.py createsuperuser
   ```

## Step 4: Update Frontend Configuration

1. **Get your backend URL**:
   - Your backend will be available at: `https://your-service-name.onrender.com`

2. **Update frontend environment variables**:
   - In your Netlify frontend, update the API base URL to point to your Render backend

## Step 5: Configure CORS

1. **Update production_settings.py** (if needed):
   ```python
   CORS_ALLOWED_ORIGINS = [
       "https://project-nexus-alx.netlify.app",
       "http://localhost:3000",
   ]
   ```

## Troubleshooting

### Common Issues:

1. **Build Fails**:
   - Check `requirements.txt` for correct dependencies
   - Ensure Python version compatibility

2. **Database Connection Issues**:
   - Verify `DATABASE_URL` environment variable
   - Check if migrations ran successfully

3. **Static Files Not Loading**:
   - Ensure `whitenoise` is in `MIDDLEWARE`
   - Run `collectstatic` command

4. **CORS Errors**:
   - Update `CORS_ALLOWED_ORIGINS` with correct frontend URL
   - Remove trailing slashes from URLs

### Useful Commands:

```bash
# View logs
render logs --service your-service-name

# Run shell commands
render shell --service your-service-name

# Deploy latest changes
git push origin main  # Render auto-deploys on push
```

## Free Tier Limitations

- **Web Service**: 750 hours/month (enough for 24/7)
- **Database**: 1GB storage, 1 million rows
- **Bandwidth**: 100GB/month
- **Sleep**: Service sleeps after 15 minutes of inactivity (spins up in ~30 seconds)

## Monitoring

- **Dashboard**: https://dashboard.render.com
- **Logs**: Available in real-time
- **Metrics**: CPU, Memory, Response times

## Next Steps

1. Test all API endpoints
2. Monitor performance and logs
3. Set up custom domain (optional)
4. Configure SSL (automatic with Render)

## Support

- **Render Docs**: https://render.com/docs
- **Community**: https://community.render.com
- **Status**: https://status.render.com

---

**Your backend will be available at**: `https://your-service-name.onrender.com`

**Remember to update your frontend to use this new backend URL!**