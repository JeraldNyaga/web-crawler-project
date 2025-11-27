"""
Rate limiting for API endpoints.
"""
from typing import Dict
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Request
from loguru import logger

from config import settings


class RateLimiter:
    """
    Simple in-memory rate limiter.
    Tracks requests per API key.
    """
    
    def __init__(self):
        """Initialize rate limiter."""
        self.requests: Dict[str, list] = {}
        self.max_requests = settings.rate_limit_requests
        self.time_window = settings.rate_limit_period  # seconds
    
    def is_allowed(self, api_key: str) -> tuple[bool, dict]:
        """
        Check if request is allowed for given API key.
        
        Args:
            api_key: API key to check
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        if not settings.rate_limit_enabled:
            return True, self._get_rate_limit_info(api_key, 0)
        
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.time_window)
        
        # Initialize if first request from this key
        if api_key not in self.requests:
            self.requests[api_key] = []
        
        # Clean old requests outside the time window
        self.requests[api_key] = [
            req_time for req_time in self.requests[api_key]
            if req_time > window_start
        ]
        
        # Check if limit exceeded
        current_count = len(self.requests[api_key])
        
        if current_count >= self.max_requests:
            # Calculate when the oldest request will expire
            oldest_request = min(self.requests[api_key])
            reset_time = oldest_request + timedelta(seconds=self.time_window)
            retry_after = int((reset_time - now).total_seconds())
            
            logger.warning(
                f"Rate limit exceeded for API key {api_key[:10]}... "
                f"({current_count}/{self.max_requests})"
            )
            
            return False, {
                "limit": self.max_requests,
                "remaining": 0,
                "reset": int(reset_time.timestamp()),
                "retry_after": max(retry_after, 1)
            }
        
        # Allow request and record it
        self.requests[api_key].append(now)
        remaining = self.max_requests - (current_count + 1)
        
        return True, self._get_rate_limit_info(api_key, remaining)
    
    def _get_rate_limit_info(self, api_key: str, remaining: int) -> dict:
        """Get rate limit info for headers."""
        now = datetime.utcnow()
        reset_time = now + timedelta(seconds=self.time_window)
        
        return {
            "limit": self.max_requests,
            "remaining": remaining,
            "reset": int(reset_time.timestamp())
        }
    
    def cleanup_old_entries(self):
        """Clean up old entries (can be called periodically)."""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.time_window)
        
        for api_key in list(self.requests.keys()):
            self.requests[api_key] = [
                req_time for req_time in self.requests[api_key]
                if req_time > window_start
            ]
            
            # Remove empty entries
            if not self.requests[api_key]:
                del self.requests[api_key]


# Global rate limiter instance
rate_limiter = RateLimiter()


async def check_rate_limit(request: Request, api_key: str) -> dict:
    """
    Check rate limit for API key.
    
    Args:
        request: FastAPI request object
        api_key: Validated API key
        
    Returns:
        Rate limit info dict
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    is_allowed, rate_info = rate_limiter.is_allowed(api_key)
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "message": f"Maximum {rate_info['limit']} requests per hour allowed",
                "retry_after": rate_info['retry_after']
            },
            headers={
                "X-RateLimit-Limit": str(rate_info['limit']),
                "X-RateLimit-Remaining": str(rate_info['remaining']),
                "X-RateLimit-Reset": str(rate_info['reset']),
                "Retry-After": str(rate_info['retry_after'])
            }
        )
    
    return rate_info