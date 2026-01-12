"""
Natural language query parser using OpenAI
Extracts meal plan requirements from user queries
"""
import json
import re
from typing import Dict, List, Optional
from openai import OpenAI
from app.config import settings


class QueryParser:
    """Parse natural language queries to extract meal plan requirements"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
    
    def parse(self, query: str) -> Dict:
        """
        Parse natural language query to extract structured requirements
        
        Returns:
            {
                "duration_days": int (1-7),
                "dietary_restrictions": List[str],
                "preferences": List[str],
                "special_requirements": List[str],
                "contradictions": List[str] (if any)
            }
        """
        # First, use LLM to extract structured information
        try:
            parsed = self._parse_with_llm(query)
            # Validate and clean up
            parsed = self._validate_and_clean(parsed)
            return parsed
        except Exception as e:
            # Fallback to regex-based parsing
            print(f"LLM parsing failed: {e}, using fallback")
            return self._parse_with_regex(query)
    
    def _parse_with_llm(self, query: str) -> Dict:
        """Use OpenAI to parse query with structured output"""
        system_prompt = """You are a meal plan query parser. Extract structured information from natural language queries about meal plans.

Extract:
- duration_days: Number of days (1-7, default 3 if not specified)
- dietary_restrictions: List of restrictions (vegan, vegetarian, gluten-free, dairy-free, nut-free, etc.)
- preferences: List of preferences (high-protein, low-carb, keto, paleo, Mediterranean, etc.)
- special_requirements: List of special requirements (budget-friendly, quick meals, under 15 minutes, etc.)
- contradictions: List any contradictory requirements (e.g., "vegan pescatarian")

Return valid JSON only."""
        
        user_prompt = f"""Parse this meal plan query: "{query}"

Return a JSON object with:
{{
  "duration_days": <int 1-7>,
  "dietary_restrictions": [<list of restrictions>],
  "preferences": [<list of preferences>],
  "special_requirements": [<list of special requirements>],
  "contradictions": [<list of contradictions if any>]
}}"""
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    
    def _validate_and_clean(self, parsed: Dict) -> Dict:
        """Validate and clean parsed results"""
        # Ensure duration is between 1-7
        duration = parsed.get("duration_days", 3)
        if isinstance(duration, str):
            # Extract number from string
            numbers = re.findall(r'\d+', duration)
            duration = int(numbers[0]) if numbers else 3
        duration = max(1, min(7, int(duration)))
        
        # Normalize lists
        dietary_restrictions = parsed.get("dietary_restrictions", [])
        if isinstance(dietary_restrictions, str):
            dietary_restrictions = [dietary_restrictions]
        
        preferences = parsed.get("preferences", [])
        if isinstance(preferences, str):
            preferences = [preferences]
        
        special_requirements = parsed.get("special_requirements", [])
        if isinstance(special_requirements, str):
            special_requirements = [special_requirements]
        
        contradictions = parsed.get("contradictions", [])
        if isinstance(contradictions, str):
            contradictions = [contradictions]
        
        return {
            "duration_days": duration,
            "dietary_restrictions": list(set(dietary_restrictions)) if dietary_restrictions else [],
            "preferences": list(set(preferences)) if preferences else [],
            "special_requirements": list(set(special_requirements)) if special_requirements else [],
            "contradictions": list(set(contradictions)) if contradictions else []
        }
    
    def _parse_with_regex(self, query: str) -> Dict:
        """Fallback regex-based parsing"""
        query_lower = query.lower()
        
        # Extract duration
        duration = 3  # default
        duration_match = re.search(r'(\d+)\s*day', query_lower)
        if duration_match:
            duration = int(duration_match.group(1))
        elif 'week' in query_lower or '7' in query_lower:
            duration = 7
        
        duration = max(1, min(7, duration))
        
        # Extract dietary restrictions
        restrictions = []
        restriction_keywords = {
            'vegan': 'vegan',
            'vegetarian': 'vegetarian',
            'gluten-free': 'gluten-free',
            'dairy-free': 'dairy-free',
            'nut-free': 'nut-free',
            'pescatarian': 'pescatarian',
            'paleo': 'paleo',
            'keto': 'keto'
        }
        
        for keyword, restriction in restriction_keywords.items():
            if keyword in query_lower:
                restrictions.append(restriction)
        
        # Extract preferences
        preferences = []
        if 'high protein' in query_lower or 'high-protein' in query_lower:
            preferences.append('high-protein')
        if 'low carb' in query_lower or 'low-carb' in query_lower:
            preferences.append('low-carb')
        if 'mediterranean' in query_lower:
            preferences.append('mediterranean')
        
        # Extract special requirements
        special = []
        if 'budget' in query_lower or 'cheap' in query_lower:
            special.append('budget-friendly')
        if 'quick' in query_lower or 'fast' in query_lower or '15 minute' in query_lower:
            special.append('quick-meals')
        
        return {
            "duration_days": duration,
            "dietary_restrictions": restrictions,
            "preferences": preferences,
            "special_requirements": special,
            "contradictions": []
        }

