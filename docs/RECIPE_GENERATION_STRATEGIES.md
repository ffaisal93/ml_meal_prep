# Recipe Generation Strategies

The Meal Planner API supports multiple recipe generation strategies, allowing you to choose the best approach for your use case and evaluate different methods.

## 🎯 Overview

The system uses a **modular strategy pattern** that allows you to switch between different recipe generation approaches without code changes. This design enables:

- **Flexibility**: Choose the best strategy for your needs
- **Evaluation**: Compare different approaches side-by-side
- **Extensibility**: Easy to add new strategies in the future

## 📋 Available Strategies

### Strategy A: LLM-Only (`llm_only`)

**Description:** Pure LLM generation - no external recipe API calls.

**How it works:**
- LLM generates recipes entirely from scratch
- No external API dependencies
- Maximum creativity and variety

**Use cases:**
- Baseline for comparison
- When Edamam API is unavailable
- Maximum creative freedom needed
- Lower API costs

**Configuration:**
```bash
RECIPE_GENERATION_MODE=llm_only
```

---

### Strategy B: RAG (`rag`)

**Description:** Retrieval-Augmented Generation - Fetch real recipe candidates from Edamam, then LLM selects and refines.

**How it works:**
1. Fetch 3-7 real recipe candidates from Edamam API (one API call per unique meal type)
2. LLM selects the best candidate matching user requirements
3. LLM generates recipe using candidate's nutritional data and ingredients as "ground truth"
4. Ensures realistic nutrition values and cookable recipes

**Example workflow (3-day vegetarian plan):**
```
Day 1: Breakfast, Lunch, Dinner
Day 2: Breakfast, Lunch, Dinner  
Day 3: Breakfast, Lunch, Dinner

API Calls to Edamam:
1. Call 1: "vegetarian breakfast" → Get 5 breakfast candidates
2. Call 2: "vegetarian lunch" → Get 5 lunch candidates
3. Call 3: "vegetarian dinner" → Get 5 dinner candidates

Total: 3 Edamam calls (not 9, because meal types repeat across days)

For Day 1 Breakfast:
- Pick best candidate from the 5 breakfast options
- LLM refines it with user preferences
- Use candidate's real nutrition data

For Day 2 Breakfast:
- Pick different candidate from the same 5 breakfast options
- LLM refines differently for variety
- Use that candidate's real nutrition data

Result: Real nutrition values, no hallucination, efficient API usage
```

**Use cases:**
- Realistic nutrition values required
- Grounded in real recipes
- Better accuracy for dietary restrictions
- Production use with quality requirements

**Configuration:**
```bash
RECIPE_GENERATION_MODE=rag
EDAMAM_APP_ID=your_app_id
EDAMAM_APP_KEY=your_app_key
EDAMAM_USER_ID=your_user_id  # Optional, defaults to App ID
```

**API Efficiency:**
- 3-day plan (breakfast/lunch/dinner): **3 Edamam calls** + **3 LLM calls** = 6 total
- 7-day plan (breakfast/lunch/dinner): **3 Edamam calls** + **21 LLM calls** = 24 total
- Edamam candidates cached for 1 hour (reused across days)
- Key: Meal TYPE determines Edamam calls, not number of days

---

### Strategy C: Hybrid (`hybrid`)

**Description:** Mix of RAG and LLM-only generation.

**How it works:**
- Uses a configurable ratio to determine which strategy to use per recipe
- Example: 70% RAG, 30% LLM-only means 7 out of 10 recipes use RAG
- Provides balance between realism and creativity

**Use cases:**
- Best of both worlds
- Testing different ratios
- Evaluation framework development
- Customizable diversity

**Configuration:**
```bash
RECIPE_GENERATION_MODE=hybrid
HYBRID_RAG_RATIO=0.7  # 70% RAG, 30% LLM-only (0.0 to 1.0)
EDAMAM_APP_ID=your_app_id
EDAMAM_APP_KEY=your_app_key
```

