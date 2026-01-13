# How Validation Works: From Prompt to Meal Plan

This document explains how the system extracts and validates information from natural language prompts.

## 📋 Complete Flow

```
User Query → LLM Parsing → Validation → Meal Generation
```

---

## Step 1: User Enters Query

**Example Query:**
```
"Create a meal plan (vegetarian), 1 day, 2 meals, under 15 minutes prep time, budget-friendly"
```

---

## Step 2: LLM Parsing (`query_parser.py`)

The LLM (GPT-4o-mini) extracts structured data from the query:

**Input to LLM:**
```json
{
  "query": "Create a meal plan (vegetarian), 1 day, 2 meals, under 15 minutes prep time, budget-friendly"
}
```

**LLM Output (JSON):**
```json
{
  "duration_days": 1,
  "meals_per_day": 2,
  "meal_types": ["breakfast", "lunch"],
  "dietary_restrictions": ["vegetarian"],
  "preferences": [],
  "special_requirements": ["budget-friendly", "quick-meals"],
  "contradictions": []
}
```

**Note:** The LLM might miss some details (like exact prep time), so validators catch those.

---

## Step 3: Validation (`query_validator.py`)

The validator runs **6 validation functions** in sequence:

### Validator 1: `_validate_meal_count`

**What it does:**
- Uses **regex patterns** to find meal count in the original query
- Patterns it looks for:
  - `(\d+)\s*meals?` → "2 meals", "3 meals per day"
  - Specific meal types → "breakfast and lunch only"
  - "only" keyword → "breakfast only"

**Example:**
```python
query = "Create a meal plan, 2 meals"
meal_count_match = re.search(r'(\d+)\s*meals?', query.lower())
# Finds: "2 meals" → meal_count = 2
```

**Validation:**
- Checks if `1 <= meal_count <= 4`
- If outside range, clamps to valid range (1-4)
- Sets `parsed['meals_per_day'] = meal_count`

**Result:**
```python
parsed['meals_per_day'] = 2
parsed['meal_types'] = ['breakfast', 'lunch']  # Based on count
```

---

### Validator 2: `_validate_duration`

**What it does:**
- Validates duration is between 1-7 days
- Clamps to valid range if outside

**Example:**
```python
duration = parsed.get('duration_days', 3)  # From LLM
if duration > 7:
    parsed['duration_days'] = 7  # Clamp to max
```

**Result:**
```python
parsed['duration_days'] = 1  # Valid
```

---

### Validator 3: `_validate_dietary_restrictions`

**What it does:**
- Checks if too many restrictions (might be contradictory)
- Warns if > 5 restrictions

**Result:**
```python
# No warnings, restrictions are reasonable
parsed['dietary_restrictions'] = ['vegetarian']
```

---

### Validator 4: `_validate_contradictions`

**What it does:**
- Checks for known contradictions:
  - "vegan" + "pescatarian" ❌
  - "keto" + "high-carb" ❌
  - "low-carb" + "high-carb" ❌

**Result:**
```python
# No contradictions found
parsed['contradictions'] = []
```

---

### Validator 5: `_validate_budget` ⭐

**What it does:**
- Uses **keyword matching** to find budget constraints
- Searches for keywords in the **original query string**

**Keyword Dictionary:**
```python
budget_keywords = {
    'budget-friendly': ['budget', 'cheap', 'affordable', 'low cost', 'inexpensive'],
    'moderate': ['moderate', 'reasonable', 'average'],
    'premium': ['premium', 'expensive', 'luxury', 'gourmet', 'high-end']
}
```

**Example:**
```python
query = "Create a meal plan, budget-friendly"
query_lower = query.lower()  # "create a meal plan, budget-friendly"

# Check each keyword list
for level, keywords in budget_keywords.items():
    if any(keyword in query_lower for keyword in keywords):
        # Found: "budget" matches 'budget-friendly' keywords
        budget_level = 'budget-friendly'
        break
```

**Result:**
```python
parsed['special_requirements'].append('budget-friendly')
```

---

### Validator 6: `_validate_prep_time` ⭐

**What it does:**
- Uses **regex patterns** to extract time constraints from the **original query**

**Patterns it searches for:**
```python
time_patterns = [
    (r'(\d+)\s*minute', 'minutes'),      # "15 minutes"
    (r'(\d+)\s*min', 'minutes'),         # "15 min"
    (r'under\s*(\d+)', 'minutes'),       # "under 15"
    (r'less\s*than\s*(\d+)', 'minutes'), # "less than 15"
    (r'(\d+)\s*minute\s*or\s*less', 'minutes'),  # "15 minutes or less"
]
```

**Example:**
```python
query = "Create a meal plan, under 15 minutes prep time"
query_lower = query.lower()

# Try each pattern
for pattern, unit in time_patterns:
    match = re.search(pattern, query_lower)
    if match:
        # Pattern 3 matches: r'under\s*(\d+)'
        # match.group(1) = "15"
        prep_time_max = int(match.group(1))  # 15
        break
```

