"""
RAG Strategy: Fetch candidates from Edamam API, then LLM selects and refines
This grounds LLM generation with real recipe data
"""
import json
import random
import asyncio
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
        self.candidate_cache = TTLCache(maxsize=100, ttl=settings.cache_ttl_seconds)
        self.used_candidates = {}
        self.max_prompt_candidates = 3
        self._lock = asyncio.Lock()
    
    def get_strategy_name(self) -> str:
        return "rag"
    
    def reset(self):
        """Reset used candidates tracker"""
        self.used_candidates.clear()
    
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
        Generate all meals for a day - RAG doesn't batch well, so generate sequentially
        but with proper diversity tracking
        """
        meals = []
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
            recipe["meal_type"] = meal_type
            meals.append(recipe)
        return meals
    
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
        
        # Filter and select candidates (thread-safe)
        async with self._lock:
            available_candidates = self._filter_used_candidates(candidates, meal_type)
            if not available_candidates:
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
            exclusions=kwargs.get('exclusions', [])
        )

        # Track used candidates (thread-safe)
        async with self._lock:
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
        
        # Calculate how many candidates needed - ensure enough for diversity
        # For 7-day plans, we need at least 21 recipes (7 days × 3 meals)
        # Fetch more candidates to ensure variety
        if duration_days:
            # Request more candidates: at least 3× duration_days, capped at 20
            count = max(10, min(duration_days * 3, 20))
        else:
            count = 10  # Default for shorter plans
        
        # Don't add query noise - it makes queries too specific and returns 0 results
        # Just use the basic preferences
        candidates = await self.retriever.get_candidates(
            meal_type=meal_type,
            dietary=dietary or [],
            preferences=preferences or [],
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
        available = [c for c in candidates if c.get("title", "") not in used]
        # If we've used too many, allow some reuse but prefer new ones
        # This ensures we always have options even for long meal plans
        if len(available) < 2 and len(candidates) > len(used):
            # Reset used list for this meal type to allow reuse
            self.used_candidates[meal_type] = []
            return candidates
        return available
    
    async def _generate_with_candidates(
        self,
        meal_type: str,
        dietary_restrictions: List[str],
        preferences: List[str],
        special_requirements: List[str],
        day: int,
        prep_time_max: Optional[int],
        candidates: List[Dict],
        exclusions: List[str] = None
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
        # Filter out excluded cuisines/styles from candidates
        exclusions = exclusions or []
        if exclusions:
            filtered_candidates = []
            for candidate in candidates:
                title = candidate.get('title', '').lower()
                source = candidate.get('source', '').lower()
                # Check if any exclusion keyword is in the recipe title or source
                excluded = False
                for exclusion in exclusions:
                    exclusion_lower = exclusion.lower()
                    if exclusion_lower in title or exclusion_lower in source:
                        excluded = True
                        break
                if not excluded:
                    filtered_candidates.append(candidate)
            
            # If we filtered everything, fallback to original
            if filtered_candidates:
                candidates = filtered_candidates
        
        requirements = []
        if dietary_restrictions:
            requirements.append(f"Dietary restrictions: {', '.join(dietary_restrictions)}")
        if preferences:
            requirements.append(f"Preferences: {', '.join(preferences)}")
        if special_requirements:
            requirements.append(f"Special requirements: {', '.join(special_requirements)}")
        if prep_time_max:
            requirements.append(f"Maximum preparation time: {prep_time_max} minutes")
        if exclusions:
            requirements.append(f"EXCLUDE: {', '.join(exclusions)} (do NOT choose recipes with these keywords)")
        
        requirements_str = "\n".join(requirements) if requirements else "No specific restrictions"
        
        system_prompt = """You are a chef selecting from real recipe candidates. Choose the best match for requirements and create a complete recipe using the candidate's exact nutritional data and core ingredients. Prioritize diversity. Return valid JSON only."""
        
        user_prompt = f"""Create a {meal_type} recipe for day {day}.

Available recipe candidates:
{candidate_prompt}

Requirements:
{requirements_str}

Choose the ONE candidate that best matches requirements. Use its EXACT nutritional values and core ingredients.

Return JSON:
{{
  "recipe_name": "Creative name based on candidate",
  "description": "Brief description",
  "ingredients": ["2 cups flour", "1 tbsp oil", ...],
  "nutritional_info": {{"calories": <exact from candidate>, "protein": <exact>, "carbs": <exact>, "fat": <exact>}},
  "preparation_time": "X mins",
  "instructions": "Clear cooking steps",
  "source": "AI Generated (based on Edamam recipe)"
}}

Critical: Use EXACT nutrition from chosen candidate. Make recipe name natural and appetizing."""
        
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
        else:
            # Validate prep time is realistic (not 0.0 or empty) and format as integer
            prep_time_str = str(recipe.get("preparation_time", "30 mins")).lower()
            # Extract number from string like "0 mins", "0.0 mins", "30.0 mins", etc.
            import re
            time_match = re.search(r'(\d+\.?\d*)', prep_time_str)
            if time_match:
                prep_time_num = float(time_match.group(1))
                if prep_time_num <= 0 or prep_time_num < 5:
                    # Default to reasonable prep time based on meal type
                    default_times = {"breakfast": 15, "lunch": 25, "dinner": 30, "snack": 10}
                    recipe["preparation_time"] = f"{default_times.get(meal_type.lower(), 20)} mins"
                else:
                    # Format as integer (no decimals)
                    recipe["preparation_time"] = f"{int(prep_time_num)} mins"
            elif not prep_time_str or prep_time_str.strip() == "":
                recipe["preparation_time"] = "30 mins"
        if "instructions" not in recipe:
            recipe["instructions"] = "Follow standard cooking procedures."
        elif isinstance(recipe["instructions"], list):
            recipe["instructions"] = "\n".join(recipe["instructions"])
        if "source" not in recipe:
            recipe["source"] = "AI Generated (based on Edamam recipe)"
        recipe["meal_type"] = meal_type
        
        # Validate nutritional values match candidate (±20% tolerance)
        # If LLM diverges too much, override with candidate values for accuracy
        if candidates and "nutritional_info" in recipe:
            candidate_nutrition = candidates[0].get("nutrition", {})
            for key in ["calories", "protein", "carbs", "fat"]:
                if key in candidate_nutrition:
                    candidate_val = candidate_nutrition[key]
                    recipe_val = recipe["nutritional_info"].get(key, candidate_val)
                    # If values differ by >20%, use candidate value (more trustworthy)
                    if candidate_val > 0 and abs(recipe_val - candidate_val) / candidate_val > 0.2:
                        recipe["nutritional_info"][key] = candidate_val
                        # Optionally log this (comment out to reduce noise)
                        # print(f"Corrected {key}: {recipe_val} → {candidate_val} (using Edamam data)")
        
        return recipe
    
    def _candidate_to_recipe(self, candidate: Dict, meal_type: str) -> Dict:
        """Convert candidate directly to recipe format"""
        # Ensure prep time is realistic (minimum 10 minutes)
        prep_time = candidate.get('prep_time_minutes', 0)
        if prep_time <= 0 or prep_time < 10:
            # Default to reasonable prep time based on meal type
            default_times = {"breakfast": 15, "lunch": 25, "dinner": 30, "snack": 10}
            prep_time = default_times.get(meal_type.lower(), 20)
        
        return {
            "recipe_name": candidate["title"],
            "description": f"A {meal_type} recipe from {candidate['source']}",
            "ingredients": [f"1 {ing}" for ing in candidate["ingredients"]],
            "nutritional_info": candidate["nutrition"],
            "preparation_time": f"{int(prep_time)} mins",  # Ensure integer, no decimals
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

