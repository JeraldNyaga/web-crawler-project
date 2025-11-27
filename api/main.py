"""
Main FastAPI application.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from loguru import logger

from config import settings
from database import db
from .routes import router
from .rate_limiter import rate_limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting API server...")
    try:
        await db.connect()
        logger.success("Database connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down API server...")
    await db.disconnect()
    logger.info("Database disconnected")


# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="""
    # Books Crawler API
    
    RESTful API for accessing crawled book data from books.toscrape.com
    
    ## Authentication
    
    All endpoints (except `/health`) require API key authentication.
    
    Include your API key in the `X-API-Key` header:
    ```
    X-API-Key: your-api-key-here
    ```
    
    ## Rate Limiting
    
    - **Limit**: 100 requests per hour per API key
    - **Headers**: Rate limit info is included in response headers
      - `X-RateLimit-Limit`: Maximum requests allowed
      - `X-RateLimit-Remaining`: Requests remaining in current window
      - `X-RateLimit-Reset`: Unix timestamp when limit resets
    
    ## Features
    
    - **Book Search**: Filter by category, price range, rating
    - **Sorting**: Sort by title, price, rating, or number of reviews
    - **Pagination**: Efficient pagination for large result sets
    - **Change Tracking**: View recent updates to book data
    
    ## Example Usage
    
    ```bash
    # Get all books in Fiction category with rating >= 4
    curl -H "X-API-Key: demo-key-123" \
         "http://localhost:8000/books?category=Fiction&rating=4"
    
    # Get specific book by ID
    curl -H "X-API-Key: demo-key-123" \
         "http://localhost:8000/books/507f1f77bcf86cd799439011"
    
    # Get recent price changes
    curl -H "X-API-Key: demo-key-123" \
         "http://localhost:8000/changes?change_type=price_change"
    ```
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    errors = exc.errors()
    logger.warning(f"Validation error: {errors}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Invalid request parameters",
            "details": errors
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.exception(f"Unhandled exception: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "details": str(exc) if settings.is_development else None
        }
    )


# Middleware to add rate limit headers
@app.middleware("http")
async def add_rate_limit_headers(request: Request, call_next):
    """Add rate limit information to response headers."""
    response = await call_next(request)
    
    # Add rate limit headers if they exist in response
    if hasattr(response, 'headers'):
        # These would be set by the rate limiter
        pass
    
    return response


# Include routers
app.include_router(router, prefix="", tags=["Books"])


# Root endpoint
@app.get(
    "/",
    summary="API Root",
    description="Get API information and available endpoints"
)
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "status": "running",
        "documentation": "/docs",
        "endpoints": {
            "books": "/books",
            "book_detail": "/books/{book_id}",
            "changes": "/changes",
            "health": "/health"
        },
        "authentication": {
            "type": "API Key",
            "header": "X-API-Key",
            "description": "Include your API key in the X-API-Key header"
        },
        "rate_limit": {
            "requests": settings.rate_limit_requests,
            "period": f"{settings.rate_limit_period} seconds"
        }
    }


# Background task to cleanup rate limiter
from fastapi_utils.tasks import repeat_every

@app.on_event("startup")
@repeat_every(seconds=300)  # Every 5 minutes
async def cleanup_rate_limiter():
    """Periodically clean up old rate limiter entries."""
    rate_limiter.cleanup_old_entries()
    logger.debug("Rate limiter cleanup completed")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development
    )