#!/bin/bash
# Test 7-day meal plan generation via API

echo "🧪 Testing 7-day meal plan generation..."
echo ""

curl -X POST http://localhost:8000/api/generate-meal-plan \
  -H "Content-Type: application/json" \
  -d '{"query": "Create a 7 day low-carb meal plan", "generation_mode": "hybrid"}' \
  --max-time 600 \
  | python -m json.tool | head -100

echo ""
echo "✅ If you see meal data above, the API is working!"
