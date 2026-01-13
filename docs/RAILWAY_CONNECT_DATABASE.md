# Connecting PostgreSQL to Your API in Railway

## Quick Steps

### 1. Connect Database Using Variable Reference

Railway uses **Variable References** to share variables between services. Here's how to connect:

1. **Go to your API service:**
   - Click on **`ml-meal-prep-api`** service
   - Go to **"Variables"** tab

2. **Add Variable Reference:**
   - Click **"+ New Variable"** button
   - In the variable name field, type: `DATABASE_URL`
   - Click the **`{}`** icon (Reference button) next to the value field
   - Select **"Postgres"** service from the dropdown
   - Select **`DATABASE_URL`** from the Postgres variables
   - **Important:** Use `DATABASE_URL` (not `DATABASE_PUBLIC_URL`) - it's faster and more secure for internal connections
   - Click **"Add"**

3. **Verify:**
   - You should see `DATABASE_URL` in your API service variables
   - It should show as a reference (may have an icon or different styling)
   - The value will be automatically synced from Postgres

### 2. Verify Connection

After the Postgres service finishes initializing (status changes from "Initializing" to "Online"):

1. **Check API Logs:**
   - Go to **`ml-meal-prep-api`** service
   - Click **"Deployments"** → Latest deployment → **"View Logs"**
   - Look for: `"Database initialized"` message

2. **Test the Connection:**
   ```bash
   # Test health endpoint
   curl https://ml-meal-prep-api-production.up.railway.app/health
   
   # Test with user_id (should save to database)
   curl -X POST https://ml-meal-prep-api-production.up.railway.app/api/generate-meal-plan \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Create a 3-day vegetarian meal plan",
       "user_id": "test_user_123"
     }'
   ```

### 3. Verify Database is Working

Check if preferences are being saved:

```bash
# Get user preferences (should return saved data)
curl https://ml-meal-prep-api-production.up.railway.app/api/user/test_user_123/preferences
```

## How Railway Connects Services

Railway uses **Variable References** to connect services:
- ✅ Reference variables from other services (like `Postgres.DATABASE_URL`)
- ✅ Automatically syncs values when the source changes
- ✅ No need to manually copy/paste connection strings
- ✅ More secure - values are referenced, not duplicated

**Variable Reference Format:**
- `{{Postgres.DATABASE_URL}}` - References DATABASE_URL from Postgres service
- Railway automatically resolves this to the actual connection string

## Troubleshooting

### Issue: `DATABASE_URL` not found

**Solution:**
1. Make sure both services are in the **same Railway project**
2. Go to **Postgres** service → **"Variables"** tab
3. Copy the **`DATABASE_URL`** value (NOT `DATABASE_PUBLIC_URL`)
4. Go to **API** service → **"Variables"** → Add `DATABASE_URL`
5. Redeploy the API service

**Note:** 
- Use `DATABASE_URL` for internal Railway connections (faster, more secure)
- `DATABASE_PUBLIC_URL` is only needed if connecting from outside Railway

### Issue: Database connection errors

**Check:**
1. Is Postgres service **"Online"** (not "Initializing")?
2. Are both services in the same project?
3. Check API logs for specific error messages

### Issue: "Database initialized" not in logs

**Solution:**
1. Wait for Postgres to finish initializing
2. Check that `DATABASE_URL` is set correctly
3. Redeploy the API service

## Expected Behavior

Once connected:
- ✅ API automatically detects `DATABASE_URL`
- ✅ Database tables are created on startup
- ✅ User preferences are saved when `user_id` is provided
- ✅ You can retrieve user preferences via API

## Next Steps

After connection is verified:
1. Test saving a preference (include `user_id` in request)
2. Test retrieving preferences
3. Check Railway Postgres dashboard to see stored data

🎉 Your database is now connected and ready to store user preferences!

