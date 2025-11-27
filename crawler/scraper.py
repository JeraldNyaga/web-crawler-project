"""
Main web crawler implementation with async support and robustness features.
"""
import asyncio
from typing import List, Optional
from datetime import datetime
import httpx
from loguru import logger

from .models.crawl_state import CrawlState
from .parser import BookParser
from .utils import fetch_with_retry
from database import db
from config import settings


class BookCrawler:
    """
    Async web crawler for books.toscrape.com with robustness features.
    """
    
    def __init__(self):
        """Initialize crawler."""
        self.base_url = settings.target_url
        self.parser = BookParser(self.base_url)
        self.concurrent_requests = settings.crawler_concurrent_requests
        self.user_agent = settings.crawler_user_agent
        
        # Statistics
        self.stats = {
            'total_books': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': None,
            'end_time': None
        }
    
    async def crawl(self, resume: bool = True):
        """
        Main crawl method - crawls entire website.
        
        Args:
            resume: Whether to resume from last crawl state
        """
        self.stats['start_time'] = datetime.utcnow()
        logger.info("Starting book crawler...")
        logger.info(f"Target URL: {self.base_url}")
        logger.info(f"Concurrent requests: {self.concurrent_requests}")
        
        try:
            async with httpx.AsyncClient(
                headers={'User-Agent': self.user_agent},
                timeout=settings.crawler_timeout,
                follow_redirects=True
            ) as client:
                
                # Check for existing crawl state
                crawl_state = None
                if resume:
                    crawl_state = await db.get_crawl_state()
                    if crawl_state:
                        logger.info(f"Resuming from previous crawl: {crawl_state.get('last_category')}")
                
                # Get all categories
                logger.info("Fetching categories...")
                homepage_html = await fetch_with_retry(client, self.base_url)
                
                if not homepage_html:
                    logger.error("Failed to fetch homepage")
                    return
                
                categories = self.parser.extract_categories(homepage_html)
                logger.info(f"Found {len(categories)} categories to crawl")
                
                # Crawl each category
                for category_name, category_url in categories:
                    # Skip if resuming and haven't reached last category yet
                    if crawl_state and crawl_state.get('last_category'):
                        if category_name != crawl_state['last_category']:
                            logger.info(f"Skipping category: {category_name} (already crawled)")
                            continue
                    
                    logger.info(f"\n{'='*60}")
                    logger.info(f"Crawling category: {category_name}")
                    logger.info(f"{'='*60}")
                    
                    await self._crawl_category(client, category_name, category_url, crawl_state)
                    
                    # Save progress after each category
                    await self._save_progress(category_name, None, 1)
                
                # Clear crawl state on successful completion
                await db.clear_crawl_state()
                
                self.stats['end_time'] = datetime.utcnow()
                self._print_summary()
                
        except Exception as e:
            logger.exception(f"Crawler failed with error: {e}")
            raise
    
    async def _crawl_category(
        self,
        client: httpx.AsyncClient,
        category_name: str,
        category_url: str,
        crawl_state: Optional[dict] = None
    ):
        """
        Crawl all books in a category, handling pagination.
        
        Args:
            client: HTTP client
            category_name: Name of the category
            category_url: URL of the category page
            crawl_state: Previous crawl state if resuming
        """
        current_url = category_url
        page_num = 1
        
        # Resume from last page if available
        if crawl_state and crawl_state.get('last_category') == category_name:
            page_num = crawl_state.get('last_page', 1)
            logger.info(f"Resuming from page {page_num}")
        
        while current_url:
            logger.info(f"Crawling page {page_num}: {current_url}")
            
            # Fetch page
            page_html = await fetch_with_retry(client, current_url)
            if not page_html:
                logger.error(f"Failed to fetch page: {current_url}")
                break
            
            # Extract book URLs from page
            book_urls = self.parser.parse_category_page(page_html)
            
            if not book_urls:
                logger.warning(f"No books found on page {page_num}")
                break
            
            # Crawl books with concurrency control
            await self._crawl_books_batch(client, book_urls, category_name)
            
            # Save progress after each page
            await self._save_progress(category_name, book_urls[-1] if book_urls else None, page_num)
            
            # Check for next page
            next_page_relative = self.parser.has_next_page(page_html)
            if next_page_relative:
                # Build absolute URL for next page
                # Remove the filename from current URL and add next page filename
                base = '/'.join(current_url.split('/')[:-1])
                current_url = f"{base}/{next_page_relative}"
                page_num += 1
            else:
                logger.info(f"No more pages in category: {category_name}")
                break
    
    async def _crawl_books_batch(
        self,
        client: httpx.AsyncClient,
        book_urls: List[str],
        category: str
    ):
        """
        Crawl a batch of books with concurrency control.
        
        Args:
            client: HTTP client
            book_urls: List of book URLs to crawl
            category: Category name for the books
        """
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.concurrent_requests)
        
        async def crawl_with_semaphore(url: str):
            async with semaphore:
                return await self._crawl_single_book(client, url, category)
        
        # Crawl all books concurrently (with limit)
        tasks = [crawl_with_semaphore(url) for url in book_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count results
        for result in results:
            if isinstance(result, Exception):
                self.stats['failed'] += 1
            elif result:
                self.stats['successful'] += 1
            else:
                self.stats['skipped'] += 1
    
    async def _crawl_single_book(
        self,
        client: httpx.AsyncClient,
        url: str,
        category: str
    ) -> bool:
        """
        Crawl a single book page.
        
        Args:
            client: HTTP client
            url: Book page URL
            category: Book category
            
        Returns:
            True if successful, False if skipped/failed
        """
        try:
            # Check if book already exists
            existing_book = await db.get_book_by_url(url)
            if existing_book:
                logger.debug(f"Book already exists: {url}")
                return False
            
            # Fetch book page
            html = await fetch_with_retry(client, url)
            if not html:
                logger.error(f"Failed to fetch book: {url}")
                return False
            
            # Parse book data
            parse_result = self.parser.parse_book_page(html, url)
            
            if not parse_result.success:
                logger.error(f"Failed to parse book {url}: {parse_result.error}")
                return False
            
            # Update category (parser might get it wrong from breadcrumb)
            book = parse_result.book
            book.category = category
            
            # Generate content hash
            book.content_hash = book.generate_content_hash()
            
            # Save to database
            book_dict = book.to_dict()
            result = await db.insert_book(book_dict)
            
            if result:
                self.stats['total_books'] += 1
                logger.success(f"Saved book: {book.title[:50]}...")
                return True
            else:
                # Already exists (race condition)
                return False
                
        except Exception as e:
            logger.error(f"Error crawling book {url}: {e}")
            return False
    
    async def _save_progress(
        self,
        category: str,
        last_book_url: Optional[str],
        page: int
    ):
        """
        Save crawl progress for resume capability.
        
        Args:
            category: Current category
            last_book_url: Last book URL processed
            page: Current page number
        """
        state = CrawlState(
            last_category=category,
            last_page=page,
            last_book_url=last_book_url,
            total_books_crawled=self.stats['total_books'],
            updated_at=datetime.utcnow(),
            status='in_progress'
        )
        
        await db.save_crawl_state(state.to_dict())
    
    def _print_summary(self):
        """Print crawl summary statistics."""
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        logger.info("\n" + "="*60)
        logger.info("CRAWL SUMMARY")
        logger.info("="*60)
        logger.info(f"Total books crawled: {self.stats['total_books']}")
        logger.info(f"Successful: {self.stats['successful']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Skipped (duplicates): {self.stats['skipped']}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Rate: {self.stats['total_books'] / duration:.2f} books/second")
        logger.info("="*60 + "\n")


async def run_crawler():
    """Convenience function to run the crawler."""
    crawler = BookCrawler()
    await crawler.crawl(resume=True)