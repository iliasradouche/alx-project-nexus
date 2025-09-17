# Movie Recommendation App - Deployment Guide

This guide covers deploying both the React frontend and Django backend of the Movie Recommendation application.

## 🚀 Frontend Deployment

### Option 1: Vercel Deployment

#### Prerequisites
- Node.js 18+ installed
- Vercel CLI installed: `npm i -g vercel`
- GitHub/GitLab account (for automatic deployments)

#### Deploy via Vercel CLI

1. **Navigate to frontend directory**:
   ```bash
   cd movie-frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Build the project**:
   ```bash
   npm run build
   ```

4. **Deploy to Vercel**:
   ```bash
   vercel --prod
   ```

#### Deploy via Vercel Dashboard

1. **Push your code to GitHub/GitLab**
2. **Connect your repository to Vercel**:
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your repository
   - Set root directory to `movie-frontend`
   - Deploy

### Option 2: Netlify Deployment

#### Prerequisites
- Node.js 18+ installed
- Netlify CLI installed: `npm i -g netlify-cli`
- GitHub/GitLab account (for automatic deployments)

#### Deploy via Netlify CLI

1. **Navigate to frontend directory**:
   ```bash
   cd movie-frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Build the project**:
   ```bash
   npm run build
   ```

4. **Deploy to Netlify**:
   ```bash
   netlify deploy --prod --dir=build
   ```

#### Deploy via Netlify Dashboard

