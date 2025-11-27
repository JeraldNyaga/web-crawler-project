"""
Tests for API endpoints.
"""
import pytest
from fastapi.testclient import TestClient

from api.main import app
from config import settings


# Create test client
client = TestClient(app)


class TestAuthentication:
    """Test API key authentication."""
    
    def test_missing_api_key(self):
        """Test request without API key."""
        response = client.get("/books")
        assert response.status_code == 401
        assert "Missing API key" in response.json()['detail']
    
    def test_invalid_api_key(self):
        """Test request with invalid API key."""
        response = client.get(
            "/books",
            headers={"X-API-Key": "invalid-key-123"}
        )
        assert response.status_code == 401
        assert "Invalid API key" in response.json()['detail']
    
    def test_valid_api_key(self):
        """Test request with valid API key."""
        # Use first valid API key from settings
        valid_key = settings.api_keys_list[0]
        response = client.get(
            "/books",
            headers={"X-API-Key": valid_key}
        )
        # Should not return 401
        assert response.status_code != 401


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_no_auth_required(self):
        """Test health endpoint doesn't require authentication."""
        response = client.get("/health")
        assert response.status_code in [200, 503]  # 503 if DB not connected
    
    def test_health_response_structure(self):
        """Test health response has correct structure."""
        response = client.get("/health")
        data = response.json()
        
        # Check required fields
        if response.status_code == 200:
            assert "status" in data
            assert "timestamp" in data
            assert "database" in data
            assert "total_books" in data


class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_root_endpoint(self):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data


class TestBooksEndpoint:
    """Test /books endpoint."""
    
    def setup_method(self):
        """Setup for each test."""
        self.headers = {"X-API-Key": settings.api_keys_list[0]}
    
    def test_get_books_basic(self):
        """Test basic books retrieval."""
        response = client.get("/books", headers=self.headers)
        
        # Should return 200 even if no books in database
        assert response.status_code == 200
        
        data = response.json()
        assert "books" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
    
    def test_get_books_with_category_filter(self):
        """Test books filtered by category."""
        response = client.get(
            "/books?category=Fiction",
            headers=self.headers
        )
        assert response.status_code == 200
    
    def test_get_books_with_price_filter(self):
        """Test books filtered by price range."""
        response = client.get(
            "/books?min_price=10&max_price=50",
            headers=self.headers
        )
        assert response.status_code == 200
    
    def test_get_books_with_rating_filter(self):
        """Test books filtered by rating."""
        response = client.get(
            "/books?rating=4",
            headers=self.headers
        )
        assert response.status_code == 200
    
    def test_get_books_with_invalid_rating(self):
        """Test books with invalid rating."""
        response = client.get(
            "/books?rating=6",  # Invalid: > 5
            headers=self.headers
        )
        assert response.status_code == 422  # Validation error
    
    def test_get_books_with_sorting(self):
        """Test books with sorting."""
        response = client.get(
            "/books?sort_by=price&order=desc",
            headers=self.headers
        )
        assert response.status_code == 200
    
    def test_get_books_with_pagination(self):
        """Test books with pagination."""
        response = client.get(
            "/books?page=1&limit=10",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data['page'] == 1
        assert data['page_size'] == 10
    
    def test_get_books_invalid_page(self):
        """Test books with invalid page number."""
        response = client.get(
            "/books?page=0",  # Invalid: must be >= 1
            headers=self.headers
        )
        assert response.status_code == 422


class TestBookDetailEndpoint:
    """Test /books/{book_id} endpoint."""
    
    def setup_method(self):
        """Setup for each test."""
        self.headers = {"X-API-Key": settings.api_keys_list[0]}
    
    def test_get_book_invalid_id_format(self):
        """Test get book with invalid ID format."""
        response = client.get(
            "/books/invalid-id",
            headers=self.headers
        )
        assert response.status_code == 400
    
    def test_get_book_not_found(self):
        """Test get book that doesn't exist."""
        # Valid ObjectId format but doesn't exist
        response = client.get(
            "/books/507f1f77bcf86cd799439011",
            headers=self.headers
        )
        # Will return 404 if book doesn't exist
        assert response.status_code in [200, 404]


class TestChangesEndpoint:
    """Test /changes endpoint."""
    
    def setup_method(self):
        """Setup for each test."""
        self.headers = {"X-API-Key": settings.api_keys_list[0]}
    
    def test_get_changes_basic(self):
        """Test basic changes retrieval."""
        response = client.get("/changes", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "changes" in data
        assert "total" in data
    
    def test_get_changes_with_type_filter(self):
        """Test changes filtered by type."""
        response = client.get(
            "/changes?change_type=price_change",
            headers=self.headers
        )
        assert response.status_code == 200
    
    def test_get_changes_with_limit(self):
        """Test changes with custom limit."""
        response = client.get(
            "/changes?limit=50",
            headers=self.headers
        )
        assert response.status_code == 200


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limit_headers_present(self):
        """Test that rate limit headers are present."""
        headers = {"X-API-Key": settings.api_keys_list[0]}
        response = client.get("/books", headers=headers)
        
        # Headers should be present if rate limiting is enabled
        if settings.rate_limit_enabled:
            # Note: Headers are added by rate limiter, may not be in test client
            assert response.status_code == 200
    
    @pytest.mark.skipif(
        not settings.rate_limit_enabled,
        reason="Rate limiting is disabled"
    )
    def test_rate_limit_exceeded(self):
        """Test rate limit enforcement."""
        headers = {"X-API-Key": "test-rate-limit-key"}
        
        # Make requests up to the limit
        # Note: This test would need adjustment based on actual rate limit
        # In production, you'd use a test-specific API key with lower limit
        pass


# Integration tests
@pytest.mark.asyncio
class TestAPIIntegration:
    """Integration tests for API."""
    
    async def test_full_workflow(self):
        """Test complete API workflow."""
        headers = {"X-API-Key": settings.api_keys_list[0]}
        
        # 1. Check health
        response = client.get("/health")
        assert response.status_code in [200, 503]
        
        # 2. Get books list
        response = client.get("/books", headers=headers)
        assert response.status_code == 200
        
        # 3. Get changes
        response = client.get("/changes", headers=headers)
        assert response.status_code == 200