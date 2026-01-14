"""
Fast LLM Strategy: Ultra-fast recipe generation with minimal detail
Optimized for speed - generates all meals for the entire plan in ONE API call
"""
import json
from typing import Dict, List, Optional
from openai import OpenAI
from app.config import settings
from app.recipe_generation.base import RecipeGenerationStrategy


class FastLLMStrategy(RecipeGenerationStrategy):
    """
    Fast LLM Strategy: Ultra-fast generation
    - Generates ALL meals for entire plan in ONE API call
    - Minimal detail (shorter recipes for longer plans)
    - Lower temperature for faster responses
    - Optimized for speed over detail
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
    
    def get_strategy_name(self) -> str:
        return "fast_llm"
    
    def reset(self):
        """No state to reset"""
        pass
    
    async def generate_full_plan(
        self,
        duration_days: int,
        meal_types: List[str],
        dietary_restrictions: List[str],
        preferences: List[str],
        special_requirements: List[str],
        exclusions: List[str] = None
    ) -> List[List[Dict]]:
        """
        Generate ALL meals for ALL days in ONE API call
        This is the fastest possible approach
        """
        exclusions = exclusions or []
        
        # Build requirements
        requirements = []
        if dietary_restrictions:
            requirements.append(f"Dietary: {', '.join(dietary_restrictions)}")
        if preferences:
            requirements.append(f"Preferences: {', '.join(preferences)}")
        if exclusions:
            requirements.append(f"EXCLUDE: {', '.join(exclusions)}")
        requirements_str = "\n".join(requirements) if requirements else "Standard diet"
        
        # Adjust detail level based on plan size
        total_meals = duration_days * len(meal_types)
        if total_meals <= 6:
            detail_level = "Include 3-5 ingredients and 2-3 step instructions."
        elif total_meals <= 12:
            detail_level = "Keep it brief: 3 key ingredients, 1-2 step instructions."
        else:
            detail_level = "Minimal detail: list main ingredients only, 1 sentence instruction."
        
        meals_str = ", ".join(meal_types)
        
        system_prompt = f"""You are a fast meal planner. Generate {total_meals} simple recipes quickly. {detail_level} Return valid JSON only."""
        
        user_prompt = f"""Generate {duration_days}-day meal plan ({len(meal_types)} meals/day: {meals_str}).

Requirements: {requirements_str}

CRITICAL: Return valid JSON. No line breaks in strings. Use this exact structure:

{{
  "days": [
    {{"day": 1, "meals": [{{"recipe_name": "Name", "description": "Desc", "ingredients": ["item1", "item2"], "nutritional_info": {{"calories": 400, "protein": 20.0, "carbs": 45.0, "fat": 12.0}}, "preparation_time": "15 mins", "instructions": "Quick steps", "source": "AI Generated"}}]}}
  ]
}}

Generate {duration_days} days. {detail_level} Each recipe different. Valid JSON only."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,  # Lower temperature for faster, more consistent responses
                max_tokens=2000 if total_meals > 15 else 3000  # Limit tokens for speed
            )
            
            result = json.loads(response.choices[0].message.content)
            days_data = result.get("days", [])
            
            # Validate and structure the response
            all_meals = []
            for day_idx in range(duration_days):
                if day_idx < len(days_data):
                    day_meals = days_data[day_idx].get("meals", [])
                else:
                    day_meals = []
                
                # Ensure we have the right number of meals
                validated_meals = []
                for meal_idx, meal_type in enumerate(meal_types):
                    if meal_idx < len(day_meals):
                        meal = day_meals[meal_idx]
                        meal = self._validate_recipe(meal, meal_type)
                    else:
                        meal = self._generate_fallback_recipe(meal_type, dietary_restrictions)
                    
                    meal["meal_type"] = meal_type
                    validated_meals.append(meal)
                
                all_meals.append(validated_meals)
            
            return all_meals
            
        except Exception as e:
            print(f"Fast LLM generation failed: {e}, using fallback")
            # Fallback: generate minimal recipes
            all_meals = []
            for day in range(duration_days):
                day_meals = []
                for meal_type in meal_types:
                    meal = self._generate_fallback_recipe(meal_type, dietary_restrictions)
                    meal["meal_type"] = meal_type
                    day_meals.append(meal)
                all_meals.append(day_meals)
            return all_meals
    
    async def generate_recipe(
        self,
        meal_type: str,
        dietary_restrictions: List[str],
        preferences: List[str],
        special_requirements: List[str],
        day: int,
        prep_time_max: Optional[int] = None,
        duration_days: Optional[int] = None,
        exclusions: List[str] = None,
        **kwargs
    ) -> Dict:
        """
        Single recipe generation (fallback for compatibility)
        Not used in normal operation - fast_llm generates all meals at once
        """
        return self._generate_fallback_recipe(meal_type, dietary_restrictions)
    
    def _validate_recipe(self, recipe: Dict, meal_type: str) -> Dict:
        """Ensure recipe has all required fields with minimal defaults"""
        if "recipe_name" not in recipe or not recipe["recipe_name"]:
            recipe["recipe_name"] = f"{meal_type.capitalize()} Bowl"
        if "description" not in recipe:
            recipe["description"] = f"Quick {meal_type}."
        if "ingredients" not in recipe or not isinstance(recipe["ingredients"], list):
            recipe["ingredients"] = ["Main ingredient", "Seasoning", "Side"]
        if "nutritional_info" not in recipe:
            recipe["nutritional_info"] = {"calories": 400, "protein": 20.0, "carbs": 45.0, "fat": 10.0}
        if "preparation_time" not in recipe:
            recipe["preparation_time"] = "15 mins"
        else:
            # Format prep time as integer (no decimals)
            import re
            prep_time_str = str(recipe.get("preparation_time", "15 mins")).lower()
            time_match = re.search(r'(\d+\.?\d*)', prep_time_str)
            if time_match:
                prep_time_num = float(time_match.group(1))
                recipe["preparation_time"] = f"{int(prep_time_num)} mins"
        if "instructions" not in recipe:
            recipe["instructions"] = "Prepare ingredients and cook."
        if "source" not in recipe:
            recipe["source"] = "AI Generated"
        return recipe
    
    def _generate_fallback_recipe(self, meal_type: str, dietary_restrictions: List[str]) -> Dict:
        """Generate minimal fallback recipe"""
        return {
            "recipe_name": f"Simple {meal_type.capitalize()}",
            "description": f"Quick {meal_type} option.",
            "ingredients": ["Main protein", "Vegetables", "Seasoning"],
            "nutritional_info": {"calories": 400, "protein": 20.0, "carbs": 45.0, "fat": 10.0},
            "preparation_time": "15 mins",
            "instructions": "Cook and serve.",
            "source": "AI Generated"
        }

