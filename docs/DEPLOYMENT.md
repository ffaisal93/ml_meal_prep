# Deployment Guide

This guide covers deploying the AI Meal Planner to production using Railway (backend) and GitHub Pages (frontend).

## Overview

- **Backend API**: Deploy to Railway (free tier available)
- **Frontend**: Auto-deploy to GitHub Pages via GitHub Actions
- **Database**: PostgreSQL provided by Railway (automatic)

## Prerequisites

- GitHub account (you already have this)
- Railway account (sign up at https://railway.app)
- OpenAI API key
- Code pushed to GitHub

## Part 1: Deploy Backend to Railway

### Step 1: Create Railway Account

1. Go to https://railway.app
2. Sign up with GitHub (easiest option)
3. Authorize Railway to access your repositories

### Step 2: Create New Project

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose `ml_meal_prep` repository
4. Railway will detect the Dockerfile automatically

### Step 3: Configure Environment Variables

1. Click on your deployed service
2. Go to "Variables" tab
3. Add these variables:

**Required:**
```
OPENAI_API_KEY=your_openai_api_key_here
```

**Optional (for RAG/Hybrid strategies):**
```
EDAMAM_APP_ID=your_edamam_id
EDAMAM_APP_KEY=your_edamam_key
```

**Optional (to change default strategy):**
```
RECIPE_GENERATION_MODE=fast_llm
```

### Step 4: Add PostgreSQL Database (Optional)

1. In your project, click "New"
2. Select "Database" → "PostgreSQL"
3. Railway automatically sets `DATABASE_URL` environment variable
4. Your app will use it automatically - no code changes needed

### Step 5: Get Your API URL

1. Go to "Settings" tab
2. Click "Generate Domain" under "Public Networking"
3. You'll get a URL like: `https://your-app.railway.app`
4. Test it: `https://your-app.railway.app/health`

**Your backend is now live!**

## Part 2: Deploy Frontend to GitHub Pages

### Step 1: Enable GitHub Pages

1. Go to your GitHub repository: `https://github.com/yourusername/ml_meal_prep`
2. Click "Settings" → "Pages"
3. Under "Build and deployment":
   - Source: Select **"GitHub Actions"**
4. Click Save

### Step 2: Frontend Auto-Deploys

The frontend automatically deploys when you push to `main` branch. The GitHub Actions workflow is already configured.

**Your frontend will be at:**
```
https://yourusername.github.io/ml_meal_prep/
```

### Step 3: Configure API URL (Optional)

Users can enter your Railway URL in the frontend, or you can set it as default:

Edit `frontend/app.js`:
```javascript
const DEFAULT_API_URL = 'https://your-app.railway.app';
```

Then commit and push:
```bash
git add frontend/app.js
git commit -m "Update default API URL"
git push
```

**Your frontend is now live!**

## Part 3: Verify Deployment

### Test Backend

```bash
# Health check
curl https://your-app.railway.app/health

# Generate meal plan
curl -X POST https://your-app.railway.app/api/generate-meal-plan \
  -H "Content-Type: application/json" \
  -d '{"query": "3-day vegetarian meal plan", "generation_mode": "fast_llm"}'
```

### Test Frontend

1. Visit: `https://yourusername.github.io/ml_meal_prep/`
2. Enter your Railway URL in the "API Endpoint" field
3. Select "Fast LLM" strategy
4. Try: "Create a 2 day meal plan"
5. Should generate in ~20-30 seconds

## Updating Your Deployment

### Update Backend (Railway)

Railway auto-deploys when you push to GitHub:

```bash
# Make your changes
git add .
git commit -m "Your changes"
git push
```

Railway will:
1. Detect the push
2. Rebuild the Docker image
3. Deploy automatically (takes 2-3 minutes)

Watch deployment in Railway dashboard → "Deployments" tab

### Update Frontend (GitHub Pages)

Same process - just push to GitHub:

```bash
git add .
git commit -m "Update frontend"
git push
```

GitHub Actions will:
1. Detect the push
2. Build and deploy
3. Live in ~1 minute

Watch deployment in GitHub → "Actions" tab

## Troubleshooting

### Railway Issues

**"Application won't start"**
- Check Railway logs: Dashboard → Your Service → "Logs"
- Verify `OPENAI_API_KEY` is set in Variables
- Check Dockerfile is in repository root

**"500 Internal Server Error"**
- Check Railway logs for Python errors
- Verify all required files are committed
- Check `requirements.txt` includes all dependencies

**"fast_llm strategy fails"**
- Make sure latest code is deployed
- Check Railway logs for error details
- Verify `main.py` includes all 4 strategies in valid_modes

### Frontend Issues

**"Failed to fetch"**
- Check API URL is correct (include https://)
- Verify Railway API is running (health check)
- Check browser console for CORS errors

**"Deployment failed" in GitHub Actions**
- Go to GitHub → Actions tab
- Click the failed deployment
- Check error logs

### Database Issues

**"Database connection failed"**
- Verify PostgreSQL is added in Railway
- Check `DATABASE_URL` is set automatically
- Railway sets this - don't manually add it

## Cost Estimates

### Railway (Free Tier)

- $5 free credit per month
- Enough for development and light production use
- Hobby plan: $5/month for production

### GitHub Pages

- Free for public repositories
- No bandwidth limits for normal use

### OpenAI API

- GPT-4o-mini: ~$0.0001-0.0002 per call
- 7-day plan: ~$0.02-0.04
- $5 free credit for new accounts

## Production Checklist

Before going live:

- [ ] Railway deployment successful
- [ ] Environment variables set (OPENAI_API_KEY)
- [ ] Health check returns 200: `/health`
- [ ] Database connected (if using PostgreSQL)
- [ ] Frontend deployed to GitHub Pages
- [ ] API URL configured in frontend
- [ ] Test all 4 strategies work
- [ ] Test 1-day, 3-day, 7-day plans
- [ ] Check Railway logs are clean

## Architecture

```
User Browser
    ↓
GitHub Pages (Frontend)
    ↓ HTTPS
Railway (Backend API)
    ↓
PostgreSQL (Railway)
    ↓
OpenAI API
```

Simple and production-ready!

## Monitoring

### Railway Dashboard

- View logs: Real-time application logs
- Check metrics: CPU, Memory, Network usage
- Monitor deployments: Build status and history

### Health Checks

Railway automatically monitors `/health` endpoint. If it fails, Railway restarts the service.

## Support

**Railway Issues**: https://railway.app/help  
**GitHub Pages**: https://docs.github.com/en/pages  
**API Documentation**: Visit `/docs` on your Railway URL

---

That's it! Your meal planner is now deployed and accessible worldwide.
