"""
Meal plan generator - orchestrates query parsing and recipe generation
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, List
from app.query_parser import QueryParser
from app.recipe_service import RecipeService


class MealPlanGenerator:
    """Generate complete meal plans based on parsed queries"""
    
    def __init__(self):
        self.query_parser = QueryParser()
        self.recipe_service = RecipeService()
    
    def generate(self, query: str) -> Dict:
        """
        Generate a complete meal plan from a natural language query
        
        Args:
            query: Natural language meal plan request
        
        Returns:
            Complete meal plan dictionary matching MealPlanResponse model
        """
        # Parse the query
        parsed = self.query_parser.parse(query)
        
        # Check for contradictions
        if parsed.get("contradictions"):
            raise ValueError(f"Contradictory requirements detected: {', '.join(parsed['contradictions'])}")
        
        # Validate duration
        duration_days = parsed["duration_days"]
        if duration_days > 7:
            duration_days = 7
        if duration_days < 1:
            duration_days = 1
        
        # Reset recipe tracking for new meal plan
        self.recipe_service.reset_used_recipes()
        
        # Generate meal plan
        meal_plan = []
        start_date = datetime.now().date()
        
        # Get meal configuration from parsed query
        meals_per_day = parsed.get("meals_per_day", 3)
        meal_types = parsed.get("meal_types", ["breakfast", "lunch", "dinner"])
        
        # Ensure we don't exceed the requested meal count
        meal_types = meal_types[:meals_per_day]
        
        for day in range(1, duration_days + 1):
            current_date = start_date + timedelta(days=day - 1)
            
            # Generate meals for the day
            meals = []
            
            for meal_type in meal_types:
                recipe = self.recipe_service.generate_recipe(
                    meal_type=meal_type,
                    dietary_restrictions=parsed["dietary_restrictions"],
                    preferences=parsed["preferences"],
                    special_requirements=parsed["special_requirements"],
                    day=day,
                    prep_time_max=parsed.get("prep_time_max")  # Pass prep time constraint
                )
                # Ensure meal_type is included in the recipe
                recipe["meal_type"] = meal_type
                meals.append(recipe)
            
            meal_plan.append({
                "day": day,
                "date": current_date.isoformat(),
                "meals": meals
            })
        
        # Calculate summary
        summary = self._calculate_summary(meal_plan, parsed)
        
        # Build response
        response = {
            "meal_plan_id": str(uuid.uuid4()),
            "duration_days": duration_days,
            "generated_at": datetime.now().isoformat(),
            "meal_plan": meal_plan,
            "summary": summary
        }
        
        return response
    
    def _calculate_summary(self, meal_plan: List[Dict], parsed: Dict) -> Dict:
        """Calculate summary statistics for the meal plan"""
        total_meals = sum(len(day["meals"]) for day in meal_plan)
        
        # Collect dietary compliance
        dietary_compliance = []
        dietary_compliance.extend(parsed.get("dietary_restrictions", []))
        dietary_compliance.extend(parsed.get("preferences", []))
        
        # Calculate average prep time
        prep_times = []
        for day in meal_plan:
            for meal in day["meals"]:
                prep_time_str = meal.get("preparation_time", "30 mins")
                # Extract number from "X mins" or "X minutes"
                import re
                time_match = re.search(r'(\d+)', prep_time_str)
                if time_match:
                    prep_times.append(int(time_match.group(1)))
        
        avg_prep_time = f"{int(sum(prep_times) / len(prep_times))} mins" if prep_times else "25 mins"
        
        # Estimate cost (rough calculation)
        total_calories = sum(
            meal.get("nutritional_info", {}).get("calories", 400)
            for day in meal_plan
            for meal in day["meals"]
        )
        # Rough estimate: $0.01 per calorie
        estimated_cost_low = int(total_calories * 0.008)
        estimated_cost_high = int(total_calories * 0.012)
        
        # Adjust for budget-friendly requirement
        if "budget-friendly" in parsed.get("special_requirements", []):
            estimated_cost_low = int(estimated_cost_low * 0.7)
            estimated_cost_high = int(estimated_cost_high * 0.7)
        
        estimated_cost = f"${estimated_cost_low}-{estimated_cost_high}"
        
        return {
            "total_meals": total_meals,
            "dietary_compliance": list(set(dietary_compliance)) if dietary_compliance else ["standard"],
            "estimated_cost": estimated_cost,
            "avg_prep_time": avg_prep_time
        }