**Ratio Examples:**
- `0.5` = 50% RAG, 50% LLM-only
- `0.7` = 70% RAG, 30% LLM-only (default)
- `0.9` = 90% RAG, 10% LLM-only

---

### Strategy D: Fast LLM (`fast_llm`)

**Description:** Ultra-fast generation for entire meal plans in a single API call.

**How it works:**
- Generates ALL meals for ALL days in ONE LLM call
- Adaptive detail based on plan duration (shorter details for longer plans)
- Prioritizes speed over detailed instructions
- Sequential generation with maximum batch optimization

**Use cases:**
- Quick previews and prototypes
- Large meal plans (5-7 days)
- Speed is critical
- Cost optimization (minimal API calls)

**Configuration:**
```bash
RECIPE_GENERATION_MODE=fast_llm
```

**Performance:**
- 7-day plan (21 meals): **1 API call** total
- 3-day plan (9 meals): **1 API call** total
- Fastest strategy available
- Good diversity through variety hints

---

## ⚙️ Configuration

### Environment Variables

Add these to your `.env` file or Railway environment variables:

```bash
# Recipe Generation Strategy (required)
RECIPE_GENERATION_MODE=rag  # Options: "llm_only", "rag", "hybrid", "fast_llm"

# Hybrid Strategy Configuration (only for hybrid mode)
HYBRID_RAG_RATIO=0.7  # Ratio of RAG recipes (0.0 to 1.0)

# Edamam API Credentials (required for RAG and hybrid modes)
EDAMAM_APP_ID=your_edamam_app_id
EDAMAM_APP_KEY=your_edamam_app_key
EDAMAM_USER_ID=your_user_id  # Optional, defaults to App ID
```

### Getting Edamam Credentials

