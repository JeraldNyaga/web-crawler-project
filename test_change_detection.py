"""
Manual test script for change detection.
This script simulates changes and tests the detection logic.
"""
import asyncio
from datetime import datetime
from loguru import logger

from database import db
from scheduler.change_detector import ChangeDetector


async def simulate_price_change():
    """Simulate a price change for testing."""
    logger.info("Simulating price change...")
    
    # Get a random book from database
    books = await db.get_all_books()
    
    if not books:
        logger.error("No books in database. Run crawler first.")
        return
    
    test_book = books[0]
    logger.info(f"Using book: {test_book['title']}")
    logger.info(f"Current price: £{test_book['price_incl_tax']}")
    
    # Create detector
    detector = ChangeDetector()
    
    # Simulate new book data with changed price
    new_book = test_book.copy()
    new_book['price_incl_tax'] = test_book['price_incl_tax'] * 0.9  # 10% discount
    
    logger.info(f"Simulated new price: £{new_book['price_incl_tax']}")
    
    # Detect changes
    changes = await detector.compare_and_log_changes(test_book, new_book)
    
    if changes:
        logger.success(f"Detected {len(changes)} change(s):")
        for change in changes:
            logger.info(f"  - {change['change_type']}: {change['old_value']} → {change['new_value']}")
    else:
        logger.info("No changes detected")
    
    return changes


async def test_report_generation():
    """Test report generation."""
    logger.info("\nTesting report generation...")
    
    detector = ChangeDetector()
    
    # Generate JSON report
    logger.info("Generating JSON report...")
    json_report = await detector.generate_change_report(format='json', limit=10)
    logger.info(f"JSON Report (truncated):\n{json_report[:500]}...")
    
    # Generate CSV report
    logger.info("\nGenerating CSV report...")
    csv_report = await detector.generate_change_report(format='csv', limit=10)
    logger.info(f"CSV Report (first 10 lines):")
    for line in csv_report.split('\n')[:10]:
        logger.info(f"  {line}")


async def test_multiple_changes():
    """Test detection of multiple types of changes."""
    logger.info("\nTesting multiple change types...")
    
    books = await db.get_all_books()
    
    if len(books) < 1:
        logger.error("Need at least 1 book in database")
        return
    
    test_book = books[0]
    detector = ChangeDetector()
    
    # Simulate multiple changes
    new_book = test_book.copy()
    new_book['price_incl_tax'] = test_book['price_incl_tax'] * 1.1  # Price increase
    new_book['availability'] = 'Out of stock'  # Availability change
    new_book['rating'] = min(5, test_book.get('rating', 3) + 1)  # Rating increase
    new_book['num_reviews'] = test_book.get('num_reviews', 0) + 5  # More reviews
    
    logger.info(f"Book: {test_book['title']}")
    logger.info("Simulated changes:")
    logger.info(f"  Price: £{test_book['price_incl_tax']} → £{new_book['price_incl_tax']}")
    logger.info(f"  Availability: {test_book['availability']} → {new_book['availability']}")
    logger.info(f"  Rating: {test_book.get('rating')} → {new_book['rating']}")
    logger.info(f"  Reviews: {test_book.get('num_reviews')} → {new_book['num_reviews']}")
    
    # Detect all changes
    changes = await detector.compare_and_log_changes(test_book, new_book)
    
    logger.success(f"\nDetected {len(changes)} change(s)")
    logger.info(f"Stats: {detector.stats}")


async def view_recent_changes():
    """View recent changes from database."""
    logger.info("\nViewing recent changes from database...")
    
    changes = await db.get_recent_changes(limit=20)
    
    if not changes:
        logger.info("No changes found in database")
        return
    
    logger.info(f"Found {len(changes)} recent change(s):\n")
    
    for i, change in enumerate(changes, 1):
        logger.info(f"{i}. {change.get('change_type', 'unknown')}")
        logger.info(f"   Changed at: {change.get('changed_at')}")
        logger.info(f"   Old value: {change.get('old_value')}")
        logger.info(f"   New value: {change.get('new_value')}")
        logger.info("")


async def main():
    """Run all tests."""
    logger.info("="*60)
    logger.info("Change Detection Test Suite")
    logger.info("="*60)
    logger.info("")
    
    try:
        # Connect to database
        await db.connect()
        logger.success("Connected to database\n")
        
        # Test 1: Simulate single price change
        logger.info("TEST 1: Single Price Change")
        logger.info("-"*60)
        await simulate_price_change()
        
        # Test 2: Multiple changes
        logger.info("\n" + "="*60)
        logger.info("TEST 2: Multiple Change Types")
        logger.info("-"*60)
        await test_multiple_changes()
        
        # Test 3: Report generation
        logger.info("\n" + "="*60)
        logger.info("TEST 3: Report Generation")
        logger.info("-"*60)
        await test_report_generation()
        
        # Test 4: View recent changes
        logger.info("\n" + "="*60)
        logger.info("TEST 4: Recent Changes from Database")
        logger.info("-"*60)
        await view_recent_changes()
        
        logger.info("\n" + "="*60)
        logger.success("All tests completed!")
        logger.info("="*60)
        
    except Exception as e:
        logger.exception(f"Test failed: {e}")
    finally:
        await db.disconnect()
        logger.info("Disconnected from database")


if __name__ == "__main__":
    asyncio.run(main())