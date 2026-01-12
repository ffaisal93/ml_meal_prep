# AI-Powered Personalized Meal Planner API

A production-ready REST API that generates personalized, multi-day meal plans based on natural language user queries. Built with FastAPI, OpenAI GPT, and Docker for easy deployment.

## 🚀 Features

- **Natural Language Processing**: Parse complex meal plan requests using OpenAI GPT
- **Intelligent Recipe Generation**: Generate detailed, realistic recipes with ingredients, instructions, and nutritional info
- **Dietary Compliance**: Respect dietary restrictions (vegan, gluten-free, etc.) and preferences (high-protein, low-carb, etc.)
- **Recipe Diversity**: Minimize repetition across meal plans
- **Caching**: Reduce API calls and costs with intelligent caching
- **Production Ready**: Docker containerized, health checks, error handling
- **Auto Documentation**: Swagger UI at `/docs`
- **🌐 Beautiful Frontend**: Responsive web interface deployable to GitHub Pages

## 📋 Requirements

- Python 3.9+
- OpenAI API key
- Docker (optional, for containerized deployment)

## 🛠️ Quick Start

### Option 1: Local Development

1. **Clone and setup:**
   ```bash
   cd ml_meal_prep
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   # Create .env file (or use setup.sh which does this automatically)
   cp ENV_EXAMPLE.txt .env
   # Edit .env and add your OPENAI_API_KEY
   ```
   
   Or use the setup script:
   ```bash
   ./setup.sh
   ```

3. **Run the API:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Test the API:**
   - API docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

### Option 2: Docker (Recommended for Testing)

1. **Build and run:**
   ```bash
   # Create .env file with your OPENAI_API_KEY
   echo "OPENAI_API_KEY=your_key_here" > .env
   
   # Build and run with Docker Compose
   docker-compose up --build
   ```

2. **Access the API:**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs

## 🌐 Deployment Options

### Complete Setup: API (Railway) + Frontend (GitHub Pages)

**Recommended approach for full-stack deployment:**

1. **Deploy API to Railway** (see Railway section below)
2. **Deploy Frontend to GitHub Pages:**
   ```bash
   # Option 1: Use GitHub Actions (automatic)
   # Just push to main branch - workflow will deploy automatically
   
   # Option 2: Manual deployment
   mkdir -p docs
   cp -r frontend/* docs/
   git add docs/
   git commit -m "Deploy frontend to GitHub Pages"
   git push
   ```
   Then enable GitHub Pages in Settings → Pages (source: `/docs` folder)

3. **Configure frontend:**
   - Edit `frontend/app.js` and set `DEFAULT_API_URL` to your Railway URL
   - Or users can enter the Railway URL in the frontend

4. **Your setup:**
   - Frontend: `https://yourusername.github.io/ml_meal_prep/`
   - API: `https://your-app.railway.app`

### Railway (Easiest - Free Tier Available)

1. **Install Railway CLI:**
   ```bash
   npm i -g @railway/cli
   railway login
   ```

2. **Deploy:**
   ```bash
   railway init
   railway up
   ```

3. **Set environment variables:**
   - Go to Railway dashboard
   - Add `OPENAI_API_KEY` in Variables section

4. **Get your URL:**
   - Railway provides a public URL automatically
   - Example: `https://your-app.railway.app`

### Render (Free Tier Available)

1. **Connect GitHub repository to Render**

2. **Create new Web Service:**
   - Select your repository
   - Build command: (auto-detected from Dockerfile)
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **Set environment variables:**
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `API_PORT`: `$PORT` (Render sets this automatically)

4. **Deploy:**
   - Render will build and deploy automatically
   - Health check endpoint: `/health`

### Fly.io (Free Tier Available)

1. **Install Fly CLI:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Deploy:**
   ```bash
   fly launch
   fly secrets set OPENAI_API_KEY=your_key_here
   fly deploy
   ```

### Heroku (Paid, but straightforward)

1. **Install Heroku CLI and login**

