# Deployment Guide

This guide provides step-by-step instructions for deploying the Meal Planner API to various platforms, plus the frontend to GitHub Pages.

## 🎯 Complete Deployment (API + Frontend)

**Recommended Setup:**
- **API**: Deploy to Railway (easiest, free tier)
- **Frontend**: Deploy to GitHub Pages (free, automatic)

This gives you:
- Public API: `https://your-app.railway.app`
- Public Frontend: `https://yourusername.github.io/ml_meal_prep/`

---

## 📄 GitHub Pages (Frontend)

**Time: ~5 minutes**

1. **Prepare frontend files:**
   ```bash
   cd ml_meal_prep
   mkdir -p docs
   cp -r frontend/* docs/
   ```

2. **Update API URL (optional):**
   - Edit `docs/app.js` (or `frontend/app.js` before copying)
   - Change `DEFAULT_API_URL` to your Railway URL:
     ```javascript
     const DEFAULT_API_URL = 'https://your-app.railway.app';
     ```

3. **Commit and push:**
   ```bash
   git add docs/
   git commit -m "Deploy frontend to GitHub Pages"
   git push
   ```

4. **Enable GitHub Pages:**
   - Go to your repository on GitHub
   - Settings → Pages
   - Source: Deploy from a branch
   - Branch: `main` (or your default)
   - Folder: `/docs`
   - Click Save

5. **Access your site:**
   - GitHub will provide: `https://yourusername.github.io/ml_meal_prep/`
   - Wait 1-2 minutes for first deployment

**Alternative: Automatic Deployment with GitHub Actions**
- The included `.github/workflows/deploy-pages.yml` will automatically deploy when you push to `main`
- Just enable GitHub Pages in Settings → Pages (no need to select folder)

---

## 🚂 Railway (API Backend)

## Prerequisites

- OpenAI API key
- GitHub account (for cloud deployments)
- Docker installed (for local Docker testing)

## Quick Deployment Options

### 🚂 Railway (Recommended - Easiest)

**Time: ~5 minutes**

1. **Install Railway CLI:**
   ```bash
   npm i -g @railway/cli
   ```

2. **Login:**
   ```bash
   railway login
   ```

3. **Initialize and deploy:**
   ```bash
   cd ml_meal_prep
   railway init
   railway up
   ```

4. **Set environment variables:**
   - Go to https://railway.app/dashboard
   - Select your project
   - Go to Variables tab
   - Add required variables:
     ```
     OPENAI_API_KEY=your_openai_key_here
     ```
   - **Optional - Recipe Generation Strategy:**
     ```
     RECIPE_GENERATION_MODE=llm_only  # Options: "llm_only", "rag", "hybrid"
     ```
   - **If using RAG or Hybrid mode, also add:**
     ```
     EDAMAM_APP_ID=your_edamam_app_id
     EDAMAM_APP_KEY=your_edamam_app_key
     EDAMAM_USER_ID=your_user_id  # Optional, defaults to App ID
     ```
   - **If using Hybrid mode, also add:**
     ```
     HYBRID_RAG_RATIO=0.7  # Ratio of RAG recipes (0.0 to 1.0)
     ```

5. **Get your URL:**
   - Railway provides a public URL automatically
   - Example: `https://your-app-name.railway.app`
   - Test: `https://your-app-name.railway.app/health`

**Railway automatically:**
- Detects Dockerfile
- Builds and deploys
- Provides HTTPS
- Handles scaling

---

### 🎨 Render (Free Tier - No CLI Needed)

**Time: ~10 minutes**

1. **Go to Render Dashboard:**
   - Visit https://render.com
   - Sign up/login with GitHub

2. **Create New Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the `ml_meal_prep` repository

3. **Configure Service:**
   - **Name:** `ml-meal-prep-api` (or your choice)
   - **Environment:** `Docker`
   - **Region:** Choose closest to you
   - **Branch:** `main` (or your default branch)
   - **Dockerfile Path:** `./Dockerfile`
   - **Docker Context:** `.`

4. **Set Environment Variables:**
   - Click "Environment" tab
   - Add: `OPENAI_API_KEY` = `your_key_here`
   - Add: `API_PORT` = `$PORT` (Render sets this automatically)
   - **Optional:** Add `RECIPE_GENERATION_MODE` = `rag` (or `llm_only`, `hybrid`)
   - **If using RAG/hybrid:** Add Edamam credentials (`EDAMAM_APP_ID`, `EDAMAM_APP_KEY`)

5. **Deploy:**
   - Click "Create Web Service"
   - Render will build and deploy automatically
   - Wait ~5-10 minutes for first deployment

6. **Get your URL:**
   - Render provides: `https://your-app-name.onrender.com`
   - Test: `https://your-app-name.onrender.com/health`

**Note:** Render free tier spins down after 15 minutes of inactivity. First request may take ~30 seconds.

---

### 🪂 Fly.io (Free Tier)

**Time: ~10 minutes**

