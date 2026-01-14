# Recipe Generation Strategies: Complete Information Flow

This document explains how the AI Meal Planner processes queries and generates meal plans, with a detailed walkthrough using a real example.

## Example Query Walkthrough

Let's trace how the system handles this query:
```
"I need a week of budget-friendly vegetarian meals"
```

### Step 1: Query Parsing (OpenAI API Call #1)

**What happens:**
The `QueryParser` sends the raw query to OpenAI GPT-4o-mini with a structured prompt.

**LLM Prompt sent:**
```
System: You are a meal plan query parser. Extract structured information...
- duration_days: Number of days (1-7, "week" = 7 days)
- dietary_restrictions: List of restrictions (vegan, vegetarian, gluten-free...)
- preferences: List of preferences (high-protein, low-carb...)
- special_requirements: List (budget-friendly, quick meals...)

User: Parse this meal plan query: "I need a week of budget-friendly vegetarian meals"
Return JSON with: duration_days, dietary_restrictions, preferences, special_requirements...
```

**LLM Response:**
```json
{
  "duration_days": 7,
  "meals_per_day": 3,
  "meal_types": ["breakfast", "lunch", "dinner"],
  "dietary_restrictions": ["vegetarian"],
  "preferences": [],
  "special_requirements": ["budget-friendly"],
  "contradictions": []
}
```

**Validation & Cleaning:**
- Duration capped at 7 days ✓
- "week" detected → confirmed as 7 days
- Extracts exclusions from query (e.g., "not Mediterranean" → adds to exclusions list)
- Checks for contradictions (e.g., "vegan" + "pescatarian")

**Final Parsed Object:**
```python
{
  "duration_days": 7,
  "meals_per_day": 3,
  "meal_types": ["breakfast", "lunch", "dinner"],
  "dietary_restrictions": ["vegetarian"],
  "preferences": [],
  "special_requirements": ["budget-friendly"],
  "exclusions": [],
  "contradictions": []
}
```

### Step 2: Contradiction Resolution

**What happens:**
The `MealPlanGenerator` checks for conflicting requirements.

**Example conflict:** "keto and high-carb meal plan"
- Detects: "keto" (low-carb) conflicts with "high-carb"
- Resolution: Keeps "keto" (dietary restriction priority), removes "high-carb"
- Generates warning: "I noticed you requested both high-carb and keto, which conflict. I've created a keto meal plan for you."

**Our example:** No contradictions detected ✓

### Step 3: Strategy Selection & Recipe Generation

Now the system generates recipes based on the selected strategy. Let's see how each strategy handles **Day 1** of our example.

---

## Strategy A: RAG (Retrieval-Augmented Generation)

**Best for:** Real recipes with verified nutrition data

### Step 3A: Fetch Edamam Candidates (Day 1 only)

**What happens:**
For each meal type, the system calls Edamam API to fetch real recipe candidates.

**Edamam API Call #1 (Breakfast):**
```
GET https://api.edamam.com/api/recipes/v2
?type=public
&q=breakfast vegetarian
&health=vegetarian
&to=10
&mealType=breakfast
```

**Edamam Response (5-10 candidates):**
```json
[
  {
    "title": "Avocado Toast with Poached Eggs",
    "ingredients": ["2 slices whole grain bread", "1 avocado", "2 eggs", "salt", "pepper"],
    "nutrition": {"calories": 320, "protein": 14.0, "carbs": 28.0, "fat": 18.0},
    "prep_time_minutes": 15,
    "url": "https://..."
  },
  {
    "title": "Greek Yogurt Parfait",
    "ingredients": ["1 cup Greek yogurt", "1/2 cup granola", "1/2 cup berries", "honey"],
    "nutrition": {"calories": 280, "protein": 18.0, "carbs": 42.0, "fat": 6.0},
    "prep_time_minutes": 10,
    "url": "https://..."
  },
  // ... 3-8 more candidates
]
```

**Edamam API Call #2 (Lunch):** Similar process for lunch candidates
**Edamam API Call #3 (Dinner):** Similar process for dinner candidates

**Caching:**
- These candidates are cached with key: `breakfast|vegetarian|None`
- Cache TTL: 1 hour
- Days 2-7: Use cached candidates (0 additional Edamam calls)

**Diversity Filter:**
- Tracks previously used candidates
- Filters out recipes already selected
- Shuffles remaining candidates for variety

### Step 3B: Generate Recipes with OpenAI (Batch per Day)

**What happens:**
All meal types for Day 1 are sent to OpenAI in ONE call with the Edamam candidates.

**OpenAI API Call #2 (Day 1 Batch):**

