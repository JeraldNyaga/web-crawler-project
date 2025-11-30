"""
Change detection logic for monitoring book updates.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger
from crawler.parser import BookParser
from database import db
from crawler.utils import fetch_with_retry
from crawler.models.book import Book
from crawler.scraper import BookCrawler
import httpx

class ChangeDetector:
    """Detect and log changes in book data."""
    
    def __init__(self):
        """Initialize change detector."""
        self.stats = {
            'new_books': 0,
            'price_changes': 0,
            'availability_changes': 0,
            'rating_changes': 0,
            'total_changes': 0
        }
    
    async def detect_changes(self):
        """
        Main change detection process.
        
        1. Crawl website
        2. Compare with existing data
        3. Log changes
        4. Update database
        """
        logger.info("Starting change detection process...")
        
        try:
            # Get current books from database
            existing_books = await self._get_existing_books()
            logger.info(f"Found {len(existing_books)} existing books in database")
            
            # Crawl website for current data
            logger.info("Crawling website for latest data...")
            crawler = BookCrawler()
            
            # Store current books temporarily
            current_books = {}
            
            # Get fresh data (this will be handled by crawler)
            # For now, we'll detect changes in existing books
            await self._detect_changes_in_books(existing_books)
            
            # Print summary
            self._print_summary()
            
            return self.stats
            
        except Exception as e:
            logger.error(f"Change detection failed: {e}")
            raise
    
    async def _get_existing_books(self) -> Dict[str, Dict]:
        """Get all existing books from database as a dict keyed by URL."""
        books = await db.get_all_books()
        return {book['url']: book for book in books}
    
    async def _detect_changes_in_books(self, existing_books: Dict[str, Dict]):
        """
        Detect changes by re-crawling and comparing.
        
        Args:
            existing_books: Dictionary of existing books keyed by URL
        """
        # For each book, we would re-fetch and compare
        # This is a placeholder - full implementation would re-crawl each book
        logger.info("Change detection on existing books...")
        
        # In a real scenario, you would:
        # 1. Re-crawl each book URL
        # 2. Compare with stored data
        # 3. Log changes
        
        # For now, we'll create a method that can be called when new data arrives
        pass
    
    async def compare_and_log_changes(
        self,
        old_book: Dict[str, Any],
        new_book: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Compare old and new book data and log changes.
        
        Args:
            old_book: Existing book data from database
            new_book: Newly crawled book data
            
        Returns:
            List of change records
        """
        changes = []
        book_id = old_book.get('_id')
        book_url = old_book.get('url')
        
        # Check price changes
        if old_book.get('price_incl_tax') != new_book.get('price_incl_tax'):
            change = await self._log_change(
                book_id=book_id,
                change_type='price_change',
                old_value=old_book.get('price_incl_tax'),
                new_value=new_book.get('price_incl_tax'),
                book_url=book_url
            )
            changes.append(change)
            self.stats['price_changes'] += 1
            logger.info(
                f"Price changed: {old_book.get('title')} "
                f"£{old_book.get('price_incl_tax')} → £{new_book.get('price_incl_tax')}"
            )
        
        # Check availability changes
        if old_book.get('availability') != new_book.get('availability'):
            change = await self._log_change(
                book_id=book_id,
                change_type='availability_change',
                old_value=old_book.get('availability'),
                new_value=new_book.get('availability'),
                book_url=book_url
            )
            changes.append(change)
            self.stats['availability_changes'] += 1
            logger.info(
                f"Availability changed: {old_book.get('title')} "
                f"{old_book.get('availability')} → {new_book.get('availability')}"
            )
        
        # Check rating changes
        if old_book.get('rating') != new_book.get('rating'):
            change = await self._log_change(
                book_id=book_id,
                change_type='rating_change',
                old_value=old_book.get('rating'),
                new_value=new_book.get('rating'),
                book_url=book_url
            )
            changes.append(change)
            self.stats['rating_changes'] += 1
            logger.info(
                f"Rating changed: {old_book.get('title')} "
                f"{old_book.get('rating')} → {new_book.get('rating')} stars"
            )
        
        # Check review count changes
        if old_book.get('num_reviews') != new_book.get('num_reviews'):
            change = await self._log_change(
                book_id=book_id,
                change_type='reviews_change',
                old_value=old_book.get('num_reviews'),
                new_value=new_book.get('num_reviews'),
                book_url=book_url
            )
            changes.append(change)
            logger.info(
                f"Reviews changed: {old_book.get('title')} "
                f"{old_book.get('num_reviews')} → {new_book.get('num_reviews')} reviews"
            )
        
        return changes
    
    async def detect_new_book(self, book_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Detect and log a new book.
        
        Args:
            book_data: New book data
            
        Returns:
            Change record if new book
        """
        # Check if book exists
        existing = await db.get_book_by_url(book_data.get('url'))
        
        if not existing:
            # Log new book
            change = {
                'change_type': 'new_book',
                'book_url': book_data.get('url'),
                'new_value': {
                    'title': book_data.get('title'),
                    'category': book_data.get('category'),
                    'price': book_data.get('price_incl_tax')
                },
                'old_value': None
            }
            
            await db.log_change(change)
            self.stats['new_books'] += 1
            logger.success(f"New book detected: {book_data.get('title')}")
            
            return change
        
        return None
    
    async def _log_change(
        self,
        book_id: Any,
        change_type: str,
        old_value: Any,
        new_value: Any,
        book_url: str
    ) -> Dict[str, Any]:
        """
        Log a change to the database.
        
        Args:
            book_id: Book ID
            change_type: Type of change
            old_value: Previous value
            new_value: New value
            book_url: Book URL
            
        Returns:
            Change record
        """
        change_data = {
            'book_id': book_id,
            'change_type': change_type,
            'old_value': old_value,
            'new_value': new_value,
            'book_url': book_url,
            'detected_by': 'scheduler'
        }
        
        await db.log_change(change_data)
        self.stats['total_changes'] += 1
        
        return change_data
    
    def _print_summary(self):
        """Print change detection summary."""
        logger.info("\n" + "="*60)
        logger.info("CHANGE DETECTION SUMMARY")
        logger.info("="*60)
        logger.info(f"New books: {self.stats['new_books']}")
        logger.info(f"Price changes: {self.stats['price_changes']}")
        logger.info(f"Availability changes: {self.stats['availability_changes']}")
        logger.info(f"Rating changes: {self.stats['rating_changes']}")
        logger.info(f"Total changes: {self.stats['total_changes']}")
        logger.info("="*60 + "\n")
    
    async def generate_change_report(
        self,
        format: str = 'json',
        limit: int = 100
    ) -> str:
        """
        Generate a change report.
        
        Args:
            format: Report format ('json' or 'csv')
            limit: Number of changes to include
            
        Returns:
            Report as string
        """
        import json
        import csv
        from io import StringIO
        
        # Get recent changes
        changes = await db.get_recent_changes(limit=limit)
        
        if format == 'json':
            # JSON format
            report_data = {
                'generated_at': datetime.utcnow().isoformat(),
                'total_changes': len(changes),
                'changes': []
            }
            
            for change in changes:
                report_data['changes'].append({
                    'change_type': change.get('change_type'),
                    'book_url': change.get('book_url', ''),
                    'old_value': change.get('old_value'),
                    'new_value': change.get('new_value'),
                    'changed_at': change.get('changed_at').isoformat() if change.get('changed_at') else None
                })
            
            return json.dumps(report_data, indent=2)
        
        elif format == 'csv':
            # CSV format
            output = StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Change Type', 'Book URL', 'Old Value', 'New Value', 'Changed At'])
            
            # Write data
            for change in changes:
                writer.writerow([
                    change.get('change_type', ''),
                    change.get('book_url', ''),
                    str(change.get('old_value', '')),
                    str(change.get('new_value', '')),
                    change.get('changed_at').isoformat() if change.get('changed_at') else ''
                ])
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported format: {format}")
             
    async def _detect_changes_in_books(self, existing_books: list[dict]):
        """
        Re-fetch each stored book, parse it again, compare with the DB version,
        update changes, and log them.

        - Detects changed fields (price, availability, rating, etc.)
        - Updates DB when changes occur
        - Logs change events in the 'changes' collection
        """
        parser = BookParser()

        async with httpx.AsyncClient(timeout=15) as client:
            for stored in existing_books:
                url = stored["url"]

                # 1. Re-fetch the book page
                html = await self._fetch_and_parse_book(client, url)

                if not html:
                    self.logger.warning(f"Book unavailable or failed to fetch: {url}")
                    continue

                # 2. Parse new page content
                parsed = parser.parse_book_page(html, url=url)

                if not parsed.success or not parsed.book:
                    self.logger.warning(f"Parser failed for: {url}")
                    continue

                new_book: Book = parsed.book
                new_book.generate_content_hash()

                # 3. Compare content hash first (fastest check)
                if new_book.content_hash == stored.get("content_hash"):
                    continue  # No changes at all

                # 4. Field-by-field comparison
                changes = await self.compare_and_log_changes(stored, new_book)

                if changes:
                    # 5. Update stored record in DB
                    await self.db.update_existing_book(
                        book_id=stored["_id"],
                        updated_data=new_book.to_dict()
                    )

                    self.stats["total_changes"] += 1

        return True

    async def _fetch_and_parse_book(self, client: httpx.AsyncClient, url: str) -> str | None:
        """
        Fetches book HTML using retry logic.
        Returns the HTML or None if failed.
        """
        try:
            html = await fetch_with_retry(client, url)
            return html
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None
async def run_change_detection():
    """Convenience function to run change detection."""
    detector = ChangeDetector()
    return await detector.detect_changes()