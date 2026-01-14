# Recipe Generation Strategies

The meal planner uses a strategy pattern to support four different recipe generation approaches. This design choice allows easy switching between methods and makes testing/comparison straightforward.

## Why Strategy Pattern?

**Design Choice**: Clean separation of concerns, easy to add new strategies, testable in isolation.

Each strategy implements the same interface but uses different approaches:
- Some prioritize speed
- Some prioritize accuracy
- Some balance both

## Strategy Comparison

| Strategy | Speed | Detail | API Calls (7-day) | Best For |
|----------|-------|--------|-------------------|----------|
| fast_llm | Fastest (40s) | Minimal | 2 OpenAI | Quick testing |
| llm_only | Fast (60s) | Detailed | 8 OpenAI | Creativity |
| rag | Medium (60-90s) | Detailed | 3 Edamam + 8 OpenAI | Real recipes |
| hybrid | Slower (135s) | Balanced | 3-9 Edamam + 8-22 OpenAI | Balance |

## Detailed Breakdown

### fast_llm (New!)

**What it does**: Generates ALL 21 meals in ONE API call

**Speed**: ~40s for 7-day plan (2-3s per meal)

**How it works**:
1. Sends one large request with all requirements
2. LLM returns all meals at once
3. Adaptive detail (shorter for longer plans)

**API calls**: Only 2
- 1 for query parsing
- 1 for full plan generation

**Output quality**: Simple but valid
- Recipe names: "Avocado Toast", "Quinoa Salad"
- Ingredients: 3-5 items
- Instructions: 1-2 sentences
- Nutrition: Estimated but accurate

**When to use**: Quick testing, demos, when speed matters more than detail

**Design choices implemented**:
- Cost optimization: Fewest API calls possible
- Batch processing: Maximum efficiency

### llm_only

**What it does**: Pure AI generation with creative recipes

**Speed**: ~60s for 7-day plan (3-4s per meal)

**How it works**:
1. Generates all meals for each day in one call
2. Uses variety hints (day-based cuisines)
3. Tracks used recipes to avoid repetition

**API calls**: 8 (1 parse + 7 day batches)

**Output quality**: Detailed and creative
- Recipe names: "Savory Spinach and Turkey Omelet"
- Ingredients: 8-10 items with quantities
- Instructions: 5-7 detailed steps
- Nutrition: AI-estimated

**When to use**: Maximum creativity, unique combinations

**Design choices implemented**:
- Diversity algorithm: Tracks used recipes, varies cuisines
- Batch generation: Reduces API calls vs sequential

### rag

**What it does**: Fetches real recipes from Edamam, LLM refines them

**Speed**: ~60-90s for 7-day plan (3-4s per meal)

**How it works**:
1. Fetches Edamam candidates for all meal types (cached per meal type)
2. Filters by dietary restrictions and exclusions
3. Sends all candidates to LLM in one batch call to generate all meals for the day
4. LLM selects best match for each meal type and formats recipes
5. Uses exact nutrition from Edamam database

**API calls for 7-day plan**:
- **Edamam calls**: 3 (one per meal type: breakfast, lunch, dinner)
  - Day 1: 3 calls (cache misses for each meal type)
  - Days 2-7: 0 calls (uses cache)
- **OpenAI calls**: 8 (1 for query parsing + 7 for batch recipe generation, one per day)
- **Total external calls**: 11

**Caching behavior**:
- Candidates cached per meal type using key: `{meal_type}|{dietary_restrictions}|{prep_time_max}`
- Cache TTL: 1 hour (configurable)
- Same meal type with same restrictions = cache hit (no Edamam call)

**Output quality**: Real recipes with verified data
- Recipe names: Actual dish names
- Ingredients: Real recipe ingredients
- Instructions: Real cooking steps
- Nutrition: From Edamam database

**When to use**: Need real recipes, accurate nutrition, verified data

**Requirements**: Edamam API credentials (free tier available)

**Design choices implemented**:
- Caching: TTLCache eliminates redundant Edamam calls (3 calls instead of 21)
- Nutritional validation: Uses real database values
- Diversity: Filters used candidates to avoid repetition

### hybrid

**What it does**: Mixes RAG (70%) and LLM-only (30%)

**Speed**: ~135s for 7-day plan (6-7s per meal)

**How it works**:
1. For 70% of meals: Uses RAG strategy
2. For 30% of meals: Uses LLM-only strategy  
3. Deterministic selection based on day/meal combination

**API calls for 7-day plan**:
- **Edamam calls**: 3-9 (depends on RAG ratio, cached per meal type)
- **OpenAI calls**: 8-22 (depends on RAG ratio)
- **Total**: 11-31 external API calls

**Output quality**: Mix of real and AI-generated
- Variety in both approach and content
- Some meals from database, some creative
- Balanced nutrition accuracy

**When to use**: Want both real recipes and creative options

**Requirements**: Edamam API credentials

**Design choices implemented**:
- Hybrid approach: Gets benefits of both strategies
- Configurable ratio: Can adjust RAG vs LLM percentage

## Configuration

Set default in `.env`:

```bash
RECIPE_GENERATION_MODE=fast_llm  # or llm_only, rag, hybrid
```

Per-request via API:

```json
{
  "query": "7-day meal plan",
  "generation_mode": "fast_llm"
}
```

Or select in frontend dropdown.

## Important Constraints

- Maximum 7 days (automatically enforced)
- Default 3 meals per day (breakfast, lunch, dinner)
- All strategies maintain >80% diversity

## Design Choices Summary

**Bonus Features Implemented**:

1. **Recipe Diversity Algorithm**: All strategies track used recipes/candidates
2. **Caching**: RAG strategy caches Edamam responses (TTLCache)
3. **Cost Optimization**: Batch generation, caching, chose GPT-4o-mini
4. **Structured Validation**: All outputs validated by Pydantic models
5. **Multiple Strategies**: Strategy pattern for clean architecture

## Performance Tips

1. Use `fast_llm` for development/testing
2. Use `llm_only` for production when speed matters
3. Use `rag` when accuracy/real recipes matter
4. Use `hybrid` for balanced results
5. All strategies benefit from caching on similar queries

## Real-World Performance

Tested locally with 7-day plans:
- fast_llm: 40s (2 OpenAI calls: 1 parse + 1 full plan)
- llm_only: 60s (8 OpenAI calls: 1 parse + 7 day batches)
- rag: 60-90s (3 Edamam calls + 8 OpenAI calls: 1 parse + 7 day batches)
- hybrid: 135s (mix of RAG and LLM-only, depends on ratio)

**Note on RAG caching**: Edamam calls are cached per meal type. For a 7-day plan:
- First day: 3 Edamam calls (breakfast, lunch, dinner)
- Remaining days: 0 Edamam calls (uses cache)
- Total: 3 Edamam calls (not 21)

All times include query parsing, generation, and validation.
