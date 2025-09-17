# Render Deployment Guide - Movie Recommendation Backend

## Overview
This guide will help you deploy your Django movie recommendation backend to Render using the standard Web Service approach (no credit card required for basic deployment).

## Prerequisites
- GitHub account
- Your code pushed to a GitHub repository
- Render account (free tier available)

## Step 1: Prepare Your Repository

1. Ensure your code is pushed to GitHub
2. Verify these files exist in your project:
   - `Procfile` (already created)
   - `requirements.txt` (already exists)
   - `production_settings.py` (already configured)

## Step 2: Deploy on Render

### Option A: Direct Web Service (Recommended - No Credit Card)

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" button
3. Select "Web Service" (NOT Blueprint)
4. Connect your GitHub repository
5. Configure the service:

   **Basic Settings:**
   - Name: `movie-recommendation-backend`
   - Environment: `Python 3`
   - Region: Choose closest to your users
   - Branch: `main` (or your default branch)

   **Build & Deploy:**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn movie_backend.wsgi:application --bind 0.0.0.0:$PORT`

   **Environment Variables:**
   ```
   DJANGO_SETTINGS_MODULE=movie_backend.production_settings
   SECRET_KEY=your-secret-key-here
   DEBUG=False
   DATABASE_URL=your-database-url (if using external DB)
   FRONTEND_URL=https://project-nexus-alx.netlify.app
   ```

6. Click "Create Web Service"

## Step 3: Database Setup

### Option 1: SQLite (Simple, included)
- No additional setup needed
- Data stored in container (will reset on redeploys)

### Option 2: External PostgreSQL (Recommended for production)
1. Use a free PostgreSQL service like:
   - Supabase (free tier)
   - ElephantSQL (free tier)
   - Aiven (free tier)
2. Add the `DATABASE_URL` to your environment variables

## Step 4: Environment Variables

In your Render service settings, add these environment variables:

```
DJANGO_SETTINGS_MODULE=movie_backend.production_settings
SECRET_KEY=your-django-secret-key
DEBUG=False
FRONTEND_URL=https://project-nexus-alx.netlify.app
DATABASE_URL=your-database-url (if using external DB)
```

## Step 5: Post-Deployment

1. Your app will be available at: `https://your-service-name.onrender.com`
2. Update your frontend to use this new backend URL
3. Test all API endpoints

## Troubleshooting

### Common Issues:

1. **Build Fails:**
   - Check your `requirements.txt` for correct dependencies
   - Ensure Python version compatibility

2. **App Won't Start:**
   - Verify your `Procfile` is correct
   - Check environment variables are set

3. **Database Errors:**
   - Ensure `DATABASE_URL` is correctly formatted
   - Check database permissions

4. **CORS Issues:**
   - Update `CORS_ALLOWED_ORIGINS` in production settings
   - Add your frontend URL to environment variables

## Free Tier Limitations

- Service sleeps after 15 minutes of inactivity
- 750 hours/month (enough for continuous use)
- Limited to 512MB RAM
- No custom domains on free tier

## Next Steps

1. Monitor your deployment in Render dashboard
2. Set up automatic deployments from GitHub
3. Configure custom domain (paid plans)
4. Set up monitoring and logging

## Support

If you encounter issues:
1. Check Render logs in the dashboard
2. Review Django logs for application errors
3. Consult Render documentation

---

**Note:** This approach uses the standard Web Service deployment and should not require credit card verification for the free tier.