# How to Check if Database is Populated

## Method 1: Use the API Endpoint (Easiest)

### Step 1: Get Your User ID

1. Open your browser's Developer Console:
   - Chrome/Edge: `F12` or `Ctrl+Shift+I` (Windows) / `Cmd+Option+I` (Mac)
   - Firefox: `F12` or `Ctrl+Shift+I` (Windows) / `Cmd+Option+I` (Mac)
   - Safari: `Cmd+Option+I` (Mac)

2. Go to **Console** tab and type:
   ```javascript
   localStorage.getItem('mealPlannerUserId')
   ```
   - This will show your user ID (e.g., `user_1234567890_abc123`)

### Step 2: Check Your Preferences

```bash
# Replace USER_ID with your actual user ID from step 1
curl https://ml-meal-prep-api-production.up.railway.app/api/user/USER_ID/preferences
```

**Example:**
```bash
curl https://ml-meal-prep-api-production.up.railway.app/api/user/user_1705123456_k3j9x2m/preferences
```

**Expected Response:**
```json
{
  "user_id": "user_1705123456_k3j9x2m",
  "count": 2,
  "preferences": [
    {
      "id": 1,
      "query": "Create a 3-day vegetarian meal plan",
      "meal_plan_id": "mp_abc123",
      "dietary_restrictions": ["vegetarian"],
      "preferences": [],
      "special_requirements": [],
      "created_at": "2024-01-12T10:00:00"
    }
  ]
}
```

**If empty:**
```json
{
  "user_id": "user_1705123456_k3j9x2m",
  "count": 0,
  "preferences": []
}
```

---

## Method 2: Check Railway PostgreSQL Dashboard

1. **Go to Railway Dashboard:**
   - Click on your **Postgres** service
   - Go to **"Database"** tab

2. **View Data:**
   - Railway provides a web-based database viewer
   - Look for the `user_preferences` table
   - You should see rows with your data

3. **Query the Database:**
   - Click **"Query"** or **"SQL Editor"**
   - Run:
   ```sql
   SELECT * FROM user_preferences ORDER BY created_at DESC LIMIT 10;
   ```

---

## Method 3: Use Railway's Database CLI

1. **In Railway Dashboard:**
   - Go to **Postgres** service
   - Click **"Database"** tab
   - Click **"Connect"** or **"Open in Terminal"**

2. **Run SQL Query:**
   ```sql
   -- Count total preferences
   SELECT COUNT(*) FROM user_preferences;
   
   -- See all preferences
   SELECT * FROM user_preferences ORDER BY created_at DESC;
   
   -- See preferences for a specific user
   SELECT * FROM user_preferences WHERE user_id = 'user_1234567890_abc123';
   ```

---

## Method 4: Check API Logs

1. **In Railway Dashboard:**
   - Go to **`ml-meal-prep-api`** service
   - Click **"Deployments"** → Latest deployment
   - Click **"View Logs"**

2. **Look for:**
   - `"Database initialized"` - Database connection successful
   - `"Saved preference for user: user_..."` - Preferences being saved
   - Any database errors

---

## Method 5: Test End-to-End

### Complete Test Flow:

1. **Generate a meal plan with user_id:**
   ```bash
   curl -X POST https://ml-meal-prep-api-production.up.railway.app/api/generate-meal-plan \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Create a 3-day vegetarian meal plan",
       "user_id": "test_user_123"
     }'
   ```

2. **Check if it was saved:**
   ```bash
   curl https://ml-meal-prep-api-production.up.railway.app/api/user/test_user_123/preferences
   ```

3. **Expected Result:**
   - Should return the preference you just created
   - `count` should be `1` or more

---

## Troubleshooting

### Issue: Database is empty

**Check:**
1. Is `DATABASE_URL` set correctly in Railway?
2. Are you including `user_id` in requests?
3. Check API logs for errors
4. Verify Postgres service is "Online"

### Issue: API returns empty preferences

**Possible causes:**
1. `user_id` not being sent (check frontend code)
2. Database connection issue (check logs)
3. User ID mismatch (different user_id used)

### Issue: Can't connect to database

**Check:**
1. Postgres service status (should be "Online")
2. `DATABASE_URL` variable in API service
3. API logs for connection errors

---

## Quick Test Script

Save this as `test_database.sh`:

```bash
#!/bin/bash

API_URL="https://ml-meal-prep-api-production.up.railway.app"
USER_ID="test_user_$(date +%s)"

echo "Testing database with user_id: $USER_ID"

# Generate meal plan
echo "1. Generating meal plan..."
curl -X POST "$API_URL/api/generate-meal-plan" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"Create a 3-day vegetarian meal plan\",
    \"user_id\": \"$USER_ID\"
  }" | jq .

# Wait a moment
sleep 2

# Check preferences
echo "2. Checking saved preferences..."
curl "$API_URL/api/user/$USER_ID/preferences" | jq .

echo "Done! Check if preferences were saved."
```

Run it:
```bash
chmod +x test_database.sh
./test_database.sh
```

---

## Summary

**Easiest way:** Use Method 1 (API endpoint) - just get your user_id from localStorage and query it!

**Most visual:** Use Method 2 (Railway Dashboard) - see the data directly in the database.

