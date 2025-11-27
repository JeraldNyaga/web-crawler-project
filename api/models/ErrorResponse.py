"""
API routes and endpoints.
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status, Request
from loguru import logger
from bson import ObjectId

from .auth import validate_api_key
from .rate_limiter import check_rate_limit
from .models import (
    BookResponse,
    BooksListResponse,
    ChangeResponse,
    ChangesListResponse,
    HealthResponse,
    ErrorResponse
)
from database import db


# Create router
router = APIRouter()


def format_book(book_dict: dict) -> dict:
    """Format book document for API response."""
    book_dict['id'] = str(book_dict.pop('_id'))
    # Remove raw_html and content_hash from response
    book_dict.pop('raw_html', None)
    book_dict.pop('content_hash', None)
    book_dict.pop('status', None)
    return book_dict


def format_change(change_dict: dict) -> dict:
    """Format change document for API response."""
    change_dict['id'] = str(change_dict.pop('_id'))
    if 'book_id' in change_dict and isinstance(change_dict['book_id'], ObjectId):
        change_dict['book_id'] = str(change_dict['book_id'])
    return change_dict


@router.get(
    "/books",
    response_model=BooksListResponse,
    summary="Get list of books",
    description="Retrieve books with optional filtering, sorting, and pagination",
    responses={
        200: {"description": "Successfully retrieved books"},
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_books(
    request: Request,
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price (inclusive)"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price (inclusive)"),
    rating: Optional[int] = Query(None, ge=1, le=5, description="Filter by rating (1-5)"),
    sort_by: Optional[str] = Query("title", regex="^(title|rating|price|num_reviews)$", description="Sort field"),
    order: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    api_key: str = Depends(validate_api_key)
):
    """
    Get books with filtering, sorting, and pagination.
    
    Requires valid API key in X-API-Key header.
    Rate limited to 100 requests per hour.
    """
    # Check rate limit
    await check_rate_limit(request, api_key)
    
    try:
        # Build query filter
        query = {}
        
        if category:
            query['category'] = category
        
        if min_price is not None or max_price is not None:
            query['price_incl_tax'] = {}
            if min_price is not None:
                query['price_incl_tax']['$gte'] = min_price
            if max_price is not None:
                query['price_incl_tax']['$lte'] = max_price
        
        if rating is not None:
            query['rating'] = rating
        
        # Count total matching documents
        total = await db.db.books.count_documents(query)
        
        # Build sort
        sort_field = sort_by if sort_by != "price" else "price_incl_tax"
        sort_direction = 1 if order == "asc" else -1
        
        # Calculate pagination
        skip = (page - 1) * limit
        total_pages = (total + limit - 1) // limit  # Ceiling division
        
        # Fetch books
        cursor = db.db.books.find(query).sort(sort_field, sort_direction).skip(skip).limit(limit)
        books = await cursor.to_list(length=limit)
        
        # Format books for response
        formatted_books = [format_book(book) for book in books]
        
        logger.info(
            f"GET /books - Returned {len(formatted_books)} books "
            f"(page {page}/{total_pages}, total: {total})"
        )
        
        return BooksListResponse(
            books=formatted_books,
            total=total,
            page=page,
            page_size=limit,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Error fetching books: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "DatabaseError", "message": "Failed to fetch books"}
        )


@router.get(
    "/books/{book_id}",
    response_model=BookResponse,
    summary="Get book by ID",
    description="Retrieve detailed information about a specific book",
    responses={
        200: {"description": "Successfully retrieved book"},
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"},
        404: {"model": ErrorResponse, "description": "Book not found"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"}
    }
)
async def get_book(
    request: Request,
    book_id: str,
    api_key: str = Depends(validate_api_key)
):
    """
    Get detailed information about a specific book.
    
    Requires valid API key in X-API-Key header.
    """
    # Check rate limit
    await check_rate_limit(request, api_key)
    
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(book_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "ValidationError", "message": "Invalid book ID format"}
            )
        
        # Fetch book
        book = await db.db.books.find_one({"_id": ObjectId(book_id)})
        
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NotFound", "message": f"Book with ID {book_id} not found"}
            )
        
        formatted_book = format_book(book)
        logger.info(f"GET /books/{book_id} - Returned book: {formatted_book.get('title')}")
        
        return formatted_book
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching book {book_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "DatabaseError", "message": "Failed to fetch book"}
        )


@router.get(
    "/changes",
    response_model=ChangesListResponse,
    summary="Get recent changes",
    description="Retrieve recent changes to books (price updates, new books, etc.)",
    responses={
        200: {"description": "Successfully retrieved changes"},
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"}
    }
)
async def get_changes(
    request: Request,
    change_type: Optional[str] = Query(None, description="Filter by change type"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of changes to return"),
    api_key: str = Depends(validate_api_key)
):
    """
    Get recent changes to books.
    
    Requires valid API key in X-API-Key header.
    """
    # Check rate limit
    await check_rate_limit(request, api_key)
    
    try:
        # Build query
        query = {}
        if change_type:
            query['change_type'] = change_type
        
        # Fetch changes (sorted by most recent first)
        cursor = db.db.changes.find(query).sort("changed_at", -1).limit(limit)
        changes = await cursor.to_list(length=limit)
        
        # Enrich changes with book titles
        for change in changes:
            if 'book_id' in change:
                book = await db.db.books.find_one({"_id": ObjectId(change['book_id'])})
                if book:
                    change['book_title'] = book.get('title')
        
        # Format changes
        formatted_changes = [format_change(change) for change in changes]
        
        logger.info(f"GET /changes - Returned {len(formatted_changes)} changes")
        
        return ChangesListResponse(
            changes=formatted_changes,
            total=len(formatted_changes)
        )
        
    except Exception as e:
        logger.error(f"Error fetching changes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "DatabaseError", "message": "Failed to fetch changes"}
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check API and database health status",
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy"}
    }
)
async def health_check():
    """
    Health check endpoint (no authentication required).
    
    Returns service status and database connection info.
    """
    try:
        # Check database connection
        await db.client.admin.command('ping')
        db_status = "connected"
        
        # Count total books
        total_books = await db.db.books.count_documents({})
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            database=db_status,
            total_books=total_books
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "timestamp": datetime.utcnow(),
                "database": "disconnected",
                "error": str(e)
            }
        )