**System Prompt:**
```
You are a chef selecting from real recipe candidates. For each meal type, choose the best candidate matching requirements and create a complete recipe using the candidate's exact nutritional data. Make each recipe unique and diverse. Return valid JSON only.
```

**User Prompt:**
```
Create 3 recipes for day 1: breakfast, lunch, dinner.

Available recipe candidates:

BREAKFAST candidates:
1. Avocado Toast with Poached Eggs
   - Ingredients: 2 slices whole grain bread, 1 avocado, 2 eggs, salt, pepper
   - Nutrition: 320 cal, 14g protein, 28g carbs, 18g fat
   - Prep time: 15 minutes

2. Greek Yogurt Parfait
   - Ingredients: 1 cup Greek yogurt, 1/2 cup granola, 1/2 cup berries, honey
   - Nutrition: 280 cal, 18g protein, 42g carbs, 6g fat
   - Prep time: 10 minutes

[... 3 more breakfast candidates]

LUNCH candidates:
1. Mediterranean Chickpea Salad
   - Ingredients: 2 cups chickpeas, cucumber, tomatoes, feta, olive oil
   - Nutrition: 380 cal, 15g protein, 45g carbs, 16g fat
   - Prep time: 20 minutes

[... 4 more lunch candidates]

DINNER candidates:
1. Vegetable Stir-Fry with Tofu
   - Ingredients: 200g tofu, mixed vegetables, soy sauce, ginger, garlic
   - Nutrition: 420 cal, 22g protein, 38g carbs, 20g fat
   - Prep time: 25 minutes

[... 4 more dinner candidates]

Requirements:
Dietary restrictions: vegetarian
Special requirements: budget-friendly

For each meal type, choose ONE candidate that best matches requirements. Use EXACT nutritional values from chosen candidates.

Return JSON with a "recipes" array:
{
  "recipes": [
    {
      "meal_type": "breakfast",
      "recipe_name": "Creative name based on candidate",
      "description": "Brief description",
      "ingredients": ["2 cups flour", "1 tbsp oil", ...],
      "nutritional_info": {"calories": <exact from candidate>, "protein": <exact>, "carbs": <exact>, "fat": <exact>},
      "preparation_time": "X mins",
      "instructions": "Clear cooking steps",
      "source": "AI Generated (based on Edamam recipe)"
    }
  ]
}

Critical: Use EXACT nutrition from chosen candidates. Make recipe names natural and appetizing. Ensure each meal type gets a different recipe.
```

**OpenAI Response (Day 1 - All 3 Meals):**
```json
{
  "recipes": [
    {
      "meal_type": "breakfast",
      "recipe_name": "Creamy Greek Yogurt Parfait",
      "description": "A protein-rich breakfast with layers of Greek yogurt, crunchy granola, and fresh berries",
      "ingredients": ["1 cup Greek yogurt", "1/2 cup granola", "1/2 cup mixed berries", "1 tbsp honey"],
      "nutritional_info": {"calories": 280, "protein": 18.0, "carbs": 42.0, "fat": 6.0},
      "preparation_time": "10 mins",
      "instructions": "1. Layer Greek yogurt in a bowl. 2. Add granola and berries. 3. Drizzle with honey. 4. Serve immediately.",
      "source": "AI Generated (based on Edamam recipe)"
    },
    {
      "meal_type": "lunch",
      "recipe_name": "Mediterranean Chickpea Bowl",
      "description": "A hearty and budget-friendly salad packed with protein and fresh vegetables",
      "ingredients": ["2 cups chickpeas", "1 cucumber diced", "2 tomatoes diced", "1/4 cup feta cheese", "2 tbsp olive oil", "lemon juice"],
      "nutritional_info": {"calories": 380, "protein": 15.0, "carbs": 45.0, "fat": 16.0},
      "preparation_time": "20 mins",
      "instructions": "1. Drain and rinse chickpeas. 2. Chop vegetables. 3. Combine all ingredients. 4. Dress with olive oil and lemon. 5. Toss well and serve.",
      "source": "AI Generated (based on Edamam recipe)"
    },
    {
      "meal_type": "dinner",
      "recipe_name": "Tofu and Vegetable Stir-Fry",
      "description": "A quick and nutritious stir-fry with crispy tofu and colorful vegetables",
      "ingredients": ["200g firm tofu cubed", "2 cups mixed vegetables", "2 tbsp soy sauce", "1 tsp ginger minced", "2 cloves garlic minced", "1 tbsp sesame oil"],
      "nutritional_info": {"calories": 420, "protein": 22.0, "carbs": 38.0, "fat": 20.0},
      "preparation_time": "25 mins",
      "instructions": "1. Press and cube tofu. 2. Heat oil in wok. 3. Fry tofu until golden. 4. Add vegetables and stir-fry. 5. Add soy sauce, ginger, and garlic. 6. Cook for 5 minutes. 7. Serve hot.",
      "source": "AI Generated (based on Edamam recipe)"
    }
  ]
}
```

