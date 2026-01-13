# Railway Deployment: Recipe Generation Strategies

Quick guide for deploying and configuring recipe generation strategies on Railway.

## 🚀 Quick Setup

### Step 1: Deploy to Railway (if not already deployed)

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `ml_meal_prep` repository
5. Railway will auto-detect Dockerfile and deploy

### Step 2: Set Environment Variables

Go to your Railway project → Select your service → **Variables** tab

#### Required Variables (All Modes)

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

#### Optional: Recipe Generation Mode

**Default:** `llm_only` (works without Edamam credentials)

```bash
RECIPE_GENERATION_MODE=llm_only
```

**Options:**
- `llm_only` - Pure LLM generation (default, no Edamam needed)
- `rag` - Edamam candidates + LLM refinement
- `hybrid` - Mix of RAG and LLM-only

#### Required for RAG/Hybrid Modes

If you set `RECIPE_GENERATION_MODE=rag` or `hybrid`, you **must** add:

```bash
EDAMAM_APP_ID=your_edamam_app_id
EDAMAM_APP_KEY=your_edamam_app_key
EDAMAM_USER_ID=your_user_id  # Optional, defaults to App ID
```

**Get Edamam Credentials:**
1. Go to [Edamam Developer Portal](https://developer.edamam.com/admin/applications)
2. Create a new application
3. Select **"Recipe Search API"** (NOT Food Database API)
4. Copy Application ID and Application Key

#### Optional: Hybrid Ratio (Only for Hybrid Mode)

```bash
HYBRID_RAG_RATIO=0.7  # 70% RAG, 30% LLM-only (0.0 to 1.0)
```

---

## 📋 Complete Variable List

### Minimal Setup (LLM-Only Mode)

```bash
OPENAI_API_KEY=sk-...
RECIPE_GENERATION_MODE=llm_only  # Optional, this is the default
```

### RAG Mode Setup

```bash
OPENAI_API_KEY=sk-...
RECIPE_GENERATION_MODE=rag
EDAMAM_APP_ID=849b2f09
EDAMAM_APP_KEY=03f610b9ee11c45c07fe371a90d8e1f6
EDAMAM_USER_ID=849b2f09  # Optional
```

### Hybrid Mode Setup

```bash
OPENAI_API_KEY=sk-...
RECIPE_GENERATION_MODE=hybrid
HYBRID_RAG_RATIO=0.7
EDAMAM_APP_ID=849b2f09
EDAMAM_APP_KEY=03f610b9ee11c45c07fe371a90d8e1f6
EDAMAM_USER_ID=849b2f09  # Optional
```

---

## 🔄 Changing Strategies

### Switch from LLM-Only to RAG

1. Go to Railway Dashboard → Your Project → Variables
2. Add Edamam credentials:
   ```
   EDAMAM_APP_ID=your_app_id
   EDAMAM_APP_KEY=your_app_key
   ```
3. Update mode:
   ```
   RECIPE_GENERATION_MODE=rag
   ```
4. Railway will automatically redeploy

### Switch from RAG to Hybrid

1. Update mode:
   ```
   RECIPE_GENERATION_MODE=hybrid
   ```
2. Add ratio (optional):
   ```
   HYBRID_RAG_RATIO=0.7
   ```
3. Railway will automatically redeploy

**No code changes needed!** The factory pattern handles strategy selection.

---

## ✅ Verification

### 1. Check Deployment Logs

Railway Dashboard → Your Service → **Deployments** → Click latest deployment → **View Logs**

Look for:
- ✅ "Application startup complete"
- ✅ "Database initialized"
- ✅ No errors about missing Edamam credentials (if using RAG/hybrid)

### 2. Test Health Endpoint

```bash
curl https://your-app.railway.app/health
```

Expected:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-15T10:30:00"
}
```

### 3. Test Recipe Generation

```bash
curl -X POST https://your-app.railway.app/api/generate-meal-plan \
  -H "Content-Type: application/json" \
  -d '{"query": "Create a 2-day vegetarian meal plan"}'
```

---

## 🐛 Troubleshooting

### Error: "Edamam credentials required"

**Problem:** Using RAG/hybrid mode without Edamam credentials.

**Solution:**
- Option 1: Add Edamam credentials to Railway Variables
- Option 2: Change `RECIPE_GENERATION_MODE=llm_only` (works without Edamam)

### Error: "Authentication failed: 401" (Edamam)

**Problem:** Invalid Edamam credentials.

**Solution:**
- Verify `EDAMAM_APP_ID` and `EDAMAM_APP_KEY` are correct
- Check you're using Recipe Search API credentials (not Food Database)
- Ensure `EDAMAM_USER_ID` is set if your app requires it

### Error: "No candidates found"

**Problem:** Edamam API returns 0 results (query too restrictive).

**Solution:**
- This is normal - RAG strategy automatically falls back to LLM-only
- Check Railway logs for details
- Try a less restrictive query

### Deployment Fails

**Problem:** Build errors or deployment issues.

**Solution:**
1. Check Railway logs for specific errors
2. Verify all files are committed to git
3. Ensure Dockerfile is in root directory
4. Check that `requirements.txt` includes all dependencies

---

## 📊 Monitoring

### View Logs

Railway Dashboard → Your Service → **Logs** tab

### Monitor API Usage

- **OpenAI:** Check OpenAI dashboard for usage
- **Edamam:** Check Edamam dashboard for API usage (free tier: 10,000 requests/month)

### Check Strategy in Use

The API doesn't expose which strategy is active, but you can check:
- Railway Variables → `RECIPE_GENERATION_MODE`
- Recipe responses will have different characteristics:
  - **LLM-only:** More creative, variable nutrition
  - **RAG:** More realistic nutrition, grounded in real recipes
  - **Hybrid:** Mix of both

---

## 💰 Cost Considerations

### LLM-Only Mode
- **OpenAI API:** ~$0.01-0.02 per meal plan
- **Edamam API:** $0 (not used)

### RAG Mode
- **OpenAI API:** ~$0.01-0.02 per meal plan
- **Edamam API:** Free tier (10,000 requests/month)
- **Efficiency:** Only 2-4 API calls per meal plan (one per unique meal type)

### Hybrid Mode
- **OpenAI API:** ~$0.01-0.02 per meal plan
- **Edamam API:** Depends on `HYBRID_RAG_RATIO` (70% = 70% of recipes use Edamam)
- **Efficiency:** Similar to RAG, but fewer Edamam calls

---

## 🔗 Related Documentation

- **[Recipe Generation Strategies](RECIPE_GENERATION_STRATEGIES.md)** - Detailed strategy documentation
- **[Deployment Guide](DEPLOYMENT.md)** - Complete deployment instructions
- **[Update Deployment](UPDATE_DEPLOYMENT.md)** - How to update after changes

---

**Need help?** Check Railway logs or the main documentation.

