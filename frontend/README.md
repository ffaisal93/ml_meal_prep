# AI Meal Planner - Frontend

A clean, responsive web interface for the AI Meal Planner API.

## Features

- Natural language meal plan requests
- Four generation strategies (fast_llm, llm_only, rag, hybrid)
- Real-time generation with progress indicators
- Stop generation button for long requests
- Automatic user ID management (localStorage)
- Responsive design (mobile-friendly)
- Configurable API URL

## Deployment

### GitHub Pages (Automatic)

The frontend deploys automatically when you push changes to the `frontend/` directory.

**Live URL**: https://ffaisal93.github.io/ml_meal_prep/

### Setup (One-time)

1. Go to repository Settings → Pages
2. Under "Build and deployment":
   - Source: Select "GitHub Actions"
3. Push any change to trigger deployment

### Local Development

Open `index.html` in your browser, or use a local server:

```bash
# Using Python
cd frontend
python3 -m http.server 8080

# Or Node.js
npx http-server -p 8080
```

Visit: http://localhost:8080

## Configuration

The frontend uses `http://localhost:8000` by default. You can:

1. **Change in UI**: Modify the "API URL" field
2. **Edit default**: Update `DEFAULT_API_URL` in `app.js`:

```javascript
const DEFAULT_API_URL = 'http://localhost:8000';
```

For production, point to your deployed backend:

```javascript
const DEFAULT_API_URL = 'https://your-backend-url.com';
```

## Files

- `index.html` - Main HTML structure
- `app.js` - JavaScript logic, API calls
- `styles.css` - Styling and responsive design
- `README.md` - This file

## API Integration

The frontend expects these endpoints:

- `POST /api/generate-meal-plan` - Generate meal plans
- `GET /health` - Health check

Request format:
```json
{
  "query": "7-day meal plan",
  "generation_mode": "fast_llm",
  "user_id": "auto-generated-uuid"
}
```

## Features Explained

### Generation Strategies

- **fast_llm**: Ultra-fast, minimal detail (2-3s per meal)
- **llm_only**: Creative, detailed recipes
- **rag**: Real recipes from Edamam API
- **hybrid**: Mix of rag and llm_only

### User ID

Automatically generated and stored in localStorage. Used for:
- Tracking user preferences
- Personalizing future suggestions
- No manual input required

### Stop Button

Allows canceling long-running requests (e.g., 7-day plans). Uses `AbortController` API.

### Timeout Handling

Requests timeout after 10 minutes to prevent browser hangs. Shows helpful error messages.

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge

Requires ES6+ support and localStorage.

## Development Notes

The code is intentionally simple:
- No build step
- No dependencies
- Pure vanilla JavaScript
- Works offline (except API calls)

This makes it easy to deploy anywhere and modify without complex tooling.
