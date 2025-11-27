"""
Authentication middleware for API key validation.
"""
from typing import Optional
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from loguru import logger

from config import settings


# API Key header configuration
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def validate_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Validate API key from request header.
    
    Args:
        api_key: API key from X-API-Key header
        
    Returns:
        Validated API key
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    if not api_key:
        logger.warning("Request missing API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Please provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Check if API key is valid
    valid_keys = settings.api_keys_list
    
    if api_key not in valid_keys:
        logger.warning(f"Invalid API key attempt: {api_key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    logger.debug(f"Valid API key: {api_key[:10]}...")
    return api_key


def get_api_key_optional(api_key: str = Security(api_key_header)) -> Optional[str]:
    """
    Get API key without requiring it (for public endpoints).
    
    Args:
        api_key: API key from X-API-Key header
        
    Returns:
        API key if provided, None otherwise
    """
    return api_key