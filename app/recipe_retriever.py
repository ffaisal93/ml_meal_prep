"""
Edamam Recipe API client for fetching real recipe candidates
"""
import base64
import httpx
from typing import List, Dict, Optional
from app.config import settings


class RecipeRetriever:
    """
    Fetches real recipe candidates from Edamam Recipe Search API
    
    API Documentation: https://developer.edamam.com/edamam-docs-recipe-api
    """
    
    def __init__(self, app_id: Optional[str] = None, app_key: Optional[str] = None, user_id: Optional[str] = None):
        """
        Initialize Edamam API client
        
        Args:
            app_id: Edamam Application ID (from config if not provided)
            app_key: Edamam Application Key (from config if not provided)
            user_id: Edamam User ID (from config if not provided)
        """
        self.app_id = app_id or getattr(settings, 'edamam_app_id', None)
        self.app_key = app_key or getattr(settings, 'edamam_app_key', None)
        self.user_id = user_id or getattr(settings, 'edamam_user_id', None) or self.app_id
        self.base_url = "https://api.edamam.com/api/recipes/v2"
        
        if not self.app_id or not self.app_key:
            raise ValueError("Edamam credentials (app_id, app_key) are required for RAG strategy")
        
        # Create Basic Auth header
        credentials = f"{self.app_id}:{self.app_key}"
        self.basic_auth = base64.b64encode(credentials.encode()).decode()
    
    async def get_candidates(
        self,
        meal_type: str,
        dietary: List[str] = None,
        preferences: List[str] = None,
        prep_time_max: Optional[int] = None,
        count: int = 5
    ) -> List[Dict]:
        """
        Fetch recipe candidates from Edamam API
        
        Args:
            meal_type: breakfast, lunch, dinner, snack
            dietary: List of dietary restrictions/preferences
            preferences: List of preferences
            prep_time_max: Maximum preparation time in minutes
            count: Number of candidates to return
        
        Returns:
            List of recipe candidate dictionaries
        """
        # Build query string
        query_parts = [meal_type]
        if dietary:
            query_parts.extend(dietary)
        if preferences:
            query_parts.extend(preferences)
        query = " ".join(query_parts)
        
        # Build parameters
        params = {
            "type": "public",
            "q": query,
            "app_id": self.app_id,
            "app_key": self.app_key,
            "to": min(count, 10)
        }
        
        # Map meal type
        meal_type_map = {
            "breakfast": "breakfast",
            "lunch": "lunch/dinner",
            "dinner": "lunch/dinner",
            "snack": "snack"
        }
        if meal_type.lower() in meal_type_map:
            params["mealType"] = meal_type_map[meal_type.lower()]
        
        # Map dietary restrictions to health labels
        health_labels = []
        health_label_map = {
            "vegetarian": "vegetarian",
            "vegan": "vegan",
            "pescatarian": "pecatarian",
            "paleo": "paleo",
            "keto": "keto-friendly",
            "gluten-free": "gluten-free",
            "dairy-free": "dairy-free",
            "nut-free": "tree-nut-free",
            "peanut-free": "peanut-free",
            "soy-free": "soy-free",
            "egg-free": "egg-free"
        }
        
        if dietary:
            for item in dietary:
                item_lower = item.lower()
                if item_lower in health_label_map:
                    health_labels.append(health_label_map[item_lower])
        
        if health_labels:
            params["health"] = list(set(health_labels))
        
        # Add time constraint
        if prep_time_max:
            params["time"] = f"1-{prep_time_max}"
        
        # Build headers
        headers = {
            "accept": "application/json",
            "Accept-Language": "en",
            "Authorization": f"Basic {self.basic_auth}",
            "Edamam-Account-User": self.user_id
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params, headers=headers, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                # Parse results
                candidates = []
                hits = data.get("hits", [])
                
                for hit in hits[:count]:
                    recipe = hit.get("recipe", {})
                    candidate = {
                        "title": recipe.get("label", "Unknown Recipe"),
                        "source": recipe.get("source", "Unknown"),
                        "url": recipe.get("url", ""),
                        "ingredients": [
                            ing.get("food", "").title()
                            for ing in recipe.get("ingredients", [])[:7]
                        ],
                        "nutrition": {
                            "calories": round(recipe.get("calories", 0) / recipe.get("yield", 1)),
                            "protein": round(recipe.get("totalNutrients", {}).get("PROCNT", {}).get("quantity", 0) / recipe.get("yield", 1), 1),
                            "carbs": round(recipe.get("totalNutrients", {}).get("CHOCDF", {}).get("quantity", 0) / recipe.get("yield", 1), 1),
                            "fat": round(recipe.get("totalNutrients", {}).get("FAT", {}).get("quantity", 0) / recipe.get("yield", 1), 1),
                        },
                        "prep_time_minutes": recipe.get("totalTime", 0),
                        "servings": recipe.get("yield", 1),
                        "health_labels": recipe.get("healthLabels", []),
                        "diet_labels": recipe.get("dietLabels", [])
                    }
                    candidates.append(candidate)
                
                return candidates
                
        except Exception as e:
            print(f"Error fetching Edamam candidates: {e}")
            return []

