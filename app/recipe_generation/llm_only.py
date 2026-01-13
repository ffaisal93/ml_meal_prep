"""
Pure LLM strategy: Generate recipes entirely using LLM (no external API)
This is the baseline strategy for comparison
"""
import json
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
    
    def get_strategy_name(self) -> str:
        return "llm_only"
    
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
        
        # Get used recipes for this meal type to ensure diversity
        used_for_meal_type = [name for name in self.used_recipes if meal_type.lower() in name.lower()]
        used_for_meal_type = used_for_meal_type[:10]  # Limit to recent 10
        
        diversity_constraint = ""
        if used_for_meal_type:
            diversity_constraint = f"\n\nIMPORTANT - DIVERSITY REQUIREMENT:\nDo NOT create recipes similar to these already used {meal_type} recipes:\n" + "\n".join(f"- {name}" for name in used_for_meal_type) + "\n\nCreate a completely different and unique recipe. Vary the cuisine style, main ingredients, and cooking method."
        
        system_prompt = """You are a professional chef and nutritionist. Generate detailed, realistic, and cookable recipes.

Generate recipes that:
- Are realistic and actually cookable
- Include specific ingredient quantities
- Have clear, step-by-step instructions
- Include accurate nutritional information
- Are appropriate for the meal type and dietary requirements
- Are diverse and unique (avoid repeating similar recipes)

Return valid JSON only."""
        
        prep_time_constraint = ""
        if prep_time_max:
            prep_time_constraint = f"\nCRITICAL: The preparation_time must be {prep_time_max} minutes or less. Choose quick, simple recipes that can be prepared in this time."
        
        user_prompt = f"""Generate a {meal_type} recipe for day {day}.

Requirements:
{requirements_str}{prep_time_constraint}{diversity_constraint}

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
- Recipe name is creative and descriptive
- Recipe is unique and different from previously generated recipes"""
        
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
            
            # Track used recipe name for diversity
            recipe_name = recipe.get("recipe_name", "").lower()
            if recipe_name:
                self.used_recipes.add(recipe_name)
                # Keep only recent 50 recipes to avoid memory bloat
                if len(self.used_recipes) > 50:
                    # Remove oldest (simple approach: keep last 50)
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

