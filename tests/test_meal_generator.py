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
    async def test_parallel_generation(self):
        """Test that meals and days are generated in parallel"""
        query = "3-day meal plan"
        
        # Track call order to verify parallel execution
        call_times = []
        
        async def mock_generate_with_timing(*args, **kwargs):
            import time
            call_times.append(time.time())
            await asyncio.sleep(0.05)  # Simulate API delay
            return {
                "recipe_name": "Test Recipe",
                "description": "Test",
                "ingredients": ["1 cup test"],
                "nutritional_info": {"calories": 300, "protein": 10.0, "carbs": 30.0, "fat": 5.0},
                "preparation_time": "20 mins",
                "instructions": "Test",
                "source": "Test"
            }
        
        with patch.object(self.generator.recipe_service, 'generate_recipe', 
                         new_callable=AsyncMock) as mock_gen:
            mock_gen.side_effect = mock_generate_with_timing
            
            import time
            start_time = time.time()
            result = await self.generator.generate(query)
            end_time = time.time()
            
            # With parallel generation across days AND meals:
            # 3 days * 3 meals = 9 recipes, but all in parallel should take ~0.05s (not 0.45s)
            # Allow generous margin for overhead
            assert (end_time - start_time) < 0.2  # Should be much faster than sequential
            assert len(result["meal_plan"]) == 3
            assert all(len(day["meals"]) == 3 for day in result["meal_plan"])
            
            # Verify all calls happened close together (parallel)
            if len(call_times) > 1:
                time_diffs = [call_times[i+1] - call_times[i] for i in range(len(call_times)-1)]
                # Most calls should start within 0.05s of each other (parallel)
                parallel_calls = sum(1 for diff in time_diffs if diff < 0.05)
                assert parallel_calls >= 5  # At least 5 calls should be truly parallel
    
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
    async def test_contradiction_detection(self):
        """Test that contradictions are detected and raise errors"""
        query = "vegan pescatarian meal plan"
        
        with pytest.raises(ValueError) as exc_info:
            await self.generator.generate(query)
        
        assert "contradictory" in str(exc_info.value).lower() or \
               "contradiction" in str(exc_info.value).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

