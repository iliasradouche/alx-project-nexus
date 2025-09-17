# 🚀 Complete Deployment Checklist

## Movie Recommendation App: Heroku + Netlify Deployment

This checklist ensures a smooth deployment of your full-stack movie recommendation application.

---

## 📋 Pre-Deployment Checklist

### Prerequisites
- [ ] **Heroku CLI installed** - [Download](https://devcenter.heroku.com/articles/heroku-cli)
- [ ] **Git installed** - [Download](https://git-scm.com/downloads)
- [ ] **Node.js & npm installed** - [Download](https://nodejs.org/)
- [ ] **Heroku account created** - [Sign up](https://signup.heroku.com/)
- [ ] **Netlify account created** - [Sign up](https://app.netlify.com/signup)
- [ ] **TMDB API key obtained** - [Get key](https://www.themoviedb.org/settings/api)

---

## 🖥️ Backend Deployment (Heroku)

### Step 1: Prepare Backend
- [ ] Navigate to `movie_recommendation_backend` directory
- [ ] Verify files exist:
  - [ ] `Procfile`
  - [ ] `requirements.txt`
  - [ ] `runtime.txt`
  - [ ] `.env.example`
  - [ ] `deploy_heroku.bat` (Windows) or `deploy_heroku.sh` (Linux/Mac)

### Step 2: Deploy Backend

#### Option A: Automated Deployment (Recommended)
**Windows:**
```cmd
cd movie_recommendation_backend
.\deploy_heroku.bat
```

**Linux/Mac:**
```bash
cd movie_recommendation_backend
chmod +x deploy_heroku.sh
./deploy_heroku.sh
```

#### Option B: Manual Deployment
Follow the detailed guide in [`movie_recommendation_backend/HEROKU_DEPLOYMENT.md`](movie_recommendation_backend/HEROKU_DEPLOYMENT.md)

### Step 3: Verify Backend Deployment
- [ ] Backend URL accessible: `https://your-app-name.herokuapp.com`
- [ ] API endpoints working:
  - [ ] `https://your-app-name.herokuapp.com/api/movies/`
  - [ ] `https://your-app-name.herokuapp.com/admin/`
- [ ] Database migrations completed
- [ ] Static files served correctly

---

## 🌐 Frontend Deployment (Netlify)

### Step 1: Prepare Frontend
- [ ] Navigate to `movie-frontend` directory
- [ ] Update `.env` file with backend URL:
  ```
  REACT_APP_API_URL=https://your-heroku-app.herokuapp.com
  ```
- [ ] Verify `netlify.toml` configuration exists

### Step 2: Deploy Frontend

#### Option A: Netlify Dashboard (Recommended)
1. [ ] Login to [Netlify](https://app.netlify.com)
2. [ ] Click "New site from Git"
3. [ ] Connect your repository
4. [ ] Set build settings:
   - Base directory: `movie-frontend`
   - Build command: `npm run build`
   - Publish directory: `movie-frontend/build`
5. [ ] Add environment variables:
   - `REACT_APP_API_URL`: `https://your-heroku-app.herokuapp.com`
   - `GENERATE_SOURCEMAP`: `false`
   - `CI`: `false`
6. [ ] Deploy site

#### Option B: Netlify CLI
Follow the detailed guide in [`movie-frontend/NETLIFY_DEPLOYMENT.md`](movie-frontend/NETLIFY_DEPLOYMENT.md)

### Step 3: Connect Frontend to Backend
- [ ] Update Heroku CORS settings:
  ```bash
  heroku config:set CORS_ALLOWED_ORIGINS="https://your-netlify-app.netlify.app,http://localhost:3000" --app your-heroku-app
  ```
- [ ] Redeploy frontend if needed

---

## 🔗 Integration Testing

### Backend Testing
- [ ] Visit backend URL: `https://your-heroku-app.herokuapp.com`
- [ ] Test API endpoints:
  - [ ] Movies API: `https://your-heroku-app.herokuapp.com/api/movies/`
  - [ ] Recommendations API: `https://your-heroku-app.herokuapp.com/api/recommendations/`
- [ ] Access Django Admin: `https://your-heroku-app.herokuapp.com/admin/`
- [ ] Check logs: `heroku logs --tail --app your-heroku-app`

### Frontend Testing
- [ ] Visit frontend URL: `https://your-netlify-app.netlify.app`
- [ ] Test core functionality:
  - [ ] App loads without errors
  - [ ] Movies display correctly
  - [ ] Search functionality works
  - [ ] Recommendations load
  - [ ] Navigation works
- [ ] Check browser console for errors
- [ ] Test on different devices/browsers

### Full Integration Testing
- [ ] Frontend successfully calls backend APIs
- [ ] No CORS errors in browser console
- [ ] Data flows correctly between frontend and backend
- [ ] User interactions work end-to-end

---

## 🎯 Post-Deployment Tasks

### Security & Performance
- [ ] Verify HTTPS is enabled on both sites
- [ ] Check that DEBUG=False on backend
- [ ] Ensure sensitive data is not exposed
- [ ] Test site performance and loading times

### Monitoring Setup
- [ ] Set up error monitoring (optional)
- [ ] Configure analytics (optional)
- [ ] Set up uptime monitoring (optional)

### Documentation
- [ ] Update README files with live URLs
- [ ] Document any custom configurations
- [ ] Share deployment URLs with team/stakeholders

---

## 📱 URLs Reference

After successful deployment, save these URLs:

| Service | URL | Purpose |
|---------|-----|----------|
| **Backend (Heroku)** | `https://your-heroku-app.herokuapp.com` | API & Admin |
| **Frontend (Netlify)** | `https://your-netlify-app.netlify.app` | User Interface |
| **Admin Panel** | `https://your-heroku-app.herokuapp.com/admin/` | Django Admin |
| **API Docs** | `https://your-heroku-app.herokuapp.com/api/` | API Endpoints |

---

## 🚨 Troubleshooting

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| **Build fails on Netlify** | Check build logs, verify Node.js version |
| **API calls fail** | Verify CORS settings and environment variables |
| **Backend not accessible** | Check Heroku logs and dyno status |
| **Database errors** | Ensure migrations ran successfully |
| **Static files not loading** | Run `collectstatic` on Heroku |

### Useful Commands

```bash
# Heroku
heroku logs --tail --app your-app
heroku restart --app your-app
heroku config --app your-app

# Netlify
netlify status
netlify logs
netlify open
```

---

## 🎉 Success!

Congratulations! Your movie recommendation app is now live:

- **Frontend**: Hosted on Netlify with modern CI/CD
- **Backend**: Deployed on Heroku with PostgreSQL
- **Full Integration**: Frontend ↔ Backend communication working

### Next Steps
- [ ] Share your app with users
- [ ] Monitor performance and usage
- [ ] Plan future features and improvements
- [ ] Set up automated backups (optional)

---

**Need Help?** 
- 📖 [Heroku Documentation](https://devcenter.heroku.com/)
- 📖 [Netlify Documentation](https://docs.netlify.com/)
- 📁 [Detailed Deployment Guides](./DEPLOYMENT.md)