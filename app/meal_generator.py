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
        
        # Create natural language warning (deduplicate items)
        if removed_items and kept_items:
            removed_str = ", ".join(list(set(removed_items)))  # Remove duplicates
            kept_str = ", ".join(list(set(kept_items)))  # Remove duplicates
            warning = f"I noticed you requested both {removed_str} and {kept_str}, which conflict. I've created a {kept_str} meal plan for you."
        else:
            warning = "I've resolved some conflicting requirements in your request."
        
        # Clear contradictions since they're resolved
        resolved["contradictions"] = []
        
        return resolved, warning
    
    async def generate(self, query: str) -> Dict:
        """
        Generate a complete meal plan from a natural language query.
        Always returns a meal plan, falling back to default if generation fails.
        
        Args:
            query: Natural language meal plan request
        
        Returns:
            Complete meal plan dictionary matching MealPlanResponse model
        """
        try:
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
                            exclusions=parsed.get("exclusions", []),
                            duration_days=duration_days  # Pass duration_days for proper caching
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
            
            # Build response - always include warning field (None if no warnings)
            response = {
                "meal_plan_id": str(uuid.uuid4()),
                "duration_days": duration_days,
                "generated_at": datetime.now().isoformat(),
                "meal_plan": meal_plan,
                "summary": summary,
                "warning": warning_message  # Warning if contradictions resolved, None otherwise
            }
            
            return response
        
        except Exception as e:
            # Log the error but always return a meal plan
            import logging
            logger = logging.getLogger(__name__)
            error_msg = str(e) if str(e) else "Unknown error during meal plan generation"
            logger.error(f"Error generating meal plan: {error_msg}", exc_info=True)
            
            # Return fallback meal plan
            return await self._generate_fallback_meal_plan(query, error_msg)
    
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
    
    async def _generate_fallback_meal_plan(self, query: Optional[str], error_message: str) -> Dict:
        """
        Generate a simple fallback meal plan when main generation fails.
        Always returns a valid meal plan with a warning message.
        """
        from datetime import datetime, timedelta
        
        if not query:
            query = "meal plan"
        
        # Simple default recipes that don't require API calls
        default_recipes = {
            "breakfast": {
                "recipe_name": "Classic Oatmeal Bowl",
                "description": "A hearty and nutritious breakfast to start your day",
                "ingredients": ["1 cup rolled oats", "2 cups water or milk", "1 banana, sliced", "1 tbsp honey", "Pinch of salt"],
                "nutritional_info": {"calories": 350, "protein": 12.0, "carbs": 65.0, "fat": 6.0},
                "preparation_time": "10 mins",
                "instructions": "1. Bring water/milk to a boil. 2. Add oats and salt, reduce heat. 3. Cook for 5 minutes, stirring occasionally. 4. Top with banana and honey.",
                "source": "Default Recipe"
            },
            "lunch": {
                "recipe_name": "Mixed Green Salad",
                "description": "Fresh and healthy salad with a variety of vegetables",
                "ingredients": ["4 cups mixed greens", "1 cucumber, sliced", "1 tomato, diced", "1/4 cup olive oil", "2 tbsp lemon juice", "Salt and pepper"],
                "nutritional_info": {"calories": 280, "protein": 8.0, "carbs": 20.0, "fat": 22.0},
                "preparation_time": "15 mins",
                "instructions": "1. Wash and prepare all vegetables. 2. Combine greens, cucumber, and tomato in a large bowl. 3. Whisk together olive oil, lemon juice, salt, and pepper. 4. Drizzle dressing over salad and toss.",
                "source": "Default Recipe"
            },
            "dinner": {
                "recipe_name": "Grilled Chicken with Vegetables",
                "description": "Simple and satisfying protein with seasonal vegetables",
                "ingredients": ["2 chicken breasts", "2 cups mixed vegetables (broccoli, carrots, bell peppers)", "2 tbsp olive oil", "Salt, pepper, garlic powder"],
                "nutritional_info": {"calories": 450, "protein": 40.0, "carbs": 15.0, "fat": 25.0},
                "preparation_time": "30 mins",
                "instructions": "1. Season chicken with salt, pepper, and garlic powder. 2. Heat oil in a pan over medium heat. 3. Cook chicken for 6-7 minutes per side. 4. Steam or roast vegetables until tender. 5. Serve together.",
                "source": "Default Recipe"
            }
        }
        
        # Generate 3-day default plan
        meal_plan = []
        start_date = datetime.now().date()
        
        for day in range(1, 4):
            current_date = start_date + timedelta(days=day - 1)
            meals = []
            
            for meal_type in ["breakfast", "lunch", "dinner"]:
                meal = default_recipes[meal_type].copy()
                meal["meal_type"] = meal_type
                meals.append(meal)
            
            meal_plan.append({
                "day": day,
                "date": current_date.isoformat(),
                "meals": meals
            })
        
        # Calculate summary
        summary = {
            "total_meals": 9,
            "dietary_compliance": ["standard"],
            "estimated_cost": "$25-35",
            "avg_prep_time": "18 mins"
        }
        
        # Build response with user-friendly warning
        # Always include a clear warning message explaining what happened
        warning = "I encountered an issue generating your custom meal plan. Here's a balanced 3-day meal plan to get you started. Please try again with a simpler request if you need something specific."
        
        response = {
            "meal_plan_id": str(uuid.uuid4()),
            "duration_days": 3,
            "generated_at": datetime.now().isoformat(),
            "meal_plan": meal_plan,
            "summary": summary,
            "warning": warning  # Always included in fallback cases
        }
        
        return response

