"""
FastAPI application - Main entry point
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging

from app.models import MealPlanRequest, MealPlanResponse, ErrorResponse, HealthResponse
from app.meal_generator import MealPlanGenerator
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Meal Planner API",
    description="Generate personalized meal plans using AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize meal generator
meal_generator = MealPlanGenerator()


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint"""
    return {
        "message": "AI Meal Planner API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint for deployment monitoring"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


@app.post(
    "/api/generate-meal-plan",
    response_model=MealPlanResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    tags=["Meal Plans"]
)
async def generate_meal_plan(request: MealPlanRequest):
    """
    Generate a personalized meal plan from a natural language query.
    
    The query can include:
    - Duration (1-7 days)
    - Dietary restrictions (vegan, vegetarian, gluten-free, etc.)
    - Preferences (high-protein, low-carb, etc.)
    - Special requirements (budget-friendly, quick meals, etc.)
    
    Example queries:
    - "Create a 5-day vegetarian meal plan with high protein"
    - "I need a 3-day gluten-free meal plan, exclude dairy and nuts"
    - "Generate a week of low-carb meals for two people, budget-friendly"
    """
    try:
        logger.info(f"Received meal plan request: {request.query[:100]}...")
        
        # Validate query
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query cannot be empty"
            )
        
        # Generate meal plan
        meal_plan = meal_generator.generate(request.query)
        
        logger.info(f"Successfully generated meal plan: {meal_plan['meal_plan_id']}")
        
        return meal_plan
        
    except ValueError as e:
        # Handle validation errors (e.g., contradictions)
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Error generating meal plan: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate meal plan: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred. Please try again later."
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )

