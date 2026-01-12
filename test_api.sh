#!/bin/bash
# Quick test script for the Meal Planner API

API_URL="${1:-http://localhost:8000}"

echo "🧪 Testing Meal Planner API at $API_URL"
echo ""

# Test 1: Health Check
echo "1. Testing Health Check..."
curl -s "$API_URL/health" | python -m json.tool
echo -e "\n"

# Test 2: Basic Query
echo "2. Testing Basic Query (3-day vegetarian)..."
curl -s -X POST "$API_URL/api/generate-meal-plan" \
  -H "Content-Type: application/json" \
  -d '{"query": "Create a 3-day vegetarian meal plan"}' \
  | python -m json.tool | head -50
echo -e "\n"

# Test 3: Complex Query
echo "3. Testing Complex Query..."
curl -s -X POST "$API_URL/api/generate-meal-plan" \
  -H "Content-Type: application/json" \
  -d '{"query": "Generate a 5-day low-carb meal plan with high protein"}' \
  | python -m json.tool | head -50
echo -e "\n"

echo "✅ Tests completed! Check output above for results."

