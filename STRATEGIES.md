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
| hybrid | Slower (135s) | Balanced | 3 Edamam + 8-15 OpenAI | Balance |

**Important**: All strategies use efficient batching:
- **"Batch"** = Multiple meals generated together in ONE API call
- NOT one call per meal (that would be 21+ calls)
- Example: "1 batch per day" = 1 call that generates breakfast + lunch + dinner together

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

**How it works** (two-step process):

**Step 1: Fetch Edamam Candidates** (External API)
- Day 1: Makes 3 Edamam API calls (one per meal type: breakfast, lunch, dinner)
- Each call fetches 5-10 recipe candidates with real nutrition data
- Days 2-7: Uses cached candidates (0 Edamam calls)

**Step 2: Generate Recipes with OpenAI** (This is the "batch")
- For each day: Makes 1 OpenAI call that generates ALL meals together
- Input: All Edamam candidates for breakfast, lunch, dinner
- Output: 3 complete recipes (one per meal type)
- LLM selects best candidate for each meal and formats it
- Uses exact nutrition from chosen Edamam candidates

**API calls for 7-day plan**:
- **Edamam calls**: 3 total
  - Day 1: 3 calls (fetch candidates for breakfast, lunch, dinner)
  - Days 2-7: 0 calls (uses cache from Day 1)
- **OpenAI calls**: 8 total
  - 1 call for query parsing
  - 7 calls for recipe generation (one "batch" per day)
  - Each batch generates all meals for that day together
- **Total external calls**: 11

**What "1 RAG batch" means**:
- 1 OpenAI API call that generates multiple meals together
- Example: Day 1 batch generates breakfast + lunch + dinner in ONE call
- NOT multiple calls (not 1 call per meal)
- Uses Edamam candidates that were already fetched

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

**How it works** (two-step process per day):

**Step 1: Fetch Edamam Candidates** (if RAG meals exist)
- Same as RAG strategy: 3 Edamam calls on Day 1, cached for Days 2-7

**Step 2: Generate Recipes with OpenAI** (batched by strategy)
- Groups meals by strategy (RAG vs LLM-only) per day
- **RAG batch**: 1 OpenAI call that generates all RAG meals together
  - Uses Edamam candidates that were already fetched
  - Example: If Day 1 has breakfast (RAG) + lunch (RAG), generates both in ONE call
- **LLM batch**: 1 OpenAI call that generates all LLM-only meals together
  - Pure AI generation (no Edamam candidates)
  - Example: If Day 1 has dinner (LLM), generates it in ONE call
- Combines results in original meal order

**API calls for 7-day plan** (with 70% RAG ratio):

**Step 1: Edamam Calls**
- **Edamam calls**: 3 total (same as RAG strategy)
  - Day 1: 3 calls (fetch candidates for breakfast, lunch, dinner)
  - Days 2-7: 0 calls (uses cache)

**Step 2: OpenAI Calls**
- **OpenAI calls**: 8-15 (depends on meal distribution)
  - 1 call for query parsing
  - RAG batches: 1 call per day (if RAG meals exist)
    - Each batch = 1 OpenAI call that generates all RAG meals together
  - LLM batches: 1 call per day (if LLM meals exist)
    - Each batch = 1 OpenAI call that generates all LLM meals together
  - **Actual**: With current formula, typically 8 calls (all meals use RAG)
  - **Maximum**: 15 calls if each day has both RAG and LLM meals

**Total**: 11-18 external API calls

**Example: How 15 calls would occur** (theoretical maximum):
- Day 1: breakfast (RAG) + lunch (RAG) + dinner (LLM)
  - 1 RAG batch (generates breakfast + lunch together) = 1 OpenAI call
  - 1 LLM batch (generates dinner) = 1 OpenAI call
  - Total for Day 1: 2 OpenAI calls
- If all 7 days follow this pattern: 7 × 2 = 14 + 1 parse = 15 calls

**Current behavior**: With the deterministic selection formula, all meals typically use RAG, resulting in 8 OpenAI calls (same as pure RAG strategy).

**What "1 RAG batch" means**:
- 1 OpenAI call that generates multiple RAG meals together
- Uses Edamam candidates that were already fetched
- NOT multiple calls (not 1 call per meal)

**What "1 LLM batch" means**:
- 1 OpenAI call that generates multiple LLM-only meals together
- Pure AI generation (no Edamam candidates)

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
- hybrid: 135s (3 Edamam calls + 8-15 OpenAI calls: depends on RAG/LLM distribution per day)

**Note on RAG caching**: Edamam calls are cached per meal type. For a 7-day plan:
- First day: 3 Edamam calls (breakfast, lunch, dinner)
- Remaining days: 0 Edamam calls (uses cache)
- Total: 3 Edamam calls (not 21)

All times include query parsing, generation, and validation.
