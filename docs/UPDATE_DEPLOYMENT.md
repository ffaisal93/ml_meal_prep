# Updating Your Deployment

Guide for updating your deployed API and frontend after making code changes.

## 🔄 Update Workflow

After making changes to your code, you need to update both:
1. **API (Railway)** - Backend changes
2. **Frontend (GitHub Pages)** - Frontend changes

---

## 🚂 Updating Railway API

### Option 1: Automatic (Recommended - Git Connected)

If you connected Railway to your GitHub repo:

1. **Make your changes locally**
   ```bash
   # Edit your code files
   # Test locally first!
   ```

2. **Commit and push to GitHub**
   ```bash
   git add .
   git commit -m "Fix: Add meal_type and fix instructions format"
   git push origin main
   ```

3. **Railway auto-deploys**
   - Railway detects the push
   - Automatically rebuilds and redeploys
   - Takes ~2-5 minutes
   - Check Railway dashboard for status

**That's it!** Railway handles everything automatically.

### Option 2: Manual (Railway CLI)

If Railway is NOT connected to GitHub:

1. **Make your changes locally**
   ```bash
   # Edit your code files
   # Test locally first!
   ```

2. **Deploy with Railway CLI**
   ```bash
   cd /Users/faisal/Projects/ml_meal_prep
   railway up
   ```

3. **Wait for deployment**
   - Railway builds new Docker image
   - Deploys the new version
   - Takes ~2-5 minutes

### Check Deployment Status

- **Railway Dashboard**: https://railway.app/dashboard
  - Click your project
  - View "Deployments" tab
  - See build logs and status

- **Test the update**:
  ```bash
  curl https://your-app.railway.app/health
  ```

---

## 🌐 Updating GitHub Pages Frontend

### If Frontend Code Changed

1. **Make your changes**
   ```bash
   # Edit files in frontend/ directory
   ```

2. **Deploy updated frontend**
   ```bash
   cd /Users/faisal/Projects/ml_meal_prep
   
   # Option A: Use the script
   ./deploy-frontend.sh
   # Enter Railway URL if prompted
   
   # Option B: Manual
   mkdir -p docs
   cp -r frontend/* docs/
   
   # Commit and push
   git add docs/
   git commit -m "Update frontend: [describe changes]"
   git push origin main
   ```

3. **Wait for GitHub Pages**
   - GitHub rebuilds automatically
   - Takes ~1-2 minutes
   - Check: Settings → Pages → See deployment status

### If Only API URL Changed

If you just need to update the Railway API URL in the frontend:

1. **Edit the frontend**
   ```bash
   # Edit frontend/app.js
   # Change DEFAULT_API_URL to your new Railway URL
   ```

2. **Redeploy frontend** (same as above)

---

## 📋 Complete Update Checklist

### After Making Code Changes:

- [ ] **Test locally first**
  ```bash
  # Make sure it works locally
  uvicorn app.main:app --reload
  # Test at http://localhost:8000/docs
  ```

- [ ] **Commit changes**
  ```bash
  git add .
  git commit -m "Description of changes"
  git push origin main
  ```

- [ ] **Railway auto-deploys** (if connected to GitHub)
  - Or run `railway up` manually
  - Wait ~2-5 minutes
  - Check Railway dashboard

- [ ] **Update frontend if needed**
  ```bash
  ./deploy-frontend.sh
  git add docs/
  git commit -m "Update frontend"
  git push
  ```

- [ ] **Verify deployment**
  - Test API: `https://your-app.railway.app/health`
  - Test Frontend: `https://yourusername.github.io/ml_meal_prep/`

---

## ⚙️ Updating Environment Variables (Strategy Configuration)

### Changing Recipe Generation Strategy

If you want to switch between `llm_only`, `rag`, or `hybrid` modes:

1. **Go to Railway Dashboard**
   - Select your project → Your service → **Variables** tab

2. **Update Strategy Mode**
   ```
   RECIPE_GENERATION_MODE=rag  # Change to desired mode
   ```

3. **If Switching to RAG/Hybrid, Add Edamam Credentials**
   ```
   EDAMAM_APP_ID=your_app_id
   EDAMAM_APP_KEY=your_app_key
   EDAMAM_USER_ID=your_user_id  # Optional
   ```

4. **If Using Hybrid Mode, Set Ratio**
   ```
   HYBRID_RAG_RATIO=0.7  # 70% RAG, 30% LLM-only
   ```

5. **Railway Auto-Redeploys**
   - Changes take effect immediately
   - No code changes needed!

### Removing Edamam Credentials (Switch to LLM-Only)

1. **Update mode:**
   ```
   RECIPE_GENERATION_MODE=llm_only
   ```

2. **Remove Edamam variables** (optional, but recommended):
   - Delete `EDAMAM_APP_ID`
   - Delete `EDAMAM_APP_KEY`
   - Delete `EDAMAM_USER_ID`

3. **Railway auto-redeploys**

**Note:** The API will work fine without Edamam credentials if `RECIPE_GENERATION_MODE=llm_only`.

---

## 🔍 Troubleshooting Updates

### Railway Not Updating

**Problem**: Changes not reflected after push

**Solutions**:
1. Check Railway dashboard → Deployments tab
2. Look for failed builds (red status)
3. Check build logs for errors
4. Try manual deploy: `railway up`
5. Verify git push succeeded: `git log --oneline`

### GitHub Pages Not Updating

**Problem**: Frontend changes not showing

**Solutions**:
1. Wait 1-2 minutes (GitHub needs time to rebuild)
2. Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)
3. Check GitHub Actions tab for build status
4. Verify `docs/` folder was updated: `git status`
5. Check GitHub Pages settings: Settings → Pages

### API Changes Not Working

**Problem**: API updated but still getting old behavior

**Solutions**:
1. Check Railway deployment status (should be "Active")
2. Verify the new code was actually pushed: `git log`
3. Check Railway logs for errors
4. Test API directly: `curl https://your-app.railway.app/health`
5. Restart Railway service (in dashboard)

---

## 🚀 Best Practices

### 1. Test Locally First
Always test changes locally before deploying:
```bash
# Test API
uvicorn app.main:app --reload
# Visit http://localhost:8000/docs

# Test frontend
cd frontend
python3 -m http.server 8080
# Visit http://localhost:8080
```

### 2. Use Meaningful Commit Messages
```bash
git commit -m "Fix: Add meal_type field to recipes"
git commit -m "Feature: Add caching for recipe generation"
git commit -m "Update: Improve error handling"
```

### 3. Check Deployment Logs
- Railway: Dashboard → Deployments → View logs
- GitHub Pages: Actions tab → See build logs

### 4. Monitor After Deployment
- Test the live API immediately
- Test the frontend
- Check for errors in logs

---

## 📝 Quick Reference

### Update API Only
```bash
# If Railway connected to GitHub:
git add app/
git commit -m "Update API"
git push

# If NOT connected:
railway up
```

### Update Frontend Only
```bash
./deploy-frontend.sh
git add docs/
git commit -m "Update frontend"
git push
```

### Update Both
```bash
# 1. Update API
git add app/
git commit -m "Update API"
git push  # Railway auto-deploys

# 2. Update Frontend
./deploy-frontend.sh
git add docs/
git commit -m "Update frontend"
git push  # GitHub Pages auto-deploys
```

---

## 🔗 Useful Links

- **Railway Dashboard**: https://railway.app/dashboard
- **GitHub Repository**: Your repo URL
- **GitHub Pages Settings**: Your repo → Settings → Pages
- **Railway Logs**: Dashboard → Your project → Deployments → View logs

---

**Remember**: Always test locally first, then deploy! 🚀

