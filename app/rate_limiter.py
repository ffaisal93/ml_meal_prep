"""
Rate limiting implementation using slowapi
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
from app.config import settings
import time
from threading import Lock

# Create limiter instance
limiter = Limiter(key_func=get_remote_address)

# System-wide rate limiting
_system_request_times = []
_system_lock = Lock()


def check_system_rate_limit() -> bool:
    """
    Check system-wide rate limit (max requests per second)
    Returns True if request is allowed, False if rate limited
    """
    if not settings.rate_limit_enabled:
        return True
    
    current_time = time.time()
    
    with _system_lock:
        # Remove requests older than 1 second
        _system_request_times[:] = [
            t for t in _system_request_times 
            if current_time - t < 1.0
        ]
        
        # Check if we're at the limit
        if len(_system_request_times) >= settings.rate_limit_system_max_rps:
            return False
        
        # Add current request
        _system_request_times.append(current_time)
        return True


async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded
    Returns HTTP 429 with the specified error message
    """
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded. Try again later."
        }
    )

