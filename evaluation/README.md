# Diversity Evaluation

Simple script to evaluate recipe diversity for the meal planner.

## Quick Evaluation

Run a simple test to compare all strategies:

```bash
cd /Users/faisal/Projects/ml_meal_prep
python evaluation/simple_eval.py
```

This will:
- Generate a 3-day meal plan for **each strategy** (LLM-Only, RAG, Hybrid)
- Check for duplicate recipe names
- Calculate diversity scores
- Display a comparison table

## What It Tests

**Diversity Score** = `(Unique Meals / Total Meals) × 100`

Example:
- 3-day plan = 9 total meals
- If 9 are unique → 100% diversity ✅
- If 8 are unique → 88.9% diversity (1 duplicate)

## Expected Results

- **90-100%**: Excellent diversity
- **75-89%**: Good diversity  
- **<75%**: Needs improvement

## Example Output

```
DIVERSITY COMPARISON TABLE
================================================================================
Strategy        Days     Total      Unique     Diversity    Grade     
--------------------------------------------------------------------------------
llm_only        3        9          9          100.0%       ✅ Excellent
rag             3        9          8          88.9%        👍 Good    
hybrid          3        9          9          100.0%       ✅ Excellent
================================================================================

🏆 Best Strategy: LLM_ONLY (100.0% diversity)
```

## Customize

Edit `simple_eval.py` to test different durations:

```python
# Change this line in main():
days = 5  # Test with 5-day plans instead of 3
```

Simple, fast, and reliable! 🎯