1. **Push your code to GitHub/GitLab**
2. **Connect your repository to Netlify**:
   - Go to [netlify.com](https://netlify.com)
   - Click "New site from Git"
   - Choose your repository
   - Set build command: `npm run build`
   - Set publish directory: `build`
   - Set base directory: `movie-frontend`
   - Deploy

#### Netlify Configuration

Create `movie-frontend/netlify.toml`:
```toml
[build]
  base = "movie-frontend"
  command = "npm run build"
  publish = "build"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[build.environment]
  NODE_VERSION = "18"
```

### Environment Variables (Both Platforms)

Set these in your deployment platform dashboard:

```bash
# Required
REACT_APP_API_URL=https://your-backend-url.herokuapp.com/api

# Optional
REACT_APP_ANALYTICS_ID=your-analytics-id
REACT_APP_ENVIRONMENT=production
```

---

## 🖥️ Backend Deployment Options

Since Vercel is primarily for frontend/serverless functions, you'll need a separate service for your Django backend.

### Option 1: Heroku (Recommended)

#### Prerequisites
- **Heroku CLI installed** - [Download here](https://devcenter.heroku.com/articles/heroku-cli)
- **Git installed** - [Download here](https://git-scm.com/downloads)
- **Heroku account** - [Sign up here](https://signup.heroku.com/)
- **Python 3.11+** installed
- **PostgreSQL** (for local development - optional) (free tier available)

#### Step-by-Step Heroku Deployment

##### Option 1: Automated Deployment (Recommended)

We've created deployment scripts to automate the process:

**For Windows:**
```cmd
cd movie_recommendation_backend
.\deploy_heroku.bat
```

**For Linux/Mac:**
```bash
cd movie_recommendation_backend
chmod +x deploy_heroku.sh
./deploy_heroku.sh
```

##### Option 2: Manual Deployment

1. **Install Heroku CLI** (if not already installed):
   ```bash
   # Windows
   winget install Heroku.CLI
   
   # macOS
   brew tap heroku/brew && brew install heroku
   
   # Linux
   curl https://cli-assets.heroku.com/install.sh | sh
   ```

2. **Login to Heroku**:
   ```bash
   heroku login
   ```

3. **Navigate to backend directory**:
   ```bash
   cd movie_recommendation_backend
   ```

4. **Initialize Git repository** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

5. **Create Heroku app**:
   ```bash
   heroku create your-movie-backend-app
   ```

6. **Add PostgreSQL addon**:
   ```bash
   heroku addons:create heroku-postgresql:essential-0
   ```

7. **Create additional files for Heroku:**

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
   echo "psycopg2-binary==2.9.7" >> requirements.txt
   ```

8. **Update Django settings for production:**
   
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

9. **Set environment variables**:
   ```bash
   heroku config:set DJANGO_SETTINGS_MODULE=movie_backend.production_settings
   heroku config:set SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
   heroku config:set DEBUG=False
   heroku config:set ALLOWED_HOSTS="your-movie-backend-app.herokuapp.com"
   heroku config:set CORS_ALLOWED_ORIGINS="https://your-frontend-url.vercel.app,https://your-frontend-url.netlify.app"
   ```

10. **Deploy to Heroku**:
    ```bash
    git add .
    git commit -m "Prepare for Heroku deployment"
    git push heroku main
    ```

11. **Run database migrations**:
    ```bash
    heroku run python manage.py migrate
    heroku run python manage.py collectstatic --noinput
    ```

12. **Create superuser** (optional):
    ```bash
    heroku run python manage.py createsuperuser
    ```

#### Heroku Environment Variables

Set these in Heroku dashboard or via CLI:

```bash
# Core Django Settings
DJANGO_SETTINGS_MODULE=movie_backend.production_settings
SECRET_KEY=your-generated-secret-key
DEBUG=False
ALLOWED_HOSTS=your-app-name.herokuapp.com

# CORS Settings
CORS_ALLOWED_ORIGINS=https://your-frontend-url.vercel.app,https://your-frontend-url.netlify.app
CORS_ALLOW_CREDENTIALS=True

# Database (automatically set by Heroku PostgreSQL addon)
DATABASE_URL=postgres://...

# Optional: Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Optional: Redis (if using caching)
REDIS_URL=redis://...
```

### Option 2: Railway

#### Prerequisites
- Railway account (free tier available)
- GitHub repository

#### Steps

1. **Create Railway account** at [railway.app](https://railway.app)

2. **Create new project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Select the backend directory

3. **Add PostgreSQL database**:
   - Click "New" → "Database" → "PostgreSQL"
   - Railway will automatically provide DATABASE_URL

4. **Configure environment variables**:
   ```bash
   DJANGO_SETTINGS_MODULE=movie_backend.production_settings
   SECRET_KEY=your-secret-key
   DEBUG=False
   ALLOWED_HOSTS=your-app-name.up.railway.app
   CORS_ALLOWED_ORIGINS=https://your-frontend-url.vercel.app
   ```

5. **Configure build settings**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn movie_backend.wsgi:application --bind 0.0.0.0:$PORT`

6. **Deploy**: Railway will automatically deploy on git push

### Option 3: Render

#### Prerequisites
- Render account (free tier available)
- GitHub repository

#### Steps

1. **Create Render account** at [render.com](https://render.com)

2. **Create new Web Service**:
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Select your backend repository

3. **Configure service settings**:
   ```bash
   # Build Command
   pip install -r requirements.txt
   
   # Start Command
   gunicorn movie_backend.wsgi:application --bind 0.0.0.0:$PORT
   
   # Environment
   Python 3.11
   ```

4. **Add PostgreSQL database**:
   - Go to Dashboard → "New" → "PostgreSQL"
   - Copy the database URL

5. **Set environment variables**:
   ```bash
   DJANGO_SETTINGS_MODULE=movie_backend.production_settings
   SECRET_KEY=your-secret-key
   DEBUG=False
   DATABASE_URL=your-postgres-url
   ALLOWED_HOSTS=your-app-name.onrender.com
   CORS_ALLOWED_ORIGINS=https://your-frontend-url.vercel.app
   ```

6. **Deploy**: Render will automatically build and deploy

### Option 4: DigitalOcean App Platform

#### Prerequisites
- DigitalOcean account
- GitHub repository

#### Steps

1. **Create DigitalOcean account** at [digitalocean.com](https://digitalocean.com)

2. **Create new App**:
   - Go to Apps → "Create App"
   - Connect GitHub repository
   - Select backend directory

3. **Configure app settings**:
   ```bash
   # Build Command
   pip install -r requirements.txt
   
   # Run Command
   gunicorn movie_backend.wsgi:application --bind 0.0.0.0:$PORT
   ```

4. **Add managed database**:
   - Add PostgreSQL database component
   - DigitalOcean will provide DATABASE_URL

5. **Set environment variables**:
   ```bash
   DJANGO_SETTINGS_MODULE=movie_backend.production_settings
   SECRET_KEY=your-secret-key
   DEBUG=False
   ALLOWED_HOSTS=your-app-name.ondigitalocean.app
   CORS_ALLOWED_ORIGINS=https://your-frontend-url.vercel.app
   ```

---

## 📊 Platform Comparison

### Frontend Hosting Comparison

| Feature | Vercel | Netlify |
|---------|--------|----------|
| **Free Tier** | 100GB bandwidth/month | 100GB bandwidth/month |
| **Build Minutes** | 6,000 minutes/month | 300 minutes/month |
| **Custom Domains** | ✅ Unlimited | ✅ Unlimited |
| **SSL Certificates** | ✅ Automatic | ✅ Automatic |
| **Edge Functions** | ✅ Yes | ✅ Yes |
| **Analytics** | ✅ Built-in | ✅ Built-in |
| **Git Integration** | ✅ GitHub, GitLab, Bitbucket | ✅ GitHub, GitLab, Bitbucket |
| **Preview Deployments** | ✅ Yes | ✅ Yes |
| **Best For** | React/Next.js apps | Static sites, JAMstack |

### Backend Hosting Comparison

| Feature | Heroku | Railway | Render | DigitalOcean |
|---------|--------|---------|--------|--------------|
| **Free Tier** | Limited (sleeps after 30min) | $5/month minimum | Limited (sleeps after 15min) | $5/month minimum |
| **Database** | PostgreSQL add-on | Built-in PostgreSQL | Built-in PostgreSQL | Managed databases |
| **Deployment** | Git-based | Git-based | Git-based | Git-based |
| **Scaling** | Easy horizontal scaling | Auto-scaling | Auto-scaling | Manual scaling |
| **Custom Domains** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **SSL Certificates** | ✅ Automatic | ✅ Automatic | ✅ Automatic | ✅ Automatic |
| **Monitoring** | Basic (paid plans) | Built-in | Built-in | Advanced |
| **Best For** | Beginners, prototypes | Modern apps | Full-stack apps | Production apps |

### Recommended Combinations

1. **For Beginners**: Netlify (Frontend) + Heroku (Backend)
2. **For Modern Stack**: Vercel (Frontend) + Railway (Backend)
3. **For Production**: Vercel (Frontend) + DigitalOcean (Backend)
4. **For Budget-Conscious**: Netlify (Frontend) + Render (Backend)

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