"""
Simple diversity evaluation script
Tests a single strategy with minimal API calls to avoid failures
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.meal_generator import MealPlanGenerator


async def evaluate_diversity_custom(strategy="llm_only", days=3, query=None):
    """
    Simple evaluation: Generate one meal plan and check diversity
    
    Args:
        strategy: "llm_only", "rag", "hybrid", or "fast_llm"
        days: Number of days (1-7)
        query: Custom query string (optional)
    """
    print(f"\n{'='*60}")
    print(f"Diversity Evaluation: {strategy.upper()} - {days} days")
    print(f"{'='*60}\n")
    
    try:
        generator = MealPlanGenerator(strategy_mode=strategy)
        
        if query is None:
            query = f"{days}-day healthy, diverse meal plan"
        print(f"Query: '{query}'")
        print("Generating...")
        
        result = await generator.generate(query)
        
        # Collect all meal names
        meal_names = []
        for day in result['meal_plan']:
            for meal in day['meals']:
                name = meal['recipe_name'].lower().strip()
                meal_names.append(name)
                print(f"  Day {day['day']} - {meal['meal_type']}: {meal['recipe_name']}")
        
        # Calculate diversity
        total_meals = len(meal_names)
        unique_meals = len(set(meal_names))
        diversity_score = (unique_meals / total_meals * 100) if total_meals > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"Results:")
        print(f"  Total meals: {total_meals}")
        print(f"  Unique meals: {unique_meals}")
        print(f"  Diversity score: {diversity_score:.1f}%")
        print(f"{'='*60}\n")
        
        # Check for duplicates
        if unique_meals < total_meals:
            duplicates = [name for name in meal_names if meal_names.count(name) > 1]
            print(f"⚠️  Duplicates found: {set(duplicates)}")
        else:
            print("✅ No duplicates - Perfect diversity!")
        
        return {
            "strategy": strategy,
            "days": days,
            "total_meals": total_meals,
            "unique_meals": unique_meals,
            "diversity_score": diversity_score
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


async def main():
    """Run simple evaluation across all strategies"""
    strategies = ["llm_only", "rag", "hybrid", "fast_llm"]
    
    # Test configurations: (days, query, description)
    test_configs = [
        (1, "1-day meal plan with just breakfast and lunch", "1-day 2-meal plan (breakfast and lunch)"),
        (2, "2-day vegetarian meal plan not Mediterranean", "2-day vegetarian (EXCLUDE Mediterranean)"),
        (3, "3-day healthy, diverse meal plan", "3-day meal plan")
    ]
    
    all_results = []
    
    for days, query, description in test_configs:
        print(f"\n{'='*80}")
        print(f"TESTING: {description}")
        print(f"{'='*80}")
        
        results = []
        for strategy in strategies:
            result = await evaluate_diversity_custom(strategy=strategy, days=days, query=query)
            if result:
                result['test_description'] = description  # Add description to result
                results.append(result)
        
        all_results.extend(results)
        
        # Print comparison table for this config
        print_comparison_table(results, description)
        
        # For Mediterranean exclusion test, check if any recipes contain "mediterranean"
        if "EXCLUDE Mediterranean" in description:
            print("\n🔍 Checking if Mediterranean recipes were excluded...")
            for result in results:
                # This info would need to be collected during generation
                # For now, just note that filtering was applied
                pass

    
def print_comparison_table(results, description):
    """Print comparison table for results"""
    print("\n" + "="*80)
    print(f"DIVERSITY COMPARISON: {description}")
    print("="*80)
    print(f"{'Strategy':<15} {'Days':<8} {'Total':<10} {'Unique':<10} {'Diversity':<12} {'Grade':<10}")
    print("-"*80)
    
    for result in results:
        score = result['diversity_score']
        
        # Grade
        if score >= 90:
            grade = "✅ Excellent"
        elif score >= 75:
            grade = "👍 Good"
        else:
            grade = "⚠️  Low"
        
        print(f"{result['strategy']:<15} {result['days']:<8} "
              f"{result['total_meals']:<10} {result['unique_meals']:<10} "
              f"{score:.1f}%{'':<7} {grade:<10}")
    
    print("="*80)
    
    # Find best
    if results:
        best = max(results, key=lambda x: x['diversity_score'])
        print(f"🏆 Best for this test: {best['strategy'].upper()} ({best['diversity_score']:.1f}% diversity)")


async def evaluate_diversity(strategy="llm_only", days=3):
    """Backward compatibility wrapper"""
    return await evaluate_diversity_custom(strategy=strategy, days=days, query=None)


if __name__ == "__main__":
    print("\n🔍 Simple Diversity Evaluation")
    print("Testing all 4 strategies (LLM-Only, RAG, Hybrid, Fast LLM)")
    print("Configurations:")
    print("  1. 1-day (2 meals)")
    print("  2. 2-day vegetarian (EXCLUDE Mediterranean)")
    print("  3. 3-day (full plan)\n")
    asyncio.run(main())

