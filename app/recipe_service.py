"""
Recipe generation service using OpenAI
Generates recipes with full details including ingredients, instructions, and nutrition
"""
import json
import uuid
from typing import Dict, List, Optional
from cachetools import TTLCache
from openai import OpenAI
from app.config import settings


class RecipeService:
    """Service for generating recipes using OpenAI"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        # Cache recipes by dietary tags to reduce API calls
        self.cache = TTLCache(maxsize=1000, ttl=settings.cache_ttl_seconds)
        self.used_recipes = set()  # Track recipes used in current meal plan
    
    def generate_recipe(
        self,
        meal_type: str,
        dietary_restrictions: List[str],
        preferences: List[str],
        special_requirements: List[str],
        day: int,
        prep_time_max: Optional[int] = None
    ) -> Dict:
        """
        Generate a single recipe using OpenAI
        
        Args:
            meal_type: breakfast, lunch, dinner, or snack
            dietary_restrictions: List of dietary restrictions
            preferences: List of preferences
            special_requirements: List of special requirements
            day: Day number (for variety)
        
        Returns:
            Recipe dictionary with all required fields
        """
        # Create cache key
        cache_key = self._create_cache_key(meal_type, dietary_restrictions, preferences, special_requirements, day)
        
        # Check cache first
        if cache_key in self.cache:
            recipe = self.cache[cache_key].copy()
            # Ensure unique recipe name
            recipe['recipe_name'] = f"{recipe['recipe_name']} (Day {day})"
            return recipe
        
        # Generate new recipe
        recipe = self._generate_with_llm(meal_type, dietary_restrictions, preferences, special_requirements, day, prep_time_max)
        
        # Cache it
        self.cache[cache_key] = recipe.copy()
        
        return recipe
    
    def _create_cache_key(
        self,
        meal_type: str,
        dietary_restrictions: List[str],
        preferences: List[str],
        special_requirements: List[str],
        day: int
    ) -> str:
        """Create a cache key from recipe parameters"""
        key_parts = [
            meal_type,
            ",".join(sorted(dietary_restrictions)),
            ",".join(sorted(preferences)),
            ",".join(sorted(special_requirements)),
            str(day % 3)  # Group days to allow some variety while caching
        ]
        return "|".join(key_parts)
    
    def _generate_with_llm(
        self,
        meal_type: str,
        dietary_restrictions: List[str],
        preferences: List[str],
        special_requirements: List[str],
        day: int,
        prep_time_max: Optional[int] = None
    ) -> Dict:
        """Generate recipe using OpenAI with structured output"""
        
        # Build requirements string
        requirements = []
        if dietary_restrictions:
            requirements.append(f"Dietary restrictions: {', '.join(dietary_restrictions)}")
        if preferences:
            requirements.append(f"Preferences: {', '.join(preferences)}")
        if special_requirements:
            requirements.append(f"Special requirements: {', '.join(special_requirements)}")
        if prep_time_max:
            requirements.append(f"IMPORTANT: Preparation time must be {prep_time_max} minutes or less")
        
        requirements_str = "\n".join(requirements) if requirements else "No specific restrictions"
        
        system_prompt = """You are a professional chef and nutritionist. Generate detailed, realistic, and cookable recipes.

Generate recipes that:
- Are realistic and actually cookable
- Include specific ingredient quantities
- Have clear, step-by-step instructions
- Include accurate nutritional information
- Are appropriate for the meal type and dietary requirements

Return valid JSON only."""
        
        prep_time_constraint = ""
        if prep_time_max:
            prep_time_constraint = f"\nCRITICAL: The preparation_time must be {prep_time_max} minutes or less. Choose quick, simple recipes that can be prepared in this time."
        
        user_prompt = f"""Generate a {meal_type} recipe for day {day}.

Requirements:
{requirements_str}{prep_time_constraint}

Return a JSON object with this exact structure:
{{
  "recipe_name": "<creative recipe name>",
  "description": "<1-2 sentence description of the dish>",
  "ingredients": ["<quantity> <ingredient>", ...],
  "nutritional_info": {{
    "calories": <integer>,
    "protein": <float in grams>,
    "carbs": <float in grams>,
    "fat": <float in grams>
  }},
  "preparation_time": "<X mins>",
  "instructions": "<step-by-step cooking instructions, 3-5 steps>",
  "source": "AI Generated"
}}

