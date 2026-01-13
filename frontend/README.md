# AI Meal Planner - Frontend

A beautiful, modern frontend for the AI Meal Planner API.

## Features

- 🎨 Clean, responsive UI
- 🍽️ Interactive meal plan generation
- 📊 Nutritional information display
- 🔄 Real-time generation with progress
- 🛑 Cancel generation feature
- 💾 Automatic user ID management (stored in localStorage)

## Deployment

### GitHub Pages (Automatic)

The frontend is automatically deployed to GitHub Pages when changes are pushed to the `frontend/` directory.

**Live URL:** https://ffaisal93.github.io/ml_meal_prep/

### Enable GitHub Pages (One-time setup)

1. Go to your repository: https://github.com/ffaisal93/ml_meal_prep
2. Click **Settings** → **Pages**
3. Under "Build and deployment":
   - **Source**: Select "GitHub Actions"
4. The workflow will automatically deploy on the next push

### Local Development

Simply open `index.html` in your browser or use a local server:

```bash
# Using Python
cd frontend
python3 -m http.server 8080

# Or using Node.js
npx http-server -p 8080
```

Then visit: http://localhost:8080

## Configuration

The frontend automatically uses `http://localhost:8000` as the default API URL. You can:

1. **Change it in the UI**: Modify the "API URL" field in the interface
2. **Edit the default**: Change `DEFAULT_API_URL` in `app.js`:

```javascript
const DEFAULT_API_URL = 'http://localhost:8000';
```

For production, update to your deployed backend URL:

```javascript
const DEFAULT_API_URL = 'https://your-backend-url.com';
```

## Files

- `index.html` - Main HTML structure
- `app.js` - JavaScript logic and API calls
- `styles.css` - Styling and responsive design
- `README.md` - This file

## API Integration

The frontend expects the backend API to be running at the configured URL. See the main project README for backend setup instructions.

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge

Requires modern browser with ES6+ support and localStorage.
