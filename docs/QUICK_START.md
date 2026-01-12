# Quick Start Guide

Get your Meal Planner API and Frontend up and running in minutes!

## 🎯 Complete Setup (API + Frontend)

### Step 1: Deploy API to Railway (~5 min)

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Deploy
cd ml_meal_prep
railway init
railway up
```

**Set environment variable:**
- Go to Railway dashboard
- Add: `OPENAI_API_KEY` = `your_key_here`

**Get your API URL:**
- Railway provides: `https://your-app.railway.app`
- Test: `https://your-app.railway.app/health`

---

### Step 2: Deploy Frontend to GitHub Pages (~3 min)

**Option A: Using the script (easiest)**
```bash
./deploy-frontend.sh
# Enter your Railway URL when prompted
git add docs/
git commit -m "Deploy frontend"
git push
```

**Option B: Manual**
```bash
mkdir -p docs
cp -r frontend/* docs/

# Update API URL (optional)
# Edit docs/app.js and change DEFAULT_API_URL to your Railway URL

git add docs/
git commit -m "Deploy frontend to GitHub Pages"
git push
```

**Enable GitHub Pages:**
1. Go to GitHub → Your Repo → Settings → Pages
2. Source: Deploy from branch
3. Branch: `main`
4. Folder: `/docs`
5. Save

**Your frontend will be at:**
```
https://yourusername.github.io/ml_meal_prep/
```

---

## ✅ You're Done!

- **API**: `https://your-app.railway.app`
- **Frontend**: `https://yourusername.github.io/ml_meal_prep/`
- **API Docs**: `https://your-app.railway.app/docs`

---

## 🧪 Test It

1. Visit your GitHub Pages URL
2. Enter a query like: "Create a 3-day vegetarian meal plan"
3. Click "Generate Meal Plan"
4. Enjoy your personalized meal plan! 🍽️

---

## 🔧 Troubleshooting

### Frontend can't connect to API
- Check that Railway API is running: `https://your-app.railway.app/health`
- Verify CORS is enabled (it should be by default)
- Make sure you entered the correct Railway URL in the frontend

### GitHub Pages not updating
- Wait 1-2 minutes for GitHub to rebuild
- Clear browser cache
- Check GitHub Actions tab for build status

### API returns errors
- Verify `OPENAI_API_KEY` is set in Railway
- Check Railway logs for detailed errors
- Test API directly at `/docs` endpoint

---

## 🔄 Making Updates After Deployment

After you make changes to your code:

1. **Update API (Railway)**:
   ```bash
   # If Railway connected to GitHub (automatic):
   git add .
   git commit -m "Your changes"
   git push  # Railway auto-deploys!
   
   # If NOT connected (manual):
   railway up
   ```

2. **Update Frontend (GitHub Pages)**:
   ```bash
   ./deploy-frontend.sh
   git add docs/
   git commit -m "Update frontend"
   git push  # GitHub Pages auto-deploys!
   ```

**See [UPDATE_DEPLOYMENT.md](UPDATE_DEPLOYMENT.md) for detailed update instructions.**

---

## 📚 More Details

- Full deployment guide: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Updating deployments**: See [UPDATE_DEPLOYMENT.md](UPDATE_DEPLOYMENT.md) ⭐
- Frontend setup: See `../frontend/README.md`
- API documentation: Visit `/docs` on your Railway URL

