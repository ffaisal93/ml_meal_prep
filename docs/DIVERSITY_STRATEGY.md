# Simple Diversity Strategy for Parallel Generation

## The Problem

When generating 21 recipes in parallel (7 days × 3 meals), **all LLM calls start at the same time** with the same empty `used_recipes` list. This could lead to duplicate recipes.

## Smart Solution ✅

### Give Each Day a Different "Variety Hint"

Instead of forcing specific cuisines (which might conflict with user preferences), we add **subtle variety hints**:

#### Case 1: User Specifies Cuisine (e.g., "Indian meals")
```
Day 1 → "Use grains as the base" (e.g., Indian rice dishes)
Day 2 → "Make it protein-focused" (e.g., Indian lentil dal)
Day 3 → "Include legumes" (e.g., Chickpea curry)
Day 4 → "Feature vegetables" (e.g., Mixed vegetable curry)
Day 5 → "Use soup/stew format" (e.g., Sambar, Rasam)
Day 6 → "Make it a bowl/salad" (e.g., Rice bowl with chutney)
Day 7 → "Try sandwich/wrap style" (e.g., Kathi roll, paratha wrap)
```
**Respects user's cuisine but varies the format!**

#### Case 2: No Cuisine Specified
```
Day 1 → "Mediterranean or Italian inspired"
Day 2 → "Asian or Mexican inspired"
Day 3 → "Middle Eastern or Indian inspired"
Day 4 → "American or European inspired"
Day 5 → "Latin American or Thai inspired"
Day 6 → "Japanese or Greek inspired"
Day 7 → "Moroccan or fusion inspired"
```

### Example

**User Query**: "7-day vegan Indian meal plan"

```
Day 1 Breakfast: "Use grains as base" → Masala Oats
Day 2 Breakfast: "Make it protein-focused" → Chickpea Scramble (Besan Chilla)
Day 3 Breakfast: "Include legumes" → Moong Dal Pancakes
Day 4 Breakfast: "Feature vegetables" → Vegetable Poha
Day 5 Breakfast: "Soup format" → Sambar with Idli
...
```

All stay **Indian + vegan**, but use **different base ingredients/formats** 🎯

## Implementation

### Simple Code
```python
def _get_variety_hint(self, day: int, preferences: List[str]) -> str:
    # Check if user wants specific cuisine
    if "indian" in preferences or "mexican" in preferences:
        # Vary by cooking method/format
        hints = {
            1: "Use grains as the base",
            2: "Make it protein-focused",
            3: "Include legumes",
            # ...
        }
    else:
        # Suggest cuisine variety
        hints = {
            1: "Mediterranean inspired",
            2: "Asian inspired",
            # ...
        }
    return hints[day]
```

## Why This Works

✅ **Respects user constraints** - Doesn't conflict with their cuisine preference  
✅ **Simple** - Just a hint in the prompt, no complex tracking  
✅ **Fast** - Zero performance impact  
✅ **Effective** - Different hints per day → different recipes  

## Also Using

- **High temperature** (`0.9`) for more LLM creativity
- **Thread-safe locks** to prevent race conditions when updating `used_recipes`

That's it! **Simple and effective** 🎯
