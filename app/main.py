"""
FastAPI application - Main entry point
"""
from fastapi import FastAPI, HTTPException, status, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from app.models import MealPlanRequest, MealPlanResponse, ErrorResponse, HealthResponse
from app.meal_generator import MealPlanGenerator
from app.config import settings
from app.rate_limiter import limiter, check_system_rate_limit, rate_limit_handler
from app.database import init_db, get_db, save_user_preference, get_user_preferences
from app.query_parser import QueryParser
from slowapi.errors import RateLimitExceeded

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

# Attach limiter to app
app.state.limiter = limiter

# Add rate limit exception handler
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize meal generator (will use config default)
meal_generator = MealPlanGenerator()
query_parser = QueryParser()

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup"""
    init_db()
    logger.info("Database initialized")


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


@app.get("/api/user/{user_id}/preferences", tags=["User Preferences"])
async def get_user_preferences_endpoint(
    user_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get recent meal plan preferences for a user
    
    Args:
        user_id: User identifier
        limit: Maximum number of preferences to return (default: 10)
    
    Returns:
        List of user preferences with meal plan history
    """
    try:
        preferences = get_user_preferences(db, user_id, limit)
        
        return {
            "user_id": user_id,
            "count": len(preferences),
            "preferences": [
                {
                    "id": pref.id,
                    "query": pref.query,
                    "meal_plan_id": pref.meal_plan_id,
                    "dietary_restrictions": pref.dietary_restrictions,
                    "preferences": pref.preferences,
                    "special_requirements": pref.special_requirements,
                    "created_at": pref.created_at.isoformat()
                }
                for pref in preferences
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching user preferences: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user preferences: {str(e)}"
        )


@app.post(
    "/api/generate-meal-plan",
    response_model=MealPlanResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    tags=["Meal Plans"]
)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def generate_meal_plan(request: Request, request_body: MealPlanRequest):
    """
    Generate a personalized meal plan from a natural language query.
    
    The query can include:
    - Duration (1-7 days)
    - Dietary restrictions (vegan, vegetarian, gluten-free, etc.)
    - Preferences (high-protein, low-carb, etc.)
    - Special requirements (budget-friendly, quick meals, etc.)
    
    Optional Parameters:
    - generation_mode: Recipe generation strategy ("llm_only", "rag", or "hybrid")
      If not provided, uses server default from RECIPE_GENERATION_MODE config.
    
    Example queries:
    - "Create a 5-day vegetarian meal plan with high protein"
    - "I need a 3-day gluten-free meal plan, exclude dairy and nuts"
    - "Generate a week of low-carb meals for two people, budget-friendly"
    
    Rate Limits:
    - 10 requests per minute per IP address
    - System-wide rate limiting applies
    """
    try:
        # Check system-wide rate limit
        if not check_system_rate_limit():
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded. Try again later."
                }
            )
        
        logger.info(f"Received meal plan request: {request_body.query[:100]}...")
        
        # Validate query
        if not request_body.query or len(request_body.query.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query cannot be empty"
            )
        
        # Parse query to extract preferences (for storage)
        parsed = query_parser.parse(request_body.query)
        
        # Use request-specific mode if provided, otherwise use default generator
        generation_mode = request_body.generation_mode
        if generation_mode:
            # Validate mode
            valid_modes = ["llm_only", "rag", "hybrid", "fast_llm"]
            if generation_mode not in valid_modes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid generation_mode: {generation_mode}. Must be one of: {', '.join(valid_modes)}"
                )
            # Create a temporary generator with the requested mode
            from app.meal_generator import MealPlanGenerator
            temp_generator = MealPlanGenerator(strategy_mode=generation_mode)
            meal_plan = await temp_generator.generate(request_body.query)
        else:
            # Use default generator (uses config setting)
            meal_plan = await meal_generator.generate(request_body.query)
        
        # Save user preference if user_id is provided
        if request_body.user_id:
            try:
                # Create a new database session
                from app.database import SessionLocal
                db = SessionLocal()
                try:
                    save_user_preference(
                        db=db,
                        user_id=request_body.user_id,
                        query=request_body.query,
                        meal_plan_id=meal_plan.get('meal_plan_id'),
                        dietary_restrictions=parsed.get('dietary_restrictions'),
                        preferences=parsed.get('preferences'),
                        special_requirements=parsed.get('special_requirements')
                    )
                    logger.info(f"Saved preference for user: {request_body.user_id}")
                finally:
                    db.close()
            except Exception as e:
                # Log error but don't fail the request
                logger.warning(f"Failed to save user preference: {str(e)}")
        
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