1. Go to [Edamam Developer Portal](https://developer.edamam.com/admin/applications)
2. Sign up or log in
3. Click "Create a new application"
4. Select **"Recipe Search API"** (NOT Food Database API)
5. Copy your Application ID and Application Key
6. Set them as environment variables

**Free Tier:** 10,000 requests/month (more than enough for most use cases)

---

## 🔄 Switching Strategies

### Local Development

1. Edit your `.env` file:
   ```bash
   RECIPE_GENERATION_MODE=rag  # Change to desired mode
   ```

2. Restart your API server:
   ```bash
   python3 -m uvicorn app.main:app --reload
   ```

### Production (Railway)

1. Go to your Railway project dashboard
2. Select your API service
3. Go to "Variables" tab
4. Add or update `RECIPE_GENERATION_MODE`
5. Railway will automatically redeploy

**No code changes needed!** The factory pattern handles strategy selection automatically.

---

## 📊 Strategy Comparison

| Feature | LLM-Only | RAG | Hybrid | Fast LLM |
|---------|----------|-----|--------|----------|
| **Speed** | Moderate | Slow | Slow | ✅ Fastest |
| **API Calls (7-day)** | 7 | 21 | 21 | 1 |
| **Nutrition Accuracy** | ⚠️ Variable | ✅ High | ✅ High | ⚠️ Variable |
| **Creativity** | ✅ High | ⚠️ Moderate | ✅ Balanced | ✅ High |
| **Detail Level** | High | High | High | ⚠️ Adaptive |
| **API Costs** | Low | Medium | Medium | ✅ Lowest |
| **External Dependencies** | None | Edamam | Edamam | None |
| **Best For** | Balanced | Production | Evaluation | Speed/Cost |

---

## 🧪 Testing Different Strategies

### Test Locally

1. **Test LLM-Only:**
   ```bash
   export RECIPE_GENERATION_MODE=llm_only
   python3 -m uvicorn app.main:app --reload
   ```

2. **Test RAG:**
   ```bash
   export RECIPE_GENERATION_MODE=rag
   export EDAMAM_APP_ID=your_id
   export EDAMAM_APP_KEY=your_key
   python3 -m uvicorn app.main:app --reload
   ```

3. **Test Hybrid:**
   ```bash
   export RECIPE_GENERATION_MODE=hybrid
   export HYBRID_RAG_RATIO=0.7
   export EDAMAM_APP_ID=your_id
   export EDAMAM_APP_KEY=your_key
   python3 -m uvicorn app.main:app --reload
   ```

4. **Test Fast LLM:**
   ```bash
   export RECIPE_GENERATION_MODE=fast_llm
   python3 -m uvicorn app.main:app --reload
   ```

### Compare Results

Send the same query to each strategy and compare:
- Recipe diversity
- Nutrition accuracy
- Recipe quality
- Response time
- API costs

---

## 🏗️ Architecture

### Strategy Pattern

```
app/recipe_generation/
├── base.py              # Abstract base class (interface)
├── llm_only.py          # Strategy A: Pure LLM
├── rag_strategy.py      # Strategy B: Edamam + LLM
├── hybrid_strategy.py   # Strategy C: Mix of both
└── factory.py           # Factory to create strategies
```

### How It Works

1. **Factory** reads `RECIPE_GENERATION_MODE` from config
2. **Factory** creates the appropriate strategy instance
3. **RecipeService** uses the strategy to generate recipes
4. All strategies implement the same interface
5. Easy to swap strategies without code changes

### Adding New Strategies

1. Create a new file in `app/recipe_generation/`
2. Inherit from `RecipeGenerationStrategy` base class
3. Implement `generate_recipe()` and `get_strategy_name()` methods
4. Add to factory
5. Update config with new mode name

---

## 🚀 Performance Considerations

### API Call Efficiency

**RAG Strategy:**
- API calls = Number of unique meal types (not total meals)
- Example: 5-day plan with breakfast/dinner = **2 API calls**
- Candidates cached for 1 hour

**LLM-Only Strategy:**
- No external API calls (only OpenAI)
- Faster response time
- Lower external API costs

**Hybrid Strategy:**
- API calls depend on `HYBRID_RAG_RATIO`
- Example: 0.7 ratio = 70% of recipes use RAG (with caching)

### Caching

- **Edamam candidates:** Cached for 1 hour (TTL)
- **LLM recipes:** Cached by dietary constraints (TTL)
- **Used candidates:** Tracked per meal plan to avoid repetition

---

## 🔍 Troubleshooting

### "Edamam credentials required"

**Problem:** Using RAG or hybrid mode without Edamam credentials.

**Solution:**
- Set `RECIPE_GENERATION_MODE=llm_only` if you don't have Edamam credentials
- Or add Edamam credentials to your environment variables

### "No candidates found"

**Problem:** Edamam API returns 0 results (too restrictive query).

**Solution:**
- RAG strategy automatically falls back to LLM-only
- Try relaxing dietary restrictions
- Check Edamam API quota

### "Authentication failed: 401"

**Problem:** Invalid Edamam credentials.

**Solution:**
- Verify `EDAMAM_APP_ID` and `EDAMAM_APP_KEY` are correct
- Check that you're using Recipe Search API credentials (not Food Database)
- Ensure `EDAMAM_USER_ID` is set if your app requires it

---

## 📈 Future: Evaluation Framework

The modular architecture makes it easy to build an evaluation framework:

1. **Run same query with different strategies**
2. **Compare metrics:**
   - Recipe diversity
   - Nutrition accuracy
   - User satisfaction
   - API costs
   - Response time

3. **A/B testing:** Deploy different strategies and compare results

The consistent interface makes this straightforward to implement!

---

## 📚 Related Documentation

- **[Deployment Guide](DEPLOYMENT.md)** - How to deploy with different strategies
- **[Testing Guide](TESTING.md)** - How to test strategies locally
- **[Update Deployment](UPDATE_DEPLOYMENT.md)** - How to update strategy configuration

---

**Questions?** Check the main `README.md` or open an issue on GitHub.

