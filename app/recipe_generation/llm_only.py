"""
Pure LLM strategy: Generate recipes entirely using LLM (no external API)
This is the baseline strategy for comparison
"""
import json
import asyncio
import random
from typing import Dict, List, Optional
from openai import OpenAI
from app.config import settings
from app.recipe_generation.base import RecipeGenerationStrategy


class LLMOnlyStrategy(RecipeGenerationStrategy):
    """
    Strategy A: Pure LLM generation
    No external recipe API, LLM generates everything from scratch
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.used_recipes = set()
        self._lock = asyncio.Lock()  # Thread-safe access to used_recipes
    
    def get_strategy_name(self) -> str:
        return "llm_only"
    
    def _get_variety_hint(self, day: int, meal_type: str, preferences: List[str], exclusions: List[str] = None) -> str:
        """
        Generate variety hints based on day to ensure diversity in parallel generation.
        Uses simple variation techniques instead of forcing specific cuisines.
        Respects exclusions to avoid suggesting excluded cuisines.
        """
        import random
        
        exclusions = exclusions or []
        exclusions_lower = [e.lower() for e in exclusions]
        
        # Check if user specified a cuisine preference
        user_has_cuisine = any(pref.lower() in ["indian", "mexican", "italian", "asian", "mediterranean", 
                                                  "chinese", "japanese", "thai", "french", "greek"]
                               for pref in preferences)
        
        if user_has_cuisine:
            # Don't suggest cuisine, just vary the cooking method/ingredients
            variety_options = [
                "grain-based",
                "protein-focused",
                "legume-based",
                "veggie-forward"
            ]
            # Randomize but use day as seed for consistency
            random.seed(day)
            hint = random.choice(variety_options)
        else:
            # Suggest cuisine variety only if user didn't specify (keep it short)
            all_cuisine_options = [
                "Italian",
                "Asian",
                "Indian",
                "Mexican",
                "American",
                "Thai"
            ]
            
            # Filter out excluded cuisines
            filtered_options = []
            for option in all_cuisine_options:
                option_lower = option.lower()
                # Check if any exclusion keyword is in this option
                if not any(excl in option_lower for excl in exclusions_lower):
                    filtered_options.append(option)
            
            # If we filtered everything, use cooking methods instead
            if not filtered_options:
                filtered_options = ["grain-based", "protein-focused", "veggie-forward"]
            
            # Randomize but use day as seed for consistency across parallel calls
            random.seed(day * 100 + hash(meal_type) % 100)
            hint = random.choice(filtered_options)
        
        return hint
    
    def reset(self):
        """Reset used recipes tracker"""
        self.used_recipes.clear()
    
    async def generate_recipe(
        self,
        meal_type: str,
        dietary_restrictions: List[str],
        preferences: List[str],
        special_requirements: List[str],
        day: int,
        prep_time_max: Optional[int] = None,
        **kwargs
    ) -> Dict:
        """Generate recipe using pure LLM (no external candidates)"""
        
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
        
        # Get used recipes for this meal type (thread-safe)
        async with self._lock:
            used_for_meal_type = [name for name in self.used_recipes if meal_type.lower() in name.lower()]
            used_for_meal_type = used_for_meal_type[:10]
        
        # Simple diversity: vary by day to ensure different recipes in parallel calls
        # Get variety hint with exclusions
        exclusions = kwargs.get('exclusions', [])
        variety_hint = self._get_variety_hint(day, meal_type, preferences, exclusions)
        
        diversity_constraint = f"\n\nVariety: {variety_hint}. Be unique."
        
        # Add exclusion constraint if present
        if exclusions:
            diversity_constraint += f" NOT {', '.join(exclusions[:2])}."  # Limit to 2 exclusions
        if used_for_meal_type:
            diversity_constraint += f"\nAvoid similar to: {', '.join(used_for_meal_type[:5])}"
        
        system_prompt = """Professional chef. Generate realistic, cookable recipes with exact quantities and nutrition. Be diverse. Return JSON only."""
        
        prep_time_constraint = f" Max {prep_time_max}min." if prep_time_max else ""
        
        user_prompt = f"""{meal_type} recipe day {day}.{requirements_str}{prep_time_constraint}{diversity_constraint}

JSON format:
{{
  "recipe_name": "name",
  "description": "brief desc",
  "ingredients": ["qty ingredient", ...],
  "nutritional_info": {{"calories": int, "protein": float, "carbs": float, "fat": float}},
  "preparation_time": "X mins",
  "instructions": "3-5 clear steps",
  "source": "AI Generated"
}}

Include quantities, realistic nutrition, be unique."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.9  # Increased temperature for more diversity
            )
            
            recipe = json.loads(response.choices[0].message.content)
            recipe = self._validate_recipe(recipe, meal_type)
            
            # Track used recipe name for diversity (thread-safe)
            recipe_name = recipe.get("recipe_name", "").lower()
            if recipe_name:
                async with self._lock:
                    self.used_recipes.add(recipe_name)
                    if len(self.used_recipes) > 50:
                        self.used_recipes = set(list(self.used_recipes)[-50:])
            
            return recipe
            
        except Exception as e:
            print(f"LLM-only recipe generation failed: {e}")
            return self._generate_fallback_recipe(meal_type, dietary_restrictions)
    
    def _validate_recipe(self, recipe: Dict, meal_type: str) -> Dict:
        """Validate and ensure recipe has all required fields"""
        if "recipe_name" not in recipe:
            recipe["recipe_name"] = f"{meal_type.capitalize()} Recipe"
        if "description" not in recipe:
            recipe["description"] = f"A delicious {meal_type} option."
        if "ingredients" not in recipe or not isinstance(recipe["ingredients"], list):
            recipe["ingredients"] = ["Ingredients to be determined"]
        if "nutritional_info" not in recipe:
            recipe["nutritional_info"] = {"calories": 400, "protein": 20.0, "carbs": 50.0, "fat": 10.0}
        if "preparation_time" not in recipe:
            recipe["preparation_time"] = "30 mins"
        if "instructions" not in recipe:
            recipe["instructions"] = "Follow standard cooking procedures."
        elif isinstance(recipe["instructions"], list):
            recipe["instructions"] = "\n".join(recipe["instructions"])
        if "source" not in recipe:
            recipe["source"] = "AI Generated"
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
        if "vegan" in dietary_restrictions or "vegetarian" in dietary_restrictions:
            recipe["ingredients"] = [ing.replace("milk", "plant-based milk") for ing in recipe["ingredients"]]
        recipe["meal_type"] = meal_type
        return recipe

