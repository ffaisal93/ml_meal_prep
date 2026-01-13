"""
Recipe generation service - uses strategy pattern for flexible generation approaches
"""
from typing import Dict, List, Optional
from app.config import settings
from app.recipe_generation.factory import RecipeStrategyFactory


class RecipeService:
    """
    Service for generating recipes using configurable strategies
    
    Supports multiple generation modes:
    - llm_only: Pure LLM generation
    - rag: Edamam candidates + LLM refinement
    - hybrid: Mix of both approaches
    """
    
    def __init__(self, strategy_mode: Optional[str] = None):
        """
        Initialize recipe service with a strategy
        
        Args:
            strategy_mode: Strategy mode to use. If None, uses config setting.
        """
        self.strategy = RecipeStrategyFactory.create(strategy_mode)
        self.strategy_name = self.strategy.get_strategy_name()
    
    async def generate_recipe(
        self,
        meal_type: str,
        dietary_restrictions: List[str],
        preferences: List[str],
        special_requirements: List[str],
        day: int,
        prep_time_max: Optional[int] = None,
        duration_days: Optional[int] = None,
        exclusions: List[str] = None
    ) -> Dict:
        """
        Generate a single recipe using the configured strategy
        
        Args:
            meal_type: breakfast, lunch, dinner, or snack
            dietary_restrictions: List of dietary restrictions
            preferences: List of preferences
            special_requirements: List of special requirements
            day: Day number (for variety)
            prep_time_max: Maximum preparation time in minutes
            duration_days: Total duration of meal plan (for candidate count)
        
        Returns:
            Recipe dictionary with all required fields
        """
        return await self.strategy.generate_recipe(
            meal_type=meal_type,
            dietary_restrictions=dietary_restrictions,
            preferences=preferences,
            special_requirements=special_requirements,
            day=day,
            prep_time_max=prep_time_max,
            duration_days=duration_days,
            exclusions=exclusions or []
        )
    
    def reset_used_recipes(self):
        """Reset the strategy's internal state (call at start of new meal plan)"""
        self.strategy.reset()
    
    def get_strategy_name(self) -> str:
        """Get the name of the current strategy"""
        return self.strategy_name
