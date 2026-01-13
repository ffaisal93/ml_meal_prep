"""
Meal plan generator - orchestrates query parsing and recipe generation
"""
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from app.query_parser import QueryParser
from app.recipe_service import RecipeService


class MealPlanGenerator:
    """Generate complete meal plans based on parsed queries"""
    
    def __init__(self, strategy_mode: Optional[str] = None):
        self.query_parser = QueryParser()
        self.recipe_service = RecipeService(strategy_mode=strategy_mode)
    
    def _resolve_contradictions(self, parsed: Dict) -> Tuple[Dict, Optional[str]]:
        """
        Resolve contradictions by intelligently choosing which requirement to keep.
        Returns (resolved_parsed, warning_message)
        """
        contradictions = parsed.get("contradictions", [])
        if not contradictions:
            return parsed, None
        
        # Priority order: dietary restrictions > preferences
        # For known pairs, prefer the more restrictive/specific one
        resolution_rules = {
            ("vegan", "pescatarian"): "vegan",  # Vegan is more restrictive
            ("vegan", "vegetarian"): "vegan",  # Vegan is more restrictive
            ("keto", "high-carb"): "keto",  # Keto is more specific
            ("low-carb", "high-carb"): "low-carb",  # Low-carb is more specific
        }
        
        resolved = parsed.copy()
        removed_items = []
        kept_items = []
        
        for contradiction in contradictions:
            # Parse contradiction string like "keto and high-carb"
            parts = [p.strip() for p in contradiction.lower().split(" and ")]
            if len(parts) != 2:
                continue
            
            item1, item2 = parts[0], parts[1]
            
            # Find which one to keep based on rules
            keep_item = None
            remove_item = None
            
            # Check resolution rules
            for (pair1, pair2), preferred in resolution_rules.items():
                if (item1 == pair1.lower() and item2 == pair2.lower()) or \
                   (item1 == pair2.lower() and item2 == pair1.lower()):
                    keep_item = preferred.lower()
                    remove_item = item2 if item1 == preferred.lower() else item1
                    break
            
            # If no rule, prefer dietary restriction over preference
            if not keep_item:
                restrictions = [r.lower() for r in resolved.get("dietary_restrictions", [])]
                preferences = [p.lower() for p in resolved.get("preferences", [])]
                
                if item1 in restrictions and item2 in preferences:
                    keep_item = item1
                    remove_item = item2
                elif item2 in restrictions and item1 in preferences:
                    keep_item = item2
                    remove_item = item1
                else:
                    # Both in same category, keep first one
                    keep_item = item1
                    remove_item = item2
            
            # Remove from appropriate list
            if remove_item:
                # Remove from dietary_restrictions
                if remove_item in [r.lower() for r in resolved.get("dietary_restrictions", [])]:
                    resolved["dietary_restrictions"] = [
                        r for r in resolved["dietary_restrictions"] 
                        if r.lower() != remove_item
                    ]
                
                # Remove from preferences
                if remove_item in [p.lower() for p in resolved.get("preferences", [])]:
                    resolved["preferences"] = [
                        p for p in resolved["preferences"] 
                        if p.lower() != remove_item
                    ]
                
                removed_items.append(remove_item)
                kept_items.append(keep_item)
        
        # Create natural language warning
        if removed_items and kept_items:
            removed_str = ", ".join(removed_items)
            kept_str = ", ".join(kept_items)
            warning = f"I noticed you requested both {removed_str} and {kept_str}, which conflict. I've created a {kept_str} meal plan for you."
        else:
            warning = "I've resolved some conflicting requirements in your request."
        
        # Clear contradictions since they're resolved
        resolved["contradictions"] = []
        
        return resolved, warning
    
    async def generate(self, query: str) -> Dict:
        """
        Generate a complete meal plan from a natural language query
        
        Args:
            query: Natural language meal plan request
        
        Returns:
            Complete meal plan dictionary matching MealPlanResponse model
        """
        # Parse the query
        parsed = self.query_parser.parse(query)
        
        # Resolve contradictions automatically
        resolved_parsed, warning_message = self._resolve_contradictions(parsed)
        parsed = resolved_parsed
        
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
        
        # Check if strategy supports full-plan generation (fastest - 1 API call for everything!)
        meal_plan = []
        if hasattr(self.recipe_service.strategy, 'generate_full_plan'):
            # Ultra-fast: generate ALL meals for ALL days in ONE call
            all_meals = await self.recipe_service.strategy.generate_full_plan(
                duration_days=duration_days,
                meal_types=meal_types,
                dietary_restrictions=parsed["dietary_restrictions"],
                preferences=parsed["preferences"],
                special_requirements=parsed["special_requirements"],
                exclusions=parsed.get("exclusions", [])
            )
            
            for day in range(1, duration_days + 1):
                current_date = start_date + timedelta(days=day - 1)
                meal_plan.append({
                    "day": day,
                    "date": current_date.isoformat(),
                    "meals": all_meals[day - 1]
                })
        else:
            # Standard: generate day by day
            for day in range(1, duration_days + 1):
                current_date = start_date + timedelta(days=day - 1)
                
                # Try batch generation if strategy supports it
                if hasattr(self.recipe_service.strategy, 'generate_day_meals'):
                    meals = await self.recipe_service.strategy.generate_day_meals(
                        day=day,
                        meal_types=meal_types,
                        dietary_restrictions=parsed["dietary_restrictions"],
                        preferences=parsed["preferences"],
                        special_requirements=parsed["special_requirements"],
                        prep_time_max=parsed.get("prep_time_max"),
                        exclusions=parsed.get("exclusions", [])
                    )
                else:
                    # Fallback to individual generation
                    meals = []
                    for meal_type in meal_types:
                        recipe = await self.recipe_service.generate_recipe(
                            meal_type=meal_type,
                            dietary_restrictions=parsed["dietary_restrictions"],
                            preferences=parsed["preferences"],
                            special_requirements=parsed["special_requirements"],
                            day=day,
                            prep_time_max=parsed.get("prep_time_max"),
                            duration_days=duration_days,
                            exclusions=parsed.get("exclusions", [])
                        )
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
            "summary": summary,
            "warning": warning_message  # Add warning if contradictions were resolved
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