**Also checks for keywords:**
```python
quick_keywords = ['quick', 'fast', 'easy', 'simple', '15 minute', '30 minute']
if any(keyword in query_lower for keyword in quick_keywords):
    if prep_time_max is None:
        # Default to 30 minutes for "quick"
        prep_time_max = 30
```

**Result:**
```python
parsed['prep_time_max'] = 15
parsed['special_requirements'].append('quick-meals')
```

---

## Step 4: Final Validated Data

After all validators run, the final `parsed` dictionary looks like:

```python
{
    "duration_days": 1,
    "meals_per_day": 2,
    "meal_types": ["breakfast", "lunch"],
    "dietary_restrictions": ["vegetarian"],
    "preferences": [],
    "special_requirements": ["budget-friendly", "quick-meals"],
    "prep_time_max": 15,  # Added by validator
    "contradictions": []
}
```

---

## Step 5: Meal Generation (`meal_generator.py`)

The validated data is used to generate meals:

```python
# Uses meals_per_day and meal_types
meals_per_day = parsed.get("meals_per_day", 3)  # 2
meal_types = parsed.get("meal_types", ["breakfast", "lunch", "dinner"])  # ["breakfast", "lunch"]

# Only generates 2 meals (not 3!)
for meal_type in meal_types:  # Only loops twice
    recipe = recipe_service.generate_recipe(
        meal_type=meal_type,
        dietary_restrictions=parsed["dietary_restrictions"],  # ["vegetarian"]
        preferences=parsed["preferences"],
        special_requirements=parsed["special_requirements"],  # ["budget-friendly", "quick-meals"]
        prep_time_max=parsed.get("prep_time_max")  # 15
    )
```

---

## Step 6: Recipe Generation (`recipe_service.py`)

The recipe service uses `prep_time_max` in the LLM prompt:

```python
if prep_time_max:
    requirements.append(f"IMPORTANT: Preparation time must be {prep_time_max} minutes or less")

# LLM prompt includes:
# "IMPORTANT: Preparation time must be 15 minutes or less"
```

---

## 🔍 Key Techniques Used

### 1. **Regex Pattern Matching**
Used for extracting:
- Meal count: `r'(\d+)\s*meals?'`
- Prep time: `r'(\d+)\s*minute'`, `r'under\s*(\d+)'`
- Duration: `r'(\d+)\s*day'`

### 2. **Keyword Matching**
Used for:
- Budget constraints: searches for "budget", "cheap", "affordable"
- Quick meals: searches for "quick", "fast", "easy"

### 3. **LLM Extraction**
Used for:
- Complex dietary restrictions
- Preferences
- General structure extraction

### 4. **Validation & Clamping**
- Ensures values are in valid ranges
- Corrects invalid inputs
- Provides warnings

---

## 📝 Example: Complete Flow

**Input Query:**
```
"Create a vegetarian meal plan, 1 day, 2 meals, under 15 minutes, budget-friendly"
```

**Step-by-step extraction:**

1. **LLM extracts:**
   - `duration_days: 1`
   - `dietary_restrictions: ["vegetarian"]`
   - `special_requirements: ["budget-friendly"]`

2. **Validator extracts (from original query):**
   - `meals_per_day: 2` (from "2 meals")
   - `prep_time_max: 15` (from "under 15 minutes")
   - Confirms `budget-friendly` (from "budget-friendly")

3. **Final validated data:**
   ```python
   {
       "duration_days": 1,
       "meals_per_day": 2,
       "meal_types": ["breakfast", "lunch"],
       "dietary_restrictions": ["vegetarian"],
       "special_requirements": ["budget-friendly", "quick-meals"],
       "prep_time_max": 15
   }
   ```

4. **Meal generation:**
   - Generates exactly **2 meals** (breakfast, lunch)
   - All recipes are **vegetarian**
   - All recipes take **≤15 minutes** prep time
   - Recipes are **budget-friendly**

---

## 🎯 Why This Two-Stage Approach?

1. **LLM** is good at understanding context and extracting complex requirements
2. **Validators** are good at:
   - Extracting specific numbers (regex is more reliable)
   - Validating ranges
   - Catching edge cases
   - Providing corrections

**Together**, they provide:
- ✅ Accurate extraction
- ✅ Validation and correction
- ✅ Extensibility (easy to add new validators)

---

## 🔧 Adding New Validators

To add a new validation rule:

1. **Create validator method:**
   ```python
   def _validate_calories(self, query: str, parsed: Dict) -> ValidationResult:
       query_lower = query.lower()
       # Extract calories constraint
       match = re.search(r'(\d+)\s*calories?', query_lower)
       if match:
           calories_max = int(match.group(1))
           parsed['calories_max'] = calories_max
       return ValidationResult(is_valid=True)
   ```

2. **Register it:**
   ```python
   self.validators = [
       # ... existing validators ...
       self._validate_calories,  # Add here
   ]
   ```

3. **Done!** It runs automatically on every query.

---

## Summary

- **LLM** extracts structured data from natural language
- **Validators** use regex/keywords to extract specific constraints from the original query
- **Both** work together to ensure accurate extraction and validation
- **System** is extensible - add new validators easily

The key insight: **Validators read the original query string**, not just the LLM output, so they can catch things the LLM might miss!

