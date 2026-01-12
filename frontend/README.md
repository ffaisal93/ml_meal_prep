# Meal Planner Frontend

A beautiful, responsive landing page for the AI Meal Planner API.

## Features

- 🎨 Modern, clean UI design
- 📱 Fully responsive (mobile-friendly)
- 🔗 Connects to Railway-deployed API
- ⚡ Fast and lightweight
- 🎯 Example queries for quick testing
- 💾 Saves API URL in localStorage

## Setup for GitHub Pages

### Option 1: Deploy to GitHub Pages (Recommended)

1. **Move frontend files to docs folder:**
   ```bash
   # In your repository root
   mkdir -p docs
   cp -r frontend/* docs/
   ```

2. **Enable GitHub Pages:**
   - Go to your repository on GitHub
   - Settings → Pages
   - Source: Deploy from a branch
   - Branch: `main` (or your default branch)
   - Folder: `/docs`
   - Click Save

3. **Your site will be available at:**
   ```
   https://yourusername.github.io/ml_meal_prep/
   ```

### Option 2: Use gh-pages branch

1. **Install gh-pages:**
   ```bash
   npm install --save-dev gh-pages
   ```

2. **Add to package.json:**
   ```json
   {
     "scripts": {
       "deploy": "gh-pages -d frontend"
     }
   }
   ```

3. **Deploy:**
   ```bash
   npm run deploy
   ```

### Option 3: Manual GitHub Pages Setup

1. Create a `gh-pages` branch:
   ```bash
   git checkout -b gh-pages
   git rm -rf .
   git checkout main -- frontend/
   git mv frontend/* .
   git commit -m "Deploy to GitHub Pages"
   git push origin gh-pages
   ```

2. Enable GitHub Pages pointing to `gh-pages` branch

## Configuration

### Setting Default API URL

Edit `app.js` and change the `DEFAULT_API_URL` constant:

```javascript
const DEFAULT_API_URL = 'https://your-railway-app.railway.app';
```

### Or let users configure it

The frontend includes an input field where users can enter their Railway API URL. The URL is saved in localStorage for convenience.

## Customization

### Update GitHub Link

Edit `index.html` and update the GitHub link:

```html
<a href="https://github.com/yourusername/ml_meal_prep" target="_blank">GitHub</a>
```

### Change Colors

Edit `styles.css` and modify the CSS variables:

```css
:root {
    --primary-color: #6366f1;
    --primary-dark: #4f46e5;
    /* ... */
}
```

## Testing Locally

1. **Serve the files:**
   ```bash
   cd frontend
   python -m http.server 8080
   # or
   npx serve .
   ```

2. **Open in browser:**
   ```
   http://localhost:8080
   ```

3. **Enter your Railway API URL** in the input field

## Troubleshooting

### CORS Issues

If you get CORS errors, make sure your Railway API has CORS enabled (it should be enabled by default in the FastAPI app).

### API Not Responding

1. Check that your Railway API is running
2. Verify the API URL is correct
3. Test the API directly: `https://your-app.railway.app/health`

### GitHub Pages Not Updating

- Wait a few minutes for GitHub to rebuild
- Clear your browser cache
- Check the GitHub Pages build status in Settings → Pages

