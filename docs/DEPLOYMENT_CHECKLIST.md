# Deployment Checklist: Recipe Generation Strategies

Quick checklist for deploying the new modular recipe generation system.

## ✅ Pre-Deployment Checklist

### 1. Code Changes
- [x] Modular strategy pattern implemented
- [x] All strategies created (LLM-only, RAG, Hybrid)
- [x] Factory pattern for strategy selection
- [x] Configuration updated
- [x] Documentation updated

### 2. Dependencies
- [x] `httpx` already in `requirements.txt` ✅
- [x] No new dependencies needed ✅

---

## 🚂 Railway Deployment Steps

### Step 1: Push Code to GitHub

```bash
cd /Users/faisal/Projects/ml_meal_prep
git add .
git commit -m "Add modular recipe generation strategies"
git push origin main
```

**Railway will automatically detect and deploy** (if connected to GitHub).

### Step 2: Set Environment Variables

Go to **Railway Dashboard** → Your Project → Your Service → **Variables** tab

#### Minimum Required (LLM-Only Mode)

```bash
OPENAI_API_KEY=your_openai_key_here
```

This is enough! The system defaults to `llm_only` mode.

#### Optional: Set Strategy Mode Explicitly

```bash
RECIPE_GENERATION_MODE=llm_only  # Default, optional to set
```

#### For RAG Mode

Add these variables:

```bash
RECIPE_GENERATION_MODE=rag
EDAMAM_APP_ID=your_edamam_app_id
EDAMAM_APP_KEY=your_edamam_app_key
EDAMAM_USER_ID=your_user_id  # Optional, defaults to App ID
```

#### For Hybrid Mode

Add these variables:

```bash
RECIPE_GENERATION_MODE=hybrid
HYBRID_RAG_RATIO=0.7  # 70% RAG, 30% LLM-only
EDAMAM_APP_ID=your_edamam_app_id
EDAMAM_APP_KEY=your_edamam_app_key
EDAMAM_USER_ID=your_user_id  # Optional
```

### Step 3: Verify Deployment

1. **Check Railway Logs**
   - Dashboard → Deployments → Latest → View Logs
   - Look for: "Application startup complete"
   - No errors about missing Edamam credentials (if using LLM-only)

2. **Test Health Endpoint**
   ```bash
   curl https://your-app.railway.app/health
   ```

3. **Test Recipe Generation**
   ```bash
   curl -X POST https://your-app.railway.app/api/generate-meal-plan \
     -H "Content-Type: application/json" \
     -d '{"query": "Create a 2-day vegetarian meal plan"}'
   ```

---

## 🔄 Switching Strategies (After Deployment)

### Switch from LLM-Only to RAG

1. **Get Edamam Credentials**
   - Go to [Edamam Developer Portal](https://developer.edamam.com/admin/applications)
   - Create Recipe Search API application
   - Copy App ID and App Key

2. **Add Variables in Railway**
   ```
   RECIPE_GENERATION_MODE=rag
   EDAMAM_APP_ID=your_app_id
   EDAMAM_APP_KEY=your_app_key
   ```

3. **Railway Auto-Redeploys**
   - No code changes needed!
   - Takes ~2-5 minutes

### Switch from RAG to Hybrid

1. **Update Variable in Railway**
   ```
   RECIPE_GENERATION_MODE=hybrid
   HYBRID_RAG_RATIO=0.7  # Optional, defaults to 0.7
   ```

2. **Railway Auto-Redeploys**

### Switch Back to LLM-Only

1. **Update Variable**
   ```
   RECIPE_GENERATION_MODE=llm_only
   ```

2. **Remove Edamam Variables** (optional, but recommended)
   - Delete `EDAMAM_APP_ID`
   - Delete `EDAMAM_APP_KEY`
   - Delete `EDAMAM_USER_ID`

3. **Railway Auto-Redeploys**

---

## 📋 Environment Variables Reference

| Variable | Required | Default | When Needed |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ Yes | - | Always |
| `RECIPE_GENERATION_MODE` | No | `llm_only` | Optional (defaults work) |
| `EDAMAM_APP_ID` | Conditional | - | RAG or Hybrid mode |
| `EDAMAM_APP_KEY` | Conditional | - | RAG or Hybrid mode |
| `EDAMAM_USER_ID` | No | App ID | RAG or Hybrid mode (optional) |
| `HYBRID_RAG_RATIO` | No | `0.7` | Hybrid mode only |

---

## 🐛 Common Issues & Solutions

### Issue: "Edamam credentials required"

**Cause:** Using RAG/hybrid mode without Edamam credentials.

**Solution:**
- Option 1: Add Edamam credentials
- Option 2: Set `RECIPE_GENERATION_MODE=llm_only`

### Issue: "Authentication failed: 401" (Edamam)

**Cause:** Invalid Edamam credentials.

**Solution:**
- Verify credentials are correct
- Check you're using Recipe Search API (not Food Database)
- Ensure User ID is set if required

### Issue: Deployment fails

**Cause:** Build errors or missing dependencies.

**Solution:**
- Check Railway logs for specific errors
- Verify all files are committed
- Ensure `requirements.txt` is up to date

---

## 📊 What Changed

### Code Structure
- ✅ New `app/recipe_generation/` directory
- ✅ Strategy pattern implementation
- ✅ Factory for strategy selection
- ✅ Updated `recipe_service.py` to use strategies
- ✅ Updated `meal_generator.py` to async
- ✅ Updated `main.py` to handle async

### Configuration
- ✅ New `RECIPE_GENERATION_MODE` setting
- ✅ New `HYBRID_RAG_RATIO` setting
- ✅ New Edamam credential settings

### Dependencies
- ✅ No new dependencies (`httpx` already included)

### Backward Compatibility
- ✅ Defaults to `llm_only` mode (existing behavior)
- ✅ Works without Edamam credentials
- ✅ No breaking changes

---

## 🎯 Recommended Setup

### For Testing/Evaluation
```bash
RECIPE_GENERATION_MODE=llm_only  # Simplest, no external API needed
```

### For Production
```bash
RECIPE_GENERATION_MODE=rag  # Best quality, realistic nutrition
EDAMAM_APP_ID=your_app_id
EDAMAM_APP_KEY=your_app_key
```

### For Experimentation
```bash
RECIPE_GENERATION_MODE=hybrid
HYBRID_RAG_RATIO=0.7
EDAMAM_APP_ID=your_app_id
EDAMAM_APP_KEY=your_app_key
```

---

## 📚 Documentation

- **[Recipe Generation Strategies](RECIPE_GENERATION_STRATEGIES.md)** - Complete guide
- **[Railway Recipe Strategies](RAILWAY_RECIPE_STRATEGIES.md)** - Railway-specific guide
- **[Deployment Guide](DEPLOYMENT.md)** - General deployment instructions
- **[Update Deployment](UPDATE_DEPLOYMENT.md)** - How to update after changes

---

## ✅ Final Checklist

Before considering deployment complete:

- [ ] Code pushed to GitHub
- [ ] Railway deployment successful
- [ ] Environment variables set correctly
- [ ] Health endpoint returns 200
- [ ] Recipe generation works
- [ ] Strategy mode matches configuration
- [ ] No errors in Railway logs

---

**Ready to deploy!** 🚀

