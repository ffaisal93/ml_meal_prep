# Information Workflow Diagram

## Complete Code Flow from Request to Response

```
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Endpoint                                           │
│  app/main.py::generate_meal_plan()                         │
│  POST /api/generate-meal-plan                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Rate Limiting                                              │
│  app/rate_limiter.py::check_system_rate_limit()            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Query Parsing                                               │
│  app/query_parser.py::QueryParser.parse()                   │
│    ├─> _parse_with_llm() [OpenAI GPT-4o-mini]              │
│    └─> _validate_and_clean()                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Query Validation                                           │
│  app/query_validator.py::QueryValidator.validate()          │
│    ├─> _validate_meal_count()                              │
│    ├─> _validate_duration()                                 │
│    └─> _validate_contradictions()                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Meal Plan Generator                                        │
│  app/meal_generator.py::MealPlanGenerator.generate()       │
│    ├─> _resolve_contradictions()                           │
│    ├─> Reset recipe tracking                               │
│    └─> Loop through days                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Recipe Service                                             │
│  app/recipe_service.py::RecipeService                       │
│    └─> Delegates to strategy                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Strategy Factory                                           │
│  app/recipe_generation/factory.py::RecipeStrategyFactory   │
│    ├─> "llm_only" → LLMOnlyStrategy                        │
│    ├─> "rag" → RAGStrategy                                 │
│    ├─> "hybrid" → HybridStrategy                           │
│    └─> "fast_llm" → FastLLMStrategy                        │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────────┐    ┌──────────────────┐
│  RAG Strategy    │    │  LLM-Only        │
│  (rag_strategy)  │    │  (llm_only)      │
└──────────────────┘    └──────────────────┘
        │                         │
        │                         │
        ▼                         ▼
┌─────────────────────────────────────────────────────────────┐
│  RAG Strategy Flow                                          │
│  app/recipe_generation/rag_strategy.py                      │
│                                                              │
│  generate_day_meals() OR generate_recipe()                   │
│    │                                                         │
│    ├─> _get_candidates()                                    │
│    │     ├─> Check TTLCache (candidate_cache)              │
│    │     │   ├─> Cache Hit? Return cached                  │
│    │     │   └─> Cache Miss? Continue...                    │
│    │     │                                                   │
│    │     └─> RecipeRetriever.get_candidates()              │
│    │           └─> HTTP call to Edamam API                  │
│    │           └─> Store in cache                           │
│    │                                                         │
│    ├─> Filter used_candidates [THREAD-SAFE with _lock]     │
│    │                                                         │
│    ├─> _generate_with_candidates()                          │
│    │     └─> OpenAI API call (selects & refines recipe)    │
│    │                                                         │
│    └─> Track used_candidates [THREAD-SAFE with _lock]      │
└─────────────────────────────────────────────────────────────┘
                     │
                     │
┌─────────────────────────────────────────────────────────────┐
│  LLM-Only Strategy Flow                                      │
│  app/recipe_generation/llm_only.py                          │
│                                                              │
│  generate_day_meals() OR generate_recipe()                   │
│    │                                                         │
│    ├─> Get used_recipes [THREAD-SAFE with _lock]           │
│    │                                                         │
│    ├─> _get_variety_hint()                                  │
│    │                                                         │
│    ├─> OpenAI API call (generates recipe)                  │
│    │                                                         │
│    └─> Track used_recipes [THREAD-SAFE with _lock]         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Response Assembly                                           │
│  app/meal_generator.py::_calculate_summary()                 │
│    ├─> Calculate total_meals                                 │
│    ├─> Calculate dietary_compliance                         │
│    ├─> Calculate estimated_cost                             │
│    └─> Calculate avg_prep_time                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Optional: Save User Preferences                             │
│  app/database.py::save_user_preference()                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  JSON Response Returned to Client                           │
└─────────────────────────────────────────────────────────────┘
```

## Key Method Invocation Points

