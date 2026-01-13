"""
Query validation system for meal plan requests
Designed to be extended incrementally with new validation rules
"""
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of a validation check"""
    is_valid: bool
    message: Optional[str] = None
    corrected_value: Optional[any] = None


class QueryValidator:
    """
    Validates and corrects meal plan queries
    Can be extended with new validation rules incrementally
    """
    
    def __init__(self):
        self.validators = [
            self._validate_meal_count,
            self._validate_duration,
            self._validate_dietary_restrictions,
            self._validate_contradictions,
            self._validate_budget,
            self._validate_prep_time,
            # Add more validators here as needed
        ]
    
    def validate(self, query: str, parsed: Dict) -> Tuple[Dict, List[str]]:
        """
        Validate parsed query and return corrected values + warnings
        
        Args:
            query: Original query string
            parsed: Parsed query dictionary
            
        Returns:
            Tuple of (corrected_parsed_dict, list_of_warnings)
        """
        warnings = []
        corrected = parsed.copy()
        
        # Run all validators
        for validator in self.validators:
            result = validator(query, corrected)
            if not result.is_valid:
                if result.message:
                    warnings.append(result.message)
                if result.corrected_value is not None:
                    # Apply correction
                    if isinstance(result.corrected_value, dict):
                        corrected.update(result.corrected_value)
                    else:
                        # For simple corrections, validator should update dict directly
                        pass
        
        return corrected, warnings
    
    def _validate_meal_count(self, query: str, parsed: Dict) -> ValidationResult:
        """
        Extract and validate meal count from query
        Examples: "2 meals", "2 meals per day", "breakfast and lunch only"
        """
        query_lower = query.lower()
        
        # Pattern 1: Explicit meal count (e.g., "2 meals", "3 meals per day")
        meal_count_match = re.search(r'(\d+)\s*meals?', query_lower)
        if meal_count_match:
            meal_count = int(meal_count_match.group(1))
            if 1 <= meal_count <= 4:  # Reasonable range
                parsed['meals_per_day'] = meal_count
                return ValidationResult(is_valid=True)
            else:
                # Clamp to valid range
                meal_count = max(1, min(4, meal_count))
                parsed['meals_per_day'] = meal_count
                return ValidationResult(
                    is_valid=False,
                    message=f"Meal count adjusted to {meal_count} (valid range: 1-4)",
                    corrected_value={'meals_per_day': meal_count}
                )
        
        # Pattern 2: Specific meal types mentioned (e.g., "breakfast and lunch only")
        meal_types_mentioned = []
        if 'breakfast' in query_lower:
            meal_types_mentioned.append('breakfast')
        if 'lunch' in query_lower:
            meal_types_mentioned.append('lunch')
        if 'dinner' in query_lower or 'supper' in query_lower:
            meal_types_mentioned.append('dinner')
        if 'snack' in query_lower:
            meal_types_mentioned.append('snack')
        
        if meal_types_mentioned:
            parsed['meals_per_day'] = len(meal_types_mentioned)
            parsed['meal_types'] = meal_types_mentioned
            return ValidationResult(is_valid=True)
        
        # Pattern 3: "only" keyword with meal type (e.g., "breakfast only")
        if 'only' in query_lower:
            if 'breakfast' in query_lower:
                parsed['meals_per_day'] = 1
                parsed['meal_types'] = ['breakfast']
                return ValidationResult(is_valid=True)
            elif 'lunch' in query_lower:
                parsed['meals_per_day'] = 1
                parsed['meal_types'] = ['lunch']
                return ValidationResult(is_valid=True)
            elif 'dinner' in query_lower:
                parsed['meals_per_day'] = 1
                parsed['meal_types'] = ['dinner']
                return ValidationResult(is_valid=True)
        
        # Default: 3 meals if not specified
        if 'meals_per_day' not in parsed:
            parsed['meals_per_day'] = 3
            parsed['meal_types'] = ['breakfast', 'lunch', 'dinner']
        
        return ValidationResult(is_valid=True)
    
    def _validate_duration(self, query: str, parsed: Dict) -> ValidationResult:
        """Validate duration is within acceptable range"""
        duration = parsed.get('duration_days', 3)
        
        if duration < 1:
            parsed['duration_days'] = 1
            return ValidationResult(
                is_valid=False,
                message="Duration adjusted to minimum 1 day",
                corrected_value={'duration_days': 1}
            )
        
        if duration > 7:
            parsed['duration_days'] = 7
            return ValidationResult(
                is_valid=False,
                message="Duration adjusted to maximum 7 days",
                corrected_value={'duration_days': 7}
            )
        
        return ValidationResult(is_valid=True)
    
    def _validate_dietary_restrictions(self, query: str, parsed: Dict) -> ValidationResult:
        """Validate dietary restrictions are reasonable"""
        restrictions = parsed.get('dietary_restrictions', [])
        
        # Check for too many restrictions (might be contradictory)
        if len(restrictions) > 5:
            return ValidationResult(
                is_valid=False,
                message=f"Many dietary restrictions specified ({len(restrictions)}). Some may conflict."
            )
        
        return ValidationResult(is_valid=True)
    
    def _validate_contradictions(self, query: str, parsed: Dict) -> ValidationResult:
        """Check for contradictory requirements"""
        restrictions = set(parsed.get('dietary_restrictions', []))
        contradictions = parsed.get('contradictions', [])
        
        # Known contradictions
        known_contradictions = [
            ('vegan', 'pescatarian'),
            ('vegan', 'vegetarian'),  # Actually not contradictory, but check
            ('keto', 'high-carb'),
            ('low-carb', 'high-carb'),
        ]
        
        for restriction in restrictions:
            for known_pair in known_contradictions:
                if restriction in known_pair:
                    other = known_pair[1] if known_pair[0] == restriction else known_pair[0]
                    if other in restrictions or other in parsed.get('preferences', []):
                        contradictions.append(f"{restriction} and {other}")
        
        if contradictions:
            parsed['contradictions'] = list(set(contradictions))
            return ValidationResult(
                is_valid=False,
                message=f"Contradictory requirements detected: {', '.join(contradictions)}"
            )
        
        return ValidationResult(is_valid=True)
    
    def _validate_budget(self, query: str, parsed: Dict) -> ValidationResult:
        """Validate and extract budget constraints"""
        query_lower = query.lower()
        
        # Extract budget keywords
        budget_keywords = {
            'budget-friendly': ['budget', 'cheap', 'affordable', 'low cost', 'inexpensive'],
            'moderate': ['moderate', 'reasonable', 'average'],
            'premium': ['premium', 'expensive', 'luxury', 'gourmet', 'high-end']
        }
        
        budget_level = None
        for level, keywords in budget_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                budget_level = level
                break
        
        if budget_level:
            if 'budget_level' not in parsed.get('special_requirements', []):
                special_requirements = parsed.get('special_requirements', [])
                # Remove any existing budget keywords
                special_requirements = [req for req in special_requirements 
                                      if req not in ['budget-friendly', 'moderate', 'premium']]
                special_requirements.append(budget_level)
                parsed['special_requirements'] = special_requirements
                return ValidationResult(
                    is_valid=True,
                    message=f"Budget constraint applied: {budget_level}"
                )
        
        return ValidationResult(is_valid=True)
    
    def _validate_prep_time(self, query: str, parsed: Dict) -> ValidationResult:
        """Validate and extract preparation time requirements"""
        query_lower = query.lower()
        
        # Extract time constraints
        time_patterns = [
            (r'(\d+)\s*minute', 'minutes'),
            (r'(\d+)\s*min', 'minutes'),
            (r'under\s*(\d+)', 'minutes'),
            (r'less\s*than\s*(\d+)', 'minutes'),
            (r'(\d+)\s*minute\s*or\s*less', 'minutes'),
        ]
        
        prep_time_max = None
        for pattern, unit in time_patterns:
            match = re.search(pattern, query_lower)
            if match:
                prep_time_max = int(match.group(1))
                break
        
        # Check for quick meal keywords
        quick_keywords = ['quick', 'fast', 'easy', 'simple', '15 minute', '30 minute']
        if any(keyword in query_lower for keyword in quick_keywords):
            if prep_time_max is None:
                # Default quick meal time
                if '15 minute' in query_lower or '15 min' in query_lower:
                    prep_time_max = 15
                elif '30 minute' in query_lower or '30 min' in query_lower:
                    prep_time_max = 30
                else:
                    prep_time_max = 30  # Default for "quick"
        
        if prep_time_max:
            parsed['prep_time_max'] = prep_time_max
            special_requirements = parsed.get('special_requirements', [])
            if 'quick-meals' not in special_requirements and prep_time_max <= 30:
                special_requirements.append('quick-meals')
            parsed['special_requirements'] = special_requirements
            return ValidationResult(
                is_valid=True,
                message=f"Preparation time constraint: {prep_time_max} minutes max"
            )
        
        return ValidationResult(is_valid=True)


# Global validator instance
validator = QueryValidator()

