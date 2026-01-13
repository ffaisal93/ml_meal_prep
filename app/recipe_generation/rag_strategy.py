"""
RAG Strategy: Fetch candidates from Edamam API, then LLM selects and refines
This grounds LLM generation with real recipe data
"""
import json
import random
from typing import Dict, List, Optional
from openai import OpenAI
from cachetools import TTLCache
from app.config import settings
from app.recipe_generation.base import RecipeGenerationStrategy
from app.recipe_retriever import RecipeRetriever


class RAGStrategy(RecipeGenerationStrategy):
    """
    Strategy B: RAG (Retrieval-Augmented Generation)
    Fetch real recipe candidates from Edamam, then LLM selects and refines
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.retriever = RecipeRetriever()
        # Cache candidates by meal_type + dietary constraints
        self.candidate_cache = TTLCache(maxsize=100, ttl=settings.cache_ttl_seconds)
        self.used_candidates = {}  # Track used candidates per meal type
        self.max_prompt_candidates = 3  # How many candidates to show the LLM per request
    
    def get_strategy_name(self) -> str:
        return "rag"
    
    def reset(self):
        """Reset used candidates tracker"""
        self.used_candidates.clear()
    
    async def generate_recipe(
        self,
        meal_type: str,
        dietary_restrictions: List[str],
        preferences: List[str],
        special_requirements: List[str],
        day: int,
        prep_time_max: Optional[int] = None,
        duration_days: Optional[int] = None,
        **kwargs
    ) -> Dict:
        """
        Generate recipe using RAG approach:
        1. Fetch candidates from Edamam
        2. LLM selects best candidate
        3. LLM generates recipe using candidate's data as ground truth
        """
        # Get candidates (cached or fetched)
        candidates = await self._get_candidates(
            meal_type, dietary_restrictions, preferences, prep_time_max, duration_days
        )
        
        if not candidates:
            # Fallback to LLM-only if no candidates
            print(f"No Edamam candidates found for {meal_type}, falling back to LLM-only")
            return await self._generate_llm_only(meal_type, dietary_restrictions, preferences, special_requirements, day, prep_time_max)
        
        # Filter out already-used candidates
        available_candidates = self._filter_used_candidates(candidates, meal_type)
        
        if not available_candidates:
            # Reset if all candidates used
            self.used_candidates[meal_type] = []
            available_candidates = candidates
        
        random.shuffle(available_candidates)
        selected_candidates = available_candidates[: self.max_prompt_candidates] or available_candidates

        recipe = await self._generate_with_candidates(
            meal_type,
            dietary_restrictions,
            preferences,
            special_requirements,
            day,
            prep_time_max,
            selected_candidates,
        )

        if meal_type not in self.used_candidates:
            self.used_candidates[meal_type] = []
        for cand in selected_candidates:
            title = cand.get("title", "")
            if title:
                self.used_candidates[meal_type].append(title)
        
        return recipe
    
    async def _get_candidates(
        self,
        meal_type: str,
        dietary: List[str],
        preferences: List[str],
        prep_time_max: Optional[int],
        duration_days: Optional[int]
    ) -> List[Dict]:
        """Get candidates from cache or fetch from Edamam"""
        # Create cache key
        cache_key = f"{meal_type}|{','.join(sorted(dietary or []))}|{prep_time_max}"
        
        # Check cache
        if cache_key in self.candidate_cache:
            return self.candidate_cache[cache_key]
        
        # Calculate how many candidates needed
        count = max(3, duration_days or 3)
        count = min(count, 10)  # Cap at 10
        
        noisy_preferences = list(preferences or [])
        noisy_preferences.extend(self._get_query_noise(meal_type))

        candidates = await self.retriever.get_candidates(
            meal_type=meal_type,
            dietary=dietary or [],
            preferences=noisy_preferences,
            prep_time_max=prep_time_max,
            count=count
        )
        
        # Cache candidates
        if candidates:
            random.shuffle(candidates)
            self.candidate_cache[cache_key] = candidates
        
        return candidates
    
    def _filter_used_candidates(self, candidates: List[Dict], meal_type: str) -> List[Dict]:
        """Filter out candidates that have already been used"""
        used = set(self.used_candidates.get(meal_type, []))
        return [c for c in candidates if c.get("title", "") not in used]
    
    async def _generate_with_candidates(
        self,
        meal_type: str,
        dietary_restrictions: List[str],
        preferences: List[str],
        special_requirements: List[str],
        day: int,
        prep_time_max: Optional[int],
        candidates: List[Dict]
    ) -> Dict:
        """Generate recipe using LLM with candidates as ground truth"""
        
        # Build candidate prompt
        candidate_list = []
        for i, candidate in enumerate(candidates[:5], 1):  # Limit to 5 candidates
            candidate_list.append(
                f"{i}. {candidate['title']}\n"
                f"   - Ingredients: {', '.join(candidate['ingredients'][:5])}\n"
                f"   - Nutrition: {candidate['nutrition']['calories']} cal, "
                f"{candidate['nutrition']['protein']}g protein, "
                f"{candidate['nutrition']['carbs']}g carbs, "
                f"{candidate['nutrition']['fat']}g fat\n"
                f"   - Prep time: {candidate['prep_time_minutes']} minutes"
            )
        
        candidate_prompt = "\n".join(candidate_list)
        
        # Build requirements
        requirements = []
        if dietary_restrictions:
            requirements.append(f"Dietary restrictions: {', '.join(dietary_restrictions)}")
        if preferences:
            requirements.append(f"Preferences: {', '.join(preferences)}")
        if special_requirements:
            requirements.append(f"Special requirements: {', '.join(special_requirements)}")
        if prep_time_max:
            requirements.append(f"Maximum preparation time: {prep_time_max} minutes")
        
        requirements_str = "\n".join(requirements) if requirements else "No specific restrictions"
        
        system_prompt = """You are a professional chef generating recipes based on real recipe candidates.
