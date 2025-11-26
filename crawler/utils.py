"""
Utility functions for the crawler.
"""
import asyncio
from typing import Callable, Any, Optional
from functools import wraps
from loguru import logger
import re

from config import settings


def retry_async(max_retries: int = None, delay: int = None, backoff: float = 2.0):
    """
    Decorator for retrying async functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay on each retry
    """
    max_retries = max_retries or settings.crawler_max_retries
    delay = delay or settings.crawler_retry_delay
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_retries} retries failed for {func.__name__}: {e}"
                        )
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    return decorator


def extract_price(price_str: str) -> float:
    """
    Extract numeric price from string.
    
    Args:
        price_str: Price string like "£51.77" or "£12.34"
        
    Returns:
        Float price value
        
    Example:
        >>> extract_price("£51.77")
        51.77
    """
    if not price_str:
        return 0.0
    
    # Remove currency symbols and whitespace
    clean_str = re.sub(r'[£$€,\s]', '', price_str)
    
    try:
        return float(clean_str)
    except ValueError:
        logger.warning(f"Could not parse price: {price_str}")
        return 0.0


def extract_rating(rating_class: str) -> int:
    """
    Extract star rating from CSS class.
    
    Args:
        rating_class: CSS class like "star-rating Three"
        
    Returns:
        Integer rating (1-5)
        
    Example:
        >>> extract_rating("star-rating Three")
        3
    """
    rating_map = {
        'One': 1,
        'Two': 2,
        'Three': 3,
        'Four': 4,
        'Five': 5
    }
    
    for word, value in rating_map.items():
        if word in rating_class:
            return value
    
    logger.warning(f"Could not parse rating from: {rating_class}")
    return 0


def extract_availability_number(availability_str: str) -> int:
    """
    Extract number of available items from availability string.
    
    Args:
        availability_str: String like "In stock (22 available)"
        
    Returns:
        Number of items available
        
    Example:
        >>> extract_availability_number("In stock (22 available)")
        22
    """
    if not availability_str:
        return 0
    
    # Match numbers in parentheses
    match = re.search(r'\((\d+)\s+available\)', availability_str)
    if match:
        return int(match.group(1))
    
    # If "In stock" but no number, assume available
    if "in stock" in availability_str.lower():
        return 1
    
    return 0


def extract_number_from_text(text: str) -> int:
    """
    Extract integer from text string.
    
    Args:
        text: Text containing number
        
    Returns:
        Extracted integer or 0 if not found
    """
    if not text:
        return 0
    
    match = re.search(r'\d+', text)
    if match:
        return int(match.group())
    return 0


def clean_text(text: Optional[str]) -> str:
    """
    Clean and normalize text content.
    
    Args:
        text: Raw text content
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def build_absolute_url(base_url: str, relative_url: str) -> str:
    """
    Build absolute URL from base and relative URLs.
    
    Args:
        base_url: Base URL (e.g., "https://books.toscrape.com")
        relative_url: Relative URL (e.g., "catalogue/book_123/index.html")
        
    Returns:
        Absolute URL
    """
    # Remove trailing slash from base
    base_url = base_url.rstrip('/')
    
    # Remove leading slash from relative
    relative_url = relative_url.lstrip('/')
    
    # Handle URLs that go up directories (../)
    if relative_url.startswith('../'):
        # Count how many levels up
        levels_up = relative_url.count('../')
        # Remove ../ from relative URL
        relative_url = relative_url.replace('../', '')
        
        # For books.toscrape.com, we typically need to add /catalogue/
        if 'catalogue' not in relative_url:
            relative_url = 'catalogue/' + relative_url
    
    return f"{base_url}/{relative_url}"


def is_valid_book_url(url: str) -> bool:
    """
    Check if URL is a valid book page URL.
    
    Args:
        url: URL to check
        
    Returns:
        True if valid book URL
    """
    # Book URLs contain "catalogue" and end with index.html
    return 'catalogue' in url and url.endswith('index.html')


async def fetch_with_retry(client, url: str) -> Optional[str]:
    """
    Fetch URL content with retry logic.
    
    Args:
        client: httpx.AsyncClient instance
        url: URL to fetch
        
    Returns:
        Page content as string or None if failed
    """
    @retry_async()
    async def _fetch():
        response = await client.get(url, timeout=settings.crawler_timeout)
        response.raise_for_status()
        return response.text
    
    try:
        return await _fetch()
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None