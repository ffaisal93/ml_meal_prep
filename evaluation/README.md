# Evaluation

This folder documents the **evaluation strategy** for comparing the three recipe generation modes:

- `llm_only`
- `rag`
- `hybrid`

The goals of the evaluation are:

1. **Diversity**: How diverse are the generated recipes (by name) across multiple runs?
2. **Stability**: How consistent are results between runs for the same configuration?
3. **Mode Comparison**: How do the three strategies compare for 1/3/5/7-day plans?

## Frontend Evaluation UI

The primary evaluation experience is implemented in the GitHub Pages frontend:

- Location: `ffaisal93.github.io/meal-planner`
- Trigger: **"Run Diversity Evaluation"** button on the main page
- Backend: Uses the existing `POST /api/generate-meal-plan` endpoint

### What the UI Does

For each combination of:

- **Durations**: 1, 3, 5, 7 days  
- **Modes**: `llm_only`, `rag`, `hybrid`

The UI runs multiple meal plan generations (configurable in code, default is 3 runs per configuration), then:

1. Collects all `recipe_name` values across all days and meals  
2. Normalizes names (lowercase + trim)  
3. Computes:
   - `total_meals` – total number of recipes generated
   - `unique_meals` – number of unique recipe names
   - `diversity_score` – `unique_meals / total_meals * 100` (percentage)
4. Displays results in a table for easy comparison across modes and durations

This evaluation is **client-driven** and does not require additional backend endpoints.

## How to Use

1. Start the API (e.g., on Railway or locally)
2. Open the GitHub Pages frontend (`meal-planner` site)
3. Enter the API URL in the **API Endpoint** field
4. Click **"Run Diversity Evaluation"**
5. Wait for the table to populate with diversity scores

## Notes

- Diversity is measured **only by recipe names**, which is a proxy for variety.
- The evaluation is intentionally lightweight and designed for **developer inspection**, not formal statistical analysis.
- For the take-home assignment, this demonstrates:
  - Awareness of evaluation needs
  - Ability to compare multiple strategies systematically
  - Frontend + backend integration for practical analysis


