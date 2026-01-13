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
        - Deterministic selection (for consistency)
        """
        # Track meal count for this meal type
        if meal_type not in self.meal_counter:
            self.meal_counter[meal_type] = 0
        self.meal_counter[meal_type] += 1
        
        # Deterministic selection based on ratio
        # Example: rag_ratio=0.7 means every 10th meal, 7 use RAG, 3 use LLM
        use_rag = (self.meal_counter[meal_type] % 10) < (self.rag_ratio * 10)
        
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

