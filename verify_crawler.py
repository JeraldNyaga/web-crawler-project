"""
Tests for crawler functionality.
"""
import pytest
from datetime import datetime

from crawler.models.book import Book
from crawler.models.crawlstate import CrawlState
from crawler.utils import (
    extract_price,
    extract_rating,
    extract_availability_number,
    clean_text,
    build_absolute_url
)
from crawler.parser import BookParser


class TestUtils:
    """Test utility functions."""
    
    def test_extract_price(self):
        """Test price extraction."""
        assert extract_price("£51.77") == 51.77
        assert extract_price("$12.34") == 12.34
        assert extract_price("€99.99") == 99.99
        assert extract_price("£1,234.56") == 1234.56
        assert extract_price("") == 0.0
        assert extract_price("invalid") == 0.0
    
    def test_extract_rating(self):
        """Test rating extraction."""
        assert extract_rating("star-rating One") == 1
        assert extract_rating("star-rating Two") == 2
        assert extract_rating("star-rating Three") == 3
        assert extract_rating("star-rating Four") == 4
        assert extract_rating("star-rating Five") == 5
        assert extract_rating("invalid") == 0
    
    def test_extract_availability_number(self):
        """Test availability number extraction."""
        assert extract_availability_number("In stock (22 available)") == 22
        assert extract_availability_number("In stock (5 available)") == 5
        assert extract_availability_number("In stock") == 1
        assert extract_availability_number("Out of stock") == 0
    
    def test_clean_text(self):
        """Test text cleaning."""
        assert clean_text("  Hello   World  ") == "Hello World"
        assert clean_text("Line1\nLine2") == "Line1 Line2"
        assert clean_text("") == ""
        assert clean_text(None) == ""
    
    def test_build_absolute_url(self):
        """Test URL building."""
        base = "https://books.toscrape.com"
        
        # Normal relative URL
        assert build_absolute_url(base, "catalogue/book.html") == \
               "https://books.toscrape.com/catalogue/book.html"
        
        # URL with ../
        result = build_absolute_url(base, "../catalogue/book.html")
        assert "catalogue/book.html" in result


class TestBookModel:
    """Test Book Pydantic model."""
    
    def test_book_creation(self):
        """Test creating a valid book."""
        book = Book(
            url="https://books.toscrape.com/catalogue/book_1/index.html",
            title="Test Book",
            description="A test book",
            category="Fiction",
            price_excl_tax=45.50,
            price_incl_tax=50.00,
            availability="In stock (10 available)",
            num_reviews=5,
            image_url="https://books.toscrape.com/media/image.jpg",
            rating=4
        )
        
        assert book.title == "Test Book"
        assert book.rating == 4
        assert book.price_incl_tax == 50.00
    
    def test_book_validation(self):
        """Test book validation."""
        # Invalid rating
        with pytest.raises(ValueError):
            Book(
                url="https://test.com",
                title="Test",
                category="Fiction",
                price_excl_tax=10.0,
                price_incl_tax=10.0,
                availability="In stock",
                num_reviews=0,
                image_url="https://test.com/img.jpg",
                rating=6  # Invalid: > 5
            )
        
        # Negative price
        with pytest.raises(ValueError):
            Book(
                url="https://test.com",
                title="Test",
                category="Fiction",
                price_excl_tax=-10.0,
                price_incl_tax=10.0,
                availability="In stock",
                num_reviews=0,
                image_url="https://test.com/img.jpg",
                rating=4
            )
    
    def test_content_hash_generation(self):
        """Test content hash generation."""
        book1 = Book(
            url="https://test.com",
            title="Test Book",
            category="Fiction",
            price_excl_tax=10.0,
            price_incl_tax=10.0,
            availability="In stock",
            num_reviews=5,
            image_url="https://test.com/img.jpg",
            rating=4
        )
        
        book2 = Book(
            url="https://test.com",
            title="Test Book",
            category="Fiction",
            price_excl_tax=10.0,
            price_incl_tax=10.0,
            availability="In stock",
            num_reviews=5,
            image_url="https://test.com/img.jpg",
            rating=4
        )
        
        # Same content should produce same hash
        assert book1.generate_content_hash() == book2.generate_content_hash()
        
        # Different price should produce different hash
        book2.price_incl_tax = 15.0
        assert book1.generate_content_hash() != book2.generate_content_hash()


class TestCrawlState:
    """Test CrawlState model."""
    
    def test_crawl_state_creation(self):
        """Test creating crawl state."""
        state = CrawlState(
            last_category="Fiction",
            last_page=5,
            total_books_crawled=100
        )
        
        assert state.last_category == "Fiction"
        assert state.last_page == 5
        assert state.total_books_crawled == 100
        assert state.status == "in_progress"


class TestBookParser:
    """Test BookParser."""
    
    def test_parser_initialization(self):
        """Test parser initialization."""
        parser = BookParser()
        assert parser.base_url == "https://books.toscrape.com"
        
        parser2 = BookParser("https://example.com")
        assert parser2.base_url == "https://example.com"
    
    def test_parse_category_page_empty(self):
        """Test parsing empty category page."""
        parser = BookParser()
        html = "<html><body></body></html>"
        books = parser.parse_category_page(html)
        assert books == []
    
    def test_has_next_page_no_pagination(self):
        """Test checking for next page when there is none."""
        parser = BookParser()
        html = "<html><body></body></html>"
        next_page = parser.has_next_page(html)
        assert next_page is None


# Integration tests would go here
# These require actual HTTP requests or mocking


@pytest.mark.asyncio
class TestCrawlerIntegration:
    """Integration tests for crawler (require network/mocks)."""
    
    async def test_crawler_initialization(self):
        """Test crawler initialization."""
        from crawler import BookCrawler
        
        crawler = BookCrawler()
        assert crawler.base_url == "https://books.toscrape.com"
        assert crawler.stats['total_books'] == 0