Make sure:
- Ingredients have specific quantities (e.g., "2 cups oats", "1 tbsp olive oil")
- Nutritional info is realistic and accurate
- Instructions are clear and actionable
- Preparation time is realistic
- Recipe name is creative and descriptive"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.8  # Higher temperature for creativity
            )
            
            recipe = json.loads(response.choices[0].message.content)
            
            # Validate and ensure all fields are present
            recipe = self._validate_recipe(recipe, meal_type)
            
            return recipe
            
        except Exception as e:
            # Fallback to a basic recipe if LLM fails
            print(f"Recipe generation failed: {e}")
            return self._generate_fallback_recipe(meal_type, dietary_restrictions)
    
    def _validate_recipe(self, recipe: Dict, meal_type: str) -> Dict:
        """Validate and ensure recipe has all required fields"""
        # Ensure all required fields exist
        if "recipe_name" not in recipe:
            recipe["recipe_name"] = f"{meal_type.capitalize()} Recipe"
        
        if "description" not in recipe:
            recipe["description"] = f"A delicious {meal_type} option."
        
        if "ingredients" not in recipe or not isinstance(recipe["ingredients"], list):
            recipe["ingredients"] = ["Ingredients to be determined"]
        
        if "nutritional_info" not in recipe:
            recipe["nutritional_info"] = {
                "calories": 400,
                "protein": 20.0,
                "carbs": 50.0,
                "fat": 10.0
            }
        
        if "preparation_time" not in recipe:
            recipe["preparation_time"] = "30 mins"
        
        if "instructions" not in recipe:
            recipe["instructions"] = "Follow standard cooking procedures."
        # Ensure instructions is a string (not a list)
        elif isinstance(recipe["instructions"], list):
            recipe["instructions"] = "\n".join(recipe["instructions"])
        
        if "source" not in recipe:
            recipe["source"] = "AI Generated"
        
        # Ensure meal_type is included
        recipe["meal_type"] = meal_type
        
        return recipe
    
    def _generate_fallback_recipe(self, meal_type: str, dietary_restrictions: List[str]) -> Dict:
        """Generate a basic fallback recipe if LLM fails"""
        base_recipes = {
            "breakfast": {
                "recipe_name": "Healthy Breakfast Bowl",
                "description": "A nutritious and filling breakfast option.",
                "ingredients": ["1 cup oats", "1 cup milk or plant-based milk", "1 banana", "1 tbsp honey"],
                "nutritional_info": {"calories": 350, "protein": 12.0, "carbs": 60.0, "fat": 8.0},
                "preparation_time": "10 mins",
                "instructions": "1. Cook oats with milk. 2. Slice banana on top. 3. Drizzle with honey.",
                "source": "AI Generated (Fallback)"
            },
            "lunch": {
                "recipe_name": "Fresh Salad Bowl",
                "description": "A light and healthy lunch option.",
                "ingredients": ["2 cups mixed greens", "1/2 cup cherry tomatoes", "1/4 cup dressing", "1/4 cup nuts"],
                "nutritional_info": {"calories": 300, "protein": 10.0, "carbs": 20.0, "fat": 20.0},
                "preparation_time": "15 mins",
                "instructions": "1. Wash and prepare greens. 2. Add tomatoes. 3. Toss with dressing. 4. Top with nuts.",
                "source": "AI Generated (Fallback)"
            },
            "dinner": {
                "recipe_name": "Balanced Dinner Plate",
                "description": "A well-rounded dinner option.",
                "ingredients": ["1 protein portion", "1 cup vegetables", "1/2 cup grains", "1 tbsp oil"],
                "nutritional_info": {"calories": 500, "protein": 30.0, "carbs": 45.0, "fat": 15.0},
                "preparation_time": "30 mins",
                "instructions": "1. Cook protein. 2. Prepare vegetables. 3. Cook grains. 4. Plate together.",
                "source": "AI Generated (Fallback)"
            }
        }
        
        recipe = base_recipes.get(meal_type, base_recipes["dinner"]).copy()
        
        # Adjust for dietary restrictions
        if "vegan" in dietary_restrictions or "vegetarian" in dietary_restrictions:
            recipe["ingredients"] = [ing.replace("milk", "plant-based milk") for ing in recipe["ingredients"]]
        
        return recipe
    
    def reset_used_recipes(self):
        """Reset the used recipes tracker (call at start of new meal plan)"""
        self.used_recipes.clear()

