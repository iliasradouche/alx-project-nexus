# 🌐 Netlify Deployment Guide for Movie Recommendation Frontend

This guide will help you deploy the React frontend to Netlify and connect it to your Heroku backend.

## 📋 Prerequisites

- ✅ **Backend deployed on Heroku** (follow the backend deployment guide first)
- ✅ **Netlify account** - [Sign up here](https://app.netlify.com/signup)
- ✅ **Git repository** with your frontend code
- ✅ **Node.js and npm** installed locally

## 🚀 Quick Deployment Options

### Option 1: Deploy via Netlify Dashboard (Recommended)

1. **Login to Netlify**
   - Go to [netlify.com](https://netlify.com)
   - Click "Log in" and sign in with GitHub/GitLab/Bitbucket

2. **Import Project**
   - Click "New site from Git"
   - Choose your Git provider (GitHub/GitLab/Bitbucket)
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
   REACT_APP_API_URL = https://your-movie-backend.herokuapp.com
   GENERATE_SOURCEMAP = false
   CI = false
   ```

5. **Deploy**
   - Click "Deploy site"
   - Wait for build to complete
   - Your site will be available at `https://random-name.netlify.app`

### Option 2: Deploy via Netlify CLI

1. **Install Netlify CLI**
   ```bash
   npm install -g netlify-cli
   ```

2. **Login to Netlify**
   ```bash
   netlify login
   ```

3. **Navigate to Frontend Directory**
   ```bash
   cd movie-frontend
   ```

4. **Build the Project**
   ```bash
   npm install
   npm run build
   ```

5. **Deploy**
   ```bash
   # For first deployment
   netlify deploy --prod --dir=build
   
   # For subsequent deployments
   netlify deploy --prod
   ```

## 🔗 Connect Frontend to Heroku Backend

### Step 1: Update Environment Variables

After your backend is deployed to Heroku:

1. **Get your Heroku backend URL**
   ```bash
   heroku apps:info --app your-movie-backend
   ```
   Your URL will be: `https://your-movie-backend.herokuapp.com`

2. **Update Netlify Environment Variables**
   - Go to Netlify Dashboard → Your Site → Site settings → Environment variables
   - Update `REACT_APP_API_URL` to your Heroku backend URL
   - Example: `https://my-movie-backend.herokuapp.com`

### Step 2: Update CORS Settings on Backend

1. **Get your Netlify site URL**
   - From Netlify dashboard, copy your site URL (e.g., `https://amazing-app-123.netlify.app`)

2. **Update Heroku backend CORS settings**
   ```bash
   heroku config:set CORS_ALLOWED_ORIGINS="https://your-netlify-app.netlify.app,http://localhost:3000" --app your-movie-backend
   ```

### Step 3: Redeploy Frontend

1. **Trigger new deployment**
   - In Netlify dashboard, go to **Deploys**
   - Click "Trigger deploy" → "Deploy site"
   - Or push a new commit to trigger auto-deployment

## 🎯 Custom Domain (Optional)

### Add Custom Domain

1. **In Netlify Dashboard**
   - Go to **Site settings** → **Domain management**
   - Click "Add custom domain"
   - Enter your domain (e.g., `movieapp.com`)

2. **Configure DNS**
   - Point your domain's DNS to Netlify:
   ```
   Type: CNAME
   Name: www
   Value: your-site-name.netlify.app
   ```

3. **Enable HTTPS**
   - Netlify automatically provides SSL certificates
   - Wait for DNS propagation (up to 24 hours)

## 📊 Monitoring and Management

### View Deployment Logs
- Netlify Dashboard → Your Site → Deploys → Click on a deployment

### Environment Variables
- Site settings → Environment variables

### Build Settings
- Site settings → Build & deploy → Build settings

### Analytics (Optional)
- Site settings → Analytics (requires paid plan)

## 🔧 Configuration Files

### netlify.toml (Already configured)
Your `netlify.toml` file is already set up with:
- Build settings
- Redirect rules
- Environment variables
- Error handling

### Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|----------|
| `REACT_APP_API_URL` | Backend API URL | `https://your-backend.herokuapp.com` |
| `GENERATE_SOURCEMAP` | Generate source maps | `false` |
| `CI` | Continuous Integration | `false` |
| `REACT_APP_ENVIRONMENT` | Environment name | `production` |

## 🚨 Troubleshooting

### Common Issues:

1. **Build fails**
   - Check build logs in Netlify dashboard
   - Ensure all dependencies are in `package.json`
   - Verify Node.js version compatibility

2. **API calls fail**
   - Check `REACT_APP_API_URL` environment variable
   - Verify CORS settings on backend
   - Check network tab in browser dev tools

3. **Environment variables not working**
   - Ensure variables start with `REACT_APP_`
   - Redeploy after changing environment variables
   - Check if variables are set in Netlify dashboard

### Useful Commands:

```bash
# Check site status
netlify status

# View site info
netlify sites:list

# Open site in browser
netlify open

# View build logs
netlify logs
```

## 🎉 Success!

Once deployed, your frontend will be available at:
`https://your-site-name.netlify.app`

Your full-stack application is now live with:
- **Frontend**: Netlify
- **Backend**: Heroku
- **Database**: PostgreSQL (Heroku)

### Test Your Deployment:

1. Visit your Netlify site URL
2. Check that the app loads correctly
3. Test API calls (check browser network tab)
4. Verify movie recommendations work
5. Test user authentication (if implemented)

---

**Need help?** Check the [Netlify documentation](https://docs.netlify.com/) or the main [DEPLOYMENT.md](../DEPLOYMENT.md) file.