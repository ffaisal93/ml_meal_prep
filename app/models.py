"""
Pydantic models for request/response validation
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class MealPlanRequest(BaseModel):
    """Request model for meal plan generation"""
    query: str = Field(..., description="Natural language meal plan request", min_length=1)
    user_id: Optional[str] = Field(None, description="Optional user ID for preference tracking")
    generation_mode: Optional[str] = Field(None, description="Recipe generation mode: 'llm_only', 'rag', or 'hybrid'. If not provided, uses server default.")


class NutritionalInfo(BaseModel):
    """Nutritional information for a meal"""
    calories: int = Field(..., ge=0)
    protein: float = Field(..., ge=0, description="Protein in grams")
    carbs: float = Field(..., ge=0, description="Carbohydrates in grams")
    fat: float = Field(..., ge=0, description="Fat in grams")


class Meal(BaseModel):
    """Individual meal model"""
    meal_type: str = Field(..., description="breakfast, lunch, dinner, or snack")
    recipe_name: str
    description: str
    ingredients: List[str]
    nutritional_info: NutritionalInfo
    preparation_time: str
    instructions: str
    source: str = Field(default="AI Generated", description="Source of the recipe")


class DayMealPlan(BaseModel):
    """Meal plan for a single day"""
    day: int = Field(..., ge=1)
    date: str = Field(..., description="ISO date string")
    meals: List[Meal]


class MealPlanSummary(BaseModel):
    """Summary statistics for the meal plan"""
    total_meals: int
    dietary_compliance: List[str]
    estimated_cost: str
    avg_prep_time: str


class MealPlanResponse(BaseModel):
    """Complete meal plan response"""
    meal_plan_id: str
    duration_days: int = Field(..., ge=1, le=7)
    generated_at: str = Field(..., description="ISO timestamp")
    meal_plan: List[DayMealPlan]
    summary: MealPlanSummary
    warning: Optional[str] = Field(None, description="User-friendly warning message if contradictions were resolved")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str = "1.0.0"
    timestamp: str

