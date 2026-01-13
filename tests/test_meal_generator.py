"""
Unit tests for MealPlanGenerator
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from app.meal_generator import MealPlanGenerator


class TestMealPlanGenerator:
    """Test meal plan generation logic"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.generator = MealPlanGenerator(strategy_mode="llm_only")
    
    @pytest.mark.asyncio
    async def test_generate_basic_plan(self):
        """Test basic meal plan generation"""
        query = "3-day vegetarian meal plan"
        
        # Mock the recipe service to avoid actual API calls
        mock_recipe = {
            "recipe_name": "Test Recipe",
            "description": "A test recipe",
            "ingredients": ["1 cup test"],
            "nutritional_info": {"calories": 300, "protein": 10.0, "carbs": 30.0, "fat": 5.0},
            "preparation_time": "20 mins",
            "instructions": "Test instructions",
            "source": "Test"
        }
        
        with patch.object(self.generator.recipe_service, 'generate_recipe', 
                         new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = mock_recipe
            
            result = await self.generator.generate(query)
            
            assert result["duration_days"] == 3
            assert len(result["meal_plan"]) == 3
            assert "meal_plan_id" in result
            assert "summary" in result
    
    @pytest.mark.asyncio
    async def test_batch_generation(self):
        """Test that generation works correctly with batch optimization"""
        query = "3-day meal plan"
        
        result = await self.generator.generate(query)
        
        # Verify structure
        assert len(result["meal_plan"]) == 3
        assert all(len(day["meals"]) == 3 for day in result["meal_plan"])
        
        # Verify all meals are unique (diversity check)
        meal_names = [meal['recipe_name'] 
                     for day in result['meal_plan'] 
                     for meal in day['meals']]
        unique_count = len(set(meal_names))
        diversity_score = (unique_count / len(meal_names)) * 100
        
        # Should have good diversity with batch generation + variety hints
        assert diversity_score >= 80.0, f"Diversity too low: {diversity_score:.1f}%"
    
    def test_calculate_summary(self):
        """Test summary calculation"""
        meal_plan = [
            {
                "day": 1,
                "date": "2025-01-15",
                "meals": [
                    {
                        "nutritional_info": {"calories": 300},
                        "preparation_time": "20 mins"
                    },
                    {
                        "nutritional_info": {"calories": 400},
                        "preparation_time": "30 mins"
                    }
                ]
            }
        ]
        
        parsed = {
            "dietary_restrictions": ["vegetarian"],
            "preferences": ["high-protein"]
        }
        
        summary = self.generator._calculate_summary(meal_plan, parsed)
        
        assert summary["total_meals"] == 2
        assert "vegetarian" in summary["dietary_compliance"]
        assert "high-protein" in summary["dietary_compliance"]
        assert "estimated_cost" in summary
        assert "avg_prep_time" in summary
    
    @pytest.mark.asyncio
    async def test_duration_capping(self):
        """Test that duration is capped at 7 days"""
        query = "10-day meal plan"
        
        with patch.object(self.generator.recipe_service, 'generate_recipe', 
                         new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = {
                "recipe_name": "Test",
                "description": "Test",
                "ingredients": ["1 cup test"],
                "nutritional_info": {"calories": 300, "protein": 10.0, "carbs": 30.0, "fat": 5.0},
                "preparation_time": "20 mins",
                "instructions": "Test",
                "source": "Test"
            }
            
            result = await self.generator.generate(query)
            assert result["duration_days"] == 7
            assert len(result["meal_plan"]) == 7
    
    @pytest.mark.asyncio
    async def test_contradiction_resolution(self):
        """Test that contradictions are automatically resolved with a warning"""
        query = "vegan pescatarian meal plan"
        
        result = await self.generator.generate(query)
        
        # Should succeed (not raise error)
        assert "meal_plan" in result
        assert len(result["meal_plan"]) > 0
        
        # Should have a warning message
        assert "warning" in result
        assert result["warning"] is not None
        assert len(result["warning"]) > 0
        
        # Warning should be user-friendly
        assert "contradictory" not in result["warning"].lower() or "conflict" in result["warning"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

