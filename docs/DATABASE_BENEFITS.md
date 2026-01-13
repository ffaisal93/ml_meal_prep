# How the Database Helps

The SQLite/PostgreSQL database stores **user preferences and meal plan history** to enable personalized experiences and analytics.

## 🎯 What It Stores

For each meal plan request (when `user_id` is provided), the database saves:

1. **User ID** - Identifies the user
2. **Original Query** - What the user asked for
3. **Meal Plan ID** - Links to the generated meal plan
4. **Dietary Restrictions** - Extracted from query (e.g., vegetarian, gluten-free)
5. **Preferences** - Extracted preferences (e.g., high-protein, low-carb)
6. **Special Requirements** - Other requirements (e.g., budget-friendly, quick meals)
7. **Timestamp** - When the request was made

## 💡 How It Helps

### 1. **User Preference History**
```
GET /api/user/{user_id}/preferences
```
- See what meal plans a user has requested before
- Track dietary preferences over time
- Understand user patterns

**Example Use Case:**
- User requests "vegetarian meal plan" multiple times
- You can see they prefer vegetarian options
- Future recommendations can default to vegetarian

### 2. **Personalization**
- Remember user preferences across sessions
- Suggest meal plans based on past requests
- Avoid repeating the same meals

**Example:**
```json
{
  "user_id": "user123",
  "preferences": [
    {
      "dietary_restrictions": ["vegetarian"],
      "preferences": ["high-protein"],
      "created_at": "2024-01-12T10:00:00"
    }
  ]
}
```

### 3. **Analytics & Insights**
- Track popular dietary restrictions
- See common meal plan patterns
- Understand user behavior

**Example Insights:**
- "60% of users request vegetarian meal plans"
- "Most users prefer 5-day meal plans"
- "High-protein is the most common preference"

### 4. **Meal Plan Retrieval**
- Link meal plans to user IDs
- Retrieve previously generated meal plans
- Build a meal plan library per user

### 5. **Future Features Enabled**
With this foundation, you can easily add:
- **Favorite meals** - Users can save favorite recipes
- **Meal plan sharing** - Share meal plans with others
- **Shopping lists** - Generate shopping lists from saved meal plans
- **Nutrition tracking** - Track nutrition over time
- **Recommendations** - AI-powered meal suggestions based on history

## 📊 Example API Usage

### Save Preference (Automatic)
```json
POST /api/generate-meal-plan
{
  "query": "Create a 5-day vegetarian meal plan",
  "user_id": "user123"
}
```
→ Automatically saves to database

### Retrieve User History
```bash
GET /api/user/user123/preferences?limit=10
```

**Response:**
```json
{
  "user_id": "user123",
  "count": 3,
  "preferences": [
    {
      "id": 1,
      "query": "Create a 5-day vegetarian meal plan",
      "meal_plan_id": "mp_abc123",
      "dietary_restrictions": ["vegetarian"],
      "preferences": [],
      "special_requirements": [],
      "created_at": "2024-01-12T10:00:00"
    },
    {
      "id": 2,
      "query": "3-day high-protein meal plan",
      "meal_plan_id": "mp_def456",
      "dietary_restrictions": [],
      "preferences": ["high-protein"],
      "special_requirements": [],
      "created_at": "2024-01-11T15:30:00"
    }
  ]
}
```

## 🔄 Without Database vs With Database

### Without Database:
- ❌ No user history
- ❌ No personalization
- ❌ Can't track preferences
- ❌ Every request is independent
- ❌ No analytics possible

### With Database:
- ✅ Complete user history
- ✅ Personalized experiences
- ✅ Preference tracking
- ✅ Connected meal plans
- ✅ Analytics and insights
- ✅ Foundation for advanced features

## 🚀 Real-World Example

**Scenario:** A user wants to create meal plans regularly

1. **First Request:**
   - User: "Create a vegetarian meal plan"
   - System saves: `{user_id: "user123", dietary_restrictions: ["vegetarian"]}`

2. **Second Request (weeks later):**
   - User: "Create another meal plan"
   - System can check history and suggest: "Based on your previous requests, would you like another vegetarian meal plan?"

3. **Analytics:**
   - System can see: "This user always requests vegetarian meal plans"
   - Can personalize future suggestions

## 📝 Summary

The database transforms the API from a **stateless service** into a **personalized meal planning system** that:
- Remembers user preferences
- Enables personalization
- Provides analytics
- Supports future features
- Creates a better user experience

**Bottom line:** The database enables the API to learn from user behavior and provide increasingly personalized meal planning experiences! 🍽️

