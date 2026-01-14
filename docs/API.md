# API Documentation

Complete API reference for the AI Meal Planner.

## Base URL

```
https://your-api-url.railway.app
```

## Authentication

No authentication required. Rate limiting applies (10 requests/minute per IP).

## Endpoints

### Health Check

#### `GET /health`

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-15T10:30:00"
}
```

---

### Generate Meal Plan

#### `POST /api/generate-meal-plan`

Generate a personalized meal plan from natural language query.

**Request Body:**
```json
{
  "query": "Create a 3-day vegetarian meal plan",
  "user_id": "optional-user-id",
  "generation_mode": "llm_only"
}
```

**Parameters:**
- `query` (required, string): Natural language meal plan request
  - Examples:
    - "Create a 7-day low-carb meal plan"
    - "2-day vegetarian meal plan, exclude Mediterranean"
    - "5-day keto meal plan, budget-friendly, under 30 minutes"
- `user_id` (optional, string): User ID for preference tracking
- `generation_mode` (optional, string): Recipe generation strategy
  - Options: `"llm_only"`, `"rag"`, `"hybrid"`, `"fast_llm"`
  - Default: Uses server configuration

**Response:**
```json
{
  "meal_plan_id": "uuid-string",
  "duration_days": 3,
  "generated_at": "2025-01-15T10:30:00",
  "meal_plan": [
    {
      "day": 1,
      "date": "2025-01-15",
      "meals": [
        {
          "meal_type": "breakfast",
          "recipe_name": "High-Protein Oatmeal Bowl",
          "description": "A hearty and nutritious breakfast",
          "ingredients": ["2 cups oats", "1 cup milk", "1 banana"],
          "nutritional_info": {
            "calories": 350,
            "protein": 25.0,
            "carbs": 45.0,
            "fat": 8.0
          },
          "preparation_time": "15 mins",
          "instructions": "1. Cook oats with milk...",
          "source": "AI Generated"
        }
      ]
    }
  ],
  "summary": {
    "total_meals": 9,
    "dietary_compliance": ["vegetarian"],
    "estimated_cost": "$45-60",
    "avg_prep_time": "25 mins"
  },
  "warning": null
}
```

**Response Fields:**
- `meal_plan_id`: Unique identifier for this meal plan
- `duration_days`: Number of days (1-7)
- `generated_at`: ISO timestamp
- `meal_plan`: Array of daily meal plans
  - `day`: Day number (1-based)
  - `date`: ISO date string
  - `meals`: Array of meal objects
    - `meal_type`: "breakfast", "lunch", "dinner", or "snack"
    - `recipe_name`: Recipe title
    - `description`: Brief description
    - `ingredients`: Array of ingredient strings
    - `nutritional_info`: Nutrition data
      - `calories`: Integer
      - `protein`: Float (grams)
      - `carbs`: Float (grams)
      - `fat`: Float (grams)
    - `preparation_time`: String (e.g., "20 mins")
    - `instructions`: Step-by-step cooking instructions
    - `source`: Recipe source
- `summary`: Summary statistics
  - `total_meals`: Total number of meals
  - `dietary_compliance`: Array of dietary restrictions/preferences
  - `estimated_cost`: Cost range string
  - `avg_prep_time`: Average preparation time
- `warning`: Optional warning message (e.g., if contradictions were resolved)

**Status Codes:**
- `200`: Success
- `400`: Bad request (invalid query or generation_mode)
- `429`: Rate limit exceeded
- `500`: Internal server error

**Notes:**
- Always returns a meal plan (fallback to default if generation fails)
- Contradictions are automatically resolved with a warning message
- Maximum duration: 7 days (longer requests are capped)

---

### Get User Preferences

#### `GET /api/user/{user_id}/preferences`

Retrieve user's meal plan history and preferences.

**Path Parameters:**
- `user_id` (required, string): User identifier

**Query Parameters:**
- `limit` (optional, int): Maximum number of preferences to return (default: 10)

**Response:**
```json
{
  "user_id": "user123",
  "preferences": [
    {
      "query": "3-day vegetarian meal plan",
      "meal_plan_id": "uuid-string",
      "dietary_restrictions": ["vegetarian"],
      "preferences": ["high-protein"],
      "special_requirements": [],
      "created_at": "2025-01-15T10:30:00"
    }
  ],
  "total": 5
}
```

**Status Codes:**
- `200`: Success
- `404`: User not found
- `500`: Internal server error

---

## Rate Limiting

- **Limit**: 10 requests per minute per IP address
- **Response**: `429 Too Many Requests` when exceeded
- **Headers**: Rate limit information in response headers

## Error Responses

All errors follow this format:

```json
{
  "error": "Error type",
  "detail": "Detailed error message"
}
```

**Common Errors:**
- `400 Bad Request`: Invalid query or parameters
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error (meal plan still returned via fallback)

## Example Requests

### cURL

```bash
# Generate meal plan
curl -X POST "https://your-api-url.railway.app/api/generate-meal-plan" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Create a 3-day vegetarian meal plan",
    "generation_mode": "rag"
  }'
```

### Python

```python
import requests

url = "https://your-api-url.railway.app/api/generate-meal-plan"
payload = {
    "query": "Create a 3-day vegetarian meal plan",
    "generation_mode": "rag"
}
response = requests.post(url, json=payload)
meal_plan = response.json()
```

### JavaScript

```javascript
const response = await fetch('https://your-api-url.railway.app/api/generate-meal-plan', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'Create a 3-day vegetarian meal plan',
    generation_mode: 'rag'
  })
});
const mealPlan = await response.json();
```

## Interactive Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`

Visit these endpoints on your deployed API for interactive testing.

## Query Examples

**Simple:**
- "Create a 3-day meal plan"
- "7-day vegetarian meal plan"

**With Preferences:**
- "2-day low-carb meal plan"
- "5-day keto meal plan, high protein"

**With Restrictions:**
- "3-day vegan meal plan, exclude Mediterranean"
- "1-day gluten-free meal plan, dairy-free"

**With Special Requirements:**
- "7-day meal plan, budget-friendly, under 30 minutes"
- "3-day meal plan, quick meals, under 15 minutes prep time"

**Complex:**
- "Create a 5-day vegetarian, high-protein meal plan, exclude Italian, budget-friendly"
- "2-day keto meal plan, low-carb, under 20 minutes prep time"

## Generation Modes

- **`llm_only`**: Pure AI generation, fastest, most creative
- **`rag`**: Uses real Edamam recipes, most accurate nutrition
- **`hybrid`**: Mix of RAG and LLM-only (configurable ratio)
- **`fast_llm`**: Ultra-fast, generates entire plan in one call

See [Recipe Generation Strategies](RECIPE_GENERATION_STRATEGIES.md) for details.

