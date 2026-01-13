"""
Factory for creating recipe generation strategies based on configuration
"""
from typing import Optional
from app.config import settings
from app.recipe_generation.base import RecipeGenerationStrategy
from app.recipe_generation.llm_only import LLMOnlyStrategy
from app.recipe_generation.rag_strategy import RAGStrategy
from app.recipe_generation.hybrid_strategy import HybridStrategy


class RecipeStrategyFactory:
    """
    Factory to create recipe generation strategies based on configuration
    
    Supported modes:
    - "llm_only": Pure LLM generation (baseline)
    - "rag": Edamam candidates + LLM refinement
    - "hybrid": Mix of RAG and LLM-only
    """
    
    @staticmethod
    def create(mode: Optional[str] = None) -> RecipeGenerationStrategy:
        """
        Create a recipe generation strategy
        
        Args:
            mode: Strategy mode. If None, uses RECIPE_GENERATION_MODE from config.
                  Options: "llm_only", "rag", "hybrid"
        
        Returns:
            RecipeGenerationStrategy instance
        """
        mode = mode or getattr(settings, 'recipe_generation_mode', 'llm_only')
        mode = mode.lower().strip()
        
        if mode == "llm_only":
            return LLMOnlyStrategy()
        elif mode == "rag":
            return RAGStrategy()
        elif mode == "hybrid":
            rag_ratio = getattr(settings, 'hybrid_rag_ratio', 0.7)
            return HybridStrategy(rag_ratio=rag_ratio)
        else:
            # Default to LLM-only if unknown mode
            print(f"Unknown recipe generation mode: {mode}. Defaulting to 'llm_only'")
            return LLMOnlyStrategy()
    
    @staticmethod
    def get_available_modes() -> list:
        """Get list of available strategy modes"""
        return ["llm_only", "rag", "hybrid"]

