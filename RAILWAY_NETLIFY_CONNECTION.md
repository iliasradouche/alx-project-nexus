# 🔗 Connecting Railway Backend with Netlify Frontend

This guide explains how to connect your Django backend deployed on Railway with your React frontend deployed on Netlify.

## 📋 Prerequisites

- ✅ **Backend deployed on Railway** (with the setuptools fix applied)
- ✅ **Frontend code ready for Netlify deployment**
- ✅ **Railway project URL** (e.g., `https://your-app-name.railway.app`)
- ✅ **Netlify account**

## 🎯 Step 1: Get Your Railway Backend URL

1. **Find Your Railway App URL**
   - Go to [railway.app](https://railway.app) and login
   - Click on your project from the dashboard
   - Click on your service/deployment (usually shows as "Web Service" or your app name)
   - Look for the **"Deployments"** tab or **"Settings"** tab
   - Find the **"Public Domain"** or **"Generated Domain"** section
   - Copy the URL (format: `https://your-project-name-production-xxxx.up.railway.app`)
   - **Your Railway URL**: `https://alx-project-nexus-production-f78f.up.railway.app`
   
   **Alternative ways to find your URL:**
   - Check the **"Overview"** tab for a public URL
   - Look in the **"Networking"** section for domain information
   - If no URL is visible, you may need to enable public networking in Settings

2. **Test Your Backend**
   ```bash
   curl https://alx-project-nexus-production-f78f.up.railway.app/api/movies/
   ```
   
   **✅ Fixed Issues**: 
   - Updated `wsgi.py` to use `production_settings`
   - Created proper `Procfile` for Railway deployment
   - Verified `railway.json` configuration
   - **CRITICAL FIX**: Disabled `SECURE_SSL_REDIRECT` in production settings (Railway handles SSL at proxy level)
   - **CORS Configuration**: Added Netlify domain to allowed origins and corrected middleware order
   - **API Functionality**: Backend now returns 200 OK with proper CORS headers
   
   **✅ Railway Backend is NOW WORKING!**
   - API endpoint: `https://alx-project-nexus-production-f78f.up.railway.app/api/movies/`
   - CORS headers properly configured for Netlify frontend
   - SSL redirect loop issue resolved
   - Preflight requests working correctly

## 🔧 Step 2: Update Backend CORS Settings

### Update Production Settings

Your backend is already configured to accept Railway domains, but you need to add your Netlify URL:

1. **Update `production_settings.py`** (already configured for Railway):
   ```python
   ALLOWED_HOSTS = [
       'localhost',
       '127.0.0.1',
       '.railway.app',  # ✅ Already configured
       '.netlify.app',  # Add this for Netlify
   ]
   
   CORS_ALLOWED_ORIGINS = [
       "https://your-netlify-app.netlify.app",  # Add your Netlify URL
       "http://localhost:3000",  # For local development
   ]
   ```

2. **Set Environment Variables on Railway**:
   - Go to Railway dashboard → Your project → Variables
   - Add: `FRONTEND_URL=https://your-netlify-app.netlify.app`
   - Your backend URL: `https://alx-project-nexus-production-f78f.up.railway.app`

## 🌐 Step 3: Deploy Frontend to Netlify

### Option A: Deploy via Netlify Dashboard

1. **Login to Netlify**
   - Go to [app.netlify.com](https://app.netlify.com)
   - Sign in with GitHub/GitLab/Bitbucket

2. **Create New Site**
   - Click "New site from Git"
   - Choose your Git provider
   - Select your repository: `alx-project-nexus`
   - Set base directory: `movie-frontend`

3. **Configure Build Settings**
   ```
   Base directory: movie-frontend
   Build command: npm run build
   Publish directory: movie-frontend/build
   ```

4. **Set Environment Variables**
   - Go to **Site settings** → **Environment variables**
   - Add these variables:
   ```
   REACT_APP_API_URL=https://your-railway-app.railway.app
   GENERATE_SOURCEMAP=false
   CI=false
   ```

5. **Deploy**
   - Click "Deploy site"
   - Wait for build to complete
   - Note your Netlify URL (e.g., `https://amazing-app-123456.netlify.app`)

### Option B: Deploy via Netlify CLI

1. **Install Netlify CLI**
   ```bash
   npm install -g netlify-cli
   ```

2. **Login to Netlify**
   ```bash
   netlify login
   ```

3. **Deploy from Frontend Directory**
   ```bash
   cd movie-frontend
   
   # Set environment variable
   echo "REACT_APP_API_URL=https://your-railway-app.railway.app" > .env.production
   
   # Build the project
   npm run build
   
   # Deploy to Netlify
   netlify deploy --prod --dir=build
   ```

## 🔄 Step 4: Update Backend with Netlify URL

Once you have your Netlify URL:

1. **Update Railway Environment Variables**:
   - Go to Railway dashboard → Your project → Variables
   - Update: `FRONTEND_URL=https://your-actual-netlify-url.netlify.app`

2. **Redeploy Backend** (Railway will auto-redeploy when you change environment variables)

## 🧪 Step 5: Test the Connection

### Test API Endpoints

1. **Test CORS from Browser Console**:
   ```javascript
   fetch('https://your-railway-app.railway.app/api/movies/')
     .then(response => response.json())
     .then(data => console.log(data))
     .catch(error => console.error('Error:', error));
   ```

2. **Test Authentication**:
   ```javascript
   fetch('https://your-railway-app.railway.app/api/auth/register/', {
     method: 'POST',
     headers: {
       'Content-Type': 'application/json',
     },
     body: JSON.stringify({
       username: 'testuser',
       email: 'test@example.com',
       password: 'testpass123'
     })
   })
   .then(response => response.json())
   .then(data => console.log(data));
   ```

### Test Frontend

1. **Open your Netlify app**
2. **Check browser console** for any CORS errors
3. **Test user registration/login**
4. **Test movie recommendations**

## 🔧 Troubleshooting

### Common Issues

1. **Can't Find Railway App URL**
   ```
   No public domain visible in Railway dashboard
   ```
   
   **Solutions**:
   - Go to your Railway project → Settings → Networking
   - Click "Generate Domain" if no domain exists
   - Ensure your service is deployed and running (check Deployments tab)
   - Make sure PORT environment variable is set (Railway auto-sets this)
   - Check if your app is listening on `0.0.0.0:$PORT` not just `localhost`

1.1. **Railway App Shows "Too Many Redirects" Error** ⚠️ **CURRENT ISSUE**
   ```
   curl: too many redirects or redirect loop detected
   ```
   
   **Immediate Solutions to Try**:
   
   **Step 1: Check Railway Deployment Logs**
   - Go to Railway dashboard → Your project → Deployments
   - Click on the latest deployment → View Logs
   - Look for startup errors or configuration issues
   
   **Step 2: Verify Environment Variables in Railway**
   - Go to Railway dashboard → Your project → Variables
   - Ensure these are set:
     ```
     DJANGO_SETTINGS_MODULE=movie_backend.production_settings
     SECRET_KEY=your-secret-key
     DEBUG=False
     TMDB_API_KEY=your-tmdb-key
     ```
   
   **Step 3: Check Django Production Settings**
   - Verify `ALLOWED_HOSTS` includes `.railway.app`
   - Ensure `SECURE_SSL_REDIRECT = True` is properly configured
   - Check that your `wsgi.py` points to the correct settings module
   
   **Step 4: Test Locally First**
   - Run `python manage.py runserver --settings=movie_backend.production_settings`
   - If it works locally, the issue is Railway-specific
   
   **Step 5: Railway Deployment Fix**
   - Try redeploying: Railway dashboard → Deployments → Redeploy
   - Check if Railway is using the correct start command
   - Verify the `Procfile` or start command is correct

2. **CORS Errors**
   ```
   Access to fetch at 'https://railway-app.railway.app' from origin 'https://netlify-app.netlify.app' has been blocked by CORS policy
   ```
   
   **Solution**: Ensure your Netlify URL is added to `CORS_ALLOWED_ORIGINS` in `production_settings.py`

2. **API URL Not Found**
   ```
   TypeError: Failed to fetch
   ```
   
   **Solution**: Check that `REACT_APP_API_URL` environment variable is set correctly in Netlify

3. **Build Failures**
   ```
   Module not found: Can't resolve...
   ```
   
   **Solution**: Ensure all dependencies are in `package.json` and `CI=false` is set

### Debug Steps

1. **Check Railway Logs**:
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login and view logs
   railway login
   railway logs
   ```

2. **Check Netlify Build Logs**:
   - Go to Netlify dashboard → Your site → Deploys
   - Click on latest deploy to see build logs

3. **Test API Directly**:
   ```bash
   curl -X GET https://your-railway-app.railway.app/api/movies/ \
        -H "Origin: https://your-netlify-app.netlify.app"
   ```

## 🎉 Final Configuration Summary

### Railway Backend Environment Variables
```
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key
DEBUG=False
FRONTEND_URL=https://your-netlify-app.netlify.app
TMDB_API_KEY=your-tmdb-key
```

### Netlify Frontend Environment Variables
```
REACT_APP_API_URL=https://your-railway-app.railway.app
GENERATE_SOURCEMAP=false
CI=false
```

### URLs to Update
- **Backend CORS**: Add Netlify URL to `CORS_ALLOWED_ORIGINS`
- **Frontend API**: Set `REACT_APP_API_URL` to Railway URL
- **Environment Variables**: Update both platforms with correct URLs

## 🚀 Next Steps

1. **Custom Domain** (Optional):
   - Set up custom domain on Netlify
   - Update CORS settings with new domain

2. **SSL/HTTPS**:
   - Both Railway and Netlify provide HTTPS by default
   - Ensure all API calls use HTTPS

3. **Monitoring**:
   - Set up error tracking (Sentry)
   - Monitor API performance
   - Set up uptime monitoring

4. **CI/CD**:
   - Set up automatic deployments on git push
   - Configure staging environments

## Final Resolution ✅

**Frontend Configuration Fixed:**
- Updated `.env` file to use Railway backend URL
- Fixed `netlify.toml` environment variable configuration
- Corrected `api.js` baseURL construction
- Rebuilt and redeployed frontend to Netlify

**Status: FULLY RESOLVED** 🎉
- Backend: Railway deployment working with proper CORS headers
- Frontend: Netlify deployment updated with correct API URL
- Connection: Frontend can now successfully communicate with backend

**Test the connection:** Visit https://project-nexus-alx.netlify.app to verify the movie recommendation app is working!

Your Railway backend and Netlify frontend should now be successfully connected! 🎉