1. **Install Fly CLI:**
   ```bash
   # macOS
   brew install flyctl
   
   # Linux/Windows
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login:**
   ```bash
   fly auth login
   ```

3. **Initialize:**
   ```bash
   cd ml_meal_prep
   fly launch
   ```
   - Choose app name (or auto-generate)
   - Select region
   - Don't deploy yet (we need to set secrets first)

4. **Set secrets:**
   ```bash
   fly secrets set OPENAI_API_KEY=your_key_here
   # Optional: Set recipe generation mode
   fly secrets set RECIPE_GENERATION_MODE=rag
   # If using RAG/hybrid, also set Edamam credentials
   fly secrets set EDAMAM_APP_ID=your_app_id EDAMAM_APP_KEY=your_app_key
   ```

5. **Deploy:**
   ```bash
   fly deploy
   ```

6. **Get your URL:**
   ```bash
   fly open
   ```
   - Or visit: `https://your-app-name.fly.dev`
   - Test: `https://your-app-name.fly.dev/health`

---

### 🐳 Local Docker (For Testing)

**Time: ~2 minutes**

1. **Create .env file:**
   ```bash
   cd ml_meal_prep
   cat > .env << EOF
   OPENAI_API_KEY=your_key_here
   RECIPE_GENERATION_MODE=llm_only
   # If using RAG/hybrid, uncomment and add:
   # EDAMAM_APP_ID=your_app_id
   # EDAMAM_APP_KEY=your_app_key
   EOF
   ```

2. **Build and run:**
   ```bash
   docker-compose up --build
   ```

3. **Test:**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

---

### 🚀 Heroku (Paid, but Simple)

**Time: ~5 minutes**

1. **Install Heroku CLI:**
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku
   ```

2. **Login:**
   ```bash
   heroku login
   ```

3. **Create app:**
   ```bash
   cd ml_meal_prep
   heroku create your-app-name
   ```

4. **Set config:**
   ```bash
   heroku config:set OPENAI_API_KEY=your_key_here
   # Optional: Set recipe generation mode
   heroku config:set RECIPE_GENERATION_MODE=rag
   # If using RAG/hybrid, also set Edamam credentials
   heroku config:set EDAMAM_APP_ID=your_app_id EDAMAM_APP_KEY=your_app_key
   ```

5. **Deploy:**
   ```bash
   git push heroku main
   ```

6. **Open:**
   ```bash
   heroku open
   ```

---

## Environment Variables

All platforms require:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ Yes | - | Your OpenAI API key |
| `API_HOST` | No | `0.0.0.0` | Host to bind to |
| `API_PORT` | No | `8000` | Port (use `$PORT` on cloud platforms) |
| `CACHE_TTL_SECONDS` | No | `3600` | Cache TTL in seconds |
| `RECIPE_GENERATION_MODE` | No | `llm_only` | Recipe generation strategy: `"llm_only"`, `"rag"`, or `"hybrid"` |
| `HYBRID_RAG_RATIO` | No | `0.7` | For hybrid mode: ratio of RAG recipes (0.0 to 1.0) |
| `EDAMAM_APP_ID` | Conditional | - | Required for RAG/hybrid modes: Edamam Application ID |
| `EDAMAM_APP_KEY` | Conditional | - | Required for RAG/hybrid modes: Edamam Application Key |
| `EDAMAM_USER_ID` | No | App ID | Optional: Edamam User ID (defaults to App ID) |

---

## Testing Your Deployment

### 1. Health Check
```bash
curl https://your-app-url.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-15T10:30:00"
}
```

### 2. Generate Meal Plan
```bash
curl -X POST https://your-app-url.com/api/generate-meal-plan \
  -H "Content-Type: application/json" \
  -d '{"query": "Create a 3-day vegetarian meal plan"}'
```

### 3. View API Docs
Visit: `https://your-app-url.com/docs`

---

## Troubleshooting

### Issue: "OPENAI_API_KEY not found"
**Solution:** Make sure you set the environment variable in your platform's dashboard/CLI.

### Issue: "Port already in use" (local)
**Solution:** Change port in `.env` or docker-compose.yml:
```bash
API_PORT=8001
```

### Issue: Build fails on cloud platform
**Solution:** 
- Check Dockerfile is in root directory
- Verify all files are committed to git
- Check platform logs for specific errors

### Issue: API returns 500 errors
**Solution:**
- Check OpenAI API key is valid
- Verify you have API credits
- Check platform logs for detailed errors

### Issue: Slow responses (Render free tier)
**Solution:** This is normal - Render free tier spins down after inactivity. First request takes ~30 seconds.

---

## Cost Estimates

### Platform Costs
- **Railway:** Free tier available (limited hours/month)
- **Render:** Free tier available (spins down after inactivity)
- **Fly.io:** Free tier available (limited resources)
- **Heroku:** Paid ($7/month minimum)

### API Costs (OpenAI)
- **GPT-4o-mini:** ~$0.01-0.02 per meal plan
- **With caching:** ~$0.003-0.006 per meal plan
- **Free tier:** $5 credit for new accounts

---

## Recommended for Evaluators

**For easiest testing, use Railway:**
1. Fastest setup (~5 minutes)
2. Automatic HTTPS
3. No credit card required (free tier)
4. Easy environment variable management
5. Real-time logs

**Alternative: Render**
- No CLI needed
- Free tier available
- Slightly slower first request (cold start)

---

## Next Steps After Deployment

1. ✅ Test health endpoint
2. ✅ Test meal plan generation
3. ✅ Check API documentation at `/docs`
4. ✅ Test with all example queries from assignment
5. ✅ Monitor logs for any errors

Your API is now live and ready for evaluation! 🎉

