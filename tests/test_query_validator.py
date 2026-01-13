"""
Unit tests for QueryValidator
"""
import pytest
from app.query_validator import QueryValidator


class TestQueryValidator:
    """Test query validation logic"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.validator = QueryValidator()
    
    def test_validate_duration_max(self):
        """Test that duration is capped at 7 days"""
        query = "10-day vegan meal plan"
        parsed = {"duration_days": 10, "dietary_restrictions": ["vegan"], "preferences": [], "special_requirements": []}
        corrected, warnings = self.validator.validate(query, parsed)
        
        assert corrected["duration_days"] == 7
        assert any("maximum" in w.lower() or "adjusted" in w.lower() or "7" in w for w in warnings)
    
    def test_validate_duration_min(self):
        """Test that duration is at least 1 day"""
        query = "0-day meal plan"
        parsed = {"duration_days": 0, "dietary_restrictions": [], "preferences": [], "special_requirements": []}
        corrected, warnings = self.validator.validate(query, parsed)
        
        assert corrected["duration_days"] == 1
    
    def test_validate_contradictions(self):
        """Test detection of contradictory requirements"""
        query = "pescatarian vegan meal plan"
        parsed = {
            "duration_days": 3,
            "dietary_restrictions": ["pescatarian", "vegan"],
            "preferences": [],
            "special_requirements": []
        }
        corrected, warnings = self.validator.validate(query, parsed)
        
        assert "contradictions" in corrected
        assert len(corrected["contradictions"]) > 0
        assert any("pescatarian" in c.lower() and "vegan" in c.lower() 
                  for c in corrected["contradictions"])
    
    def test_validate_meal_count(self):
        """Test meal count extraction and validation"""
        query = "2 meals per day"
        parsed = {"duration_days": 3, "meals_per_day": 2, "dietary_restrictions": [], "preferences": [], "special_requirements": []}
        corrected, warnings = self.validator.validate(query, parsed)
        
        assert corrected["meals_per_day"] == 2
    
    def test_validate_prep_time(self):
        """Test preparation time extraction"""
        query = "quick meals under 15 minutes"
        parsed = {"duration_days": 3, "special_requirements": [], "dietary_restrictions": [], "preferences": []}
        corrected, warnings = self.validator.validate(query, parsed)
        
        assert "prep_time_max" in corrected
        assert corrected["prep_time_max"] == 15
        assert "quick-meals" in corrected.get("special_requirements", [])
    
    def test_validate_budget(self):
        """Test budget constraint extraction"""
        query = "budget-friendly meals"
        parsed = {"duration_days": 3, "special_requirements": [], "dietary_restrictions": [], "preferences": []}
        corrected, warnings = self.validator.validate(query, parsed)
        
        assert "budget-friendly" in corrected.get("special_requirements", [])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

