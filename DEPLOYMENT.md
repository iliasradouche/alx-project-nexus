# Movie Recommendation App - Deployment Guide

This guide covers deploying both the React frontend and Django backend of the Movie Recommendation application.

## 🚀 Frontend Deployment (Vercel)

### Prerequisites
- Node.js 16+ installed
- Vercel account (free tier available)
- Git repository

### Step 1: Prepare Your Frontend

1. **Navigate to the frontend directory:**
   ```bash
   cd movie-frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Test the build locally:**
   ```bash
   npm run build:prod
   ```

### Step 2: Deploy to Vercel

#### Option A: Vercel CLI (Recommended)

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel:**
   ```bash
   vercel login
   ```

3. **Deploy from the frontend directory:**
   ```bash
   cd movie-frontend
   vercel
   ```

4. **Follow the prompts:**
   - Link to existing project? **N**
   - Project name: `movie-recommendation-frontend`
   - Directory: `./` (current directory)
   - Override settings? **N**

#### Option B: Vercel Dashboard

1. **Push your code to GitHub/GitLab/Bitbucket**

2. **Go to [Vercel Dashboard](https://vercel.com/dashboard)**

3. **Click "New Project"**

4. **Import your repository**

5. **Configure project settings:**
   - Framework Preset: **Create React App**
   - Root Directory: `movie-frontend`
   - Build Command: `npm run build:prod`
   - Output Directory: `build`

### Step 3: Configure Environment Variables

In your Vercel dashboard:

1. Go to **Project Settings** → **Environment Variables**

2. Add the following variables:
   ```
   REACT_APP_API_URL = https://your-backend-url.herokuapp.com/api
   GENERATE_SOURCEMAP = false
   ```

3. **Redeploy** after adding environment variables

---

## 🖥️ Backend Deployment Options

Since Vercel is primarily for frontend/serverless functions, you'll need a separate service for your Django backend.

### Option 1: Heroku (Recommended for beginners)

#### Prerequisites
- Heroku account
- Heroku CLI installed

#### Steps:

1. **Navigate to backend directory:**
   ```bash
   cd movie_recommendation_backend
   ```

2. **Create additional files for Heroku:**

   **Procfile:**
   ```
   web: gunicorn movie_backend.wsgi:application --bind 0.0.0.0:$PORT
   ```

   **runtime.txt:**
   ```
   python-3.11.0
   ```

   **Update requirements.txt:**
   ```bash
   echo "gunicorn==21.2.0" >> requirements.txt
   echo "whitenoise==6.6.0" >> requirements.txt
   echo "dj-database-url==2.1.0" >> requirements.txt
   ```

3. **Update Django settings for production:**
   
   Add to `movie_backend/settings.py`:
   ```python
   import dj_database_url
   
   # Production settings
   if not DEBUG:
       ALLOWED_HOSTS = ['your-app-name.herokuapp.com', 'localhost']
       
       # Database
       DATABASES['default'] = dj_database_url.parse(
           config('DATABASE_URL', default='sqlite:///db.sqlite3')
       )
       
       # Static files
       STATIC_ROOT = BASE_DIR / 'staticfiles'
       STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
       
       # Add whitenoise to middleware
       MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
   ```

4. **Deploy to Heroku:**
   ```bash
   heroku login
   heroku create your-movie-backend
   git add .
   git commit -m "Prepare for Heroku deployment"
   git push heroku main
   ```

5. **Set environment variables:**
   ```bash
   heroku config:set SECRET_KEY="your-secret-key"
   heroku config:set DEBUG=False
   heroku config:set DATABASE_URL="your-database-url"
   ```

6. **Run migrations:**
   ```bash
   heroku run python manage.py migrate
   heroku run python manage.py createsuperuser
   ```

### Option 2: Railway

1. **Go to [Railway](https://railway.app/)**
2. **Connect your GitHub repository**
3. **Select the backend directory**
4. **Railway will auto-detect Django and deploy**
5. **Add environment variables in Railway dashboard**

### Option 3: Render

1. **Go to [Render](https://render.com/)**
2. **Create a new Web Service**
3. **Connect your repository**
4. **Configure:**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn movie_backend.wsgi:application`
   - Environment: `Python 3`

---

## 🔧 Post-Deployment Configuration

### Update Frontend Environment Variables

Once your backend is deployed, update the Vercel environment variables:

1. **Go to Vercel Dashboard** → Your Project → Settings → Environment Variables

2. **Update `REACT_APP_API_URL`:**
   ```
   REACT_APP_API_URL = https://your-backend-url.herokuapp.com/api
   ```

3. **Redeploy the frontend**

### Configure CORS in Django

Update your Django settings to allow your Vercel domain:

```python
# In movie_backend/settings.py
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend-url.vercel.app",
    "http://localhost:3000",  # for local development
]

CORS_ALLOW_CREDENTIALS = True
```

---

## 🧪 Testing Your Deployment

### Frontend Tests
1. **Visit your Vercel URL**
2. **Check browser console for errors**
3. **Test user registration/login**
4. **Verify movie search and recommendations work**

### Backend Tests
1. **Visit your backend URL + `/admin/`**
2. **Test API endpoints:**
   ```bash
   curl https://your-backend-url.herokuapp.com/api/movies/
   ```

---

## 🔍 Troubleshooting

### Common Frontend Issues

**Build fails:**
- Check for TypeScript errors
- Ensure all dependencies are in `package.json`
- Check build logs in Vercel dashboard

**API calls fail:**
- Verify `REACT_APP_API_URL` is set correctly
- Check CORS configuration in Django
- Ensure backend is running

### Common Backend Issues

**Static files not loading:**
- Run `python manage.py collectstatic`
- Check `STATIC_ROOT` and `STATICFILES_STORAGE` settings

**Database errors:**
- Run migrations: `heroku run python manage.py migrate`
- Check database URL configuration

**CORS errors:**
- Update `CORS_ALLOWED_ORIGINS` in Django settings
- Install and configure `django-cors-headers`

---

## 📊 Monitoring and Maintenance

### Vercel
- **Analytics:** Built-in analytics in Vercel dashboard
- **Logs:** Real-time function logs
- **Performance:** Core Web Vitals monitoring

### Backend Monitoring
- **Heroku:** Use Heroku metrics and logs
- **Error Tracking:** Consider integrating Sentry
- **Database:** Monitor database performance

### Regular Maintenance
- **Dependencies:** Keep packages updated
- **Security:** Regular security audits
- **Backups:** Regular database backups
- **SSL:** Ensure HTTPS is enabled

---

## 🚀 Advanced Deployment Options

### Custom Domain
1. **Purchase a domain**
2. **Add to Vercel:** Project Settings → Domains
3. **Configure DNS:** Point to Vercel's nameservers

### CI/CD Pipeline
- **GitHub Actions:** Automate testing and deployment
- **Vercel Git Integration:** Auto-deploy on push
- **Environment Branches:** Separate staging/production

### Performance Optimization
- **CDN:** Vercel includes global CDN
- **Caching:** Configure appropriate cache headers
- **Bundle Analysis:** Use `npm run analyze`

---

## 📞 Support

If you encounter issues:
1. **Check the logs** (Vercel dashboard, Heroku logs)
2. **Review this guide** for common solutions
3. **Check documentation** for your chosen platforms
4. **Community forums** for platform-specific help

---

**Happy Deploying! 🎉**