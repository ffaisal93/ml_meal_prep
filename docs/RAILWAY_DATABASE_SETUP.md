# Railway Database Setup Guide

This guide explains how to set up the database for Railway deployment.

## Option 1: PostgreSQL (Recommended for Production)

Railway provides managed PostgreSQL databases. This is the recommended approach for production deployments.

### Steps:

1. **Add PostgreSQL Service in Railway:**
   - Go to your Railway project dashboard
   - Click "New" → "Database" → "Add PostgreSQL"
   - Railway will automatically create a PostgreSQL database

2. **Railway automatically provides `DATABASE_URL`:**
   - Railway automatically sets the `DATABASE_URL` environment variable
   - The application will detect and use it automatically
   - No additional configuration needed!

3. **Verify:**
   - Check your Railway project's "Variables" tab
   - You should see `DATABASE_URL` automatically added
   - Format: `postgres://user:password@host:port/dbname`

### Benefits:
- ✅ Persistent data (survives redeployments)
- ✅ Managed service (automatic backups, scaling)
- ✅ Production-ready
- ✅ No additional setup required

---

## Option 2: SQLite with Persistent Volume

If you prefer SQLite, you can use Railway's persistent volume feature.

### Steps:

1. **Add Persistent Volume in Railway:**
   - Go to your Railway project dashboard
   - Click on your service → "Settings" → "Volumes"
   - Click "Add Volume"
   - Mount path: `/data` (or your preferred path)

2. **Set Environment Variable:**
   - Go to "Variables" tab
   - Add: `PERSISTENT_VOLUME_PATH=/data`
   - Add: `DB_PATH=meal_planner.db` (optional, defaults to this)

3. **Deploy:**
   - The database file will be stored at `/data/meal_planner.db`
   - Data persists across redeployments

### Benefits:
- ✅ Simple setup
- ✅ No external service needed
- ✅ Good for small to medium applications

### Limitations:
- ⚠️ Not recommended for high-traffic applications
- ⚠️ Single instance only (no horizontal scaling)

---

## Local Development

For local development, the app defaults to SQLite:

```bash
# Database file will be created at: meal_planner.db
# No configuration needed!
```

To use PostgreSQL locally:

```bash
# In your .env file:
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/meal_planner
```

---

## Database Initialization

The database tables are automatically created on application startup. You don't need to run migrations manually.

---

## Troubleshooting

### Database connection errors:

1. **Check Railway logs:**
   ```bash
   # In Railway dashboard → Deployments → View logs
   ```

2. **Verify DATABASE_URL:**
   - Railway automatically provides this
   - Check "Variables" tab in Railway dashboard

3. **For SQLite with persistent volume:**
   - Ensure `PERSISTENT_VOLUME_PATH` is set correctly
   - Check that the volume is mounted

### Reset database:

**PostgreSQL:**
- In Railway dashboard → PostgreSQL service → "Data" tab → "Reset Database"

**SQLite:**
- Delete the database file in the persistent volume
- Or redeploy (data will be lost if no persistent volume)

---

## Migration Notes

The application automatically:
- Detects `DATABASE_URL` → Uses PostgreSQL
- Detects `PERSISTENT_VOLUME_PATH` → Uses SQLite with persistent storage
- Otherwise → Uses SQLite in current directory (local dev)

No manual migration needed! 🎉