1. **Entry Point**: `main.py::generate_meal_plan()` - FastAPI endpoint handler
2. **Parsing**: `query_parser.py::QueryParser.parse()` → `_parse_with_llm()` → `_validate_and_clean()`
3. **Validation**: `query_validator.py::QueryValidator.validate()` → multiple `_validate_*()` methods
4. **Orchestration**: `meal_generator.py::MealPlanGenerator.generate()` → `_resolve_contradictions()`
5. **Strategy Selection**: `factory.py::RecipeStrategyFactory.create()` → returns strategy instance
6. **RAG Path**: `rag_strategy.py::RAGStrategy._get_candidates()` → `recipe_retriever.py::RecipeRetriever.get_candidates()` → Edamam API
7. **LLM Path**: `llm_only.py::LLMOnlyStrategy.generate_recipe()` → direct OpenAI call
8. **Caching**: `rag_strategy.py::_get_candidates()` checks `self.candidate_cache` (TTLCache)
9. **Thread Safety**: `asyncio.Lock()` protects `used_candidates` and `used_recipes` dictionaries

## Data Flow Summary

```
Natural Language Query
    ↓
QueryParser.parse() → Structured Dict
    ↓
QueryValidator.validate() → Validated Dict
    ↓
MealPlanGenerator.generate() → Orchestrates day-by-day
    ↓
RecipeService → Delegates to Strategy
    ↓
Strategy (RAG/LLM-only/Hybrid)
    ├─> RAG: _get_candidates() → Cache Check → Edamam API → LLM
    └─> LLM-only: Direct OpenAI call
    ↓
Meal Plan (List of Days with Meals)
    ↓
_calculate_summary() → Statistics
    ↓
JSON Response
```

## Component Responsibilities

### 1. **Entry Point** (`app/main.py`)
- FastAPI endpoint handler
- Rate limiting enforcement
- Request validation
- Error handling

### 2. **Query Parsing** (`app/query_parser.py`)
- Natural language → structured data
- Uses LLM (GPT-4o-mini) for extraction
- Fallback to regex parsing

### 3. **Query Validation** (`app/query_validator.py`)
- Validates parsed query data
- Corrects invalid values
- Detects contradictions

### 4. **Meal Plan Generator** (`app/meal_generator.py`)
- Orchestrates entire meal plan generation
- Resolves contradictions
- Manages day-by-day generation
- Calculates summary statistics

### 5. **Recipe Service** (`app/recipe_service.py`)
- Strategy pattern wrapper
- Delegates to concrete strategy implementations

### 6. **Strategy Factory** (`app/recipe_generation/factory.py`)
- Creates appropriate strategy instance
- Based on configuration or request parameter

### 7. **RAG Strategy** (`app/recipe_generation/rag_strategy.py`)
- Fetches candidates from Edamam API
- Caches candidates (TTLCache, 1 hour TTL)
- Uses LLM to select and refine recipes
- Tracks used candidates (thread-safe)

### 8. **LLM-Only Strategy** (`app/recipe_generation/llm_only.py`)
- Pure LLM generation (no external API)
- Tracks used recipes for diversity (thread-safe)

### 9. **Recipe Retriever** (`app/recipe_retriever.py`)
- Edamam API client
- Fetches recipe candidates
- Maps dietary restrictions to API parameters

## Caching & Thread Safety

### Caching Layers:
1. **TTLCache** (`rag_strategy.py`)
   - Caches Edamam API responses
   - Key: `{meal_type}|{dietary_restrictions}|{prep_time_max}`
   - TTL: 1 hour (configurable via `CACHE_TTL_SECONDS`)
   - Thread-safe (internal to cachetools)

### Thread Safety:
1. **`used_candidates` dictionary** (`rag_strategy.py`)
   - Protected by `asyncio.Lock()`
   - Prevents duplicate candidates across concurrent requests

2. **`used_recipes` set** (`llm_only.py`)
   - Protected by `asyncio.Lock()`
   - Prevents duplicate recipe names across concurrent requests

## Strategy Selection Flow

```
Request with generation_mode parameter?
    ├─> Yes → Use specified mode
    └─> No → Use RECIPE_GENERATION_MODE from config
            ↓
        RecipeStrategyFactory.create(mode)
            ↓
        Returns appropriate strategy:
        • LLMOnlyStrategy
        • RAGStrategy
        • HybridStrategy (combines RAG + LLM-only)
        • FastLLMStrategy
```

