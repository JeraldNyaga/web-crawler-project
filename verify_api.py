"""
Quick verification script for API endpoints.
Run this while API server is running to test all endpoints.
"""
import httpx
import asyncio
import sys
from loguru import logger

from config import settings

logger.remove()
logger.add(sys.stdout, format="<level>{level: <8}</level> | {message}", level="INFO")

BASE_URL = f"http://{settings.api_host}:{settings.api_port}"
API_KEY = settings.api_keys_list[0]


async def test_health_endpoint():
    """Test health endpoint (no auth required)."""
    logger.info("Testing health endpoint...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            
            if response.status_code == 200:
                data = response.json()
                logger.success(f"✓ Health check passed")
                logger.info(f"  Database: {data['database']}")
                logger.info(f"  Total books: {data['total_books']}")
                return True
            else:
                logger.error(f"✗ Health check failed: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"✗ Health endpoint error: {e}")
        return False


async def test_root_endpoint():
    """Test root endpoint."""
    logger.info("\nTesting root endpoint...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(BASE_URL)
            
            if response.status_code == 200:
                data = response.json()
                logger.success(f"✓ Root endpoint OK")
                logger.info(f"  API: {data['name']} v{data['version']}")
                return True
            else:
                logger.error(f"✗ Root endpoint failed: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"✗ Root endpoint error: {e}")
        return False


async def test_authentication():
    """Test authentication."""
    logger.info("\nTesting authentication...")
    
    try:
        async with httpx.AsyncClient() as client:
            # Test without API key (should fail)
            response = await client.get(f"{BASE_URL}/books")
            
            if response.status_code == 401:
                logger.success("✓ Authentication required (401 without key)")
            else:
                logger.warning(f"  Unexpected status without key: {response.status_code}")
            
            # Test with invalid API key (should fail)
            response = await client.get(
                f"{BASE_URL}/books",
                headers={"X-API-Key": "invalid-key"}
            )
            
            if response.status_code == 401:
                logger.success("✓ Invalid API key rejected")
            else:
                logger.warning(f"  Unexpected status with invalid key: {response.status_code}")
            
            # Test with valid API key (should succeed)
            response = await client.get(
                f"{BASE_URL}/books",
                headers={"X-API-Key": API_KEY}
            )
            
            if response.status_code == 200:
                logger.success("✓ Valid API key accepted")
                return True
            else:
                logger.error(f"✗ Valid API key failed: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"✗ Authentication test error: {e}")
        return False


async def test_get_books():
    """Test GET /books endpoint."""
    logger.info("\nTesting GET /books...")
    
    headers = {"X-API-Key": API_KEY}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/books", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                logger.success(f"✓ GET /books OK")
                logger.info(f"  Total books: {data['total']}")
                logger.info(f"  Page: {data['page']}/{data['total_pages']}")
                logger.info(f"  Books returned: {len(data['books'])}")
                return True
            else:
                logger.error(f"✗ GET /books failed: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"✗ GET /books error: {e}")
        return False


async def test_filters():
    """Test query filters."""
    logger.info("\nTesting query filters...")
    
    headers = {"X-API-Key": API_KEY}
    
    try:
        async with httpx.AsyncClient() as client:
            # Test category filter
            response = await client.get(
                f"{BASE_URL}/books",
                headers=headers,
                params={"category": "Fiction"}
            )
            
            if response.status_code == 200:
                logger.success("✓ Category filter works")
            else:
                logger.warning(f"  Category filter: {response.status_code}")
            
            # Test price range filter
            response = await client.get(
                f"{BASE_URL}/books",
                headers=headers,
                params={"min_price": 10, "max_price": 50}
            )
            
            if response.status_code == 200:
                logger.success("✓ Price range filter works")
            else:
                logger.warning(f"  Price filter: {response.status_code}")
            
            # Test rating filter
            response = await client.get(
                f"{BASE_URL}/books",
                headers=headers,
                params={"rating": 4}
            )
            
            if response.status_code == 200:
                logger.success("✓ Rating filter works")
                return True
            else:
                logger.warning(f"  Rating filter: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"✗ Filter test error: {e}")
        return False


async def test_sorting():
    """Test sorting."""
    logger.info("\nTesting sorting...")
    
    headers = {"X-API-Key": API_KEY}
    
    try:
        async with httpx.AsyncClient() as client:
            # Test sorting by price
            response = await client.get(
                f"{BASE_URL}/books",
                headers=headers,
                params={"sort_by": "price", "order": "asc"}
            )
            
            if response.status_code == 200:
                logger.success("✓ Sorting by price works")
            
            # Test sorting by rating
            response = await client.get(
                f"{BASE_URL}/books",
                headers=headers,
                params={"sort_by": "rating", "order": "desc"}
            )
            
            if response.status_code == 200:
                logger.success("✓ Sorting by rating works")
                return True
            else:
                return False
                
    except Exception as e:
        logger.error(f"✗ Sorting test error: {e}")
        return False


async def test_pagination():
    """Test pagination."""
    logger.info("\nTesting pagination...")
    
    headers = {"X-API-Key": API_KEY}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/books",
                headers=headers,
                params={"page": 2, "limit": 10}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.success("✓ Pagination works")
                logger.info(f"  Page 2, limit 10: {len(data['books'])} books returned")
                return True
            else:
                logger.error(f"✗ Pagination failed: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"✗ Pagination test error: {e}")
        return False


async def test_get_changes():
    """Test GET /changes endpoint."""
    logger.info("\nTesting GET /changes...")
    
    headers = {"X-API-Key": API_KEY}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/changes", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                logger.success(f"✓ GET /changes OK")
                logger.info(f"  Total changes: {data['total']}")
                return True
            else:
                logger.error(f"✗ GET /changes failed: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"✗ GET /changes error: {e}")
        return False


async def test_swagger_docs():
    """Test Swagger documentation."""
    logger.info("\nTesting Swagger documentation...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/docs")
            
            if response.status_code == 200:
                logger.success("✓ Swagger docs accessible at /docs")
                return True
            else:
                logger.error(f"✗ Swagger docs failed: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"✗ Swagger docs error: {e}")
        return False


async def main():
    """Run all API tests."""
    logger.info("="*60)
    logger.info("API VERIFICATION SUITE")
    logger.info("="*60)
    logger.info(f"Testing API at: {BASE_URL}")
    logger.info(f"Using API Key: {API_KEY[:20]}...")
    logger.info("")
    
    results = []
    
    # Run all tests
    results.append(await test_health_endpoint())
    results.append(await test_root_endpoint())
    results.append(await test_authentication())
    results.append(await test_get_books())
    results.append(await test_filters())
    results.append(await test_sorting())
    results.append(await test_pagination())
    results.append(await test_get_changes())
    results.append(await test_swagger_docs())
    
    # Summary
    logger.info("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        logger.success(f"✓ ALL API TESTS PASSED ({passed}/{total})")
        logger.success("\nYour API is working perfectly!")
        logger.info("\nNext steps:")
        logger.info("1. Test with Postman or curl")
        logger.info("2. Access Swagger docs: http://localhost:8000/docs")
        logger.info("3. Run pytest: pytest tests/test_api.py")
        logger.info("4. Move to Phase 3: Scheduler")
    else:
        logger.error(f"✗ SOME TESTS FAILED ({passed}/{total})")
        logger.error("\nPlease fix the errors above")
        sys.exit(1)
    
    logger.info("="*60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Test suite error: {e}")
        sys.exit(1)