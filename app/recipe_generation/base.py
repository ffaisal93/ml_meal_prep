"""
Abstract base class for recipe generation strategies
All strategies must implement this interface for consistency and evaluation
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class RecipeGenerationStrategy(ABC):
    """
    Abstract base class for recipe generation strategies
    
    This interface ensures all strategies:
    - Can be swapped easily
    - Return consistent output format
    - Can be evaluated side-by-side
    """
    
    @abstractmethod
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
        Generate a recipe using this strategy
        
        Args:
            meal_type: breakfast, lunch, dinner, or snack
            dietary_restrictions: List of dietary restrictions
            preferences: List of preferences
            special_requirements: List of special requirements
            day: Day number (for variety)
            prep_time_max: Maximum preparation time in minutes
            **kwargs: Additional strategy-specific parameters
        
        Returns:
            Recipe dictionary with all required fields matching the Recipe model
        """
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Return the name of this strategy for logging/evaluation"""
        pass
    
    def reset(self):
        """
        Reset any internal state (e.g., used recipes tracker)
        Called at the start of a new meal plan generation
        """
        pass