**Validation:**
- Checks nutrition values match Edamam candidates (within 20% tolerance)
- If mismatch detected: Auto-corrects to use exact Edamam nutrition
- Tracks selected candidates to avoid repetition
- Ensures prep time is realistic (minimum 10 minutes)

**Day 2-7:** Repeat Step 3B (OpenAI calls #3-8)
- Uses cached Edamam candidates
- 1 OpenAI call per day (batch generation)
- Total: 7 OpenAI calls for 7 days

**RAG Strategy Total API Calls:**
- 1 OpenAI for parsing
- 3 Edamam for candidates (Day 1 only)
- 7 OpenAI for generation (1 per day)
- **Total: 11 external API calls**

---

## Strategy B: LLM-Only

**Best for:** Creative recipes, maximum speed (no external recipe API)

### Step 3: Generate Recipes with OpenAI (Batch per Day)

**What happens:**
Pure AI generation without Edamam candidates. Uses variety hints for diversity.

**Variety Hint System (LLM-Only Strategy ONLY):**
- Day 1: "Mediterranean style"
- Day 2: "Asian fusion style"
- Day 3: "Italian style"
- Day 4: "American style"
- Day 5: "Mexican style"
- Day 6: "Indian style"
- Day 7: "French style"

**Hints are:**
- Randomized from a pool of 15+ cuisines
- Filtered to exclude user-specified exclusions (e.g., "not Mediterranean")
- Only suggestions (LLM can deviate if needed)
- **Not used in RAG, Fast LLM, or Hybrid strategies** (RAG uses candidate diversity, Fast LLM uses single call, Hybrid uses both approaches)

**OpenAI API Call #2 (Day 1 Batch):**

**System Prompt:**
```
You are a creative chef. Generate unique, realistic recipes that follow requirements. Make each recipe diverse and appetizing. Return valid JSON only.
```

**User Prompt:**
```
Create 3 recipes for day 1: breakfast, lunch, dinner.

Requirements:
Dietary: vegetarian
Special: budget-friendly

Variety: Mediterranean style. Be unique.

Return JSON with a "recipes" array:
{
  "recipes": [
    {
      "meal_type": "breakfast",
      "recipe_name": "Realistic, creative, appetizing name",
      "description": "Brief description",
      "ingredients": ["2 cups flour", "1 tbsp oil", ...],
      "nutritional_info": {"calories": <int>, "protein": <float>, "carbs": <float>, "fat": <float>},
      "preparation_time": "X mins",
      "instructions": "Step-by-step cooking instructions",
      "source": "AI Generated"
    }
  ]
}

Make recipe names natural (e.g., "Spinach and Feta Omelet", not "An Ideal Breakfast Recipe"). Include 8-10 ingredients with quantities. Provide 5-7 detailed cooking steps.
```

**OpenAI Response (Day 1 - All 3 Meals):**
```json
{
  "recipes": [
    {
      "meal_type": "breakfast",
      "recipe_name": "Spinach and Feta Scramble",
      "description": "A protein-rich Mediterranean breakfast with eggs, spinach, and tangy feta cheese",
      "ingredients": ["4 large eggs", "2 cups fresh spinach", "1/4 cup feta cheese crumbled", "1 tbsp olive oil", "1/4 onion diced", "salt and pepper to taste"],
      "nutritional_info": {"calories": 310, "protein": 22.0, "carbs": 8.0, "fat": 22.0},
      "preparation_time": "15 mins",
      "instructions": "1. Heat olive oil in a pan over medium heat. 2. Sauté onions until translucent. 3. Add spinach and cook until wilted. 4. Beat eggs and pour into pan. 5. Scramble gently. 6. Add feta cheese. 7. Season with salt and pepper. 8. Serve hot.",
      "source": "AI Generated"
    },
    {
      "meal_type": "lunch",
      "recipe_name": "Lentil and Vegetable Soup",
      "description": "A hearty, budget-friendly soup packed with protein and vegetables",
      "ingredients": ["1 cup red lentils", "2 carrots diced", "2 celery stalks diced", "1 onion diced", "3 cloves garlic minced", "4 cups vegetable broth", "1 tsp cumin", "1 tsp paprika", "2 tbsp olive oil", "salt and pepper"],
      "nutritional_info": {"calories": 340, "protein": 18.0, "carbs": 52.0, "fat": 8.0},
      "preparation_time": "35 mins",
      "instructions": "1. Heat olive oil in a large pot. 2. Sauté onions, carrots, and celery for 5 minutes. 3. Add garlic and spices, cook for 1 minute. 4. Add lentils and broth. 5. Bring to boil, then simmer for 25 minutes. 6. Season with salt and pepper. 7. Serve with crusty bread.",
      "source": "AI Generated"
    },
    {
      "meal_type": "dinner",
      "recipe_name": "Eggplant Parmesan",
      "description": "A classic Italian dish with layers of breaded eggplant, marinara, and melted cheese",
      "ingredients": ["2 medium eggplants sliced", "2 cups marinara sauce", "1 cup mozzarella cheese shredded", "1/2 cup parmesan cheese grated", "1 cup breadcrumbs", "2 eggs beaten", "1/4 cup olive oil", "fresh basil", "salt and pepper"],
      "nutritional_info": {"calories": 480, "protein": 24.0, "carbs": 48.0, "fat": 22.0},
      "preparation_time": "45 mins",
      "instructions": "1. Preheat oven to 375°F. 2. Dip eggplant slices in egg, then breadcrumbs. 3. Fry in olive oil until golden. 4. Layer eggplant, marinara, and cheese in baking dish. 5. Repeat layers. 6. Bake for 25 minutes until bubbly. 7. Garnish with fresh basil. 8. Let cool for 5 minutes before serving.",
      "source": "AI Generated"
    }
  ]
}
```

**Diversity Tracking:**
- Stores recipe names in thread-safe dictionary
- Checks for duplicates before accepting
- If duplicate detected: Regenerates that specific meal

**Day 2-7:** Repeat Step 3 (OpenAI calls #3-8)
- Different variety hints per day
- 1 OpenAI call per day (batch generation)
- Total: 7 OpenAI calls for 7 days

**LLM-Only Strategy Total API Calls:**
- 1 OpenAI for parsing
- 7 OpenAI for generation (1 per day)
- **Total: 8 OpenAI calls**

---

## Strategy C: Fast LLM

**Best for:** Ultra-fast generation, testing, demos

### Step 3: Generate ALL Meals in ONE Call

**What happens:**
Generates all 21 meals (7 days × 3 meals) in a single OpenAI call.

**Adaptive Detail:**
- 1-6 meals: Full detail (8-10 ingredients, 5-7 steps)
- 7-15 meals: Medium detail (5-7 ingredients, 3-5 steps)
- 16+ meals: Minimal detail (3-5 ingredients, 2-3 steps)

**OpenAI API Call #2 (Entire Plan):**

**System Prompt:**
```
You are an efficient chef. Generate simple, valid recipes quickly. Keep it concise. Return valid JSON only.
```

**User Prompt:**
```
Create 21 recipes for a 7-day meal plan (breakfast, lunch, dinner each day).

Requirements:
Dietary: vegetarian
Special: budget-friendly

Keep recipes simple with 3-5 ingredients and 2-3 step instructions.

Return JSON with a "days" array:
{
  "days": [
    {
      "day": 1,
      "meals": [
        {
          "meal_type": "breakfast",
          "recipe_name": "Simple name",
          "description": "One sentence",
          "ingredients": ["item 1", "item 2", "item 3"],
          "nutritional_info": {"calories": <int>, "protein": <float>, "carbs": <float>, "fat": <float>},
          "preparation_time": "X mins",
          "instructions": "Quick steps",
          "source": "AI Generated"
        }
      ]
    }
  ]
}

Be concise but realistic. All 21 meals should be different.
```

**OpenAI Response (All 21 Meals):**
```json
{
  "days": [
    {
      "day": 1,
      "meals": [
        {"meal_type": "breakfast", "recipe_name": "Oatmeal with Berries", ...},
        {"meal_type": "lunch", "recipe_name": "Veggie Wrap", ...},
        {"meal_type": "dinner", "recipe_name": "Pasta Primavera", ...}
      ]
    },
    {
      "day": 2,
      "meals": [...]
    },
    // ... days 3-7
  ]
}
```

**Fast LLM Strategy Total API Calls:**
- 1 OpenAI for parsing
- 1 OpenAI for entire plan generation
- **Total: 2 OpenAI calls**

---

## Strategy D: Hybrid

**Best for:** Balance of real recipes and creativity

### How It Works:

**Meal Distribution (70% RAG, 30% LLM):**
- Uses deterministic formula: `(day * 10 + meal_index) % 10 < 7` → RAG, else LLM
- Day 1: breakfast (RAG), lunch (RAG), dinner (RAG)
- Day 2: breakfast (RAG), lunch (RAG), dinner (LLM)
- Etc.

**Step 3A:** Fetch Edamam candidates (same as RAG)
**Step 3B:** Generate recipes per day
- Groups RAG meals → 1 batch OpenAI call with candidates
- Groups LLM meals → 1 batch OpenAI call without candidates
- Combines in original order

**Hybrid Strategy Total API Calls:**
- 1 OpenAI for parsing
- 3 Edamam for candidates
- 8-15 OpenAI for generation (depends on RAG/LLM distribution per day)
- **Total: 12-19 external API calls**

---

## Design Considerations & Protections

### 1. Cost Optimization
- **Batch generation**: Multiple meals per API call (not 1 call per meal)
- **Caching**: Edamam responses cached for 1 hour (3 calls instead of 21)
- **Model choice**: GPT-4o-mini (20x cheaper than GPT-4)
- **Fast mode**: 2 calls for entire 7-day plan

### 2. Diversity Protection
- **Variety hints**: Day-based cuisine suggestions (LLM-only strategy only, randomized, filtered by exclusions)
- **Candidate filtering**: Tracks used Edamam recipes, filters duplicates (RAG and Hybrid strategies)
- **Recipe tracking**: Thread-safe dictionary prevents repetition (all strategies)
- **Shuffle candidates**: Randomizes order before LLM selection (RAG and Hybrid strategies)
- **Diversity validation**: Tests ensure >80% unique meals (all strategies)

### 3. Data Validation
- **Pydantic models**: All inputs/outputs validated
- **Nutrition validation**: RAG strategy checks LLM nutrition vs Edamam (±20% tolerance)
- **Auto-correction**: If nutrition mismatch, uses exact Edamam values
- **Prep time validation**: Minimum 10 minutes, removes decimals
- **Duration capping**: Maximum 7 days enforced

### 4. Error Handling
- **Contradiction resolution**: Automatically resolves conflicts (e.g., keto + high-carb)
- **Fallback meal plan**: Always returns a valid 3-day plan on any error
- **User-friendly warnings**: Natural language messages (not technical errors)
- **Graceful degradation**: RAG falls back to LLM if no candidates found

### 5. Performance Optimization
- **Sequential days, batch meals**: Generates all meals for a day together
- **Async operations**: Non-blocking I/O for API calls
- **Connection pooling**: Reuses HTTP connections
- **Timeout handling**: 10-minute frontend timeout for large plans

### 6. Rate Limiting
- **System-wide**: 100 requests per minute
- **Per-IP**: 10 requests per minute
- **Graceful response**: Returns 429 with retry-after header

### 7. Caching Strategy
- **Key format**: `{meal_type}|{dietary_restrictions}|{prep_time_max}`
- **TTL**: 1 hour (configurable)
- **Thread-safe**: Uses locks for concurrent access
- **Cache hits**: Days 2-7 use cached Edamam candidates

---

## Strategy Comparison Table

| Strategy | Speed | Detail | API Calls (7-day) | Best For |
|----------|-------|--------|-------------------|----------|
| fast_llm | Fastest (40s) | Minimal | 2 OpenAI | Quick testing |
| llm_only | Fast (60s) | Detailed | 8 OpenAI | Creativity |
| rag | Medium (60-90s) | Detailed | 3 Edamam + 8 OpenAI | Real recipes |
| hybrid | Slower (135s) | Balanced | 3 Edamam + 8-15 OpenAI | Balance |

---

## Configuration

Set default in `.env`:
```bash
RECIPE_GENERATION_MODE=rag  # or llm_only, fast_llm, hybrid
```

Per-request via API:
```json
{
  "query": "week of budget-friendly vegetarian meals",
  "generation_mode": "rag"
}
```

Or select in frontend dropdown.

---

## Summary

The system processes queries through a pipeline:
1. **Parse** → Extract structured requirements (OpenAI)
2. **Validate** → Check constraints, resolve contradictions
3. **Generate** → Use selected strategy (RAG/LLM/Fast/Hybrid)
4. **Validate** → Check nutrition, diversity, format
5. **Return** → Complete meal plan with summary

All strategies prioritize:
- **Cost efficiency** (batch generation, caching, GPT-4o-mini)
- **Diversity** (variety hints, candidate filtering, tracking)
- **Reliability** (fallback plans, auto-correction, validation)
- **User experience** (natural warnings, always returns a plan)
