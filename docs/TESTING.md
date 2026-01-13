# Local Testing Guide

Step-by-step instructions to test the Meal Planner API locally.

## Prerequisites

- Python 3.9 or higher
- OpenAI API key

## Step 1: Check Python Version

```bash
cd /Users/faisal/Projects/ml_meal_prep
python3 --version
```

Should show Python 3.9+.

## Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# OR
# venv\Scripts\activate  # On Windows
```

You should see `(venv)` in your terminal prompt.

## Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

## Step 4: Create .env File

```bash
# Copy the example file
cp ENV_EXAMPLE.txt .env

# Edit .env and add your OpenAI API key
# You can use: nano .env  or  open -e .env  (macOS)
```

Or create it manually:
```bash
cat > .env << EOF
OPENAI_API_KEY=your_actual_openai_api_key_here
API_HOST=0.0.0.0
API_PORT=8000
CACHE_TTL_SECONDS=3600
EOF
```

**Important:** Replace `your_actual_openai_api_key_here` with your real OpenAI API key!

## Step 5: Start the API Server

```bash
# Make sure venv is activated (you should see (venv) in prompt)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Step 6: Test the API

### Option A: Using the Test Script

Open a **new terminal** (keep the server running), then:

```bash
cd /Users/faisal/Projects/ml_meal_prep
./test_api.sh
```

### Option B: Using curl

```bash
# Health check
curl http://localhost:8000/health

# Generate a meal plan
curl -X POST http://localhost:8000/api/generate-meal-plan \
  -H "Content-Type: application/json" \
  -d '{"query": "Create a 3-day vegetarian meal plan"}'
```

### Option C: Using the Interactive API Docs

Open in browser:
```
http://localhost:8000/docs
```

This gives you a Swagger UI where you can:
1. Click on `/api/generate-meal-plan`
2. Click "Try it out"
3. Enter a query like: `"Create a 3-day vegetarian meal plan"`
4. Click "Execute"
5. See the response!

### Option D: Test with Frontend

Open the frontend HTML file:
```bash
# In another terminal
cd /Users/faisal/Projects/ml_meal_prep/frontend
python3 -m http.server 8080
```

Then open: `http://localhost:8080`

Enter `http://localhost:8000` as the API endpoint and test!

## Step 7: Test Different Queries

Try these example queries:

1. **Basic:**
   ```json
   {"query": "Create a 3-day vegetarian meal plan"}
   ```

2. **Complex:**
   ```json
   {"query": "Generate a 7-day low-carb, dairy-free meal plan with high protein, budget-friendly options"}
   ```

3. **Quick meals:**
   ```json
   {"query": "5-day Mediterranean diet plan with quick breakfast options under 15 minutes"}
   ```

## Troubleshooting

### Error: "OPENAI_API_KEY not found"
- Make sure `.env` file exists in the project root
- Check that it contains `OPENAI_API_KEY=your_key_here`
- Restart the server after creating/editing `.env`

### Error: "Module not found"
- Make sure virtual environment is activated
- Run: `pip install -r requirements.txt`

### Error: "Address already in use"
- Port 8000 is already in use
- Change port: `uvicorn app.main:app --reload --port 8001`
- Or kill the process using port 8000

### API returns errors
- Check your OpenAI API key is valid
- Verify you have API credits
- Check server logs for detailed error messages

### CORS errors (when testing frontend)
- The API should have CORS enabled by default
- Make sure you're accessing the frontend from `http://localhost:8080` (not `file://`)

## Unit Tests

The project includes comprehensive unit tests for core components.

### Running Unit Tests

```bash
# Make sure you're in the project root and venv is activated
source venv/bin/activate

# Install test dependencies (if not already installed)
pip install -r requirements.txt

# Run all unit tests
pytest tests/ -v

# Run specific test file
pytest tests/test_edge_cases.py -v
pytest tests/test_query_validator.py -v
pytest tests/test_meal_generator.py -v

# Run with coverage report (if pytest-cov installed)
pytest tests/ --cov=app --cov-report=html
```

### Test Files

- **`tests/test_query_validator.py`**: Tests for query validation (duration limits, contradictions, meal count)
- **`tests/test_edge_cases.py`**: Tests for assignment edge cases (all 5 test cases from requirements)
- **`tests/test_meal_generator.py`**: Tests for meal plan generation (batch generation, diversity, summary calculation)

### What's Tested

- ✅ Query parsing and validation
- ✅ Duration limits (1-7 days)
- ✅ Contradiction detection
- ✅ Edge cases from assignment requirements
- ✅ Meal plan generation logic
- ✅ Batch generation performance and diversity
- ✅ Error handling

### Test Examples

The test suite includes tests for:
- Basic queries: `"Create a 3-day vegetarian meal plan"`
- Complex queries: `"7-day low-carb, dairy-free meal plan with high protein"`
- Edge cases: `"10-day vegan plan"` (should cap at 7 days)
- Contradictions: `"Pescatarian vegan meal plan"` (should raise error)
- Ambiguous queries: `"healthy meals for next week"` (should use defaults)

## Quick Commands Reference

```bash
# Activate venv
source venv/bin/activate

# Start server
uvicorn app.main:app --reload

# Run manual API tests
./test_api.sh

# Run unit tests
pytest tests/ -v

# Deactivate venv (when done)
deactivate
```

## Next Steps

Once local testing works:
1. Deploy API to Railway
2. Update frontend with Railway URL
3. Deploy frontend to GitHub Pages
4. Test the full stack!

