"""
Tests for all recipe generation strategies
"""
import pytest
import asyncio
from app.meal_generator import MealPlanGenerator


class TestAllStrategies:
    """Test that all strategies work correctly"""
    
    @pytest.mark.asyncio
    async def test_llm_only_strategy(self):
        """Test LLM-only strategy"""
        generator = MealPlanGenerator(strategy_mode="llm_only")
        result = await generator.generate("3-day vegetarian meal plan")
        
        assert result["duration_days"] == 3
        assert len(result["meal_plan"]) == 3
        assert "meal_plan_id" in result
        assert "summary" in result
    
    @pytest.mark.asyncio
    async def test_fast_llm_strategy(self):
        """Test Fast LLM strategy"""
        generator = MealPlanGenerator(strategy_mode="fast_llm")
        result = await generator.generate("3-day healthy meal plan")
        
        assert result["duration_days"] == 3
        assert len(result["meal_plan"]) == 3
        assert "meal_plan_id" in result
        assert "summary" in result
    
    @pytest.mark.asyncio
    async def test_rag_strategy(self):
        """Test RAG strategy (requires Edamam API)"""
        generator = MealPlanGenerator(strategy_mode="rag")
        result = await generator.generate("2-day vegetarian meal plan")
        
        assert result["duration_days"] == 2
        assert len(result["meal_plan"]) == 2
        assert "meal_plan_id" in result
        assert "summary" in result
    
    @pytest.mark.asyncio
    async def test_hybrid_strategy(self):
        """Test Hybrid strategy (requires Edamam API)"""
        generator = MealPlanGenerator(strategy_mode="hybrid")
        result = await generator.generate("2-day healthy meal plan")
        
        assert result["duration_days"] == 2
        assert len(result["meal_plan"]) == 2
        assert "meal_plan_id" in result
        assert "summary" in result
    
    @pytest.mark.asyncio
    async def test_generate_day_meals_with_duration_days(self):
        """Test that generate_day_meals accepts duration_days parameter"""
        from app.recipe_generation.llm_only import LLMOnlyStrategy
        
        strategy = LLMOnlyStrategy()
        
        # This should not raise TypeError
        result = await strategy.generate_day_meals(
            day=1,
            meal_types=["breakfast", "lunch", "dinner"],
            dietary_restrictions=["vegetarian"],
            preferences=[],
            special_requirements=[],
            prep_time_max=None,
            exclusions=[],
            duration_days=7  # This parameter was missing before
        )
        
        assert isinstance(result, list)
        assert len(result) == 3
        assert all("recipe_name" in meal for meal in result)
        assert all("meal_type" in meal for meal in result)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

