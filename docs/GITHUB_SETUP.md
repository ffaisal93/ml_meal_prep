# GitHub Setup Guide

Step-by-step instructions to push your Meal Planner project to GitHub.

## 📋 Prerequisites

- GitHub account (create at https://github.com if you don't have one)
- Git installed (usually comes with macOS)

## 🚀 Step-by-Step Instructions

### Step 1: Create GitHub Repository

1. Go to https://github.com and sign in
2. Click the **"+"** icon → **"New repository"**
3. Repository name: `ml_meal_prep` (or your choice)
4. Description: "AI-Powered Personalized Meal Planner API"
5. Set to **Public** (or Private if you prefer)
6. **DO NOT** initialize with README, .gitignore, or license (we already have these)
7. Click **"Create repository"**

### Step 2: Initialize Git (if not already done)

```bash
cd /Users/faisal/Projects/ml_meal_prep

# Check if git is already initialized
git status

# If not initialized, run:
git init
```

### Step 3: Verify What Will Be Committed

```bash
# Add all files (respects .gitignore)
git add .

# Check what will be committed
git status

# IMPORTANT: Verify these are NOT in the list:
# - .env (should NOT appear)
# - venv/ (should NOT appear)
# - __pycache__/ (should NOT appear)
```

### Step 4: Commit Your Files

```bash
git commit -m "Initial commit: AI Meal Planner API

- FastAPI backend with OpenAI integration
- Frontend UI for meal plan generation
- Docker configuration for Railway deployment
- Complete documentation and setup scripts"
```

### Step 5: Connect to GitHub Repository

```bash
# Replace 'yourusername' with your GitHub username
git remote add origin https://github.com/yourusername/ml_meal_prep.git

# Verify remote was added
git remote -v
```

### Step 6: Push to GitHub

```bash
# Push to main branch
git push -u origin main

# If your default branch is 'master' instead:
# git push -u origin master
```

## ✅ Verification

After pushing, verify:

1. Go to your GitHub repository: `https://github.com/yourusername/ml_meal_prep`
2. Check that all files are there:
   - ✅ `app/` folder
   - ✅ `frontend/` folder
   - ✅ `docs/` folder
   - ✅ `Dockerfile`
   - ✅ `requirements.txt`
   - ✅ `README.md`
3. Verify `.env` and `venv/` are **NOT** visible (they shouldn't be)

## 🔍 Quick Checklist

Before pushing, make sure:

- [ ] `.env` file is NOT in `git status` (it's in .gitignore)
- [ ] `venv/` folder is NOT in `git status` (it's in .gitignore)
- [ ] All code files (`app/`, `frontend/`) ARE in `git status`
- [ ] `Dockerfile` and `requirements.txt` ARE in `git status`
- [ ] `.gitignore` IS in `git status`

## 🐛 Troubleshooting

### Error: "remote origin already exists"
```bash
# Remove existing remote
git remote remove origin

# Add it again
git remote add origin https://github.com/yourusername/ml_meal_prep.git
```

### Error: "failed to push some refs"
```bash
# If GitHub repo has files you don't have locally:
git pull origin main --allow-unrelated-histories

# Then push again
git push -u origin main
```

### Error: Authentication required
```bash
# GitHub now requires personal access token instead of password
# Go to: GitHub → Settings → Developer settings → Personal access tokens
# Create a token with 'repo' permissions
# Use the token as password when pushing
```

### Error: "branch 'main' does not exist"
```bash
# Create and switch to main branch
git branch -M main

# Then push
git push -u origin main
```

## 📝 Complete Command Sequence

Here's the complete sequence (copy-paste ready):

```bash
cd /Users/faisal/Projects/ml_meal_prep

# Initialize git (if needed)
git init

# Add all files
git add .

# Verify .env is NOT included
git status | grep -i ".env"  # Should return nothing

# Commit
git commit -m "Initial commit: AI Meal Planner API"

# Add remote (replace 'yourusername' with your GitHub username)
git remote add origin https://github.com/yourusername/ml_meal_prep.git

# Push
git push -u origin main
```

## 🎯 After Pushing

Once your code is on GitHub:

1. ✅ Your code is now public and shareable
2. ✅ You can deploy to Railway (connect to GitHub for auto-deploy)
3. ✅ Evaluators can clone and test your code
4. ✅ You can share the repository link

## 🔗 Next Steps

After pushing to GitHub:

1. **Deploy to Railway** (see [QUICK_START.md](QUICK_START.md))
2. **Set up Railway auto-deploy** (connect GitHub repo)
3. **Deploy frontend** to your personal website

---

**Need help?** Check [PRE_COMMIT_CHECKLIST.md](PRE_COMMIT_CHECKLIST.md) for what to commit.

