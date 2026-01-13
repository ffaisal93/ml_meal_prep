# Diversity Evaluation

Simple script to evaluate recipe diversity across different generation strategies.

## What It Tests

- Generates meal plans with all 4 strategies
- Counts unique recipes vs total meals
- Checks exclusion compliance (e.g., "not Mediterranean")
- Compares strategies side-by-side

## Test Cases

1. **1-day, 2-meal plan** (breakfast and lunch)
   - Tests basic functionality
   - Fast execution

2. **2-day vegetarian (exclude Mediterranean)**
   - Tests exclusion filtering
   - Verifies no Mediterranean recipes appear

3. **3-day full plan**
   - Tests diversity over multiple days
   - Standard meal plan size

## Running

```bash
cd evaluation
python simple_eval.py
```

## Output

```
Testing: 1-day 2-meal plan
================================================
Strategy          | Time   | Diversity | Unique/Total
------------------------------------------------
fast_llm          | 12.3s  | 100%      | 2/2
llm_only          | 15.7s  | 100%      | 2/2
rag               | 18.2s  | 100%      | 2/2
hybrid            | 21.4s  | 100%      | 2/2

Exclusion Check (not Mediterranean):
✓ fast_llm: No Mediterranean recipes
✓ llm_only: No Mediterranean recipes
...
```

## Diversity Calculation

```
Diversity Score = (Unique Recipes / Total Recipes) × 100
```

**Target**: >80% for good diversity

## Implementation Notes

This is a simple backend evaluation. No complex frontend needed - just runs the API directly and reports results.

The evaluation:
- Tests actual generation (not mocked)
- Checks real diversity (recipe name matching)
- Verifies exclusions work correctly
- Compares strategy performance

## Typical Results

- **fast_llm**: 80-90% diversity (optimized for speed)
- **llm_only**: 90-100% diversity (variety hints)
- **rag**: 85-95% diversity (real recipe pool)
- **hybrid**: 85-95% diversity (mixed approach)

All strategies maintain good diversity with minimal repetition.
