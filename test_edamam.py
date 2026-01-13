#!/usr/bin/env python3
"""
Standalone test script for Edamam Recipe Search API
Tests fetching recipe candidates similar to meal planner use cases
"""

import os
import json
import base64
import httpx
from typing import List, Dict, Optional


class EdamamTester:
    """
    Test Edamam API for recipe candidate retrieval
    
    API Documentation: https://developer.edamam.com/edamam-docs-recipe-api
    
    Available API Parameters:
    - type: "public" (required)
    - q: Query string (required)
    - app_id, app_key: Authentication (required)
    - mealType: breakfast, brunch, lunch/dinner, snack, teatime
    - diet: balanced, high-fiber, high-protein, low-carb, low-fat, low-sodium (one at a time)
    - health: vegetarian, vegan, gluten-free, dairy-free, etc. (multiple allowed)
    - cuisineType: american, asian, italian, mediterranean, etc.
    - dishType: main course, salad, soup, dessert, etc.
    - time: Prep time range (e.g., "1-30" for 1-30 minutes)
    - imageSize: THUMBNAIL, SMALL, REGULAR, LARGE
    - co2EmissionsClass: A+ through G (requires beta=true)
    - from, to: Pagination (from=0, to=10)
    """
    
    def __init__(self, app_id: str, app_key: str, user_id: Optional[str] = None):
        """
        Initialize with Edamam credentials
        
        Get these from: https://developer.edamam.com/edamam-recipe-api
        
        Args:
            app_id: Edamam Application ID
            app_key: Edamam Application Key
            user_id: Optional user ID (required if your app requires it)
        """
        self.app_id = app_id.strip() if app_id else ""
        self.app_key = app_key.strip() if app_key else ""
        # If user_id not provided, use app_id (common pattern)
        self.user_id = user_id.strip() if user_id else self.app_id
        self.base_url = "https://api.edamam.com/api/recipes/v2"
        
        # Create Basic Auth header (base64 encoded app_id:app_key)
        credentials = f"{self.app_id}:{self.app_key}"
        self.basic_auth = base64.b64encode(credentials.encode()).decode()
        
        # Validate credentials format
        if not self.app_id:
            raise ValueError("App ID is required but appears to be empty. Please check your EDAMAM_APP_ID environment variable.")
        if not self.app_key:
            raise ValueError("App Key is required but appears to be empty. Please check your EDAMAM_APP_KEY environment variable.")
        
        # Validate credential lengths (Edamam IDs are typically 16-32 chars, keys are 32+ chars)
        if len(self.app_id) < 8:
            print(f"⚠️  Warning: App ID seems too short ({len(self.app_id)} chars). Expected 16-32 characters.")
        if len(self.app_key) < 16:
            print(f"⚠️  Warning: App Key seems too short ({len(self.app_key)} chars). Expected 32+ characters.")
        
        # Show masked credentials for debugging
        if len(self.app_id) > 8:
            masked_id = self.app_id[:4] + "..." + self.app_id[-4:]
        else:
            masked_id = self.app_id[:2] + "***" if len(self.app_id) > 2 else "***"
        
        if len(self.app_key) > 8:
            masked_key = self.app_key[:4] + "..." + self.app_key[-4:]
        else:
            masked_key = self.app_key[:2] + "***" if len(self.app_key) > 2 else "***"
        
        print(f"🔑 Using credentials:")
        print(f"   App ID: {masked_id} (length: {len(self.app_id)})")
        print(f"   App Key: {masked_key} (length: {len(self.app_key)})")
        masked_user = self.user_id[:4] + "..." + self.user_id[-4:] if len(self.user_id) > 8 else self.user_id
        print(f"   User ID: {masked_user} (length: {len(self.user_id)})")
    
    def search_recipes(
        self,
        meal_type: str = "breakfast",
        dietary: List[str] = None,
        preferences: List[str] = None,
        prep_time_max: Optional[int] = None,
        count: int = 5,
        cuisine_type: Optional[str] = None,
        dish_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for recipe candidates using Edamam Recipe Search API
        
        API Documentation: https://developer.edamam.com/edamam-docs-recipe-api
        
        Args:
            meal_type: breakfast, brunch, lunch, dinner, snack, teatime
            dietary: List of dietary restrictions/preferences
                - Diet labels: balanced, high-fiber, high-protein, low-carb, low-fat, low-sodium
                - Health labels: vegetarian, vegan, gluten-free, dairy-free, etc.
            preferences: List of preferences (same format as dietary)
            prep_time_max: Maximum preparation time in minutes
            count: Number of recipes to return (max 100)
            cuisine_type: Optional cuisine filter (e.g., "asian", "italian", "mediterranean")
            dish_type: Optional dish type filter (e.g., "main course", "salad", "soup")
        
        Returns:
            List of recipe candidates with key information
        """
        # Build query string
        query_parts = [meal_type]
        
        # Add dietary restrictions to query
        if dietary:
            query_parts.extend(dietary)
        
        # Add preferences to query
        if preferences:
            query_parts.extend(preferences)
        
        query = " ".join(query_parts)
        
        # Build parameters
        # According to API docs: type=public, q=query string, app_id, app_key are required
        params = {
            "type": "public",
            "q": query,
            "app_id": self.app_id,
            "app_key": self.app_key,
            "to": min(count, 10)  # Limit to 10 for testing
        }
        
        # Optional: Add beta=true if using beta features like co2EmissionsClass
        # params["beta"] = "true"
        
        # Add meal type filter (according to API docs: breakfast, brunch, lunch/dinner, snack, teatime)
        meal_type_map = {
            "breakfast": "breakfast",
            "lunch": "lunch/dinner",  # API uses "lunch/dinner" for both
            "dinner": "lunch/dinner",  # API uses "lunch/dinner" for both
            "snack": "snack",
            "brunch": "brunch",
            "teatime": "teatime"
        }
        if meal_type.lower() in meal_type_map:
            params["mealType"] = meal_type_map[meal_type.lower()]
        
        # Separate diet labels and health labels
        # Diet labels (from API docs): balanced, high-fiber, high-protein, low-carb, low-fat, low-sodium
        diet_labels = []
        diet_map = {
            "balanced": "balanced",
            "high-fiber": "high-fiber",
            "high-protein": "high-protein",
            "low-carb": "low-carb",
            "low-fat": "low-fat",
            "low-sodium": "low-sodium"
        }
        
        # Health labels (from API docs): vegetarian, vegan, gluten-free, dairy-free, etc.
        health_labels = []
        health_label_map = {
            # Main diets (these are health labels, not diet labels)
            "vegetarian": "vegetarian",
            "vegan": "vegan",
            "pescatarian": "pecatarian",  # Note: API uses "pecatarian" not "pescatarian"
            "paleo": "paleo",
            "keto": "keto-friendly",
            "mediterranean": "Mediterranean",
            # Restrictions
            "gluten-free": "gluten-free",
            "dairy-free": "dairy-free",
            "nut-free": "tree-nut-free",
            "peanut-free": "peanut-free",
            "soy-free": "soy-free",
            "egg-free": "egg-free",
            "fish-free": "fish-free",
            "shellfish-free": "shellfish-free",
            "wheat-free": "wheat-free",
            "sugar-conscious": "sugar-conscious",
            "low-sugar": "low-sugar"
        }
        
        # Process dietary restrictions and preferences
        if dietary:
            for item in dietary:
                item_lower = item.lower()
                # Check if it's a diet label
                if item_lower in diet_map:
                    diet_labels.append(diet_map[item_lower])
                # Check if it's a health label
                elif item_lower in health_label_map:
                    health_labels.append(health_label_map[item_lower])
        
        if preferences:
            for pref in preferences:
                pref_lower = pref.lower()
                # Check if preference maps to a diet label
                if pref_lower in diet_map:
                    diet_labels.append(diet_map[pref_lower])
                # Check if preference maps to a health label
                elif pref_lower in health_label_map:
                    health_labels.append(health_label_map[pref_lower])
        
        # Add diet parameter (API allows one diet label)
        if diet_labels:
            params["diet"] = diet_labels[0]  # API typically allows one diet at a time
        
        # Add health parameter (API allows multiple health labels)
        if health_labels:
            # Remove duplicates and add as list
            params["health"] = list(set(health_labels))
        
        # Add cuisine type filter (optional)
        # Valid values: american, asian, british, caribbean, chinese, french, greek, 
        # indian, italian, japanese, korean, mediterranean, mexican, middle eastern, etc.
        if cuisine_type:
            params["cuisineType"] = cuisine_type.lower()
        
        # Add dish type filter (optional)
        # Valid values: main course, salad, soup, dessert, side dish, etc.
        if dish_type:
            params["dishType"] = dish_type.lower()
        
        # Add time constraint (prep time in minutes)
        # API accepts time as a range like "1-30" or single value
        if prep_time_max:
            params["time"] = f"1-{prep_time_max}"  # Edamam uses range format
        
        # Make API call
        try:
            print(f"\n🔍 Searching Edamam API...")
            print(f"   Query: {query}")
            print(f"   Meal Type: {meal_type} → {params.get('mealType', 'N/A')}")
            if params.get('diet'):
                print(f"   Diet Label: {params.get('diet')}")
            if params.get('health'):
                print(f"   Health Labels: {', '.join(params.get('health', []))}")
            if params.get('cuisineType'):
                print(f"   Cuisine: {params.get('cuisineType')}")
            if params.get('dishType'):
                print(f"   Dish Type: {params.get('dishType')}")
            print(f"   Max Prep Time: {prep_time_max or 'None'} minutes")
            print(f"   Requesting: {count} candidates")
            
            # Debug: Show the URL being called (without sensitive data)
            debug_params = {k: v for k, v in params.items() if k not in ['app_id', 'app_key']}
            debug_url = f"{self.base_url}?{'&'.join([f'{k}={v}' for k, v in debug_params.items()])}"
            print(f"   API Parameters: {debug_params}")
            print()
            
            # Build headers (Basic Auth + User ID header)
            headers = {
                "accept": "application/json",
                "Accept-Language": "en",
                "Authorization": f"Basic {self.basic_auth}",
                "Edamam-Account-User": self.user_id
            }
            
            response = httpx.get(self.base_url, params=params, headers=headers, timeout=10.0)
            
            # Debug: Check response status
            print(f"   Response Status: {response.status_code}")
            
            response.raise_for_status()
            
            data = response.json()
            
            # Parse results
            candidates = []
            hits = data.get("hits", [])
            
            print(f"✅ Found {len(hits)} recipes\n")
            
            for hit in hits[:count]:
                recipe = hit.get("recipe", {})
                
                # Extract key information
                candidate = {
                    "title": recipe.get("label", "Unknown Recipe"),
                    "source": recipe.get("source", "Unknown"),
                    "url": recipe.get("url", ""),
                    "image": recipe.get("image", ""),
                    
                    # Ingredients (first 5-7 core ingredients)
                    "ingredients": [
                        ing.get("food", "").title() 
                        for ing in recipe.get("ingredients", [])[:7]
                    ],
                    
                    # Nutritional info
                    "nutrition": {
                        "calories": round(recipe.get("calories", 0) / recipe.get("yield", 1)),
                        "protein": round(recipe.get("totalNutrients", {}).get("PROCNT", {}).get("quantity", 0) / recipe.get("yield", 1), 1),
                        "carbs": round(recipe.get("totalNutrients", {}).get("CHOCDF", {}).get("quantity", 0) / recipe.get("yield", 1), 1),
                        "fat": round(recipe.get("totalNutrients", {}).get("FAT", {}).get("quantity", 0) / recipe.get("yield", 1), 1),
                    },
                    
                    # Prep time (Edamam provides totalTime)
                    "prep_time_minutes": recipe.get("totalTime", 0),
                    
                    # Servings
                    "servings": recipe.get("yield", 1),
                    
                    # Health labels
                    "health_labels": recipe.get("healthLabels", []),
                    
                    # Diet labels
                    "diet_labels": recipe.get("dietLabels", [])
                }
                
                candidates.append(candidate)
            
            return candidates
            
        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error: {e.response.status_code}")
            error_text = e.response.text
            print(f"   Response: {error_text}")
            
            if e.response.status_code == 401:
                error_text_lower = error_text.lower()
                if "userid" in error_text_lower or "edamam-account-user" in error_text_lower:
                    print(f"\n💡 Your application requires a User ID header.")
                    print(f"   Set it with: export EDAMAM_USER_ID='your_user_id'")
                    print(f"   Or create a new application that doesn't require user ID")
                    print(f"   (Check your Edamam dashboard application settings)")
                else:
                    print(f"\n💡 Troubleshooting 401 Authentication Error:")
                    print(f"   1. Verify your App ID and App Key are correct")
                    print(f"   2. Check that you're using the Recipe Search API credentials (not Food Database)")
                    print(f"   3. Ensure credentials don't have extra spaces or quotes")
                    print(f"   4. Get new credentials from: https://developer.edamam.com/edamam-recipe-api")
                    print(f"   5. Make sure your application is activated in the Edamam dashboard")
                
                # Show what we're sending (masked)
                print(f"\n   Debug Info:")
                print(f"   - App ID length: {len(self.app_id)} characters")
                print(f"   - App Key length: {len(self.app_key)} characters")
                print(f"   - App ID starts with: {self.app_id[:3]}...")
                print(f"   - App Key starts with: {self.app_key[:3]}...")
            
            return []
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return []
    
    def test_authentication(self) -> bool:
        """Test if credentials are valid with a simple API call"""
        print("\n🔐 Testing authentication...")
        try:
            params = {
                "type": "public",
                "q": "chicken",
                "app_id": self.app_id,
                "app_key": self.app_key,
                "to": 1
            }
            
            # Build headers (Basic Auth + User ID header)
            headers = {
                "accept": "application/json",
                "Accept-Language": "en",
                "Authorization": f"Basic {self.basic_auth}",
                "Edamam-Account-User": self.user_id
            }
            
            response = httpx.get(self.base_url, params=params, headers=headers, timeout=10.0)
            
            if response.status_code == 200:
                print("✅ Authentication successful!")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
        except Exception as e:
            print(f"❌ Authentication test error: {str(e)}")
            return False
    
    def print_candidates(self, candidates: List[Dict]):
        """Pretty print recipe candidates"""
        if not candidates:
            print("No candidates found.")
            return
        
        for i, candidate in enumerate(candidates, 1):
            print(f"\n{'='*60}")
            print(f"📋 Candidate #{i}: {candidate['title']}")
            print(f"{'='*60}")
            print(f"Source: {candidate['source']}")
            print(f"Prep Time: {candidate['prep_time_minutes']} minutes")
            print(f"Servings: {candidate['servings']}")
            print(f"\n🥘 Core Ingredients:")
            for ing in candidate['ingredients']:
                print(f"   • {ing}")
            print(f"\n📊 Nutrition (per serving):")
            nut = candidate['nutrition']
            print(f"   Calories: {nut['calories']} kcal")
            print(f"   Protein: {nut['protein']}g")
            print(f"   Carbs: {nut['carbs']}g")
            print(f"   Fat: {nut['fat']}g")
            if candidate['diet_labels']:
                print(f"\n🏷️  Diet Labels: {', '.join(candidate['diet_labels'])}")
            if candidate['health_labels']:
                print(f"🏷️  Health Labels: {', '.join(candidate['health_labels'][:5])}")
            print(f"\n🔗 URL: {candidate['url']}")


def main():
    """Test Edamam API with sample queries"""
    
    # Get credentials from environment or user input
    app_id = os.getenv("EDAMAM_APP_ID")
    app_key = os.getenv("EDAMAM_APP_KEY")
    user_id = os.getenv("EDAMAM_USER_ID")  # Optional, defaults to app_id if not provided
    
    # Debug: Show if env vars exist (but not their values)
    print("🔍 Checking environment variables...")
    print(f"   EDAMAM_APP_ID: {'✅ Set' if app_id else '❌ Not set'} ({len(app_id) if app_id else 0} chars)")
    print(f"   EDAMAM_APP_KEY: {'✅ Set' if app_key else '❌ Not set'} ({len(app_key) if app_key else 0} chars)")
    print(f"   EDAMAM_USER_ID: {'✅ Set' if user_id else '⚠️  Not set (will use App ID)'} ({len(user_id) if user_id else 0} chars)")
    
    if not app_id or not app_key:
        print("⚠️  Edamam credentials not found in environment variables.")
        print("\n📋 Step-by-step setup:")
        print("   1. Go to: https://developer.edamam.com/admin/applications")
        print("   2. Click 'Create a new application'")
        print("   3. Select 'Recipe Search API' (NOT Food Database API)")
        print("   4. Copy your Application ID and Application Key")
        print("\n   5. Set environment variables:")
        print("      export EDAMAM_APP_ID='your_app_id_here'")
        print("      export EDAMAM_APP_KEY='your_app_key_here'")
        print("\n   OR enter them now:")
        app_id = input("\nEdamam App ID: ").strip()
        app_key = input("Edamam App Key: ").strip()
        user_id_input = input("Edamam User ID (optional, press Enter if not needed): ").strip()
        if user_id_input:
            user_id = user_id_input
    
    if not app_id or not app_key:
        print("❌ Credentials required. Exiting.")
        return
    
    # Remove quotes if user accidentally included them
    app_id = app_id.strip('"').strip("'").strip()
    app_key = app_key.strip('"').strip("'").strip()
    if user_id:
        user_id = user_id.strip('"').strip("'").strip()
    
    # Additional validation
    if len(app_id) < 8:
        print(f"\n⚠️  Warning: App ID seems too short ({len(app_id)} characters)")
        print("   Edamam App IDs are typically 16-32 characters long.")
        print("   Please verify you copied the complete Application ID.")
    
    if len(app_key) < 16:
        print(f"\n⚠️  Warning: App Key seems too short ({len(app_key)} characters)")
        print("   Edamam App Keys are typically 32+ characters long.")
        print("   Please verify you copied the complete Application Key.")
    
    tester = EdamamTester(app_id, app_key, user_id=user_id)
    
    # First, test authentication
    if not tester.test_authentication():
        print("\n❌ Authentication failed. Please check your credentials.")
        print("\nCommon issues:")
        print("   1. Using wrong API credentials (Food Database vs Recipe Search)")
        print("   2. Credentials have extra spaces or quotes")
        print("   3. Application not activated in Edamam dashboard")
        print("   4. API quota exceeded (check dashboard)")
        return
    
    # Test Case 1: Vegetarian Breakfast
    print("\n" + "="*60)
    print("TEST CASE 1: Vegetarian Breakfast (Quick)")
    print("="*60)
    candidates1 = tester.search_recipes(
        meal_type="breakfast",
        dietary=["vegetarian"],
        prep_time_max=30,
        count=5
    )
    tester.print_candidates(candidates1)
    
    # Test Case 2: Vegan Lunch
    print("\n\n" + "="*60)
    print("TEST CASE 2: Vegan Lunch (High Protein)")
    print("="*60)
    print("💡 Note: Combining 'diet: high-protein' (>50% calories from protein) with")
    print("   'health: vegan' is very restrictive. Most vegan recipes don't meet this threshold.")
    print("   The API will return 0 results if the combination is too strict.\n")
    
    # Try with high-protein diet filter first
    candidates2 = tester.search_recipes(
        meal_type="lunch",
        dietary=["vegan"],
        preferences=["high-protein"],
        count=5
    )
    
    # If no results, try without the diet filter (just vegan + query string)
    # In production, we'd let the LLM choose high-protein candidates from vegan results
    if not candidates2:
        print("⚠️  No results with diet filter. Trying without diet filter...")
        print("   (In production, LLM would select high-protein candidates from vegan results)")
        candidates2 = tester.search_recipes(
            meal_type="lunch",
            dietary=["vegan"],
            preferences=[],  # Remove high-protein from preferences
            count=5
        )
        if candidates2:
            print("✅ Found vegan recipes (LLM can filter/select high-protein ones)")
    
    tester.print_candidates(candidates2)
    
    # Test Case 3: Gluten-Free Dinner
    print("\n\n" + "="*60)
    print("TEST CASE 3: Gluten-Free Dinner (Quick)")
    print("="*60)
    candidates3 = tester.search_recipes(
        meal_type="dinner",
        dietary=["gluten-free"],
        prep_time_max=45,
        count=5
    )
    tester.print_candidates(candidates3)
    
    # Summary
    print("\n\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"✅ Test Case 1: {len(candidates1)} candidates")
    print(f"✅ Test Case 2: {len(candidates2)} candidates")
    print(f"✅ Test Case 3: {len(candidates3)} candidates")
    print("\n🎉 All tests completed!")


if __name__ == "__main__":
    main()

