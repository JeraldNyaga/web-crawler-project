"""
Quick verification script to check crawler components.
Run this before running the full crawler.
"""
import asyncio
import sys
from loguru import logger

logger.remove()
logger.add(sys.stdout, format="<level>{level: <8}</level> | {message}", level="INFO")


async def verify_imports():
    """Verify all modules can be imported."""
    logger.info("Verifying imports...")
    
    try:
        from crawler import BookCrawler, BookParser
        from crawler.models.book import Book
        from crawler.utils import extract_price, extract_rating
        from database import db
        from config import settings
        logger.success("✓ All imports successful")
        return True
    except Exception as e:
        logger.error(f"✗ Import failed: {e}")
        return False


async def verify_models():
    """Verify Pydantic models work correctly."""
    logger.info("\nVerifying Pydantic models...")
    
    try:
        from crawler.models.book import Book
        
        book = Book(
            url="https://test.com",
            title="Test Book",
            category="Fiction",
            price_excl_tax=10.0,
            price_incl_tax=10.5,
            availability="In stock",
            num_reviews=5,
            image_url="https://test.com/img.jpg",
            rating=4
        )
        
        assert book.title == "Test Book"
        assert book.rating == 4
        
        # Test content hash
        hash1 = book.generate_content_hash()
        assert len(hash1) == 64  # SHA256 hash length
        
        logger.success("✓ Models working correctly")
        return True
        
    except Exception as e:
        logger.error(f"✗ Model verification failed: {e}")
        return False


async def verify_utils():
    """Verify utility functions."""
    logger.info("\nVerifying utility functions...")
    
    try:
        from crawler.utils import extract_price, extract_rating, clean_text
        
        # Test price extraction
        assert extract_price("£51.77") == 51.77
        assert extract_price("$12.34") == 12.34
        
        # Test rating extraction
        assert extract_rating("star-rating Four") == 4
        assert extract_rating("star-rating Five") == 5
        
        # Test text cleaning
        assert clean_text("  Hello   World  ") == "Hello World"
        
        logger.success("✓ Utility functions working correctly")
        return True
        
    except Exception as e:
        logger.error(f"✗ Utility verification failed: {e}")
        return False


async def verify_database():
    """Verify database connection."""
    logger.info("\nVerifying database connection...")
    
    try:
        from database import db
        
        await db.connect()
        logger.success("✓ Database connection successful")
        
        # Test write
        test_doc = {
            "test": "verification",
            "timestamp": "2025-11-26"
        }
        await db.db.test_verification.insert_one(test_doc)
        logger.success("✓ Database write successful")
        
        # Test read
        doc = await db.db.test_verification.find_one({"test": "verification"})
        assert doc is not None
        logger.success("✓ Database read successful")
        
        # Cleanup
        await db.db.test_verification.delete_many({})
        logger.success("✓ Database cleanup successful")
        
        await db.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"✗ Database verification failed: {e}")
        logger.error("Make sure MongoDB URI is correct in .env")
        return False


async def verify_parser():
    """Verify HTML parser."""
    logger.info("\nVerifying HTML parser...")
    
    try:
        from crawler.parser import BookParser
        
        parser = BookParser()
        assert parser.base_url == "https://books.toscrape.com"
        
        # Test simple HTML parsing
        html = """
        <html>
            <body>
                <article class="product_pod">
                    <h3><a href="catalogue/book_1/index.html">Test Book</a></h3>
                </article>
            </body>
        </html>
        """
        
        books = parser.parse_category_page(html)
        assert len(books) == 1
        assert "catalogue/book_1/index.html" in books[0]
        
        logger.success("✓ HTML parser working correctly")
        return True
        
    except Exception as e:
        logger.error(f"✗ Parser verification failed: {e}")
        return False


async def verify_crawler_init():
    """Verify crawler can be initialized."""
    logger.info("\nVerifying crawler initialization...")
    
    try:
        from crawler import BookCrawler
        
        crawler = BookCrawler()
        assert crawler.base_url == "https://books.toscrape.com"
        assert crawler.stats['total_books'] == 0
        
        logger.success("✓ Crawler initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Crawler initialization failed: {e}")
        return False


async def main():
    """Run all verifications."""
    logger.info("="*60)
    logger.info("CRAWLER VERIFICATION SUITE")
    logger.info("="*60)
    
    results = []
    
    # Run all checks
    results.append(await verify_imports())
    results.append(await verify_models())
    results.append(await verify_utils())
    results.append(await verify_database())
    results.append(await verify_parser())
    results.append(await verify_crawler_init())
    
    # Summary
    logger.info("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        logger.success(f"✓ ALL CHECKS PASSED ({passed}/{total})")
        logger.success("\nYour crawler is ready to run!")
        logger.info("\nNext steps:")
        logger.info("1. Run crawler: python main.py crawl")
        logger.info("2. Check logs: tail -f logs/app.log")
        logger.info("3. Monitor progress in terminal")
    else:
        logger.error(f"✗ SOME CHECKS FAILED ({passed}/{total})")
        logger.error("\nPlease fix the errors above before running crawler")
        sys.exit(1)
    
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())