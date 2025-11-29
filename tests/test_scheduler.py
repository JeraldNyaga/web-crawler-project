"""
Tests for scheduler functionality.
"""
import pytest
from datetime import datetime

from scheduler.change_detector import ChangeDetector
from scheduler.scheduler import ChangeDetectionScheduler
from database import db


@pytest.fixture(scope="function")
async def db_connection():
    """Fixture to connect and disconnect database for each test."""
    await db.connect()
    yield db
    await db.disconnect()


class TestChangeDetector:
    """Test change detector functionality."""
    
    def test_detector_initialization(self):
        """Test change detector can be initialized."""
        detector = ChangeDetector()
        assert detector.stats['new_books'] == 0
        assert detector.stats['price_changes'] == 0
        assert detector.stats['total_changes'] == 0
    
    @pytest.mark.asyncio
    async def test_compare_no_changes(self, db_connection):
        """Test comparison when no changes exist."""
        detector = ChangeDetector()
        
        old_book = {
            '_id': 'test123',
            'url': 'https://test.com/book',
            'title': 'Test Book',
            'price_incl_tax': 10.99,
            'availability': 'In stock',
            'rating': 4,
            'num_reviews': 5
        }
        
        new_book = old_book.copy()
        
        changes = await detector.compare_and_log_changes(old_book, new_book)
        
        # No changes should be detected
        assert len(changes) == 0
        assert detector.stats['price_changes'] == 0
    
    @pytest.mark.asyncio
    async def test_detect_price_change(self, db_connection):
        """Test price change detection."""
        detector = ChangeDetector()
        
        old_book = {
            '_id': 'test123',
            'url': 'https://test.com/book',
            'title': 'Test Book',
            'price_incl_tax': 10.99,
            'availability': 'In stock',
            'rating': 4,
            'num_reviews': 5
        }
        
        new_book = old_book.copy()
        new_book['price_incl_tax'] = 8.99  # Price decreased
        
        changes = await detector.compare_and_log_changes(old_book, new_book)
        
        # Should detect price change
        assert len(changes) == 1
        assert changes[0]['change_type'] == 'price_change'
        assert changes[0]['old_value'] == 10.99
        assert changes[0]['new_value'] == 8.99
        assert detector.stats['price_changes'] == 1
    
    @pytest.mark.asyncio
    async def test_detect_multiple_changes(self, db_connection):
        """Test detection of multiple changes."""
        detector = ChangeDetector()
        
        old_book = {
            '_id': 'test123',
            'url': 'https://test.com/book',
            'title': 'Test Book',
            'price_incl_tax': 10.99,
            'availability': 'In stock',
            'rating': 4,
            'num_reviews': 5
        }
        
        new_book = old_book.copy()
        new_book['price_incl_tax'] = 8.99
        new_book['availability'] = 'Out of stock'
        new_book['rating'] = 5
        
        changes = await detector.compare_and_log_changes(old_book, new_book)
        
        # Should detect all three changes
        assert len(changes) == 3
        assert detector.stats['price_changes'] == 1
        assert detector.stats['availability_changes'] == 1
        assert detector.stats['rating_changes'] == 1
        assert detector.stats['total_changes'] == 3
    
    @pytest.mark.asyncio
    async def test_generate_json_report(self, db_connection):
        """Test JSON report generation."""
        detector = ChangeDetector()
        
        report = await detector.generate_change_report(format='json', limit=10)
        
        assert report is not None
        assert isinstance(report, str)
        
        # Should be valid JSON
        import json
        data = json.loads(report)
        
        assert 'generated_at' in data
        assert 'total_changes' in data
        assert 'changes' in data
    
    @pytest.mark.asyncio
    async def test_generate_csv_report(self, db_connection):
        """Test CSV report generation."""
        detector = ChangeDetector()
        
        report = await detector.generate_change_report(format='csv', limit=10)
        
        assert report is not None
        assert isinstance(report, str)
        
        # Should contain CSV header
        assert 'Change Type' in report
        assert 'Book URL' in report


class TestScheduler:
    """Test scheduler functionality."""
    
    def test_scheduler_initialization(self):
        """Test scheduler can be initialized."""
        scheduler = ChangeDetectionScheduler()
        assert scheduler.scheduler is not None
        assert scheduler.detector is not None
    
    def test_schedule_setup(self):
        """Test schedule setup."""
        from config import settings
        
        # Temporarily enable scheduler
        original = settings.scheduler_enabled
        settings.scheduler_enabled = True
        
        try:
            scheduler = ChangeDetectionScheduler()
            scheduler.setup_schedule()
            
            # Check job was added
            jobs = scheduler.scheduler.get_jobs()
            assert len(jobs) > 0
            assert jobs[0].id == 'change_detection_job'
        finally:
            settings.scheduler_enabled = original
    
    @pytest.mark.asyncio
    async def test_run_once(self, db_connection):
        """Test running detection once."""
        scheduler = ChangeDetectionScheduler()
        
        # Should not raise error
        await scheduler.run_once()


@pytest.mark.asyncio
class TestIntegration:
    """Integration tests for scheduler."""
    
    async def test_full_change_detection_flow(self):
        """Test complete change detection flow."""
        # Connect to database
        await db.connect()
        
        try:
            # Run change detection
            detector = ChangeDetector()
            stats = await detector.detect_changes()
            
            # Stats should be populated
            assert 'new_books' in stats
            assert 'price_changes' in stats
            assert 'total_changes' in stats
            
        finally:
            await db.disconnect()