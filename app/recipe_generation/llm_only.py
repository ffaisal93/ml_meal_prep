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
        Generate variety hints based on day to ensure diversity across sequential days.
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
            
            # Randomize but use day as seed for consistent variety across days
            random.seed(day * 100 + hash(meal_type) % 100)
            hint = random.choice(filtered_options)
        
        return hint
    
    def reset(self):
        """Reset used recipes tracker"""
        self.used_recipes.clear()
    
    async def generate_day_meals(
        self,
        day: int,
        meal_types: List[str],
        dietary_restrictions: List[str],
        preferences: List[str],
        special_requirements: List[str],
        prep_time_max: Optional[int] = None,
        exclusions: List[str] = None
    ) -> List[Dict]:
        """
        Generate ALL meals for a single day in ONE API call
        Much faster and cheaper than generating meals individually
        """
        exclusions = exclusions or []
        
        # Build requirements string
        requirements = []
        if dietary_restrictions:
            requirements.append(f"Dietary: {', '.join(dietary_restrictions)}")
        if preferences:
            requirements.append(f"Preferences: {', '.join(preferences)}")
        if special_requirements:
            requirements.append(f"Special: {', '.join(special_requirements)}")
        requirements_str = "\n".join(requirements) if requirements else "No specific restrictions"
        
        # Get variety hint
        variety_hint = self._get_variety_hint(day, meal_types[0], preferences, exclusions)
        diversity_constraint = f"\n\nVariety: {variety_hint}. Be unique."
        if exclusions:
            diversity_constraint += f" NOT {', '.join(exclusions[:2])}."
        
        prep_time_constraint = f"\n- Must be {prep_time_max} minutes or less" if prep_time_max else ""
        
        system_prompt = """You are a professional chef. Generate realistic, creative recipes with specific ingredients and accurate nutrition. Make each recipe unique and diverse. Return valid JSON only."""
        
        meal_list = ", ".join(meal_types)
        user_prompt = f"""Create {len(meal_types)} recipes for day {day}: {meal_list}.

Requirements:
{requirements_str}{prep_time_constraint}{diversity_constraint}

Return JSON with a "recipes" array:
{{
  "recipes": [
    {{
      "recipe_name": "Creative name",
      "description": "Brief description",
      "ingredients": ["2 cups oats", "1 tbsp honey"],
      "nutritional_info": {{"calories": 400, "protein": 20.0, "carbs": 45.0, "fat": 12.0}},
      "preparation_time": "20 mins",
      "instructions": "Clear step-by-step precise cooking instructions",
      "source": "AI Generated"
    }}
  ]
}}

Make each recipe different, with specific quantities and realistic nutrition."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.9
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Handle different response formats
            if "recipes" in result:
                recipes = result["recipes"]
            elif "meals" in result:
                recipes = result["meals"]
            elif isinstance(result, list):
                recipes = result
            else:
                recipes = [result]
            
            # Validate and assign meal types
            validated_recipes = []
            for i, recipe in enumerate(recipes[:len(meal_types)]):
                recipe = self._validate_recipe(recipe, meal_types[i])
                recipe["meal_type"] = meal_types[i]
                validated_recipes.append(recipe)
                
                # Track for diversity
                recipe_name = recipe.get("recipe_name", "").lower()
                if recipe_name:
                    async with self._lock:
                        self.used_recipes.add(recipe_name)
            
            # If we didn't get enough recipes, generate fallbacks
            while len(validated_recipes) < len(meal_types):
                fallback = self._generate_fallback_recipe(meal_types[len(validated_recipes)], dietary_restrictions)
                fallback["meal_type"] = meal_types[len(validated_recipes)]
                validated_recipes.append(fallback)
            
            return validated_recipes
            
        except Exception as e:
            print(f"Batch meal generation failed: {e}, falling back to individual generation")
            # Fallback to individual generation
            recipes = []
            for meal_type in meal_types:
                recipe = await self.generate_recipe(
                    meal_type=meal_type,
                    dietary_restrictions=dietary_restrictions,
                    preferences=preferences,
                    special_requirements=special_requirements,
                    day=day,
                    prep_time_max=prep_time_max,
                    exclusions=exclusions
                )
                recipes.append(recipe)
            return recipes
    
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
        
        # Simple diversity: vary by day to ensure different recipes across days
        # Get variety hint with exclusions
        exclusions = kwargs.get('exclusions', [])
        variety_hint = self._get_variety_hint(day, meal_type, preferences, exclusions)
        
        diversity_constraint = f"\n\nVariety: {variety_hint}. Be unique."
        
        # Add exclusion constraint if present
        if exclusions:
            diversity_constraint += f" NOT {', '.join(exclusions[:2])}."  # Limit to 2 exclusions
        if used_for_meal_type:
            diversity_constraint += f"\nAvoid similar to: {', '.join(used_for_meal_type[:5])}"
        
        system_prompt = """You are a professional chef. Generate realistic, creative recipes with specific ingredients and accurate nutrition. Make each recipe unique and diverse. Return valid JSON only."""
        
        prep_time_constraint = f"\n- Must be {prep_time_max} minutes or less" if prep_time_max else ""
        
        user_prompt = f"""Create a {meal_type} recipe for day {day}.

Requirements:
{requirements_str}{prep_time_constraint}{diversity_constraint}

Return JSON:
{{
  "recipe_name": "Creative, natural recipe name",
  "description": "Brief description of the dish",
  "ingredients": ["2 cups oats", "1 tbsp honey", ...],
  "nutritional_info": {{"calories": 400, "protein": 20.0, "carbs": 45.0, "fat": 12.0}},
  "preparation_time": "20 mins",
  "instructions": "Clear step-by-step precise cooking instructions",
  "source": "AI Generated"
}}

Important:
- Use a creative, appetizing recipe name
- Include specific quantities for all ingredients
- Provide realistic nutritional values
- Make it different from other recipes"""
        
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

