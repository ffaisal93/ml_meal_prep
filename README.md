# AI Meal Planner

An intelligent meal planning system that generates personalized meal plans from natural language queries. Built with FastAPI, OpenAI GPT-4o-mini, and optional Edamam API integration for real recipe data.

**🚀 Live Demo:** [https://fahimfaisal.info/ml_meal_prep/](https://fahimfaisal.info/ml_meal_prep/)

## Table of Contents

- [What It Does](#what-it-does)
- [Quick Start](#quick-start)
- [Recipe Generation Strategies](#recipe-generation-strategies)
- [Features](#features)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Design Choices](#design-choices)
- [Cost Estimates](#cost-estimates)
- [Troubleshooting](#troubleshooting)
- [Evaluation Framework](#evaluation-framework)
- [Future Work](#future-work-comprehensive-evaluation--scaling)
- [Documentation](#documentation)

## System Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Query                              │
│          "I need a week of budget-friendly meals"               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Query Parser (OpenAI)                        │
│  • Extract: duration, dietary restrictions, preferences         │
│  • Validate: duration (1-7 days), contradictions                │
│  • Output: Structured requirements                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Contradiction Resolution & User History            │
│  • Resolve conflicts (e.g., keto + high-carb → keep keto)       │
│  • Store query in PostgreSQL/SQLite (if user_id provided)       │
│  • Generate user-friendly warning if needed                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Strategy Selection                            │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │Fast LLM  │  │LLM-Only  │  │   RAG    │  │ Hybrid   │         │
│  │ 2 calls  │  │ 8 calls  │  │ 11 calls │  │ 11 calls │         │
│  │ 40s      │  │ 60s      │  │ 60-90s   │  │ 60-90s   │         │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Recipe Generation                            │
│  • Day-by-day generation (batch meals per day)                  │
│  • Diversity tracking (variety hints, candidate filtering)      │
│  • Nutritional validation (RAG: exact Edamam data)              │
│  • Caching (Edamam responses cached 1 hour)                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Response Validation                            │
│  • Pydantic model validation                                    │
│  • Nutrition checks (realistic values)                          │
│  • Prep time formatting (no decimals)                           │
│  • Summary calculation (cost, avg prep time)                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Complete Meal Plan                           │
│  • 21 recipes (7 days × 3 meals)                                │
│  • Ingredients, instructions, nutrition                         │
│  • Cost estimate, prep times                                    │
│  • Warning message (if contradictions resolved)                 │
│  • Stored in user history (if user_id provided)                 │
└─────────────────────────────────────────────────────────────────┘
```

## What It Does

Ask for a meal plan in plain English, and the system generates complete recipes with ingredients, instructions, and nutritional information.

**Example queries:**
- "I need a week of budget-friendly vegetarian meals"
- "Create a 5-day high-protein meal plan"
- "Generate 3 days of quick meals under 20 minutes"

**What you get:**
- Complete recipes with ingredients and step-by-step instructions
- Accurate nutritional information (calories, protein, carbs, fat)
- Diverse meals (no repetitive recipes)
- Budget estimates and preparation times

## Quick Start

### Prerequisites

- Python 3.9 or higher
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))
- (Optional) Edamam API credentials for real recipes ([free tier available](https://developer.edamam.com/))

### 1. Clone and Setup

   ```bash
# Clone the repository
git clone https://github.com/ffaisal93/ml_meal_prep.git
   cd ml_meal_prep

# Create virtual environment
python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
   pip install -r requirements.txt
   ```

### 2. Configure Environment

Create a `.env` file in the project root:

   ```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional (for RAG/Hybrid strategies)
EDAMAM_APP_ID=your_edamam_app_id
EDAMAM_APP_KEY=your_edamam_app_key

# Optional settings
RECIPE_GENERATION_MODE=llm_only  # Options: llm_only, rag, hybrid, fast_llm
API_HOST=0.0.0.0
API_PORT=8000
CACHE_TTL_SECONDS=3600
```

**Getting API keys:**
- **OpenAI**: Sign up at [platform.openai.com](https://platform.openai.com/), go to API keys, create new key
- **Edamam** (optional): Sign up at [developer.edamam.com](https://developer.edamam.com/), choose Recipe Search API (free tier: 10 calls/min)

### 3. Run the API

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

The API will be available at `http://localhost:8000`

**Test it:**
   ```bash
# Health check
curl http://localhost:8000/health

# Generate a meal plan
curl -X POST http://localhost:8000/api/generate-meal-plan \
  -H "Content-Type: application/json" \
  -d '{"query": "Create a 3-day vegetarian meal plan"}'
```

**Or use the interactive docs:**
Open `http://localhost:8000/docs` in your browser for Swagger UI.

### 4. Use the Frontend

   ```bash
# In a new terminal (keep the API running)
cd frontend
python3 -m http.server 8080
```

Open `http://localhost:8080` in your browser. The frontend will automatically connect to your local API.

## Recipe Generation Strategies

The system supports four different generation strategies. Choose based on your needs:

| Strategy | Speed | Detail | API Calls (7-day) | Best For |
|----------|-------|--------|-------------------|----------|
| **fast_llm** | Fastest (40s) | Minimal | 2 OpenAI | Quick testing, demos |
| **llm_only** | Fast (60s) | Detailed | 8 OpenAI | Creative recipes, no Edamam needed |
| **rag** | Medium (60-90s) | Detailed | 3 Edamam + 8 OpenAI | Real recipes, accurate nutrition |
| **hybrid** | Medium (60-90s) | Balanced | 3 Edamam + 8 OpenAI | Mix of real and creative (70% RAG, 30% LLM) |

**Switch strategies:**
- In `.env`: Set `RECIPE_GENERATION_MODE=llm_only`
- Via API: Add `"generation_mode": "rag"` to request body
- In frontend: Use the dropdown menu

**Note:** RAG and Hybrid strategies require Edamam API credentials. If not configured, they'll fall back to LLM-only generation.

## Features

### Core Functionality
- ✅ Natural language query parsing (handles typos, ambiguity)
- ✅ Duration limits (1-7 days, automatically enforced)
- ✅ Dietary restrictions (vegan, vegetarian, gluten-free, etc.)
- ✅ Preferences (high-protein, low-carb, keto, paleo, etc.)
- ✅ Special requirements (budget-friendly, quick meals, prep time limits)
- ✅ Exclusions (e.g., "not Mediterranean", "no Italian")

### Smart Features
- ✅ **Contradiction resolution**: Automatically resolves conflicts (e.g., "keto and high-carb" → keeps keto, shows friendly warning)
- ✅ **Always returns a plan**: Fallback to default meal plan on any error
- ✅ **Recipe diversity**: >80% unique meals using variety hints and candidate filtering
- ✅ **Cost optimization**: Batch generation (multiple meals per API call), caching, GPT-4o-mini
- ✅ **Nutritional validation**: RAG strategy uses exact Edamam nutrition data
- ✅ **Rate limiting**: System-wide (100/min) and per-IP (10/min) protection
- ✅ **User preferences**: Stores query history per user (localStorage-based user IDs)

### Technical Features
- ✅ **Caching**: Edamam responses cached for 1 hour (reduces 21 calls to 3)
- ✅ **Batch generation**: All meals for a day in one API call (not 1 call per meal)
- ✅ **Structured validation**: Pydantic models for all inputs/outputs
- ✅ **Error handling**: Graceful degradation with user-friendly messages
- ✅ **CORS enabled**: Frontend works from any domain
- ✅ **Health checks**: `/health` endpoint for monitoring

## API Documentation

### Generate Meal Plan

**Endpoint:** `POST /api/generate-meal-plan`

**Request:**
```json
{
  "query": "I need a week of budget-friendly vegetarian meals",
  "generation_mode": "rag",  // Optional: llm_only, rag, hybrid, fast_llm
  "user_id": "user-123"  // Optional: for preference tracking
}
```

**Response:**
```json
{
  "meal_plan_id": "uuid",
  "duration_days": 7,
  "generated_at": "2026-01-14T10:30:00",
  "meal_plan": [
    {
      "day": 1,
      "date": "2026-01-14",
      "meals": [
        {
          "meal_type": "breakfast",
          "recipe_name": "Spinach and Feta Scramble",
          "description": "A protein-rich Mediterranean breakfast...",
          "ingredients": ["4 large eggs", "2 cups spinach", "1/4 cup feta", ...],
          "nutritional_info": {
            "calories": 310,
            "protein": 22.0,
            "carbs": 8.0,
            "fat": 22.0
          },
          "preparation_time": "15 mins",
          "instructions": "1. Heat olive oil... 2. Sauté onions...",
          "source": "AI Generated"
        }
        // ... lunch, dinner
      ]
    }
    // ... days 2-7
  ],
  "summary": {
    "total_meals": 21,
    "dietary_compliance": ["vegetarian", "budget-friendly"],
    "estimated_cost": "$45-60",
    "avg_prep_time": "25 mins"
  },
  "warning": null  // Or user-friendly message if contradictions were resolved
}
```

**Rate limits:**
- 10 requests per minute per IP
- 100 requests per minute system-wide

### Get User Preferences

**Endpoint:** `GET /api/user/{user_id}/preferences?limit=10`

**Response:**
```json
{
  "user_id": "user-123",
  "preferences": [
    {
      "id": 1,
      "query": "I need a week of budget-friendly vegetarian meals",
      "meal_plan_id": "uuid",
      "dietary_restrictions": ["vegetarian"],
      "preferences": [],
      "special_requirements": ["budget-friendly"],
      "created_at": "2026-01-14T10:30:00"
    }
    // ... up to 10 most recent queries
  ]
}
```

**Full API documentation:** Visit `/docs` when the server is running for interactive Swagger UI.

## Deployment

### Deploy Backend (Railway)

1. **Create Railway account** at [railway.app](https://railway.app)

2. **Add PostgreSQL database:**
   - In your Railway project, click "New" → "Database" → "Add PostgreSQL"
   - Railway automatically creates the database and sets `DATABASE_URL` environment variable
   - This enables user preference storage and query history

3. **Deploy from GitHub:**
   - Click "New" → "Deploy from GitHub repo"
   - Select `ml_meal_prep` repository
   - Railway auto-detects Python and uses `Procfile`

4. **Add environment variables:**
   ```
   OPENAI_API_KEY=your_key
   EDAMAM_APP_ID=your_id (optional)
   EDAMAM_APP_KEY=your_key (optional)
   RECIPE_GENERATION_MODE=llm_only
   DATABASE_URL=postgresql://... (auto-set by Railway when you add PostgreSQL)
   ```

5. **Get your API URL:**
   - Railway provides: `https://your-app.railway.app`
   - Test: `https://your-app.railway.app/health`

**User History Feature:**
- PostgreSQL stores user preferences and query history
- Each user gets a unique ID (auto-generated in browser via localStorage)
- API endpoint: `GET /api/user/{user_id}/preferences?limit=10`
- Frontend shows smart suggestions based on previous queries
- Locally: Uses SQLite (no setup needed)
- Production: Uses PostgreSQL (Railway auto-configures)

### Deploy Frontend (GitHub Pages)

The frontend auto-deploys via GitHub Actions when you push to `main`.

1. **Enable GitHub Pages:**
   - Go to repository Settings → Pages
   - Source: "GitHub Actions"

2. **Frontend will be available at:**
   ```
   https://your-username.github.io/ml_meal_prep/
   ```

3. **Set API URL:**
   - Open the frontend
   - Enter your Railway API URL in the "API URL" field
   - It will be saved in localStorage

**That's it!** The system is now fully deployed and accessible from anywhere.

## Project Structure

```
ml_meal_prep/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Settings and environment variables
│   ├── models.py               # Pydantic request/response models
│   ├── query_parser.py         # Natural language query parsing
│   ├── query_validator.py      # Query validation and correction
│   ├── meal_generator.py       # Orchestrates meal plan generation
│   ├── recipe_service.py       # Recipe generation facade
│   ├── recipe_retriever.py     # Edamam API client
│   ├── database.py             # User preference storage
│   ├── rate_limiter.py         # Rate limiting logic
│   └── recipe_generation/      # Strategy pattern implementation
│       ├── base.py             # Abstract base strategy
│       ├── factory.py          # Strategy factory
│       ├── llm_only.py         # Pure AI generation
│       ├── rag_strategy.py     # Retrieval-augmented generation
│       ├── hybrid_strategy.py  # Mix of RAG and LLM
│       └── fast_llm.py         # Ultra-fast generation
├── frontend/
│   ├── index.html              # Web interface
│   ├── app.js                  # Frontend logic
│   └── styles.css              # Styling
├── tests/
│   ├── test_edge_cases.py      # Assignment edge cases
│   ├── test_meal_generator.py  # Generation logic tests
│   ├── test_query_validator.py # Validation tests
│   ├── test_strategies.py      # Strategy tests
│   └── test_performance.py     # Performance benchmarks
├── docs/
│   ├── TESTING.md              # Local testing guide
│   ├── DEPLOYMENT.md           # Deployment instructions
│   ├── API.md                  # Complete API documentation
│   ├── RECIPE_GENERATION_STRATEGIES.md  # Strategy details
│   └── DIVERSITY_STRATEGY.md   # Diversity algorithm explanation
├── evaluation/
│   ├── simple_eval.py          # Diversity evaluation script
│   └── README.md               # Evaluation guide
├── STRATEGIES.md               # Complete information flow walkthrough
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── Procfile                    # Railway deployment config
└── README.md                   # This file
```

## Testing

### Run Unit Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_edge_cases.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Skip slow performance tests
pytest tests/ -v -k "not performance"
```

**Test coverage:**
- Query parsing and validation
- All 4 recipe generation strategies
- Contradiction resolution
- Fallback handling
- Edge cases (duration limits, conflicts, ambiguous queries)
- Performance benchmarks (speed and diversity)

### Manual Testing

   ```bash
# Test API directly
./test_api.sh

# Or use curl
   curl -X POST http://localhost:8000/api/generate-meal-plan \
     -H "Content-Type: application/json" \
  -d '{"query": "3-day vegetarian meal plan", "generation_mode": "llm_only"}'
```

## Design Choices

This project implements several bonus features from the assignment:

### 1. Recipe Diversity Algorithm
- **LLM-only**: Variety hints (day-based cuisine suggestions), recipe tracking
- **RAG**: Candidate filtering, shuffle before selection
- **All strategies**: Thread-safe tracking, >80% unique meals guaranteed

### 2. Nutritional Validation
- **RAG strategy**: Uses exact Edamam nutrition data
- **Auto-correction**: If LLM deviates >20%, uses real values
- **Validation**: All nutrition values checked for realism

### 3. Caching Mechanism
- **Edamam responses**: Cached for 1 hour (reduces 21 calls to 3)
- **Cache key**: `{meal_type}|{dietary_restrictions}|{prep_time_max}`
- **Thread-safe**: Uses locks for concurrent access

### 4. Rate Limiting
- **System-wide**: 100 requests/minute
- **Per-IP**: 10 requests/minute
- **Graceful**: Returns 429 with retry-after header

### 5. User Preference Storage
- **Database**: SQLAlchemy ORM with dual support
  - **Production (Railway)**: PostgreSQL (auto-configured via DATABASE_URL)
  - **Local development**: SQLite (no setup needed)
- **User IDs**: Auto-generated per browser (localStorage, no signup required)
- **History**: Stores up to 10 most recent queries per user
- **Smart suggestions**: Frontend displays previous queries as clickable chips
- **API endpoint**: `GET /api/user/{user_id}/preferences?limit=10`
- **Privacy**: User data isolated by user_id, no cross-user access

### 6. Unit Tests
- **5 test files**: Edge cases, strategies, validation, generation, performance
- **Coverage**: All critical components tested
- **CI-ready**: Can integrate with GitHub Actions

### 7. Cost Optimization
- **Batch generation**: Multiple meals per API call (not 1 per meal)
- **Caching**: Reuses Edamam responses
- **Model choice**: GPT-4o-mini (20x cheaper than GPT-4)
- **Fast mode**: 2 calls for entire 7-day plan

### 8. Observability
- **Logging**: Structured logs with context
- **Health checks**: `/health` endpoint
- **Error tracking**: All exceptions logged with stack traces
- **Metrics**: API call counts, generation times

### 9. Structured Output Validation
- **Pydantic models**: All inputs/outputs validated
- **JSON schema**: OpenAI structured output mode
- **Type safety**: Full type hints throughout

### 10. Multiple Strategies
- **Strategy pattern**: Clean architecture, easy to extend
- **4 strategies**: Fast LLM, LLM-only, RAG, Hybrid
- **Runtime switching**: Via API or frontend

## Cost Estimates

Using GPT-4o-mini pricing ($0.150 per 1M input tokens, $0.600 per 1M output tokens):

**7-day meal plan (21 meals):**
- **Fast LLM**: ~$0.02 (2 API calls)
- **LLM-only**: ~$0.08 (8 API calls)
- **RAG**: ~$0.10 (3 Edamam free + 8 OpenAI)
- **Hybrid**: ~$0.12-0.15 (3 Edamam free + 8-15 OpenAI)

**Edamam free tier:** 10 calls/minute, unlimited total (with attribution)

## Troubleshooting

### "OPENAI_API_KEY not found"
- Ensure `.env` file exists in project root
- Check the key is correct (starts with `sk-`)
- Restart the server after creating/editing `.env`

### "Module not found" errors
- Activate virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

### "Address already in use"
- Port 8000 is occupied
- Use different port: `uvicorn app.main:app --port 8001`
- Or kill the process: `lsof -i :8000` then `kill -9 <PID>`

### Frontend shows "Failed to fetch"
- Check API is running: `curl http://localhost:8000/health`
- Verify API URL in frontend matches your server
- If using GitHub Pages: Set Railway URL, not localhost

### RAG strategy returns LLM-only recipes
- Check Edamam credentials are set in `.env`
- Verify Edamam API is accessible (not rate limited)
- Check logs for "No Edamam candidates found" messages

### Slow generation times
- Use `fast_llm` strategy for testing
- Check your internet connection
- Verify OpenAI API is responsive

## Documentation

- **[STRATEGIES.md](STRATEGIES.md)**: Complete information flow walkthrough with examples
- **[docs/TESTING.md](docs/TESTING.md)**: Local testing guide
- **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**: Deployment instructions
- **[docs/API.md](docs/API.md)**: Complete API reference
- **[docs/RECIPE_GENERATION_STRATEGIES.md](docs/RECIPE_GENERATION_STRATEGIES.md)**: Strategy details
- **[docs/DIVERSITY_STRATEGY.md](docs/DIVERSITY_STRATEGY.md)**: Diversity algorithm

## Contributing

This is an assignment project, but feel free to fork and extend it!

**Ideas for extension:**
- Add more strategies (e.g., hybrid with different ratios)
- Support more meal types (snacks, desserts)
- Add meal prep instructions (batch cooking)
- Implement shopping list generation
- Add calorie/macro targets
- Support multiple cuisines simultaneously
- Add image generation for recipes

## License

MIT License - feel free to use this code for your own projects.

## Evaluation Framework

The project includes a simple diversity evaluation framework in the `evaluation/` directory.

### Current Evaluation

**What it tests:**
- Recipe diversity across all 4 strategies
- Exclusion compliance (e.g., "not Mediterranean")
- Generation time comparison
- Unique meals vs total meals ratio

**Test cases:**
1. 1-day, 2-meal plan (quick test)
2. 2-day vegetarian with exclusions
3. 3-day full plan (standard size)

**Run evaluation:**
```bash
cd evaluation
python simple_eval.py
```

**Typical results:**
- fast_llm: 80-90% diversity
- llm_only: 90-100% diversity
- rag: 85-95% diversity
- hybrid: 85-95% diversity

All strategies maintain >80% unique meals with minimal repetition.

### Future Work: Comprehensive Evaluation & Scaling

Given more time, here's a thoughtful plan for expanding the system:

#### 1. Enhanced Evaluation Framework

**API Call Tracking:**
- API calls cost metrics
- Monitor Edamam API usage and cache hit rates
- Generate cost reports per strategy per query
- Compare actual costs vs theoretical estimates

**Diversity Metrics:**
- Semantic similarity analysis (not just exact name matching)
- Ingredient overlap detection (e.g., two recipes with 80% same ingredients)
- Cuisine distribution analysis (ensure variety across cuisines)
- Cooking method diversity (baking, grilling, sautéing, etc.)
- Nutritional diversity (ensure varied macro profiles)

**Quality Metrics:**
- Recipe realism score (compare AI recipes vs real recipe databases)
- Instruction clarity (step count, detail level)
- Ingredient availability (common vs exotic ingredients)
- Preparation time accuracy (compare estimated vs typical actual times)

**Performance Benchmarks:**
- Latency percentiles (p50, p95, p99)
- Throughput testing (concurrent requests)
- Cache effectiveness (hit rate, memory usage)

**Automated Testing:**
- Continuous evaluation on every commit
- Regression detection (diversity drops, cost increases)
- A/B testing framework for strategy improvements
- Load testing with realistic traffic patterns

#### 2. System Optimization & Scaling

**Cost Optimization:**
- **Prompt compression**: Reduce token usage by 20-30% through careful prompt engineering
- **Response streaming**: Stream recipes as they're generated (better UX, same cost)
- **Smart caching layers**: 
  - L1: In-memory cache (current Edamam cache)
  - L2: Redis cache for parsed queries and common meal plans
  - L3: CDN cache for static recipe data
- **Batch processing**: Group multiple user requests for bulk API calls
- **Model selection**: Dynamic model choice (GPT-4o-mini for simple, GPT-4o for complex)

**Performance Scaling:**
- **Horizontal scaling**: 
  - Stateless API design (already done)
  - Load balancer across multiple Railway instances
  - Database connection pooling and read replicas
- **Async optimization**:
  - Parallel Edamam fetches for different meal types
  - Background tasks for user history updates
  - Async database writes (don't block response)
- **CDN integration**: Serve frontend and static assets via CDN
- **Database optimization**:
  - Index optimization for user preference queries
  - Materialized views for common aggregations
  - Partition large tables by date

**Reliability Improvements:**
- **Circuit breakers**: Fail fast on external API issues
- **Retry logic**: Exponential backoff for transient failures
- **Fallback chains**: RAG → LLM-only → Cached → Default
- **Health checks**: Deep health checks (DB, OpenAI, Edamam)
- **Monitoring**: Prometheus metrics, Grafana dashboards
- **Alerting**: PagerDuty/Slack alerts for errors, latency spikes

**Feature Enhancements:**
- **Meal prep mode**: Batch cooking instructions for multiple days
- **Nutritional targets**: Hit specific calorie/macro goals
- **Dietary scoring**: Rate how well plan matches dietary goals
- **Recipe variations**: Generate alternatives for disliked meals
- **Meal swapping**: Swap individual meals without regenerating entire plan
- **Image generation**: AI-generated food images (DALL-E integration)
- **Voice interface**: Alexa/Google Home integration

**Data & Learning:**
- **User feedback loop**: Collect ratings, improve recommendations
- **Recipe database**: Build proprietary recipe database from successful generations
- **Personalization**: Learn user preferences over time (ML model)
- **Collaborative filtering**: "Users like you also enjoyed..."
- **Seasonal adjustments**: Suggest seasonal ingredients
- **Regional preferences**: Adapt to user's location/culture

**Infrastructure:**
- **Multi-region deployment**: Reduce latency for global users
- **Database sharding**: Partition users across DB instances
- **Message queue**: RabbitMQ/Kafka for async tasks
- **Microservices**: Split into auth, generation, storage services
- **Kubernetes**: Container orchestration for complex deployments

#### 3. Evaluation Automation

**Continuous Monitoring:**
```python
# Automated daily evaluation
- Generate 100 meal plans across all strategies
- Track: cost, latency, diversity, cache hits
- Compare vs baseline metrics
- Alert on regressions (>10% worse)
- Generate daily report dashboard
```

**Cost Dashboard:**
```
Strategy    | Avg Cost | Cache Hit | Latency | Diversity
------------|----------|-----------|---------|----------
fast_llm    | $0.02    | N/A       | 40s     | 85%
llm_only    | $0.08    | N/A       | 60s     | 95%
rag         | $0.10    | 85%       | 75s     | 90%
hybrid      | $0.12    | 85%       | 90s     | 92%
```

**Optimization Targets:**
- Reduce 7-day plan cost to <$0.05 (currently $0.02-0.15)
- Achieve <30s latency for all strategies
- Maintain >90% diversity across all strategies
- Reach >95% cache hit rate for RAG
- Support 1000+ concurrent users

## Acknowledgments

- **OpenAI GPT-4o-mini**: Powers the natural language understanding and recipe generation
- **Edamam Recipe Search API**: Provides real recipe data and nutrition information
- **FastAPI**: Modern, fast web framework for building APIs
- **Railway**: Simple, powerful deployment platform

---

**Built as part of an ML engineering assignment. The goal was to demonstrate API design, LLM integration, cost optimization, and production-ready code practices.**

For questions or issues, please open a GitHub issue.