Choose the BEST candidate that matches the user's requirements, then generate a complete recipe using that candidate's data as ground truth.

IMPORTANT:
- Use the EXACT nutritional values from the chosen candidate
- Use the EXACT core ingredients from the chosen candidate
- You may rephrase instructions for clarity, but stay true to the dish
- Do NOT invent new ingredients or nutritional values"""
        
        user_prompt = f"""Generate a {meal_type} recipe for day {day}.

Here are real recipe candidates from Edamam API:
{candidate_prompt}

Requirements:
{requirements_str}

Choose ONE candidate that best matches the requirements, then generate a complete recipe JSON using that candidate's nutritional data and ingredients.

Return JSON:
{{
  "recipe_name": "<creative name based on chosen candidate>",
  "description": "<1-2 sentence description>",
  "ingredients": ["<quantity> <ingredient>", ...],  // Use candidate's ingredients
  "nutritional_info": {{
    "calories": <EXACT from chosen candidate>,
    "protein": <EXACT from chosen candidate>,
    "carbs": <EXACT from chosen candidate>,
    "fat": <EXACT from chosen candidate>
  }},
  "preparation_time": "<X mins>",  // EXACT from chosen candidate
  "instructions": "<step-by-step instructions, 3-5 steps>",
  "source": "AI Generated (based on Edamam recipe)"
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3  # Lower temperature for more consistent results
            )
            
            recipe = json.loads(response.choices[0].message.content)
            recipe = self._validate_recipe(recipe, meal_type, candidates)
            return recipe
            
        except Exception as e:
            print(f"RAG recipe generation failed: {e}")
            # Fallback to first candidate if LLM fails
            if candidates:
                return self._candidate_to_recipe(candidates[0], meal_type)
            return await self._generate_llm_only(meal_type, dietary_restrictions, preferences, special_requirements, day, prep_time_max)
    
    async def _generate_llm_only(
        self,
        meal_type: str,
        dietary_restrictions: List[str],
        preferences: List[str],
        special_requirements: List[str],
        day: int,
        prep_time_max: Optional[int]
    ) -> Dict:
        """Fallback to LLM-only generation"""
        from app.recipe_generation.llm_only import LLMOnlyStrategy
        llm_strategy = LLMOnlyStrategy()
        return await llm_strategy.generate_recipe(
            meal_type, dietary_restrictions, preferences, special_requirements, day, prep_time_max
        )
    
    def _validate_recipe(self, recipe: Dict, meal_type: str, candidates: List[Dict]) -> Dict:
        """Validate recipe and ensure it matches candidate data"""
        # Basic validation
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
            recipe["source"] = "AI Generated (based on Edamam recipe)"
        recipe["meal_type"] = meal_type
        
        # Validate nutritional values match candidate (±10% tolerance)
        if candidates and "nutritional_info" in recipe:
            candidate_nutrition = candidates[0].get("nutrition", {})
            for key in ["calories", "protein", "carbs", "fat"]:
                if key in candidate_nutrition:
                    candidate_val = candidate_nutrition[key]
                    recipe_val = recipe["nutritional_info"].get(key, candidate_val)
                    # Allow ±10% tolerance
                    if abs(recipe_val - candidate_val) / candidate_val > 0.1:
                        print(f"Warning: {key} value {recipe_val} differs significantly from candidate {candidate_val}")
        
        return recipe
    
    def _candidate_to_recipe(self, candidate: Dict, meal_type: str) -> Dict:
        """Convert candidate directly to recipe format"""
        return {
            "recipe_name": candidate["title"],
            "description": f"A {meal_type} recipe from {candidate['source']}",
            "ingredients": [f"1 {ing}" for ing in candidate["ingredients"]],
            "nutritional_info": candidate["nutrition"],
            "preparation_time": f"{candidate['prep_time_minutes']} mins",
            "instructions": f"See full recipe at: {candidate['url']}",
            "source": f"Edamam: {candidate['source']}",
            "meal_type": meal_type
        }

    def _get_query_noise(self, meal_type: str) -> List[str]:
        """Add neutral descriptors to diversify Edamam results without breaking constraints."""
        ambience_terms = [
            "seasonal", "chef-inspired", "fresh", "vibrant", "modern", "comfort",
            "home-style", "rustic", "colorful", "balanced", "weekday-friendly"
        ]
        meal_type_tags = {
            "breakfast": ["energizing", "sunrise", "brunch-ready"],
            "lunch": ["midday", "bistro", "light"],
            "dinner": ["evening", "family-style", "hearty"],
            "snack": ["bite-sized", "quick", "grab-and-go"],
        }
        noise = []
        if meal_type.lower() in meal_type_tags:
            noise.append(random.choice(meal_type_tags[meal_type.lower()]))
        noise.extend(random.sample(ambience_terms, k=2))
        return noise

