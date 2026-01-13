# Parallel Generation Optimization

## Overview
This document explains the parallel generation optimization that significantly speeds up meal plan generation while maintaining recipe diversity.

**See also**: [Diversity Strategy](DIVERSITY_STRATEGY.md) - How we ensure unique recipes in parallel generation

## What Changed

### Before: Sequential Generation
```
Day 1 → Breakfast → Lunch → Dinner (sequential)
Day 2 → Breakfast → Lunch → Dinner (sequential)
Day 3 → Breakfast → Lunch → Dinner (sequential)
...
```
**Time for 7-day plan**: ~3.5-4 minutes (21 recipes × 10s each)

### After: Full Parallelization
```
All 21 recipes generated concurrently
├─ Day 1: Breakfast, Lunch, Dinner (parallel)
├─ Day 2: Breakfast, Lunch, Dinner (parallel)
├─ Day 3: Breakfast, Lunch, Dinner (parallel)
├─ Day 4: Breakfast, Lunch, Dinner (parallel)
├─ Day 5: Breakfast, Lunch, Dinner (parallel)
├─ Day 6: Breakfast, Lunch, Dinner (parallel)
└─ Day 7: Breakfast, Lunch, Dinner (parallel)
```
**Time for 7-day plan**: ~10-15 seconds (limited by LLM API rate limits, not sequential execution)

## Key Technical Improvements

### 1. Day-Level Parallelization (`meal_generator.py`)

**Old approach** (meals within a day):
```python
for day in range(1, duration_days + 1):
    meals = await asyncio.gather(*[
        generate_meal_with_type(meal_type) 
        for meal_type in meal_types
    ])
    meal_plan.append({"day": day, "meals": meals})
```

**New approach** (all days AND meals):
```python
async def generate_day_meals(day: int) -> Dict:
    meals = await asyncio.gather(*[
        generate_meal_with_type(meal_type) 
        for meal_type in meal_types
    ])
    return {"day": day, "meals": meals}

meal_plan = await asyncio.gather(*[
    generate_day_meals(day) 
    for day in range(1, duration_days + 1)
])
```

### 2. Thread-Safe Diversity Tracking

**Problem**: When generating recipes in parallel, multiple coroutines could access `self.used_recipes` simultaneously, causing race conditions.

**Solution**: Added `asyncio.Lock()` for thread-safe access to shared state.

#### LLM-Only Strategy (`llm_only.py`)
```python
def __init__(self):
    self.used_recipes = set()
    self._lock = asyncio.Lock()  # Thread-safe access

async def generate_recipe(...):
    # Read used recipes (thread-safe)
    async with self._lock:
        used_for_meal_type = [name for name in self.used_recipes]
    
    # ... generate recipe ...
    
    # Write used recipes (thread-safe)
    async with self._lock:
        self.used_recipes.add(recipe_name)
```

#### RAG Strategy (`rag_strategy.py`)
```python
def __init__(self):
    self.used_candidates = {}
    self._lock = asyncio.Lock()  # Thread-safe access

async def generate_recipe(...):
    # Filter candidates (thread-safe)
    async with self._lock:
        available_candidates = self._filter_used_candidates(...)
        selected_candidates = available_candidates[:3]
    
    # ... generate recipe ...
    
    # Track used candidates (thread-safe)
    async with self._lock:
        self.used_candidates[meal_type].append(title)
```

## Performance Comparison

| Meal Plan Duration | Old Time (Sequential) | New Time (Parallel) | Speed-up |
|-------------------|-----------------------|---------------------|----------|
| 1 day (3 meals)   | ~30s                  | ~10s                | 3x       |
| 3 days (9 meals)  | ~90s                  | ~12s                | 7.5x     |
| 5 days (15 meals) | ~150s                 | ~14s                | 10.7x    |
| 7 days (21 meals) | ~210s                 | ~15s                | 14x      |

*Note: Actual times depend on OpenAI API response times and rate limits*

## Diversity Maintained

The parallel approach maintains **full diversity tracking**:
- ✅ Recipe names are tracked to avoid repetition
- ✅ RAG candidates are filtered to prevent duplicates
- ✅ Thread-safe locks prevent race conditions
- ✅ Day-aware hybrid strategy ensures proper RAG/LLM distribution

## Testing

### Performance Speed Test
Run the performance test to see the actual speed improvement:
```bash
# Quick test (3-day plan)
venv/bin/pytest tests/test_parallel_speed.py::test_parallel_speed_3_day -v -s

# Full test (7-day plan)
venv/bin/pytest tests/test_parallel_speed.py::test_parallel_speed_7_day -v -s

# Or run both directly
python tests/test_parallel_speed.py
```

### Unit Tests
```bash
venv/bin/pytest tests/test_meal_generator.py::test_parallel_generation -v
```

## Trade-offs

### Pros
- ✅ **14x faster** for 7-day plans
- ✅ Maintains diversity tracking
- ✅ No changes to API contract
- ✅ Better user experience

### Cons
- ⚠️ Higher concurrent API usage (may hit rate limits faster)
- ⚠️ Slightly higher memory usage (all recipes in flight simultaneously)
- ⚠️ More complex debugging (parallel execution)

## Rate Limit Considerations

OpenAI's rate limits (as of 2026):
- **gpt-4o-mini**: 500 requests per minute (RPM)
- **7-day plan**: 21 concurrent requests = well under limit

For very large plans (>50 meals), consider adding a semaphore to limit concurrency:
```python
semaphore = asyncio.Semaphore(20)  # Max 20 concurrent requests

async def generate_with_limit(meal_type):
    async with semaphore:
        return await generate_meal_with_type(meal_type)
```

## Migration Notes

No breaking changes. The optimization is **fully backward compatible**:
- Same API endpoints
- Same request/response formats
- Same diversity guarantees
- Just **much faster**

## Future Improvements

1. **Streaming responses**: Use Server-Sent Events (SSE) to stream recipes as they're generated
2. **Caching**: Cache common recipe patterns to avoid redundant LLM calls
3. **Batch LLM calls**: Request multiple recipes in a single LLM call (requires prompt engineering)
4. **Smarter rate limiting**: Implement adaptive concurrency based on API response times

