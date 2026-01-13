# Recipe Generation Strategies

The AI Meal Planner supports 4 different recipe generation strategies, each optimized for different use cases.

## Strategy Comparison

| Strategy | Speed | Detail | API Calls (7-day) | Best For |
|----------|-------|--------|-------------------|----------|
| **fast_llm** | ⚡⚡⚡ Fastest | ⭐ Minimal | 2 | Quick testing, demos |
| **llm_only** | ⚡⚡ Fast | ⭐⭐⭐ Detailed | 8 | Creative variety |
| **hybrid** | ⚡ Medium | ⭐⭐ Balanced | 8-22 | Best balance |
| **rag** | ⚡ Medium | ⭐⭐⭐ Detailed | 22 | Real recipes, accuracy |

## Strategy Details

### ⚡ fast_llm (NEW!)
**Ultra-fast generation with minimal detail**

- **Speed**: ~40s for 7-day plan (~2-3s per meal)
- **API Calls**: 2 (1 parse + 1 full plan generation)
- **How it works**: Generates ALL 21 meals in ONE API call
- **Detail level**: Adaptive - shorter for longer plans
- **Perfect for**: Quick testing, demos, when speed > detail

**Example output:**
- Recipe name: "Avocado Toast"
- Ingredients: 3-5 items
- Instructions: 1-2 sentences
- Nutrition: Accurate estimates

### 🤖 llm_only
**Creative AI generation with full detail**

- **Speed**: ~60s for 7-day plan (~3-4s per meal)
- **API Calls**: 8 (1 parse + 7 day batches)
- **How it works**: Generates all meals for each day in one call
- **Detail level**: Full recipes with detailed instructions
- **Perfect for**: Maximum creativity, unique combinations

**Example output:**
- Recipe name: "Savory Spinach and Turkey Omelet"
- Ingredients: 8-10 items with quantities
- Instructions: 5-7 detailed steps
- Nutrition: AI-estimated

### 🔍 rag
**Real recipes from Edamam + AI refinement**

- **Speed**: ~60s for 7-day plan (~3-4s per meal)
- **API Calls**: 22 (1 parse + 21 individual)
- **How it works**: Fetches real recipes, LLM selects and refines
- **Detail level**: Full recipes with verified nutrition
- **Perfect for**: Real recipes, accurate nutrition
- **Requires**: Edamam API credentials

**Example output:**
- Recipe name: "Mediterranean Chickpea Salad"
- Ingredients: Real recipe ingredients
- Instructions: Real cooking steps
- Nutrition: From Edamam database

### ⚡ hybrid
**Mix of RAG and LLM-only**

- **Speed**: ~135s for 7-day plan (~6-7s per meal)
- **API Calls**: 8-22 (depends on RAG ratio, default 70%)
- **How it works**: 70% RAG, 30% LLM-only (configurable)
- **Detail level**: Balanced mix
- **Perfect for**: Best of both worlds
- **Requires**: Edamam API credentials

**Example output:**
- Mix of real recipes and AI-generated
- Variety in both approach and content
- Balanced nutrition accuracy

## Configuration

Set the default strategy in `.env`:

```bash
RECIPE_GENERATION_MODE=fast_llm  # or llm_only, rag, hybrid
```

Or specify per request via API:

```json
{
  "query": "7-day meal plan",
  "generation_mode": "fast_llm"
}
```

Or select in the frontend dropdown!

## Important Constraints

- ✅ **Maximum 7 days**: Plans are automatically capped at 7 days
- ✅ **3 meals per day**: Default (breakfast, lunch, dinner)
- ✅ **100% diversity**: Each recipe is unique (no duplicates)

## Recommendations

- **Development/Testing**: Use `fast_llm` for quick iterations
- **Production (speed)**: Use `llm_only` for fast, creative results  
- **Production (accuracy)**: Use `rag` for real recipes with verified nutrition
- **Production (balanced)**: Use `hybrid` for mix of both

## Performance Tips

1. **fast_llm** is 3-4x faster than other strategies
2. All strategies benefit from caching (subsequent similar queries)
3. Shorter meal plans (3 days) are faster across all strategies
4. RAG requires Edamam API - ensure credentials are set
