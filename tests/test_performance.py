"""
Performance test to measure batch generation speed and diversity.
Tests sequential generation with batch optimization (all meals for a day in one API call).

Usage:
    python -m pytest tests/test_performance.py -v -s
    OR
    python tests/test_performance.py
"""
import asyncio
import time
import pytest
from app.meal_generator import MealPlanGenerator

@pytest.mark.asyncio
async def test_batch_generation_7_day():
    """
    Performance test: Generate a 7-day meal plan and measure speed + diversity.
    This demonstrates batch generation (all meals for a day in one call).
    """
    generator = MealPlanGenerator(strategy_mode="llm")
    
    print("\n" + "="*60)
    print("Testing batch generation (7 API calls for 7 days)...")
    print("Generating 7-day meal plan (21 recipes total)...")
    print("="*60 + "\n")
    
    start = time.time()
    result = await generator.generate("7-day healthy meal plan")
    end = time.time()
    
    duration = end - start
    print(f"✅ Generated {len(result['meal_plan'])} days in {duration:.2f} seconds")
    print(f"   Total meals: {result['summary']['total_meals']}")
    print(f"   Average time per recipe: {duration / result['summary']['total_meals']:.2f}s")
    print(f"\n📊 Meal diversity:")
    
    # Check diversity
    meal_names = []
    for day in result['meal_plan']:
        for meal in day['meals']:
            meal_names.append(meal['recipe_name'])
    
    unique_meals = len(set(meal_names))
    diversity_score = unique_meals/len(meal_names)*100
    print(f"   Unique meals: {unique_meals}/{len(meal_names)}")
    print(f"   Diversity score: {diversity_score:.1f}%")
    print("\n" + "="*60)
    
    # Assertions
    assert len(result['meal_plan']) == 7
    assert result['summary']['total_meals'] == 21
    assert diversity_score >= 85.0, f"Diversity too low: {diversity_score:.1f}%"

@pytest.mark.asyncio
async def test_batch_generation_3_day():
    """
    Quick performance test with 3-day meal plan.
    """
    generator = MealPlanGenerator(strategy_mode="llm")
    
    print("\n" + "="*60)
    print("Quick test: 3-day meal plan (9 recipes)...")
    print("="*60 + "\n")
    
    start = time.time()
    result = await generator.generate("3-day balanced meal plan")
    end = time.time()
    
    duration = end - start
    print(f"✅ Generated in {duration:.2f} seconds")
    print(f"   Total meals: {result['summary']['total_meals']}")
    
    # Check diversity
    meal_names = [meal['recipe_name'] 
                  for day in result['meal_plan'] 
                  for meal in day['meals']]
    unique_meals = len(set(meal_names))
    diversity_score = unique_meals/len(meal_names)*100
    print(f"   Diversity: {unique_meals}/{len(meal_names)} ({diversity_score:.1f}%)")
    print("="*60)
    
    assert len(result['meal_plan']) == 3
    assert result['summary']['total_meals'] == 9

if __name__ == "__main__":
    # Allow running directly for quick testing
    print("Running batch generation performance tests...\n")
    asyncio.run(test_batch_generation_3_day())
    print("\n")
    asyncio.run(test_batch_generation_7_day())

