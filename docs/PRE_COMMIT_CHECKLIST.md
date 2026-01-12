# Pre-Commit Checklist

Verify what to commit before pushing to GitHub.

## ✅ Files That SHOULD Be Committed

### Core Application Code
- [ ] `app/__init__.py`
- [ ] `app/config.py`
- [ ] `app/main.py`
- [ ] `app/models.py`
- [ ] `app/query_parser.py`
- [ ] `app/recipe_service.py`
- [ ] `app/meal_generator.py`

### Frontend
- [ ] `frontend/index.html`
- [ ] `frontend/app.js`
- [ ] `frontend/styles.css`
- [ ] `frontend/README.md`

### Configuration Files
- [ ] `requirements.txt` ⭐ (Railway needs this!)
- [ ] `Dockerfile` ⭐ (Railway needs this!)
- [ ] `docker-compose.yml`
- [ ] `railway.json` ⭐ (Railway config)
- [ ] `render.yaml`
- [ ] `.gitignore` ⭐ (Important!)

### Documentation
- [ ] `README.md`
- [ ] `docs/` folder (all documentation)
- [ ] `ENV_EXAMPLE.txt` (template, safe to commit)

### Scripts
- [ ] `setup.sh`
- [ ] `test_api.sh`
- [ ] `deploy-frontend.sh`
- [ ] `organize_docs.sh`

## ❌ Files That SHOULD NOT Be Committed

These are already in `.gitignore`:

- [ ] `.env` ❌ (Contains your API key!)
- [ ] `venv/` ❌ (Virtual environment)
- [ ] `__pycache__/` ❌ (Python cache)
- [ ] `.DS_Store` ❌ (macOS file)
- [ ] `*.log` ❌ (Log files)

## 🔍 Quick Verification Commands

Run these in your terminal:

```bash
cd /Users/faisal/Projects/ml_meal_prep

# Check if git is initialized
git status

# See what will be committed
git add .
git status  # Review the list

# Verify .env is NOT in the list
git status | grep -i ".env"  # Should return nothing

# Verify venv is NOT in the list
git status | grep -i "venv"  # Should return nothing
```

## 📝 Commit Command

Once verified, commit everything:

```bash
git add .
git commit -m "Initial commit: AI Meal Planner API

- FastAPI backend with OpenAI integration
- Frontend UI for meal plan generation
- Docker configuration for Railway deployment
- Complete documentation and setup scripts"
```

## 🚀 Push to GitHub

```bash
# If first time, add remote:
git remote add origin https://github.com/yourusername/ml_meal_prep.git

# Push
git push -u origin main
```

## ⚠️ Double-Check Before Pushing

Before `git push`, verify:

1. ✅ `.env` file is NOT in `git status` output
2. ✅ `venv/` folder is NOT in `git status` output
3. ✅ All code files (`app/`, `frontend/`) ARE included
4. ✅ `Dockerfile` and `requirements.txt` ARE included
5. ✅ `.gitignore` is committed

## 🎯 What Railway Needs

Railway will look for these files:
- ✅ `Dockerfile` (to build the container)
- ✅ `requirements.txt` (to install dependencies)
- ✅ `app/` folder (your Python code)
- ✅ `railway.json` (optional, but helpful)

All of these should be in your commit!

---

**Ready?** Run `git status` to see what will be committed, then proceed! 🚀

