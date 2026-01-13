"""
Hybrid Strategy: Mix of RAG and LLM-only generation
For a meal plan, some recipes come from Edamam candidates, some are pure LLM
"""
import random
from typing import Dict, List, Optional
from app.config import settings
from app.recipe_generation.base import RecipeGenerationStrategy
from app.recipe_generation.llm_only import LLMOnlyStrategy
from app.recipe_generation.rag_strategy import RAGStrategy


class HybridStrategy(RecipeGenerationStrategy):
    """
    Strategy C: Hybrid approach
    Mix of RAG (Edamam + LLM) and pure LLM generation
    
    Uses hybrid_rag_ratio to determine percentage of recipes from RAG
    Example: 0.7 means 70% RAG, 30% LLM-only
    """
    
    def __init__(self, rag_ratio: float = None):
        """
        Initialize hybrid strategy
        
        Args:
            rag_ratio: Ratio of RAG recipes (0.0 to 1.0). Defaults to config value.
        """
        self.rag_strategy = RAGStrategy()
        self.llm_strategy = LLMOnlyStrategy()
        self.rag_ratio = rag_ratio or getattr(settings, 'hybrid_rag_ratio', 0.7)
        self.rag_ratio = max(0.0, min(1.0, self.rag_ratio))  # Clamp to [0, 1]
        self.meal_counter = {}  # Track meal count per meal type for deterministic selection
    
    def get_strategy_name(self) -> str:
        return f"hybrid_{int(self.rag_ratio * 100)}rag"
    
    def reset(self):
        """Reset both strategies"""
        self.rag_strategy.reset()
        self.llm_strategy.reset()
        self.meal_counter.clear()
    
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
        Generate all meals for a day using hybrid approach
        Mix RAG and LLM-only for diversity
        """
        meals = []
        for i, meal_type in enumerate(meal_types):
            # Determine strategy per meal
            meal_type_idx = {"breakfast": 0, "lunch": 1, "dinner": 2, "snack": 3}.get(meal_type.lower(), 0)
            combined_index = (day * 10 + meal_type_idx) % 10
            use_rag = combined_index < (self.rag_ratio * 10)
            
            if use_rag:
                recipe = await self.rag_strategy.generate_recipe(
                    meal_type=meal_type,
                    dietary_restrictions=dietary_restrictions,
                    preferences=preferences,
                    special_requirements=special_requirements,
                    day=day,
                    prep_time_max=prep_time_max,
                    exclusions=exclusions
                )
            else:
                recipe = await self.llm_strategy.generate_recipe(
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
        **kwargs
    ) -> Dict:
        """
        Generate recipe using hybrid approach
        
        Determines whether to use RAG or LLM-only based on:
        - hybrid_rag_ratio configuration
        - Day number and meal type for better diversity distribution
        """
        # Use day number and meal type to create a unique identifier
        # This ensures better distribution across days, not just meal types
        meal_type_idx = {"breakfast": 0, "lunch": 1, "dinner": 2, "snack": 3}.get(meal_type.lower(), 0)
        
        # Create a combined index: (day * 10 + meal_type_index) % 10
        # This ensures different days get different strategy mixes
        combined_index = (day * 10 + meal_type_idx) % 10
        
        # Deterministic selection based on ratio and day/meal combination
        # Example: rag_ratio=0.7 means 7 out of 10 use RAG, 3 use LLM
        # Using combined_index ensures variety across days
        use_rag = combined_index < (self.rag_ratio * 10)
        
        if use_rag:
            # Use RAG strategy
            return await self.rag_strategy.generate_recipe(
                meal_type=meal_type,
                dietary_restrictions=dietary_restrictions,
                preferences=preferences,
                special_requirements=special_requirements,
                day=day,
                prep_time_max=prep_time_max,
                **kwargs
            )
        else:
            # Use LLM-only strategy
            return await self.llm_strategy.generate_recipe(
                meal_type=meal_type,
                dietary_restrictions=dietary_restrictions,
                preferences=preferences,
                special_requirements=special_requirements,
                day=day,
                prep_time_max=prep_time_max,
                **kwargs
            )

