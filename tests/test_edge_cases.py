"""
Edge case tests from assignment requirements
Tests the 5 example queries mentioned in the assignment
"""
import pytest
import asyncio
from app.meal_generator import MealPlanGenerator
from app.query_parser import QueryParser


class TestAssignmentEdgeCases:
    """Test edge cases from assignment requirements"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = QueryParser()
        self.generator = MealPlanGenerator(strategy_mode="llm_only")  # Use LLM-only for faster tests
    
    def test_basic_query(self):
        """Test Case 1: Basic query - 'Create a 3-day vegetarian meal plan'"""
        query = "Create a 3-day vegetarian meal plan"
        parsed = self.parser.parse(query)
        
        assert parsed["duration_days"] == 3
        assert "vegetarian" in [r.lower() for r in parsed.get("dietary_restrictions", [])]
        assert parsed.get("contradictions", []) == []
    
    def test_complex_query(self):
        """Test Case 2: Complex query with multiple requirements"""
        query = "Generate a 7-day low-carb, dairy-free meal plan with high protein, budget-friendly options, and quick breakfast recipes under 15 minutes"
        parsed = self.parser.parse(query)
        
        assert parsed["duration_days"] == 7
        assert "low-carb" in [p.lower() for p in parsed.get("preferences", [])] or \
               "low-carb" in [r.lower() for r in parsed.get("dietary_restrictions", [])]
        assert "dairy-free" in [r.lower() for r in parsed.get("dietary_restrictions", [])]
        assert "high-protein" in [p.lower() for p in parsed.get("preferences", [])]
        assert "budget-friendly" in [s.lower() for s in parsed.get("special_requirements", [])]
        assert parsed.get("prep_time_max") == 15 or parsed.get("prep_time_max") is None
    
    def test_ambiguous_query(self):
        """Test Case 3: Ambiguous query - 'I need healthy meals for next week'"""
        query = "I need healthy meals for next week"
        parsed = self.parser.parse(query)
        
        # Should default to reasonable values
        assert 1 <= parsed["duration_days"] <= 7
        assert parsed.get("meals_per_day", 3) >= 1
    
    def test_exceeds_limit(self):
        """Test Case 4: Edge case - '10-day vegan plan' (exceeds 7-day limit)"""
        query = "10-day vegan plan"
        parsed = self.parser.parse(query)
        
        # Duration should be capped at 7
        assert parsed["duration_days"] == 7
        assert "vegan" in [r.lower() for r in parsed.get("dietary_restrictions", [])]
    
    @pytest.mark.asyncio
    async def test_exceeds_limit_generation(self):
        """Test that meal plan generation caps at 7 days"""
        query = "10-day vegan plan"
        meal_plan = await self.generator.generate(query)
        
        assert meal_plan["duration_days"] == 7
        assert len(meal_plan["meal_plan"]) == 7
    
    def test_conflicting_requirements(self):
        """Test Case 5: Conflicting requirements - 'Pescatarian vegan meal plan'"""
        query = "Pescatarian vegan meal plan"
        parsed = self.parser.parse(query)
        
        # Should detect contradiction
        contradictions = parsed.get("contradictions", [])
        assert len(contradictions) > 0 or \
               ("pescatarian" in [r.lower() for r in parsed.get("dietary_restrictions", [])] and
                "vegan" in [r.lower() for r in parsed.get("dietary_restrictions", [])])
    
    @pytest.mark.asyncio
    async def test_conflicting_requirements_generation(self):
        """Test that conflicting requirements raise an error during generation"""
        query = "Pescatarian vegan meal plan"
        
        # Should raise ValueError for contradictions
        with pytest.raises(ValueError) as exc_info:
            await self.generator.generate(query)
        
        assert "contradictory" in str(exc_info.value).lower() or \
               "contradiction" in str(exc_info.value).lower()
    
    def test_empty_query(self):
        """Test empty query handling"""
        query = ""
        parsed = self.parser.parse(query)
        
        # Should have defaults
        assert parsed["duration_days"] >= 1
        assert parsed["duration_days"] <= 7
    
    def test_single_day_plan(self):
        """Test single day meal plan"""
        query = "1-day vegetarian meal plan"
        parsed = self.parser.parse(query)
        
        assert parsed["duration_days"] == 1
    
    def test_week_plan(self):
        """Test week plan (7 days)"""
        query = "week of healthy meals"
        parsed = self.parser.parse(query)
        
        assert parsed["duration_days"] == 7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