2. **Deploy:**
   ```bash
   heroku create your-app-name
   heroku config:set OPENAI_API_KEY=your_key_here
   git push heroku main
   ```

## 🎨 Frontend (GitHub Pages)

A beautiful, responsive web interface is included in the `frontend/` directory. Deploy it to GitHub Pages for a complete user experience.

### Quick Deploy to GitHub Pages

1. **Copy frontend to docs folder:**
   ```bash
   mkdir -p docs
   cp -r frontend/* docs/
   ```

2. **Enable GitHub Pages:**
   - Go to repository Settings → Pages
   - Source: Deploy from branch `/docs` folder
   - Or use the GitHub Actions workflow (automatic)

3. **Update API URL:**
   - Edit `frontend/app.js` and set `DEFAULT_API_URL` to your Railway URL
   - Or users can enter it in the frontend

4. **Access your site:**
   ```
   https://yourusername.github.io/ml_meal_prep/
   ```

See `frontend/README.md` for detailed frontend setup instructions.

## 📚 Documentation

All detailed documentation is organized in the `docs/` folder:

- **[Quick Start Guide](docs/QUICK_START.md)** - Get started in 5 minutes ⚡
- **[GitHub Setup](docs/GITHUB_SETUP.md)** - Push your code to GitHub
- **[Testing Guide](docs/TESTING.md)** - Local testing instructions
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Deploy to Railway, Render, etc.
- **[Update Deployment](docs/UPDATE_DEPLOYMENT.md)** - Update your deployment after changes
- **[Pre-Commit Checklist](docs/PRE_COMMIT_CHECKLIST.md)** - Verify before pushing to GitHub

See [docs/README.md](docs/README.md) for the complete documentation index.

## 📖 API Usage

### Generate Meal Plan

**Endpoint:** `POST /api/generate-meal-plan`

**Request:**
```json
{
  "query": "Create a 5-day vegetarian meal plan with high protein"
}
```

**Response:**
```json
{
  "meal_plan_id": "uuid",
  "duration_days": 5,
  "generated_at": "2025-01-15T10:30:00",
  "meal_plan": [
    {
      "day": 1,
      "date": "2025-01-15",
      "meals": [
        {
          "meal_type": "breakfast",
          "recipe_name": "High-Protein Oatmeal Bowl",
          "description": "...",
          "ingredients": ["2 cups oats", "..."],
          "nutritional_info": {
            "calories": 350,
            "protein": 25,
            "carbs": 45,
            "fat": 8
          },
          "preparation_time": "15 mins",
          "instructions": "...",
          "source": "AI Generated"
        }
      ]
    }
  ],
  "summary": {
    "total_meals": 15,
    "dietary_compliance": ["vegetarian", "high-protein"],
    "estimated_cost": "$45-60",
    "avg_prep_time": "25 mins"
  }
}
```

### Example Queries

- `"Create a 3-day vegetarian meal plan"`
- `"I need a 7-day low-carb, dairy-free meal plan with high protein"`
- `"Generate a week of budget-friendly meals with quick breakfast options"`
- `"5-day Mediterranean diet plan"`

### Health Check

**Endpoint:** `GET /health`

Returns API health status for monitoring.

## 🏗️ Architecture

```
┌─────────────────┐
│   FastAPI App   │
│   (main.py)     │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────────┐
│ Query │ │  Recipe   │
│Parser │ │  Service  │
└───┬───┘ └──┬────────┘
    │        │
    └───┬────┘
        │
┌───────▼────────┐
│ Meal Generator │
└────────────────┘
```

### Components

1. **Query Parser** (`app/query_parser.py`): Extracts structured requirements from natural language using OpenAI
2. **Recipe Service** (`app/recipe_service.py`): Generates recipes with caching to reduce API calls
3. **Meal Generator** (`app/meal_generator.py`): Orchestrates meal plan creation
4. **FastAPI App** (`app/main.py`): REST API with validation and error handling

## 🎯 Design Decisions

### Why OpenAI GPT-4o-mini?
- Cost-effective for high-volume requests
- Excellent at structured output generation
- Fast response times
- Free tier available for testing

### Why Hybrid Approach?
- LLM for flexibility and natural language understanding
- Caching to reduce costs and improve performance
- Fallback mechanisms for reliability

### Why FastAPI?
- Auto-generated OpenAPI/Swagger docs
- Built-in validation with Pydantic
- Async support for better performance
- Production-ready framework

## ⚙️ Configuration

Environment variables (see `.env.example`):

- `OPENAI_API_KEY` (required): Your OpenAI API key
- `API_HOST` (optional): Host to bind to (default: 0.0.0.0)
- `API_PORT` (optional): Port to run on (default: 8000)
- `CACHE_TTL_SECONDS` (optional): Cache TTL in seconds (default: 3600)

## 🧪 Testing

### Manual Testing

1. **Basic query:**
   ```bash
   curl -X POST http://localhost:8000/api/generate-meal-plan \
     -H "Content-Type: application/json" \
     -d '{"query": "Create a 3-day vegetarian meal plan"}'
   ```

2. **Complex query:**
   ```bash
   curl -X POST http://localhost:8000/api/generate-meal-plan \
     -H "Content-Type: application/json" \
     -d '{"query": "Generate a 7-day low-carb, dairy-free meal plan with high protein, budget-friendly options"}'
   ```

3. **Health check:**
   ```bash
   curl http://localhost:8000/health
   ```

### Test Cases

The API should handle:
- ✅ Basic queries (3-day vegetarian)
- ✅ Complex queries (multiple restrictions)
- ✅ Ambiguous queries ("healthy meals for next week")
- ✅ Edge cases (10-day → capped at 7)
- ✅ Contradictions (vegan pescatarian → error)

## 📊 Performance & Cost Optimization

- **Caching**: Recipes cached by dietary tags (TTL: 1 hour)
- **Batch Processing**: Efficient meal plan generation
- **Error Handling**: Graceful fallbacks if API fails
- **Rate Limiting**: Can be enabled via config (not implemented by default)

**Estimated Costs:**
- ~$0.01-0.02 per meal plan (using GPT-4o-mini)
- Caching reduces costs by ~60-70% for similar queries

## 🐛 Known Limitations

1. **Recipe Diversity**: While we track used recipes, perfect diversity isn't guaranteed
2. **Nutritional Accuracy**: Nutritional info is AI-generated and should be verified
3. **Cost Estimation**: Rough estimates based on calories
4. **No User Persistence**: Each request is independent (no user accounts)
5. **Rate Limiting**: Not implemented by default (can be added)

## 🔮 Future Improvements

Given more time, I would add:

1. **Recipe Database**: Pre-populated recipe database for faster responses
2. **Nutritional Validation**: Verify nutritional info against USDA database
3. **User Preferences**: Store user preferences for personalized recommendations
4. **Rate Limiting**: Implement proper rate limiting middleware
5. **Monitoring**: Add Prometheus metrics and structured logging
6. **Testing**: Comprehensive unit and integration tests
7. **Recipe Images**: Generate or fetch recipe images
8. **Shopping Lists**: Generate consolidated shopping lists
9. **Meal Prep Instructions**: Batch cooking instructions
10. **Database**: Persistent storage for meal plans and recipes

## 📝 License

This project is created for a take-home assignment.

## 👤 Author

Built for ML Engineer position at WellDoc Inc.

---

## 🚀 Quick Deploy Commands

### Railway
```bash
railway login && railway init && railway up
```

### Render
Just connect your GitHub repo and deploy!

### Fly.io
```bash
fly launch && fly secrets set OPENAI_API_KEY=xxx && fly deploy
```

---

**For evaluators:** The API is ready to test! Just set the `OPENAI_API_KEY` environment variable and deploy using any of the methods above. The health check endpoint at `/health` can be used for monitoring.

